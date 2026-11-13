"""Hermetic tests for the memory and CPU a cluster job requests per operation.

Site configuration, the cluster submission and the operating system are mocked, so no tools,
site-config or Slurm are needed.  Operations are driven through RcsbDpUtility.op() with RunRemote
replaced, and one test runs the real RunRemote against a mocked sbatch/squeue/sacct.
"""

import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from typing import Any, Dict, List, Optional
from unittest import mock

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.abspath(__file__)))

import wwpdb.utils.dp.RcsbDpUtility as dpmod
from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility
from wwpdb.utils.dp.RunRemote import JobStatus

VALIDATE = "annot-wwpdb-validate-all-v2"
BLAST = "seq-blastp"


class ResourceTestBase(unittest.TestCase):
    """Builds an RcsbDpUtility whose site configuration is a dict and whose cluster submission is mocked."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.site_config: Dict[str, Any] = {"USE_COMPUTE_CLUSTER": True, "PDBE_CLUSTER_QUEUE": "queue"}
        patches = [
            mock.patch.object(dpmod, "ConfigInfo"),
            mock.patch.object(dpmod, "ConfigInfoAppCommon"),
            mock.patch.object(dpmod, "ConfigInfoAppCc"),
            mock.patch.object(dpmod, "ConfigInfoAppValidation"),
        ]
        mocks = [p.start() for p in patches]
        for p in patches:
            self.addCleanup(p.stop)
        self.config_info = mocks[0].return_value
        self.config_info.get.side_effect = lambda key, default=None: self.site_config.get(key, default)
        common = mocks[1].return_value
        common.get_site_packages_path.return_value = "/pkg"
        common.get_site_refdata_sequence_path.return_value = "/seq"
        common.get_site_refdata_sequence_db_path.return_value = "/seqdb"
        validation = mocks[3].return_value
        validation.get_chimerax.return_value = "/chimerax"
        validation.get_chimera.return_value = "/chimera"
        seqdb = mock.patch.object(RcsbDpUtility, "_RcsbDpUtility__locateSeqDb", return_value="/db/x")
        seqdb.start()
        self.addCleanup(seqdb.stop)

    def write_config(self, data: Dict[str, Any]) -> str:
        path_ = os.path.join(self.tmp, "resource_allocation.yaml")
        with open(path_, "w", encoding="utf-8") as fh:
            json.dump(data, fh)  # JSON is valid YAML
        self.site_config["RESOURCE_ALLOCATION_CONFIG_FILE"] = path_
        return path_

    def make(self) -> RcsbDpUtility:
        return RcsbDpUtility(tmpPath=self.tmp, siteId="TEST")

    def run_op(self, dp: RcsbDpUtility, op: str) -> Dict[str, Any]:
        """Run ``op`` and return the memory and CPUs given to RunRemote."""
        with mock.patch.object(dpmod, "RunRemote") as run_remote:
            run_remote.return_value.run.return_value = mock.Mock(status=JobStatus.COMPLETED)
            if op == BLAST:
                dp.addInput(name="one_letter_code_sequence", value="MKV")
            else:
                dp.addInput(name="request_validation_mode", value="annotate")
                dp.addInput(name="run_dir", value=os.path.join(self.tmp, "rundir"))
            self.assertEqual(dp.op(op), 0)  # type: ignore[arg-type]
        kwargs = run_remote.call_args.kwargs
        return {"memory": kwargs["memory_limit"], "cpus": kwargs["number_of_processors"]}


class OperationDefaultsTests(ResourceTestBase):
    def test_unconfigured_validation_keeps_the_historic_request(self) -> None:
        self.assertEqual(self.run_op(self.make(), VALIDATE), {"memory": 2000, "cpus": 1})

    def test_unconfigured_blast_keeps_its_builtin_memory_and_input_threads(self) -> None:
        dp = self.make()
        dp.addInput(name="num_threads", value="4")
        self.assertEqual(self.run_op(dp, BLAST), {"memory": 20000, "cpus": 4})

    def test_unconfigured_blast_without_threads_keeps_two_thousand(self) -> None:
        self.assertEqual(self.run_op(self.make(), BLAST), {"memory": 2000, "cpus": 1})

    def test_missing_configuration_file_keeps_defaults(self) -> None:
        self.site_config["RESOURCE_ALLOCATION_CONFIG_FILE"] = os.path.join(self.tmp, "absent.yaml")
        self.assertEqual(self.run_op(self.make(), VALIDATE), {"memory": 2000, "cpus": 1})


class ConfiguredResourcesTests(ResourceTestBase):
    def test_configured_operation_requests_configured_memory_and_cpus(self) -> None:
        self.write_config({"jobs": {VALIDATE: {"memory": "4G", "cpus": 3}}})
        self.assertEqual(self.run_op(self.make(), VALIDATE), {"memory": 4096, "cpus": 3})

    def test_operation_without_an_entry_is_not_affected(self) -> None:
        self.write_config({"jobs": {VALIDATE: {"memory": "4G", "cpus": 3}}})
        self.assertEqual(self.run_op(self.make(), BLAST), {"memory": 2000, "cpus": 1})

    def test_configuration_beats_the_operations_builtin_default(self) -> None:
        self.write_config({"jobs": {BLAST: {"memory": "8G", "cpus": 2}}})
        dp = self.make()
        dp.addInput(name="num_threads", value="4")
        self.assertEqual(self.run_op(dp, BLAST), {"memory": 8192, "cpus": 2})

    def test_defaults_section_applies_to_every_operation(self) -> None:
        self.write_config({"defaults": {"memory": "3000", "cpus": 2}})
        self.assertEqual(self.run_op(self.make(), VALIDATE), {"memory": 3000, "cpus": 2})

    def test_caller_set_values_beat_configuration(self) -> None:
        self.write_config({"jobs": {VALIDATE: {"memory": "4G", "cpus": 3}}})
        dp = self.make()
        dp.setStartMemory(6000)
        dp.setNumThreads(5)
        self.assertEqual(self.run_op(dp, VALIDATE), {"memory": 6000, "cpus": 5})

    def test_caller_set_values_survive_the_validation_reset_and_blast_override(self) -> None:
        dp = self.make()
        dp.setStartMemory(6000)
        self.assertEqual(self.run_op(dp, VALIDATE)["memory"], 6000)
        dp2 = self.make()
        dp2.setNumThreads(2)
        dp2.addInput(name="num_threads", value="4")
        self.assertEqual(self.run_op(dp2, BLAST)["cpus"], 2)

    def test_explicit_all_memory_is_ignored_with_a_warning(self) -> None:
        self.write_config({"jobs": {VALIDATE: {"memory": "all", "cpus": 3}}})
        with self.assertLogs(dpmod.logger, level="WARNING") as logs:
            result = self.run_op(self.make(), VALIDATE)
        self.assertEqual(result, {"memory": 2000, "cpus": 3})
        self.assertTrue(any(VALIDATE in line for line in logs.output))

    def test_malformed_values_fall_back_to_defaults(self) -> None:
        self.write_config({"jobs": {VALIDATE: {"memory": "lots", "cpus": 0}}})
        self.assertEqual(self.run_op(self.make(), VALIDATE), {"memory": 2000, "cpus": 1})


class NoLeakBetweenOperationsTests(ResourceTestBase):
    def test_blast_then_validation_on_one_instance(self) -> None:
        dp = self.make()
        dp.addInput(name="num_threads", value="4")
        self.assertEqual(self.run_op(dp, BLAST), {"memory": 20000, "cpus": 4})
        self.assertEqual(self.run_op(dp, VALIDATE), {"memory": 2000, "cpus": 1})

    def test_configured_validation_then_blast_on_one_instance(self) -> None:
        self.write_config({"jobs": {VALIDATE: {"memory": "4G", "cpus": 3}}})
        dp = self.make()
        self.assertEqual(self.run_op(dp, VALIDATE), {"memory": 4096, "cpus": 3})
        self.assertEqual(self.run_op(dp, BLAST), {"memory": 2000, "cpus": 1})


class MetalThreadsTests(ResourceTestBase):
    """OMP threads inside the metal-coordination jobs follow the CPUs available to the process."""

    STATS = "metal-metalcoord-stats"

    def threads(self, op: str = STATS) -> int:
        """Run ``op`` through the public interface and return the OMP_NUM_THREADS the job command exports."""
        dp = self.make()
        model = os.path.join(self.tmp, "model.cif")
        with open(model, "w", encoding="utf-8") as fh:
            fh.write("data_x\n")
        dp.imp(model)
        dp.addInput(name="ligands", value="0KA")
        with mock.patch.object(dpmod, "RunRemote") as run_remote:
            run_remote.return_value.run.return_value = mock.Mock(status=JobStatus.COMPLETED)
            dp.op(op)  # type: ignore[arg-type]
        found = re.findall(r"OMP_NUM_THREADS=(\d+)", run_remote.call_args.kwargs["command"])
        self.assertEqual(len(found), 1)
        return int(found[0])

    def with_cpus(self, count: int) -> "mock._patch[Any]":
        return mock.patch.object(os, "sched_getaffinity", lambda _pid: set(range(count)), create=True)

    def test_unconfigured_uses_the_legacy_fraction_of_available_cpus(self) -> None:
        with self.with_cpus(8):
            self.assertEqual(self.threads(), 4)

    def test_odd_cpu_counts_round_up_as_before(self) -> None:
        with self.with_cpus(5):
            self.assertEqual(self.threads(), 3)

    def test_one_available_cpu_gives_one_thread(self) -> None:
        with self.with_cpus(1):
            self.assertEqual(self.threads(), 1)

    def test_configured_value_is_used(self) -> None:
        self.write_config({"jobs": {self.STATS: {"cpus": 3}}})
        with self.with_cpus(8):
            self.assertEqual(self.threads(), 3)

    def test_configured_value_above_available_is_clamped_with_a_warning(self) -> None:
        self.write_config({"jobs": {self.STATS: {"cpus": 20}}})
        with self.with_cpus(4), self.assertLogs(dpmod.logger, level="WARNING"):
            self.assertEqual(self.threads(), 4)

    def test_the_regular_geometry_variant_follows_the_same_rule(self) -> None:
        self.write_config({"jobs": {"metal-metalcoord-stats-filter-regular": {"cpus": 2}}})
        with self.with_cpus(8):
            self.assertEqual(self.threads("metal-metalcoord-stats-filter-regular"), 2)


class RetryRegressionTests(ResourceTestBase):
    """A configured first attempt requests the configured memory and an out-of-memory retry doubles it."""

    def test_first_attempt_uses_configured_memory_and_retry_doubles_it(self) -> None:
        self.write_config({"jobs": {VALIDATE: {"memory": "4G", "cpus": 3}}})
        submitted: List[List[str]] = []
        states = iter(["OUT_OF_MEMORY", "COMPLETED"])
        next_job = iter([101, 102])

        def fake_run(cmd: List[str], **_kwargs: Any) -> mock.Mock:
            if cmd[0] == "sbatch":
                submitted.append(cmd)
                return mock.Mock(returncode=0, stdout=("Submitted batch job %d" % next(next_job)).encode())
            if cmd[0] == "squeue":
                return mock.Mock(returncode=0, stdout=next(states).encode())
            return mock.Mock(returncode=0, stdout=json.dumps({"jobs": []}).encode())

        remote_cfg = mock.patch("wwpdb.utils.dp.RunRemote.ConfigInfo")
        site_id = mock.patch("wwpdb.utils.dp.RunRemote.getSiteId", return_value="TEST")
        run = mock.patch("wwpdb.utils.dp.RunRemote.subprocess.run", side_effect=fake_run)
        sleep = mock.patch("wwpdb.utils.dp.RunRemote.time.sleep")
        with site_id, run, sleep, remote_cfg as cfg:
            cfg.return_value.get.return_value = "queue"
            self.assertEqual(self.run_real_remote(), 0)

        mem = [next(a for a in cmd if a.startswith("--mem=")) for cmd in submitted]
        cpus = [next(a for a in cmd if a.startswith("--cpus-per-task=")) for cmd in submitted]
        self.assertEqual(mem, ["--mem=4096", "--mem=8192"])
        self.assertEqual(cpus, ["--cpus-per-task=3", "--cpus-per-task=3"])

    def run_real_remote(self) -> Optional[int]:
        dp = self.make()
        dp.addInput(name="request_validation_mode", value="annotate")
        dp.addInput(name="run_dir", value=os.path.join(self.tmp, "rundir"))
        return dp.op(VALIDATE)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
