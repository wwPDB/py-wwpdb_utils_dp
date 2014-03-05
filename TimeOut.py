import socket,shlex
from subprocess import call,Popen

def __runTimeout(self,command, timeout, logPath=None):
    """ Execute the input command string (sh semantics) as a subprocess with a timeout.


    """
    import subprocess, datetime, os, time, signal, stat
    self.__lfh.write("+__runTimeout() - Execution time out %d (seconds)\n" % timeout)
    start = datetime.datetime.now()
    cmdfile=os.path.join(self.__wrkPath,'timeoutscript.sh')
    ofh=open(cmdfile,'w')
    ofh.write("#!/bin/sh\n")
    ofh.write(command)
    ofh.write("#\n")
    ofh.close()
    st = os.stat(cmdfile)
    os.chmod(cmdfile, st.st_mode | stat.S_IEXEC)
    self.__lfh.write("+__runTimeout() running command %r\n" % cmdfile)        
    process = subprocess.Popen(cmdfile, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False,close_fds=True,preexec_fn=os.setsid)
    while process.poll() is None:
        time.sleep(0.1)
        now = datetime.datetime.now()
        if (now - start).seconds> timeout:
            #os.kill(-process.pid, signal.SIGKILL)
            os.killpg(process.pid, signal.SIGKILL)
            os.waitpid(-1, os.WNOHANG)
            self.__lfh.write("+ERROR __runTimeout() - Execution terminated by timeout %d (seconds)\n" % timeout)
            if logPath is not None:
                ofh=open(logPath,'a')
                ofh.write("+ERROR __runTimeout() Execution terminated by timeout %d (seconds)\n" % timeout)
                ofh.close()
            return None
    self.__lfh.write("+__runTimeout() completed with return code %r\n" % process.stdout.read())
    return 0

