##
# File:    MultiProcUtil.py
# Author:  jdw
# Date:    3-Nov-2014
# Version: 0.001
#
# Updates:
##
"""
Multiprocessing execuction wrapper.  

"""

__docformat__ = "restructuredtext en"
__author__    = "John Westbrook"
__email__     = "jwest@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.001"

import sys, traceback, multiprocessing

class MultiProcWorker(multiprocessing.Process):
    """  Multi-processing working method wrapper -- 

         Worker method must support the following prototype -
    
         retList,diagList=self.__workerFunc(dataList=nextList)            
    """
    def __init__(self,taskQueue,resultQueue,diagQueue,workerFunc,verbose=False,log=sys.stderr):
        multiprocessing.Process.__init__(self)
        self.__taskQueue=taskQueue
        self.__resultQueue=resultQueue
        self.__lfh=log
        self.__verbose=verbose
        self.__workerFunc=workerFunc
        self.__diagQueue=diagQueue
        
    def run(self):
        processName=self.name
        while True:
            nextList=self.__taskQueue.get()
            if nextList is None:
                # end of queue condition
                if self.__verbose:
                    self.__lfh.write("+MultiProcWorker(run)  %s completed task list\n" % processName)
                    self.__lfh.flush()
                break
            #
            retList,diagList=self.__workerFunc(dataList=nextList)            
            self.__resultQueue.put(retList)
            self.__diagQueue.put(diagList)
        return


class MultiProcUtil(object):
    def __init__(self,verbose=True,log=sys.stderr):
        self.__lfh=log
        self.__verbose=verbose
        self.__workFunc=None

    def set(self,workerObj=None,workerMethod=None):
        """  WorkerObject is the instance of object with method named workerMethod() 

             Worker method must support the following prototype - 

             retList=self.__workerFunc(runList=nextList)            
        """  
        try:
            self.__workerFunc = getattr(workerObj, workerMethod)
            return True
        except AttributeError:
            self.__lfh.write("+MultiProcWorker.set() object/attribute error\n")
            return False
        
    ##
    def runMulti(self, dataList=None, numProc=0):
        """ Start multiple processes ... 
        """
        #
        if numProc < 1:
            numProc=multiprocessing.cpu_count()*2

        subLists=[dataList[i::numProc] for i in range(numProc)]
        #
        if (self.__verbose):
            self.__lfh.write("+MultiProcUtil.runMulti() numProc %d subLists %r\n" % (numProc,subLists))
            self.__lfh.flush()
        #
        taskQueue=multiprocessing.Queue()
        resultQueue=multiprocessing.Queue()
        diagQueue=multiprocessing.Queue()        
        #
        # Create list of worker processes
        #
        workers=[MultiProcWorker(taskQueue,resultQueue,diagQueue,self.__workerFunc,verbose=self.__verbose,log=self.__lfh) for i in xrange(numProc) ]
        for w in workers:
            w.start()

        for subList in subLists:
            if len(subList) > 0:
                taskQueue.put(subList)

        for i in xrange(numProc):
            taskQueue.put(None)

        np = numProc
        result=[]
        diagList=[]
        tL=[]
        while np:
            r = resultQueue.get()
            if r is not None and len(r) > 0:
                result.extend(r)

            d = diagQueue.get()
            if d is not None and len(d) > 0:
                for tt in d:
                    if len(str(tt).strip())  > 0:
                        tL.append(tt)
            np -= 1
        diagList=list(set(tL))
        self.__lfh.write("+MultiProcUtil(runMulti() inpput task length %d success length %d\n"  % (len(dataList),len(result)))
        if len(dataList) == len(result):
            self.__lfh.write("+MultiProcUtil(runMulti) all tasks completed\n")
            self.__lfh.flush()
            return True,[],diagList
        else:
            failList=list(set(dataList)-set(result))
            self.__lfh.write("+MultiProcUtil(runMulti) incomplete run\n")
            self.__lfh.flush()
            return False,failList,diagList
