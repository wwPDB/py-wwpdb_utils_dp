"""Hermetic unit tests for wwpdb.utils.dp.RunRemote job-status classification.

These mock subprocess and site-config calls, unlike RcsbDpUtilityRunRemoteTests.py, which is a
real-tool integration suite that submits actual Slurm jobs. Scope: get_job_status_by_id()'s
squeue/sacct fallback, _get_job_status_from_sacct()'s accounting-lag backoff, and monitor()'s
terminal-state handling.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.abspath(__file__)))

from wwpdb.utils.dp.RunRemote import JobStatus, RunRemote


def _make_run_remote(command="echo hi", run_dir=None):
    """Construct a real RunRemote instance without needing a live site-config environment.

    run_dir defaults to None (RunRemote auto-generates a /tmp/run_remote_* tempdir, matching
    RunRemote's own default), but retry-loop tests that call _cleanup() more than once should
    pass an explicit non-"/tmp/run_remote_"-prefixed run_dir, matching how RcsbDpUtility always
    supplies an explicit workflow-instance run_dir for the ValMod path in production -- _cleanup()
    is a no-op for those, same as it is live.
    """
    with mock.patch("wwpdb.utils.dp.RunRemote.getSiteId", return_value="WWPDB_DEPLOY_TEST"), mock.patch(
        "wwpdb.utils.dp.RunRemote.ConfigInfo"
    ) as mock_config_info:
        mock_config_info.return_value.get.return_value = "test_queue"
        return RunRemote(command=command, job_name="test_job", log_dir=tempfile.mkdtemp(), run_dir=run_dir)


def _sacct_json(job_id=12345, state=None):
    jobs = [{"job_id": job_id, "state": {"current": state}}] if state is not None else []
    return json.dumps({"jobs": jobs})


def _fake_subprocess_run(fake_squeue=None, fake_sacct_sequence=None):
    """Build a subprocess.run side_effect that dispatches on the command name.

    fake_squeue: (returncode, stdout_text) for the squeue call.
    fake_sacct_sequence: list of (returncode, stdout_text) consumed one per sacct call, in order.
    """
    sacct_iter = iter(fake_sacct_sequence or [])

    def _run(cmd, **_kwargs):
        if cmd[0] == "squeue":
            rc, stdout_text = fake_squeue
            return mock.Mock(returncode=rc, stdout=stdout_text.encode("utf-8"))
        if cmd[0] == "sacct":
            try:
                rc, stdout_text = next(sacct_iter)
            except StopIteration as exc:
                raise AssertionError("sacct called more times than fake_sacct_sequence provides") from exc
            if rc != 0:
                raise subprocess.CalledProcessError(rc, cmd)
            return mock.Mock(returncode=rc, stdout=stdout_text)
        raise AssertionError(f"unexpected command: {cmd}")

    return _run


class GetJobStatusByIdTests(unittest.TestCase):
    def setUp(self):
        self.run_remote = _make_run_remote()

    def test_squeue_classifies_directly_unchanged_behavior(self):
        """Regression guard: when squeue succeeds, its answer is used as-is, no sacct call."""
        fake_run = _fake_subprocess_run(fake_squeue=(0, "COMPLETED"))
        with mock.patch("wwpdb.utils.dp.RunRemote.subprocess.run", side_effect=fake_run) as mock_run:
            status = self.run_remote.get_job_status_by_id(12345)
        self.assertEqual(status, JobStatus.COMPLETED)
        self.assertEqual(mock_run.call_count, 1)  # only squeue, no sacct fallback

    def test_squeue_reports_oom_directly(self):
        fake_run = _fake_subprocess_run(fake_squeue=(0, "OUT_OF_MEMORY"))
        with mock.patch("wwpdb.utils.dp.RunRemote.subprocess.run", side_effect=fake_run):
            status = self.run_remote.get_job_status_by_id(12345)
        self.assertEqual(status, JobStatus.OOM)

    def test_squeue_forgets_job_falls_back_to_sacct_oom(self):
        """The diagnosed bug: squeue rc=1 for a reaped job; sacct still has OUT_OF_MEMORY."""
        fake_run = _fake_subprocess_run(
            fake_squeue=(1, "slurm_load_jobs error: Invalid job id specified"),
            fake_sacct_sequence=[(0, _sacct_json(state=["OUT_OF_MEMORY"]))],
        )
        with mock.patch("wwpdb.utils.dp.RunRemote.subprocess.run", side_effect=fake_run):
            status = self.run_remote.get_job_status_by_id(12345)
        self.assertEqual(status, JobStatus.OOM)

    def test_squeue_blank_output_falls_back_to_sacct(self):
        fake_run = _fake_subprocess_run(
            fake_squeue=(0, ""),
            fake_sacct_sequence=[(0, _sacct_json(state=["COMPLETED"]))],
        )
        with mock.patch("wwpdb.utils.dp.RunRemote.subprocess.run", side_effect=fake_run):
            status = self.run_remote.get_job_status_by_id(12345)
        self.assertEqual(status, JobStatus.COMPLETED)

    def test_squeue_and_sacct_both_fail_to_classify_returns_other(self):
        """Never fabricate a terminal state -- fall back to OTHER, not a false positive."""
        fake_run = _fake_subprocess_run(
            fake_squeue=(1, "slurm_load_jobs error: Invalid job id specified"),
            fake_sacct_sequence=[(0, _sacct_json(state=None))] * 3,  # empty jobs list every attempt
        )
        with mock.patch("wwpdb.utils.dp.RunRemote.subprocess.run", side_effect=fake_run), mock.patch(
            "wwpdb.utils.dp.RunRemote.time.sleep"
        ):
            status = self.run_remote.get_job_status_by_id(12345)
        self.assertEqual(status, JobStatus.OTHER)


class GetJobStatusFromSacctTests(unittest.TestCase):
    def setUp(self):
        self.run_remote = _make_run_remote()

    def test_backoff_on_empty_then_populated(self):
        """sacct accounting lag: empty jobs list on first attempt, populated on the second."""
        fake_run = _fake_subprocess_run(
            fake_sacct_sequence=[
                (0, _sacct_json(state=None)),
                (0, _sacct_json(state=["COMPLETED"])),
            ]
        )
        with mock.patch("wwpdb.utils.dp.RunRemote.subprocess.run", side_effect=fake_run) as mock_run, mock.patch(
            "wwpdb.utils.dp.RunRemote.time.sleep"
        ) as mock_sleep:
            status = self.run_remote._get_job_status_from_sacct(12345)  # noqa: SLF001
        self.assertEqual(status, JobStatus.COMPLETED)
        self.assertEqual(mock_run.call_count, 2)
        self.assertEqual(mock_sleep.call_count, 1)

    def test_never_classifies_after_max_attempts_returns_none(self):
        fake_run = _fake_subprocess_run(fake_sacct_sequence=[(0, _sacct_json(state=None))] * 3)
        with mock.patch("wwpdb.utils.dp.RunRemote.subprocess.run", side_effect=fake_run), mock.patch(
            "wwpdb.utils.dp.RunRemote.time.sleep"
        ):
            status = self.run_remote._get_job_status_from_sacct(12345, max_attempts=3, backoff=0)  # noqa: SLF001
        self.assertIsNone(status)


class MonitorTests(unittest.TestCase):
    def setUp(self):
        self.run_remote = _make_run_remote()

    def test_returns_terminal_status_without_extra_query_after_break(self):
        """Regression guard for the redundant re-query bug: monitor() must not call
        get_job_status_by_id() again after it already has a terminal status."""
        with mock.patch.object(
            self.run_remote, "get_job_status_by_id", side_effect=[JobStatus.RUNNING, JobStatus.RUNNING, JobStatus.COMPLETED]
        ) as mock_status, mock.patch("wwpdb.utils.dp.RunRemote.time.sleep"):
            status = self.run_remote.monitor(12345, frequency=0)
        self.assertEqual(status, JobStatus.COMPLETED)
        self.assertEqual(mock_status.call_count, 3)  # exactly the 3 polls, no extra call after break

    def test_returns_oom_status_without_extra_query_after_break(self):
        with mock.patch.object(self.run_remote, "get_job_status_by_id", side_effect=[JobStatus.RUNNING, JobStatus.OOM]) as mock_status:
            status = self.run_remote.monitor(12345, frequency=0)
        self.assertEqual(status, JobStatus.OOM)
        self.assertEqual(mock_status.call_count, 2)


class RedirectRundirForRetryTests(unittest.TestCase):
    def setUp(self):
        self.run_remote = _make_run_remote()

    def test_redirects_rundir_with_attempt_suffix(self):
        command = "python -m wwpdb.apps.validation.src.validator --mode annotate --rundir /nfs/data/sessions/validation_123 --kind foo"
        redirected = self.run_remote._redirect_rundir_for_retry(command, 1)  # noqa: SLF001
        self.assertIn("--rundir /nfs/data/sessions/validation_123_retry1", redirected)
        self.assertNotIn("--rundir /nfs/data/sessions/validation_123 ", redirected)

    def test_different_attempt_numbers_produce_different_suffixes(self):
        command = "cmd --rundir /nfs/data/sessions/validation_123"
        self.assertIn("_retry1", self.run_remote._redirect_rundir_for_retry(command, 1))  # noqa: SLF001
        self.assertIn("_retry2", self.run_remote._redirect_rundir_for_retry(command, 2))  # noqa: SLF001

    def test_only_the_rundir_token_changes(self):
        command = "cmd --before flag --rundir /nfs/data/sessions/validation_123 --after flag"
        redirected = self.run_remote._redirect_rundir_for_retry(command, 3)  # noqa: SLF001
        self.assertEqual(redirected, "cmd --before flag --rundir /nfs/data/sessions/validation_123_retry3 --after flag")

    def test_command_without_rundir_is_unchanged(self):
        """The majority of RunRemote-dispatched jobs (e.g. chem-comp-link, sf-convert) have no --rundir."""
        command = "python -m some.other.tool --input foo.cif --output bar.cif"
        self.assertEqual(self.run_remote._redirect_rundir_for_retry(command, 1), command)  # noqa: SLF001


class RunRetryRedirectsRundirTests(unittest.TestCase):
    def setUp(self):
        # A non-"/tmp/run_remote_"-prefixed run_dir, matching production's ValMod path, so
        # _cleanup() (called once per attempt) is a safe no-op across multiple retries.
        self.run_dir = tempfile.mkdtemp(prefix="workflow_instance_")
        self.run_remote = _make_run_remote(
            command="python -m wwpdb.apps.validation.src.validator --rundir /nfs/data/sessions/validation_999",
            run_dir=self.run_dir,
        )

    def test_second_attempt_uses_redirected_rundir(self):
        submitted_job_ids = iter([111, 222])

        def fake_sbatch_run(cmd, **_kwargs):
            return mock.Mock(returncode=0, stdout=f"Submitted batch job {next(submitted_job_ids)}\n".encode("utf-8"))

        with mock.patch("wwpdb.utils.dp.RunRemote.subprocess.run", side_effect=fake_sbatch_run), mock.patch.object(
            self.run_remote, "_build_sbatch_command", wraps=self.run_remote._build_sbatch_command
        ) as mock_build, mock.patch.object(
            self.run_remote, "monitor", side_effect=[JobStatus.OOM, JobStatus.COMPLETED]
        ), mock.patch.object(
            self.run_remote, "_get_job_metrics", return_value={}
        ):
            result = self.run_remote.run(retries=3)

        self.assertEqual(result.status, JobStatus.COMPLETED)
        self.assertEqual(mock_build.call_count, 2)
        first_attempt_command = mock_build.call_args_list[0].kwargs["command"]
        second_attempt_command = mock_build.call_args_list[1].kwargs["command"]
        self.assertIn("--rundir /nfs/data/sessions/validation_999", first_attempt_command)
        self.assertNotIn("_retry", first_attempt_command)
        self.assertIn("--rundir /nfs/data/sessions/validation_999_retry1", second_attempt_command)


if __name__ == "__main__":
    unittest.main()
