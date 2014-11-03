##
# File:    MultiProcUtilTests.py
# Author:  jdw
# Date:    2-Oct-2011
# Version: 0.001
#
# Updates:
#
##
"""

"""
__docformat__ = "restructuredtext en"
__author__    = "John Westbrook"
__email__     = "jwest@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.01"


import sys, os, time, unittest, traceback, multiprocessing
from MultiProcUtil import MultiProcUtil

class FileStatus(object):
    """  A skeleton class that implements the interface expected by the multiprocessing 
         utility module --

    """
    def __init__(self,topCachePath=None,verbose=True,log=sys.stderr):
        self.__verbose=verbose
        self.__lfh=log
        self.__topCachePath=topCachePath

    def check(self,dataList):
        """  Performs a file system check on the input dataList of directory keys
             within the chemical component repository sandbox.

             Read input list and perform require operation and return list of 
                inputs with successful outcomes.
        """
        retList=[]
        for d in dataList:
            dirPath=os.path.join(self.__topCachePath,d[0])
            #self.__lfh.write("FileStatus.check() testing directory %s\n" % dirPath)            
            if os.access(dirPath,os.R_OK):
                #self.__lfh.write("FileStatus.check() directory %s is ok\n" % dirPath)
                retList.append(d)
        return retList

                 
class MultiProcUtilTests(unittest.TestCase):
    def setUp(self):
        self.__lfh=sys.stderr
        self.__verbose=True
        #
        # Chemical component repository path -
        self.__topCachePath="../../../../../../reference/components/ligand-dict-v3"
        
    def tearDown(self):
        pass
    
    def testMultiProcFs(self):
        """Test case -  
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__,sys._getframe().f_code.co_name))

        try:
            dataS='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            dataList=[a for a in dataS]
            fS=FileStatus(topCachePath=self.__topCachePath,verbose=self.__verbose,log=self.__lfh)
            mpu=MultiProcUtil(verbose=True,log=self.__lfh)
            mpu.set(workerObj=fS,workerMethod="check")
            mpu.runMulti(dataList=dataList,numProc=4)
            self.__lfh.write("Run completed")
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

def suiteMultiProc():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(MultiProcUtilTests("testMultiProcFs"))
    return suiteSelect

    
if __name__ == '__main__':
    #
    if (False):
        pass

    mySuite1=suiteMultiProc()
    unittest.TextTestRunner(verbosity=2).run(mySuite1)    
