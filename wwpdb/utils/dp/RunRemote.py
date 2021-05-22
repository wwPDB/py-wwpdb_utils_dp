import os
import sys
import time
import logging
import subprocess
import argparse
from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId
import prefect
from prefect import task, Flow,Parameter
from prefect.tasks.mysql import mysql

logger = logging.getLogger()


class RunRemote:

    def __init__(self, command, job_name, log_dir, timeout=5600, memory_limit=0, number_of_processors=1,
                 add_site_config=False, add_site_config_database=False):
        self.command = self.escape_substitution(command)
        if timeout:
            self.timeout = timeout
        else:
            self.timeout = 5600
        self.memory_limit = memory_limit
        self.number_of_processors = number_of_processors
        self.job_name = job_name
        self.log_dir = log_dir
        self.max_memory_used = 0
        self.memory_unit = 'MB'
        self.bsub_exit_status = 0
        self.siteId = getSiteId()
        self.cI = ConfigInfo(self.siteId)
        self.bsub_source_command = self.cI.get('BSUB_SOURCE')
        self.bsub_run_command = self.cI.get('BSUB_COMMAND')
        self.pdbe_cluster_queue = self.cI.get('PDBE_CLUSTER_QUEUE')
        self.pdbe_memory_limit = 100000
        self.bsub_login_node = self.cI.get('BSUB_LOGIN_NODE')
        self.bsub_timeout = self.cI.get('BSUB_TIMEOUT')
        self.bsub_retry_delay = self.cI.get('BSUB_RETRY_DELAY')
        self.bsub_log_file = os.path.join(self.log_dir, self.job_name + '.log')
        self.bsub_out_file = os.path.join(self.log_dir, self.job_name + '.out')
        self.add_site_config = add_site_config
        self.add_site_config_database = add_site_config_database
        self.executed_command = ''
        self.out = None
        self.err = None
        self.run_duration = None
        self.ret_code = 1
        self.bsub_try = 1
        self.avg_memory_used = 0
        self.max_threads = 0
        self.max_processes = 0
        self.cpu_time = 0
        self.job_time = 0

    def escape_substitution(self, command):
        """
        Escapes dollars, stops variables being interpretted early when passed to bsub.
        """
        command = command.replace('$', '\$')
        return command

    def run(self):
        self.ret_code = 1

        if self.add_site_config_database:
            self.pre_pend_sourcing_site_config(database=True)
        if self.add_site_config:
            self.pre_pend_sourcing_site_config()

        if self.bsub_run_command:
            self.bsub_try = 1
            self.ret_code, self.out, self.err = self.run_bsub()
            while self.bsub_exit_status != 0:
                if self.max_memory_used:
                    try:
                        if self.max_memory_used > self.memory_limit:
                            self.memory_limit = int(self.max_memory_used)
                    except:
                        pass

                if self.memory_limit >= 100000:
                    self.memory_limit = self.memory_limit + 40000
                elif self.memory_limit >= 20000:
                    self.memory_limit = self.memory_limit + 30000
                else:
                    self.memory_limit = self.memory_limit + 10000
                self.bsub_try += 1
                logging.info('try {}, memory {}'.format(self.bsub_try, self.memory_limit))
                self.ret_code, self.out, self.err = self.run_bsub()

        if self.ret_code != 0:
            logging.error('return code: {}'.format(self.ret_code))
            logging.error('out: {}'.format(self.out))
            logging.error('error: {}'.format(self.err))
        else:
            logging.info('worked')

        return self.ret_code

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
            open(fname, 'a').close()

    def get_site_config_command(self, suffix=''):
        site_config_init_path = self.cI.get('TOP_WWPDB_SITE_CONFIG_INIT')
        site_loc = self.cI.get('WWPDB_SITE_LOC')
        site_config_command = '. {} --siteid {} --location {} {} > /dev/null;'.format(site_config_init_path,
                                                                                      self.siteId, site_loc,
                                                                                      suffix)
        return site_config_command

    def pre_pend_sourcing_site_config(self, database=False):

        self.command = '{} {}'.format(self.get_site_config_command(), self.command)
        if database:
            self.command = '{} {}'.format(self.get_site_config_command(suffix='--database'), self.command)

    def check_bsub_finished(self):
        # pause to allow system to write out bsub out file.
        time.sleep(10)
        if not os.path.exists(self.bsub_out_file):
            retries = 0
            logging.info('bsub out file not present - waiting for bsub to finish')
            max_num_of_retries = (int(self.bsub_timeout) / int(self.bsub_retry_delay))
            while retries < max_num_of_retries:
                if os.path.exists(self.bsub_out_file):
                    logging.info('found bsub out file')
                    break
                else:
                    retries += 1
                    logging.info(
                        'try {} of {}, wait for {} seconds'.format(retries, max_num_of_retries, self.bsub_retry_delay))
                    time.sleep(int(self.bsub_retry_delay))

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

        if os.path.exists(self.bsub_out_file):
            os.remove(self.bsub_out_file)

        bsub_command = list()
        if self.bsub_login_node:
            bsub_command.append("ssh {} '".format(self.bsub_login_node))
        if self.bsub_source_command:
            bsub_command.append('{};'.format(self.bsub_source_command))
        bsub_command.append(self.bsub_run_command)
        bsub_command.append('-J {}'.format(self.job_name))
        bsub_command.append('-oo {}'.format(self.bsub_log_file))
        bsub_command.append('-eo {}/{}_error.log'.format(self.log_dir, self.job_name))
        bsub_command.append('-Ep "touch {}"'.format(self.bsub_out_file))
        if self.pdbe_memory_limit and self.memory_limit > self.pdbe_memory_limit:
            bsub_command.append('-P {}'.format('bigmem'))

        bsub_command.append('-q {}'.format(self.pdbe_cluster_queue))
        if 'LSB_JOBGROUP' in os.environ and os.environ['LSB_JOBGROUP']:
            bsub_command.append('-g {}'.format(os.environ['LSB_JOBGROUP']))


        bsub_command.append('-n {}'.format(self.number_of_processors))
        bsub_command.append('-W {}'.format(self.timeout))
        if self.memory_limit:
            bsub_command.append('-R "rusage[mem={0}]" -M {0}'.format(self.memory_limit))
        bsub_command.append('-K "{}"'.format(self.command))
        # bsub_command.append('"{}"'.format(self.command))
        if self.bsub_login_node:
            bsub_command.append("'")

        command_string = ' '.join(bsub_command)
        self.executed_command = command_string
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

    def normalise_mem_units(self, memory, memory_unit):
        if memory_unit == 'GB':
            memory = memory * 1024
        elif memory_unit == 'KB':
            memory = int(memory / 1024)
        return memory

    def parse_bsub_log(self):
        self.bsub_exit_status = 0
        self.max_memory_used = 0
        if os.path.exists(self.bsub_log_file):
            with open(self.bsub_log_file, 'r') as log_file:
                for l in log_file:
                    if 'Max Memory :' in l:
                        try:
                            memory_used = l.split(':')[-1].strip()
                            memory_unit = memory_used.split(' ')[1]
                            max_memory_used = int(memory_used.split(' ')[0])
                            self.max_memory_used = self.normalise_mem_units(max_memory_used, memory_unit)
                        except Exception as e:
                            logging.error(e)
                        continue

                    if 'Average Memory :' in l:
                        try:
                            memory_used = l.split(':')[-1].strip()
                            memory_unit = memory_used.split(' ')[1]
                            avg_memory_used = int(memory_used.split(' ')[0])
                            self.avg_memory_used = self.normalise_mem_units(avg_memory_used, memory_unit)
                        except Exception as e:
                          logging.error(e)
                        continue

                    if 'CPU time :' in l:
                        try:
                            cpu_time = l.split(':')[-1].strip()
                            self.cpu_time = float(cpu_time.split()[0])
                        except Exception as e:
                            logging.error(e)
                        continue

                    if 'Run time :' in l:
                        try:
                            job_time = l.split(':')[-1].strip()
                            self.job_time = float(job_time.split()[0])
                        except Exception as e:
                            logging.error(e)
                        continue

                    if 'Max Threads :' in l:
                        try:
                            self.max_threads = int(l.split(':')[-1].strip())
                        except Exception as e:
                            logging.error(e)
                        continue

                    if 'Max Processes :' in l:
                        try:
                            self.max_processes = int(l.split(':')[-1].strip())
                        except Exception as e:
                            logging.error(e)
                        continue


                    if 'TERM_MEMLIMIT' in l:
                        self.bsub_exit_status = 1

        logging.info('Max memory used: {} {}'.format(self.max_memory_used, self.memory_unit))
        logging.info('bsub exit status: {}'.format(self.bsub_exit_status))

    def run_bsub(self):
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        temp_file = os.path.join(self.log_dir, 'bsub_temp_file.out')

        # if get non ok exit status from bsub then wait 30 seconds and try again.
        i = 0
        rc, out, err = 0, None, None

        # error codes
        # 0 everything is ok
        # 159/153 file too large - need additional resources, trying again wont help
        # 255 is ssh connection dropped so task is still ongoing - this is also when lsf is not ready
        allowed_codes = (0, 153, 159)

        while i < 10:
            rc, out, err = self.launch_bsub()
            if rc in allowed_codes:
                break
            delay_time = i * 2
            logging.info('bsub return code of {}. Waiting for {}'.format(rc, delay_time))
            time.sleep(delay_time)
            i += 1

        if rc not in allowed_codes:
            return rc, out, err

        self.touch(temp_file)
        self.check_bsub_finished()
        self.parse_bsub_log()

        return rc, out, err

