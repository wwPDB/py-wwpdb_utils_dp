import logging
import os
import subprocess
import time

from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId


class RunRemote:

    def __init__(self, command, job_name, log_dir, timeout=5600, memory_limit=0, number_of_processors=1):
        self.command = command
        if timeout:
            self.timeout = timeout
        else:
            self.timeout = 5600
        self.memory_limit = memory_limit
        self.number_of_processors = number_of_processors
        self.job_name = job_name
        self.log_dir = log_dir
        self.bsub_log_file = None
        self.memory_used = 0
        self.bsub_exit_status = 0
        self.siteId = getSiteId()
        self.cI = ConfigInfo(self.siteId)
        self.bsub_source_command = self.cI.get('BSUB_SOURCE')
        self.bsub_run_command = self.cI.get('BSUB_COMMAND')
        self.pdbe_cluster_queue = self.cI.get('PDBE_CLUSTER_QUEUE')

    def run(self):
        rc = 1
        out = None
        err = None

        if 'pdbe' in self.siteId.lower():
            bsub_try = 1
            rc, out, err = self.run_bsub()
            while self.bsub_exit_status != 0:
                self.memory_limit = self.memory_limit + 10000
                bsub_try += 1
                logging.info('try {}, memory {}'.format(bsub_try, self.memory_limit))
                rc, out, err = self.run_bsub()

        if rc != 0:
            logging.error('return code: {}'.format(rc))
            logging.error('out: {}'.format(out))
            logging.error('error: {}'.format(err))
        else:
            logging.info('worked')

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

    def run_command(self, command, log_file=None, new_env=None):
        # command_list = shlex.split(command)
        logging.info('Starting: %s' % self.job_name)
        logging.debug(command)
        if log_file:
            logging.info('logging to: {}'.format(log_file))
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
            logging.error('Exit status: %s - process failed: %s' % (rc, self.job_name))
        else:
            logging.info('process worked: %s' % self.job_name)

        if log_file:
            with open(log_file, 'wb') as lf:
                if out:
                    lf.write(out)
                    # logging.info(out)
                if err:
                    lf.write(err)
                    logging.error(err)

        t2 = os.times()[4]
        ht = self.check_timing(t1, t2)
        # logging.info("Timing: %s took %s" %(name, ht[0]))
        logging.info("Finished: %s, %s" % (self.job_name, ht[1]))

        return rc, out, err

    def launch_bsub(self):
        self.bsub_log_file = os.path.join(self.log_dir, self.job_name + '.log')
        bsub_command = list()
        bsub_command.append("{};".format(self.bsub_source_command))
        bsub_command.append(self.bsub_run_command)
        bsub_command.append('-J "{}"'.format(self.job_name))
        bsub_command.append('-oo "{}"'.format(self.bsub_log_file))
        bsub_command.append('-eo "{}/{}_error.log"'.format(self.log_dir, self.job_name))
        bsub_command.append('-q {}'.format(self.pdbe_cluster_queue))
        bsub_command.append('-n {}'.format(self.number_of_processors))
        bsub_command.append('-W {}'.format(self.timeout))
        if self.memory_limit:
            bsub_command.append('-R "rusage[mem={0}]" -M {0}'.format(self.memory_limit))
        bsub_command.append('"{}"'.format(self.command))

        command_string = ' '.join(bsub_command)
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
        bsub_command.append('-q {}'.format(self.pdbe_cluster_queue))
        bsub_command.append('-K "uname -a; date"')
        command_string = ' '.join(bsub_command)
        rc, out, err = self.run_command(command=command_string)

        return rc, out, err

    def parse_bsub_log(self):
        self.bsub_exit_status = 0
        if os.path.exists(self.bsub_log_file):
            with open(self.bsub_log_file, 'r') as log_file:
                for l in log_file:
                    if 'Max Memory :' in l:
                        self.memory_used = l.split(':')[-1].strip()

                    if 'TERM_MEMLIMIT' in l:
                        self.bsub_exit_status = 1

        logging.info('memory used: {}'.format(self.memory_used))
        logging.info('bsub exit status: {}'.format(self.bsub_exit_status))

    def run_bsub(self):

        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        # if get non zero exit status from bsub then wait 30 seconds and try again.
        i = 0
        rc, out, err = 0, None, None
        # rc, out, err = self.launch_bsub()
        while i < 3:
            rc, out, err = self.launch_bsub()
            if rc == 0:
                break
            time.sleep(30)
            i += 1

        if rc != 0:
            return rc, out, err

        # pause before submitting second job
        time.sleep(5)

        # if get non zero exit status from bsub then wait 30 seconds and try again.
        i = 0
        rc, out, err = 0, None, None
        # rc, out, err = self.launch_bsub_wait_process()

        while i < 3:
            rc, out, err = self.launch_bsub_wait_process()
            if rc == 0:
                break
            time.sleep(30)
            i += 1

        self.parse_bsub_log()

        return rc, out, err
