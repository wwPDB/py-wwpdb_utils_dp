# pylint: disable=logging-format-interpolation
import argparse
import logging
import os
import re
import subprocess
import sys
import time

from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId

logger = logging.getLogger()


def remove_file(file_path):
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as _e:  # noqa: F841
            pass


class RunRemote:
    def __init__(
        self,
        command,
        job_name,
        log_dir,
        run_dir=None,
        timeout=5600,
        memory_limit=16000,
        number_of_processors=1,
        add_site_config=False,
        add_site_config_database=False,
    ):
        # self.command = self.escape_substitution(command)
        self.command = command
        if timeout:
            self.timeout = timeout
        else:
            self.timeout = 5600
        self.memory_limit = memory_limit
        self.number_of_processors = number_of_processors
        self.job_name = job_name
        self.log_dir = log_dir
        self.run_dir = run_dir
        self.memory_used = 0
        self.memory_unit = "MB"
        self.time_taken = 0
        self.slurm_exit_status = 0
        self.slurm_success = False
        self.siteId = getSiteId()
        self.cI = ConfigInfo(self.siteId)
        self.slurm_source_command = self.cI.get("SLURM_SOURCE")
        self.slurm_run_command = self.cI.get("SLURM_COMMAND")
        self.pdbe_cluster_queue = self.cI.get("PDBE_CLUSTER_QUEUE")
        self.pdbe_memory_limit = 100000
        self.slurm_login_node = self.cI.get("SLURM_LOGIN_NODE")
        self.slurm_timeout = self.cI.get("SLURM_TIMEOUT")
        self.slurm_retry_delay = self.cI.get("SLURM_RETRY_DELAY", 4)
        self.command_prefix = self.cI.get("REMOTE_COMMAND_PREFIX")
        self.slurm_run_dir = run_dir or log_dir
        self.slurm_log_file = os.path.join(self.log_dir, self.job_name + ".log")
        self.slurm_in_file = os.path.join(self.slurm_run_dir, self.job_name + ".in")
        self.slurm_out_file = os.path.join(self.log_dir, self.job_name + ".out")
        self.add_site_config = add_site_config
        self.add_site_config_database = add_site_config_database

        self.out = None
        self.err = None

    @staticmethod
    def escape_substitution(command):
        """
        Escapes dollars, stops variables being interpretted early when passed to slurm.
        """
        command = command.replace("$", "\$")  # noqa: W605 pylint: disable=anomalous-backslash-in-string
        return command

    def get_shell_script(self):
        if self.run_dir:
            return os.path.join(self.run_dir, "run_{}.sh".format(self.job_name))
        return None

    def write_run_script(self):
        shell_script = self.get_shell_script()
        if shell_script:
            logging.info(self.command)
            with open(shell_script, "w") as out_file:
                out_file.write(self.command)
            os.chmod(shell_script, 0o775)
            self.command = shell_script
        else:
            self.command = self.escape_substitution(self.command)

    def run(self):
        rc = 1

        self.write_run_script()

        if self.add_site_config_database:
            self.pre_pend_sourcing_site_config(database=True)
        if self.add_site_config:
            self.pre_pend_sourcing_site_config()
        if self.command_prefix:
            self.prefix_command()

        if self.slurm_run_command:
            run_try = 1
            rc, self.out, self.err = self.run_slurm()
            while self.slurm_exit_status != 0:
                if self.memory_used:
                    try:
                        if self.memory_used > self.memory_limit:
                            self.memory_limit = int(self.memory_used)
                    except:  # noqa: E722 pylint: disable=bare-except
                        pass

                if self.memory_limit >= 100000:
                    self.memory_limit = self.memory_limit + 40000
                elif self.memory_limit >= 20000:
                    self.memory_limit = self.memory_limit + 30000
                else:
                    self.memory_limit = self.memory_limit + 10000
                run_try += 1
                logging.info("try {}, memory {}".format(run_try, self.memory_limit))
                rc, self.out, self.err = self.run_slurm()

        if rc != 0:
            logging.error("return code: {}".format(rc))  # pylint: disable=logging-format-interpolation
            logging.error("out: {}".format(self.out))  # pylint: disable=logging-format-interpolation
            logging.error("error: {}".format(self.err))  # pylint: disable=logging-format-interpolation
        else:
            logging.info("worked")
            remove_file(self.slurm_in_file)
            remove_file(self.slurm_out_file)
            if self.get_shell_script():
                remove_file(self.get_shell_script())

        return rc

    @staticmethod
    def check_timing(t1, t2):
        t = t2 - t1
        human_time = []
        if t > 3600:
            human_time.append("%.2f hours" % (t / 3600))
        elif t > 60:
            human_time.append("%.2f minutes" % (t / 60))
        else:
            human_time.append("%.2f seconds" % t)

        abs_time = "TIMING, %.2f, minutes" % (t / 60)

        human_time.append(abs_time)

        return human_time

    @staticmethod
    def touch(fname):
        if os.path.exists(fname):
            os.utime(fname, None)
        else:
            open(fname, "a").close()

    def get_site_config_command(self, suffix=""):
        site_config_path = self.cI.get("TOP_WWPDB_SITE_CONFIG_DIR")
        site_loc = self.cI.get("WWPDB_SITE_LOC")
        site_config_command = ". {}/init/env.sh --siteid {} --location {} {} > /dev/null".format(site_config_path, self.siteId, site_loc, suffix)
        return site_config_command

    def pre_pend_sourcing_site_config(self, database=False):
        self.command = "{}; {}".format(self.get_site_config_command(), self.command)
        if database:
            self.command = "{}; {}".format(self.get_site_config_command(suffix="--database"), self.command)

    def prefix_command(self):
        if self.command_prefix:
            self.command = "{} {}".format(self.command_prefix, self.command)

    def extract_state(self, output):
        """This method can be expanded to parse the entire
        output.
        """
        if isinstance(output, bytes):
            output = output.decode("utf-8")

        match = re.search(r"State\s*:\s*(\S+)", output)
        if match:
            return match.group(1)
        return None

    def check_sbatch_finished(self, job_id):
        slurm_command = list()
        if self.slurm_login_node:
            slurm_command.append("ssh {} '".format(self.slurm_login_node))
        if self.slurm_source_command:
            slurm_command.append("{};".format(self.slurm_source_command))
        slurm_command.append("jobinfo {}".format(job_id))
        if self.slurm_login_node:
            slurm_command.append("'")

        command_string = " ".join(slurm_command)

        _rc, out, _err = self.run_command(command=command_string)
        # rc, out, err = self.run_command(command="jobinfo {}".format(job_id))
        state = self.extract_state(out)

        while state in ("PENDING", "RUNNING", "COMPLETING"):
            time.sleep(60)
            _rc, out, _err = self.run_command(command=command_string)
            state = self.extract_state(out)

        logging.info("Job {} finished with state: {}".format(self.job_name, state))  # pylint: disable=logging-format-interpolation

        return state

    def run_command(self, command, log_file=None, new_env=None):
        # command_list = shlex.split(command)
        logging.info("Starting: %s", self.job_name)
        logging.info(command)
        if log_file:
            logging.info("logging to: {}".format(log_file))  # pylint: disable=logging-format-interpolation
            if not os.path.exists(os.path.dirname(log_file)):
                os.makedirs(os.path.dirname(log_file))
        t1 = os.times()[4]
        # child = subprocess.Popen(command_list)
        if new_env:
            child = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=new_env)
        else:
            child = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = child.communicate()
        rc = child.returncode
        if rc != 0:
            logging.error("Exit status: %s - process failed: %s", rc, self.job_name)
            logging.error(command)
            logging.error(out)
            logging.error(err)
        else:
            logging.info("process worked: %s", self.job_name)

        if log_file:
            with open(log_file, "wb") as lf:
                if out:
                    lf.write(out)
                    logging.info(out)
                if err:
                    lf.write(err)
                    logging.error(err)

        t2 = os.times()[4]
        ht = self.check_timing(t1, t2)
        # logging.info("Timing: %s took %s" %(name, ht[0]))
        logging.info("Finished: %s %s", self.job_name, ht[1])

        if not self.check_was_submitted(job_log_string=str(out)):
            logging.error("Error: task was not submitted")
            return 255, out, err

        return rc, out, err

    @staticmethod
    def check_was_submitted(job_log_string):
        logging.info(job_log_string)
        if "Submitted batch job" in job_log_string:
            return True
        return False

    @staticmethod
    def was_executed(job_log_string):
        logging.info(job_log_string)
        if "Job was executed" in job_log_string:
            return True
        return False

    def launch_sbatch(self):
        remove_file(self.slurm_out_file)

        remove_file(self.slurm_in_file)

        slurm_command = list()
        if self.slurm_login_node:
            slurm_command.append("ssh {} '".format(self.slurm_login_node))
        if self.slurm_source_command:
            slurm_command.append("{};".format(self.slurm_source_command))
        slurm_command.append(self.slurm_run_command)
        slurm_command.append("-J {}".format(self.job_name))
        slurm_command.append("-o {}".format(self.slurm_log_file))
        slurm_command.append("-e {}/{}_error.log".format(self.log_dir, self.job_name))
        if self.pdbe_memory_limit and self.memory_limit > self.pdbe_memory_limit:
            slurm_command.append("-p {}".format("bigmem"))
        else:
            slurm_command.append("-p {}".format(self.pdbe_cluster_queue))

        slurm_command.append("-n {}".format(self.number_of_processors))
        slurm_command.append("-t {}".format(self.timeout))
        slurm_command.append("--mem={0}".format(self.memory_limit))
        slurm_command.append('--wrap="{}"'.format(self.command))
        if self.slurm_login_node:
            slurm_command.append("'")

        command_string = " ".join(slurm_command)

        rc, out, err = self.run_command(command=command_string)

        if isinstance(out, bytes):
            out = out.decode("utf-8")

        # Regular expression to find the job id
        match = re.search(r"Submitted batch job (\d+)", out)
        if match:
            return match.group(1), rc, out, err
        return None, rc, out, err

    def launch_sbatch_wait_process(self):
        sbatch_command = list()
        sbatch_command.append("{};".format(self.slurm_source_command))
        sbatch_command.append(self.slurm_run_command)
        sbatch_command.append('-J "end_{}"'.format(self.job_name))
        sbatch_command.append('-o "{}/{}_wait.log"'.format(self.log_dir, self.job_name))
        sbatch_command.append('-e "{}/{}_wait_error.log"'.format(self.log_dir, self.job_name))
        sbatch_command.append("-p {}".format(self.pdbe_cluster_queue))
        sbatch_command.append('--wrap="uname -a; date"')
        command_string = " ".join(sbatch_command)
        rc, out, err = self.run_command(command=command_string)

        return rc, out, err

    def run_slurm(self):
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        # temp_file = os.path.join(self.slurm_run_dir, "slurm_temp_file.out")

        # if get non ok exit status from sbatch then wait 30 seconds and try again.
        # i = 0
        job_id, out, err = 0, None, None

        #
        # run command
        job_id, rc, out, err = self.launch_sbatch()

        if job_id is None:
            logging.error("sbatch failed to run")
            return rc, out, err

        logging.info("sbatch job id: {}".format(job_id))  # pylint: disable=logging-format-interpolation

        time.sleep(5)
        self.check_sbatch_finished(job_id=job_id)

        return rc, out, err


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        "--debug",
        help="debugging",
        action="store_const",
        dest="loglevel",
        const=logging.DEBUG,
        default=logging.INFO,
    )
    parser.add_argument("--command", help="command to run", type=str, required=True)
    parser.add_argument("--job_name", help="name for the job", type=str, required=True)
    parser.add_argument("--log_dir", help="directory to store log file in", type=str, required=True)
    parser.add_argument("--run_dir", help="directory to run", type=str)
    parser.add_argument("--memory_limit", help="starting memory limit", type=int, default=0)
    parser.add_argument("--num_processors", help="number of processors", type=int, default=1)
    parser.add_argument("--add_site_config", help="add site config to command", action="store_true")
    parser.add_argument("--add_site_config_with_database", help="add site config with database to command", action="store_true")

    args = parser.parse_args()
    logger.setLevel(args.loglevel)

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

    ret = run_remote.run()

    if ret != 0:
        message = "{} failed".format(args.job_name)
        annotation_email = run_remote.cI.get("ANNOTATION_EMAIL")
        if annotation_email:
            mcommand = 'mail -s "{} failed" {}'.format(args.job_name, annotation_email)
            run_remote.run_command(command=mcommand)

    sys.exit(ret)