class RunRemoteFlow():

    def __init__(self, job_name, command, lPathFull, timeout, num_threads, starting_memory):
        self.job_name = job_name
        self.command = command
        self.lPathFull = lPathFull
        self.timeout = timeout
        self.num_threads = num_threads
        self.starting_memory = starting_memory
        self.flow_id = 'efcd4cd5-dadc-451f-9df6-32c8114e431e' # Group Flow ID for RunRemotely


    def register_flow(self):
        job_name = Parameter('job_name', default = "Default Job")
        command =  Parameter('command', default = "ls")
        lPathFull =  Parameter('lPathFull', default = "/tmp")
        timeout = Parameter('timeout', default = 5600)
        numThreads = Parameter('number_of_processors', default= 1)
        startingMemory = Parameter('memory_limit', 0)

        with Flow('Run Remotely') as flow:
            rr = run_remote_task(command=command, job_name=job_name, log_dir=lPathFull,
                                 timeout=timeout, number_of_processors=numThreads,
                                 memory_limit=startingMemory)
            state = save_remote_run_detail(rr)

        # self.flow_id = flow.register("Remote Running")
        self.flow_id = flow.register("Remote Running", idempotency_key=flow.serialized_hash())

    def run_flow(self):
        client = prefect.Client()
        params= {
            'job_name' : self.job_name,
            'command' : self.command,
            'lPathFull' : self.lPathFull,
            'timeout' : self.timeout,
            'number_of_processors' : self.num_threads,
            'memory_limit' : self.starting_memory
        }
        flow_run_id = client.create_flow_run(flow_id=self.flow_id, parameters=params, run_name=self.job_name)
        state = client.get_flow_run_state(flow_run_id )

        # We are making this a blocking call
        while not state.is_finished():
            state = client.get_flow_run_state(flow_run_id )
            time.sleep(1)

        if state.is_successful():
            return 0
        else:
            return 1

    def run(self):
        self.register_flow()
        exit_code = self.run_flow()
        return exit_code

