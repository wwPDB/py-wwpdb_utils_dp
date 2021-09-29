# pylint: disable=logging-format-interpolation
import os
import sys
import time
import logging
import subprocess
import argparse
from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId

logger = logging.getLogger()


def remove_file(file_path):
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            pass


class RunRemote:
    def __init__(self, command, job_name,
                 log_dir,
                 run_dir=None,
                 timeout=5600,
                 memory_limit=0,
                 number_of_processors=1,
                 add_site_config=False,
                 add_site_config_database=False):
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
        self.bsub_exit_status = 0
        self.bsub_success = False
        self.siteId = getSiteId()
        self.cI = ConfigInfo(self.siteId)
        self.bsub_source_command = self.cI.get("BSUB_SOURCE")
        self.bsub_run_command = self.cI.get("BSUB_COMMAND")
        self.pdbe_cluster_queue = self.cI.get("PDBE_CLUSTER_QUEUE")
        self.pdbe_memory_limit = 100000
        self.bsub_login_node = self.cI.get("BSUB_LOGIN_NODE")
        self.bsub_timeout = self.cI.get("BSUB_TIMEOUT")
        self.bsub_retry_delay = self.cI.get("BSUB_RETRY_DELAY", 4)
        self.command_prefix = self.cI.get('REMOTE_COMMAND_PREFIX')
        self.bsub_run_dir = run_dir if run_dir else log_dir
        self.bsub_log_file = os.path.join(self.log_dir, self.job_name + ".log")
        self.bsub_in_file = os.path.join(self.bsub_run_dir, self.job_name + ".in")
        self.bsub_out_file = os.path.join(self.log_dir, self.job_name + ".out")
        self.add_site_config = add_site_config
        self.add_site_config_database = add_site_config_database

        self.out = None
        self.err = None

    @staticmethod
    def escape_substitution(command):
        """
        Escapes dollars, stops variables being interpretted early when passed to bsub.
        """
        command = command.replace("$", "\$")  # noqa: W605 pylint: disable=anomalous-backslash-in-string
        return command

    def get_shell_script(self):
        if self.run_dir:
            return os.path.join(self.run_dir, 'run_{}.sh'.format(self.job_name))
        return None

    def write_run_script(self):
        shell_script = self.get_shell_script()
        if shell_script:
            logging.info(self.command)
            with open(shell_script, 'w') as out_file:
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

        if self.bsub_run_command:
            bsub_try = 1
            rc, self.out, self.err = self.run_bsub()
            while self.bsub_exit_status != 0:
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
                bsub_try += 1
                logging.info("try {}, memory {}".format(bsub_try,
                                                        self.memory_limit))
                rc, self.out, self.err = self.run_bsub()

        if rc != 0:
            logging.error("return code: {}".format(rc))  # pylint: disable=logging-format-interpolation
            logging.error("out: {}".format(self.out))  # pylint: disable=logging-format-interpolation
            logging.error("error: {}".format(self.err))  # pylint: disable=logging-format-interpolation
        else:
            logging.info("worked")
            remove_file(self.bsub_in_file)
            remove_file(self.bsub_out_file)
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
        site_config_command = ". {}/init/env.sh --siteid {} --location {} {} > /dev/null".format(site_config_path,
                                                                                                 self.siteId, site_loc,
                                                                                                 suffix)
        return site_config_command

    def pre_pend_sourcing_site_config(self, database=False):

        self.command = "{}; {}".format(self.get_site_config_command(), self.command)
        if database:
            self.command = "{}; {}".format(self.get_site_config_command(suffix="--database"), self.command)

    def prefix_command(self):
        if self.command_prefix:
            self.command = "{} {}".format(self.command_prefix, self.command)

    def check_bsub_finished(self):
        # pause to allow system to write out bsub out file.
        i = 1
        retry_times = 15
        while i < retry_times:
            if os.path.exists(self.bsub_out_file):
                break
            else:
                delay_time = i * 2
                logging.info(
                    "bsub out file {} not present - waiting {}secs (try {} of {}) for bsub to finish".format(
                        self.bsub_out_file, delay_time, i,
                        retry_times))  # pylint: disable=logging-format-interpolation
                time.sleep(delay_time)
                i += 1

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
            logging.error('Error: task was not submitted')
            return 255, out, err

        return rc, out, err

    @staticmethod
    def check_was_submitted(job_log_string):
        logging.info(job_log_string)
        if "is submitted to queue" in job_log_string:
            return True
        return False

    @staticmethod
    def was_executed(job_log_string):
        logging.info(job_log_string)
        if "Job was executed" in job_log_string:
            return True
        return False

    def launch_bsub(self):

        remove_file(self.bsub_out_file)

        remove_file(self.bsub_in_file)

        bsub_command = list()
        if self.bsub_login_node:
            bsub_command.append("ssh {} '".format(self.bsub_login_node))
        if self.bsub_source_command:
            bsub_command.append("{};".format(self.bsub_source_command))
        bsub_command.append(self.bsub_run_command)
        bsub_command.append("-J {}".format(self.job_name))
        bsub_command.append('-E "touch {}"'.format(self.bsub_in_file))
        bsub_command.append("-oo {}".format(self.bsub_log_file))
        bsub_command.append("-eo {}/{}_error.log".format(self.log_dir, self.job_name))
        bsub_command.append('-Ep "touch {}"'.format(self.bsub_out_file))
        if self.pdbe_memory_limit and self.memory_limit > self.pdbe_memory_limit:
            bsub_command.append("-P {}".format("bigmem"))

        bsub_command.append("-q {}".format(self.pdbe_cluster_queue))
        if "LSB_JOBGROUP" in os.environ and os.environ["LSB_JOBGROUP"]:
            bsub_command.append("-g {}".format(os.environ["LSB_JOBGROUP"]))

        bsub_command.append("-n {}".format(self.number_of_processors))
        bsub_command.append("-W {}".format(self.timeout))
        if self.memory_limit:
            bsub_command.append('-R "rusage[mem={0}]" -M {0}'.format(self.memory_limit))
        bsub_command.append('-K "{}"'.format(self.command))
        # bsub_command.append('"{}"'.format(self.command))
        if self.bsub_login_node:
            bsub_command.append("'")

        command_string = " ".join(bsub_command)

        rc, out, err = self.run_command(command=command_string)

        return rc, out, err

    def launch_bsub_wait_process(self):
        bsub_command = list()
        bsub_command.append("{};".format(self.bsub_source_command))
        bsub_command.append(self.bsub_run_command)
        bsub_command.append('-J "end_{}"'.format(self.job_name))
        bsub_command.append('-w "ended({})"'.format(self.job_name))
        bsub_command.append('-oo "{}/{}_wait.log"'.format(self.log_dir, self.job_name))
        bsub_command.append('-eo "{}/{}_wait_error.log"'.format(self.log_dir, self.job_name))
        bsub_command.append("-q {}".format(self.pdbe_cluster_queue))
        bsub_command.append('-K "uname -a; date"')
        command_string = " ".join(bsub_command)
        rc, out, err = self.run_command(command=command_string)

        return rc, out, err

    def parse_bsub_log(self):
        self.bsub_exit_status = 0
        self.memory_used = 0
        self.memory_unit = "MB"
        self.time_taken = 0
        self.bsub_success = False
        logging.info('reading: {}'.format(self.bsub_log_file))  # pylint: disable=logging-format-interpolation
        if os.path.exists(self.bsub_log_file):
            with open(self.bsub_log_file, "r") as log_file:
                for log_file_line in log_file:
                    if "Successfully completed." in log_file_line:
                        self.bsub_success = True
                    if "Max Memory :" in log_file_line:
                        try:
                            memory_used = log_file_line.split(":")[-1].strip()
                            if memory_used:
                                self.memory_unit = memory_used.split(" ")[1]
                                self.memory_used = int(memory_used.split(" ")[0])
                        except Exception as e:
                            logging.error(e)
                            logging.error(log_file_line)

                    if "TERM_MEMLIMIT" in log_file_line:
                        logging.info('task killed due to hitting memory limit')
                        self.bsub_exit_status = 1
                    if "Turnaround time" in log_file_line:
                        time_taken = log_file_line.split(":")[-1].strip()
                        try:
                            self.time_taken = int(time_taken.split(" ")[0])
                        except Exception as e:
                            logging.error(e)
                            logging.error(log_file_line)
        if self.memory_unit == "GB":
            self.memory_unit = "MB"
            self.memory_used = self.memory_used * 1024
        elif self.memory_unit == "KB":
            self.memory_unit = "MB"
            self.memory_used = int(self.memory_used / 1024)
        logging.info(
            'Bsub successfully run: {}'.format(self.bsub_success))  # pylint: disable=logging-format-interpolation
        logging.info("memory used: {} {}".format(self.memory_used,
                                                 self.memory_unit))  # pylint: disable=logging-format-interpolation
        logging.info('Bsub time taken: {} secs'.format(self.time_taken))  # pylint: disable=logging-format-interpolation
        logging.info(
            "Bsub exit status: {}".format(self.bsub_exit_status))  # pylint: disable=logging-format-interpolation

    def run_bsub(self):

        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        temp_file = os.path.join(self.bsub_run_dir, "bsub_temp_file.out")

        # if get non ok exit status from bsub then wait 30 seconds and try again.
        # i = 0
        rc, out, err = 0, None, None

        #
        # error codes
        # 0 everything is ok
        # 127 task failed - retrying wont help
        # 130 memory limit reached
        # 143 memory limit reached
        # 159/153 file too large - need additional resources, trying again wont help
        # 255 is ssh connection dropped so task is still ongoing - this is also when lsf is not ready
        # allowed_codes = (0, 130, 143, 153, 159)
        #
        # run command
        i = 0
        lsf_not_ready_codes = [255]
        # task_failed_codes = [1, 127]
        task_failed_codes = [1]
        while i < 5:
            rc, out, err = self.launch_bsub()
            if rc not in lsf_not_ready_codes:
                break
            else:
                delay_time = i * 2
                logging.info("bsub return code of {}. Waiting for {}".format(rc,
                                                                             delay_time))  # pylint: disable=logging-format-interpolation
                time.sleep(delay_time)
                i += 1

        # ensure NFS cache doesn't cause issues
        self.touch(temp_file)
        remove_file(temp_file)
        if rc not in task_failed_codes:
            self.check_bsub_finished()

        self.parse_bsub_log()

        return rc, out, err


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", help="debugging", action="store_const", dest="loglevel", const=logging.DEBUG,
                        default=logging.INFO)
    parser.add_argument("--command", help="command to run", type=str, required=True)
    parser.add_argument("--job_name", help="name for the job", type=str, required=True)
    parser.add_argument("--log_dir", help="directory to store log file in", type=str, required=True)
    parser.add_argument("--run_dir", help="directory to run", type=str)
    parser.add_argument("--memory_limit", help="starting memory limit", type=int, default=0)
    parser.add_argument("--num_processors", help="number of processors", type=int, default=1)
    parser.add_argument("--add_site_config", help="add site config to command", action="store_true")
    parser.add_argument("--add_site_config_with_database", help="add site config with database to command",
                        action="store_true")

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
