# pylint: disable=logging-format-interpolation
import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import time
from enum import Enum
from textwrap import dedent

from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def remove_file(file_path):
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as _e:  # noqa: F841
            pass


class JobStatus(Enum):
    OOM = "OUT_OF_MEMORY"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    OTHER = "OTHER"


class JobResult:
    """Result object containing job status and metrics.
    May be used both for local and remote jobs.
    """

    def __init__(
        self,
        status: JobStatus,
        job_id=None,
        retries_used=0,
        total_time_seconds=None,
        execution_time_seconds=None,
        queue_time_seconds=None,
        requested_memory_mb=None,
        used_memory_mb=None,
        cpu_count=None,
        cpu_time_seconds=None,
    ):
        self.status: JobStatus = status
        self.job_id = job_id
        self.retries_used = retries_used
        # Timing metrics
        self.total_time_seconds = total_time_seconds  # submission + execution
        self.execution_time_seconds = execution_time_seconds  # actual job execution
        self.queue_time_seconds = queue_time_seconds  # time waiting for node
        # Resource metrics
        self.requested_memory_mb = requested_memory_mb
        self.used_memory_mb = used_memory_mb
        self.cpu_count = cpu_count
        self.cpu_time_seconds = cpu_time_seconds


class RunRemote:
    def __init__(
        self,
        command,
        job_name,
        log_dir,
        run_dir=None,
        timeout=90,
        memory_limit=16000,
        number_of_processors=1,
        add_site_config=False,
        add_site_config_database=False,
    ):
        self.command = command
        self.job_name = job_name
        self.log_dir = log_dir
        self.run_dir = run_dir
        self.timeout = 90 if timeout == 0 else str(timeout)
        self.memory_limit = str(memory_limit)
        self.number_of_processors = str(number_of_processors)
        self.add_site_config = add_site_config
        self.add_site_config_database = add_site_config_database

        if not self.run_dir:
            self.run_dir = tempfile.mkdtemp(prefix="run_remote_")  # this won't work as cluster nodes have different temp dirs
        self._shell_script = os.path.join(self.run_dir, "run_{}.sh".format(self.job_name))

        self.siteId = getSiteId()
        self.cI = ConfigInfo(self.siteId)
        self.pdbe_cluster_queue = str(self.cI.get("PDBE_CLUSTER_QUEUE"))
        self._stdout_file = os.path.join(self.log_dir, self.job_name + ".out")
        self._stderr_file = os.path.join(self.log_dir, self.job_name + ".err")

    @staticmethod
    def _map_status_text(status_text) -> JobStatus:
        """Map a Slurm state string (from squeue or sacct) to a JobStatus."""
        if status_text in ["FAILED", "TIMEOUT"]:
            return JobStatus.FAILED
        if status_text == "OUT_OF_MEMORY":
            return JobStatus.OOM
        if status_text == "COMPLETED":
            return JobStatus.COMPLETED
        if status_text in ["RUNNING", "PENDING", "CONFIGURING", "COMPLETING"]:
            return JobStatus.RUNNING
        if status_text == "CANCELLED":
            return JobStatus.CANCELLED
        return JobStatus.OTHER

    def get_job_status_by_id(self, job_id) -> JobStatus:
        """Get the status of a single job by ID.

        squeue is the fast path, but squeue stops reporting a job shortly after it finishes --
        returning a non-zero return code or blank output -- even though the job actually
        completed (e.g. hit OUT_OF_MEMORY). sacct retains the accounting record after squeue
        has forgotten it, so fall back to sacct only when squeue itself fails to produce a
        usable answer; when squeue does answer, that answer is preserved unchanged.
        """
        cmd = [
            "squeue",
            "--noheader",
            "-t",
            "all",
            "--Format",
            "State",
            "--jobs",
            str(job_id),
        ]
        squeue_output = subprocess.run(cmd, check=False, capture_output=True)
        status_text = squeue_output.stdout.decode("utf-8").strip()

        if squeue_output.returncode == 0 and status_text:
            return self._map_status_text(status_text)

        logger.debug(f"squeue could not classify job {job_id} (rc={squeue_output.returncode}, output={status_text!r}); falling back to sacct")
        sacct_status = self._get_job_status_from_sacct(job_id)
        return sacct_status if sacct_status is not None else JobStatus.OTHER

    def _get_job_status_from_sacct(self, job_id, max_attempts=3, backoff=2):
        """Classify a job's terminal status via sacct, tolerating brief accounting lag.

        Right after a job finishes, sacct can briefly have no record yet -- retry a few times
        with backoff before giving up rather than treating a momentary gap as classification
        failure.
        """
        for attempt in range(1, max_attempts + 1):
            try:
                cmd = ["sacct", "--json", "--jobs", str(job_id)]
                output = subprocess.run(cmd, check=True, capture_output=True, text=True)
                data = json.loads(output.stdout)
            except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
                logger.warning(f"Error querying sacct for job {job_id} status (attempt {attempt}/{max_attempts}): {e}")
                time.sleep(backoff)
                continue

            jobs = data.get("jobs")
            if not jobs:
                logger.debug(f"sacct has no record yet for job {job_id} (attempt {attempt}/{max_attempts})")
                time.sleep(backoff)
                continue

            state_list = jobs[0].get("state", {}).get("current", [])
            if not state_list:
                logger.warning(f"sacct record for job {job_id} has no state.current: {jobs[0]}")
                time.sleep(backoff)
                continue

            return self._map_status_text(state_list[0])

        logger.warning(f"sacct did not classify job {job_id} after {max_attempts} attempts")
        return None

    def requeue_job(self, job_id):
        """Requeue a single job."""
        cmd = ["scontrol", "requeue", str(job_id)]
        subprocess.run(cmd, check=True)
        logger.info(f"Requeued failed job {job_id}")

    def _get_job_metrics(self, job_id):
        """Extract job metrics from SLURM using sacct."""
        try:
            cmd = ["sacct", "--json", "--jobs", str(job_id)]
            output = subprocess.run(cmd, check=True, capture_output=True, text=True)
            data = json.loads(output.stdout)

            if not data.get("jobs"):
                logger.warning(f"No job data found for job {job_id}")
                return {}

            # Get the main job entry (first one should be the parent job)
            job_data = data["jobs"][0]

            if job_data.get("job_id") != job_id:
                logger.warning(f"Job ID mismatch: expected {job_id}, got {job_data.get('job_id')}")

            metrics = {}
            time_data = job_data.get("time", {})

            # Extract timing metrics (Unix timestamps in seconds)
            submit_time = time_data.get("submission")
            start_time = time_data.get("start")
            end_time = time_data.get("end")

            if submit_time and end_time:
                metrics["total_time_seconds"] = end_time - submit_time

            if start_time and end_time:
                metrics["execution_time_seconds"] = end_time - start_time

            if submit_time and start_time:
                metrics["queue_time_seconds"] = start_time - submit_time

            # Extract CPU time from user and system time
            user_time = time_data.get("user", {})
            system_time = time_data.get("system", {})

            user_seconds = user_time.get("seconds", 0)
            user_microseconds = user_time.get("microseconds", 0)
            system_seconds = system_time.get("seconds", 0)
            system_microseconds = system_time.get("microseconds", 0)

            metrics["cpu_time_seconds"] = user_seconds + user_microseconds / 1_000_000 + system_seconds + system_microseconds / 1_000_000

            # Extract CPU count from required resources
            required = job_data.get("required", {})
            cpu_count = required.get("CPUs")
            if cpu_count:
                metrics["cpu_count"] = cpu_count

            # Extract requested memory from required resources (in MB)
            mem_per_node = required.get("memory_per_node", {})
            if mem_per_node.get("set"):
                metrics["requested_memory_mb"] = mem_per_node.get("number")

            # Extract used memory from steps (if available)
            steps = job_data.get("steps", [])
            if steps:
                batch_step = steps[0]  # Usually the batch step
                tres_data = batch_step.get("tres", {})
                requested_max = tres_data.get("requested", {}).get("max", [])

                # Find memory in the tres array
                for tres_item in requested_max:
                    if tres_item.get("type") == "mem":
                        # Memory is in bytes, convert to MB
                        mem_bytes = tres_item.get("count", 0)
                        metrics["used_memory_mb"] = mem_bytes // (1024 * 1024)
                        break

            logger.debug(f"Job {job_id} metrics: {metrics}")
            return metrics

        except subprocess.CalledProcessError as e:
            logger.warning(f"Error running sacct for job {job_id}: {e}")
            return {}
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Error parsing sacct output for job {job_id}: {e}")
            return {}

    def monitor(self, job_id, frequency=10):
        """Monitor a job by ID, requeueing if it fails."""
        logging.info(f"Monitoring job {job_id}")  # noqa: LOG015

        while True:
            status = self.get_job_status_by_id(job_id)

            if status in (JobStatus.CANCELLED, JobStatus.FAILED, JobStatus.OOM):
                logger.warning(f"Job {job_id} failed with status {status}")
                return status
            if status == JobStatus.COMPLETED:
                logger.info(f"Job {job_id} completed successfully")
                return status

            logger.debug(f"Job {job_id} status: {status}")
            time.sleep(frequency)

    def _build_sbatch_command(self, command):
        sbatch_args = [
            "sbatch",
            "--job-name=%s" % self.job_name,
            "--partition=%s" % self.pdbe_cluster_queue,
            "--cpus-per-task=%s" % self.number_of_processors,
            "--mem=%s" % self.memory_limit,
            "--time=%s" % self.timeout,
            "--chdir=%s" % self.run_dir,
            "--output=%s" % self._stdout_file,
            "--error=%s" % self._stderr_file,
        ]

        with open(self._shell_script, "w") as f:
            cmd = f"""\
            #!/bin/bash
            set -e
            export XDG_RUNTIME_DIR={self.run_dir}
            {command}
            """
            f.write(dedent(cmd))
            f.flush()
        os.chmod(self._shell_script, 0o775)

        sbatch_args += [self._shell_script]
        return sbatch_args

    def _cleanup(self):
        if self.run_dir.startswith("/tmp/run_remote_"):  # noqa: S108
            shutil.rmtree(self.run_dir)

    def _source_site_config(self, database=False):
        suffix = ""
        if database:
            suffix = "--database"

        site_config_path = self.cI.get("TOP_WWPDB_SITE_CONFIG_DIR")
        site_loc = self.cI.get("WWPDB_SITE_LOC")
        site_config_command = ". {}/init/env.sh --siteid {} --location {} {} > /dev/null".format(site_config_path, self.siteId, site_loc, suffix)

        return "{}; {}".format(site_config_command, self.command)

    _RUNDIR_PATTERN = re.compile(r"--rundir (\S+)")

    def _redirect_rundir_for_retry(self, command, attempt):
        """Point a retried command's --rundir at a fresh, never-used sibling directory.

        Some commands (the wwPDB validator's run_multithread(), see py-wwpdb_apps_validation
        wwpdb/apps/validation/src/run_validator/runvalidation.py) are not safe to rerun
        against a --rundir a previous attempt already used: they create per-run working
        subdirectories with a bare os.mkdir() (no exist_ok), which raises FileExistsError if
        a prior attempt already created them -- even if that prior attempt did real, useful
        work before being killed (e.g. by OOM). Redirecting each retry to an unused sibling
        directory avoids the collision entirely without needing to fix the callee. Commands
        with no --rundir (the majority of RunRemote-dispatched jobs) are returned unchanged.
        """
        match = self._RUNDIR_PATTERN.search(command)
        if not match:
            return command
        original_rundir = match.group(1)
        retry_rundir = f"{original_rundir}_retry{attempt}"
        return command[: match.start()] + f"--rundir {retry_rundir}" + command[match.end() :]

    def run(self, retries=3) -> JobResult:
        status = JobStatus.OTHER
        job_id = None
        wf_command = self.command

        if self.add_site_config_database or self.add_site_config:
            wf_command = self._source_site_config(database=self.add_site_config_database)

        retries_used = 0
        while retries > 0:
            try:
                sbatch_cmd = self._build_sbatch_command(command=wf_command)
                logger.info(" ".join(sbatch_cmd))

                output = subprocess.run(sbatch_cmd, check=True, capture_output=True)
                job_id = int(output.stdout.decode("utf-8").split()[-1])
                logger.debug(f"Submitted: {job_id}")

                self._cleanup()
                status = self.monitor(job_id=job_id)

                if status == JobStatus.COMPLETED:
                    break

                if status == JobStatus.OOM:
                    self.memory_limit = str(int(self.memory_limit) * 2)

                logger.info(f"Retrying job {job_id} with memory limit {self.memory_limit}")
                retries -= 1
                retries_used += 1
                wf_command = self._redirect_rundir_for_retry(wf_command, retries_used)
            except subprocess.CalledProcessError as e:
                logger.error(f"Error submitting job: {e}")
                break

        # Extract metrics from SLURM
        metrics = self._get_job_metrics(job_id) if job_id else {}

        # Create result object with metrics
        result = JobResult(
            status=status,
            job_id=job_id,
            retries_used=retries_used,
            total_time_seconds=metrics.get("total_time_seconds"),
            execution_time_seconds=metrics.get("execution_time_seconds"),
            queue_time_seconds=metrics.get("queue_time_seconds"),
            requested_memory_mb=metrics.get("requested_memory_mb"),
            used_memory_mb=metrics.get("used_memory_mb"),
            cpu_count=metrics.get("cpu_count"),
            cpu_time_seconds=metrics.get("cpu_time_seconds"),
        )

        return result


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="comm")

    parser_run = subparsers.add_parser("run")
    parser_run.add_argument("-d", "--debug", help="debugging", action="store_const", dest="loglevel", const=logging.DEBUG, default=logging.INFO)
    parser_run.add_argument("--command", help="command to run", type=str, required=True)
    parser_run.add_argument("--job_name", help="name for the job", type=str, required=True)
    parser_run.add_argument("--log_dir", help="directory to store log file in", type=str, required=True)
    parser_run.add_argument("--run_dir", help="directory to run", type=str)
    parser_run.add_argument("--memory_limit", help="starting memory limit", type=int, default=16000)
    parser_run.add_argument("--num_processors", help="number of processors", type=int, default=1)
    parser_run.add_argument("--add_site_config", help="add site config to command", action="store_true")
    parser_run.add_argument("--add_site_config_with_database", help="add site config with database to command", action="store_true")

    args = parser.parse_args()

    logger.info(f"Running command: {args.comm}")
    if args.comm == "run":
        run_remote = RunRemote(
            command=args.command,
            job_name=args.job_name,
            log_dir=args.log_dir,
            run_dir=args.run_dir,
            memory_limit=args.memory_limit,
            number_of_processors=args.num_processors,
            add_site_config=args.add_site_config,
            add_site_config_database=args.add_site_config_with_database,
        )
        result = run_remote.run()
        logger.info(f"Job finished with status: {result.status}")
        logger.info(f"Job ID: {result.job_id}, Execution time: {result.execution_time_seconds}s, Queue time: {result.queue_time_seconds}s")


if __name__ == "__main__":
    main()