@task
def run_remote_task(command, job_name, log_dir, timeout, number_of_processors,memory_limit):
    logger = prefect.context.get("logger")
    logger.info(f"Job: {job_name}")
    logger.info(f"Command to execute: {command}")
    rr = RunRemote(command=command, job_name=job_name, log_dir=log_dir,
              timeout=timeout, number_of_processors=number_of_processors,
              memory_limit=memory_limit)
    start_time = time.time()
    rr.ret_code = rr.run()
    try:
        logger.info(f"Executed: {rr.executed_command}")
        logger.info(f"Remote Task Ended | Exit Code: {rr.ret_code}")
        logger.info(f'BSUB Log path: {rr.bsub_log_file}')
        end_time = time.time()
        rr.run_duration = end_time - start_time
        logger.info(f"Duration: {rr.run_duration} seconds")
        logger.info(f"Memory Used: {rr.max_memory_used} MB")
        logger.info(f"Number of Processors: {rr.number_of_processors}")
    except Exception as e:
        logger.info(e)
    return rr


@task
def save_remote_run_detail(rr):
    db_Host = rr.cI.get("SITE_DB_HOST_NAME")
    db_Name = rr.cI.get("SITE_DB_DATABASE_NAME")
    db_User = rr.cI.get("SITE_DB_USER_NAME")
    db_Pw = rr.cI.get("SITE_DB_PASSWORD")
    db_Port = int(rr.cI.get("SITE_DB_PORT_NUMBER"))
    if rr.memory_limit  == 0:
        rr.memory_limit = "NULL"
    else:
        rr.memory_limit = f"'{str(rr.memory_limit)}'"
    #     Need to add Depositin ID,, correct no.of process, threads, cpu time
    insertion_query= f'''INSERT into run_statistics 
            (job_name, memory_requested, max_memory_used, avg_memory_used, exit_status, attempts, number_of_processor, 
            max_threads, max_processes, job_time, cpu_time, total_time) 
            VALUES ('{rr.job_name}', {rr.memory_limit}, '{rr.max_memory_used}', '{rr.avg_memory_used}', 
            '{rr.ret_code}', '{rr.bsub_try}','{rr.number_of_processors}','{rr.max_threads}', '{rr.max_processes}', 
            '{rr.job_time}', '{rr.cpu_time}', '{rr.run_duration}')
            '''
    logger.info(insertion_query)
    db_task = mysql.MySQLExecute(db_Name, db_User, db_Pw, db_Host, port=db_Port, commit=True)
    db_task.run(query=insertion_query)
    return rr.ret_code


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', help='debugging', action='store_const', dest='loglevel', const=logging.DEBUG,
                        default=logging.INFO)
    parser.add_argument('--command', help='command to run', type=str, required=True)
    parser.add_argument('--job_name', help='name for the job', type=str, required=True)
    parser.add_argument('--log_dir', help='directory to store log file in', type=str, required=True)
    parser.add_argument('--memory_limit', help='starting memory limit', type=int, default=0)
    parser.add_argument('--num_processors', help='number of processors', type=int, default=1)
    parser.add_argument('--add_site_config', help='add site config to command', action='store_true')
    parser.add_argument('--add_site_config_with_database', help='add site config with database to command',
                        action='store_true')

    args = parser.parse_args()
    logger.setLevel(args.loglevel)

    run_remote = RunRemote(command=args.command,
                           job_name=args.job_name,
                           log_dir=args.log_dir,
                           memory_limit=args.memory_limit,
                           number_of_processors=args.num_processors,
                           add_site_config=args.add_site_config,
                           add_site_config_database=args.add_site_config_with_database)

    ret = run_remote.run()

    if ret != 0:
        message = '{} failed'.format(args.job_name)
        annotation_email = run_remote.cI.get('ANNOTATION_EMAIL')
        if annotation_email:
            command = 'mail -s "{} failed" {}'.format(args.job_name, annotation_email)
            run_remote.run_command(command=command)

    sys.exit(ret)
