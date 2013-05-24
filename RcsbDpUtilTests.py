"""

File:    RcsbDpUtilTests.py
Author:  jdw
Date:    5-Feb-2010
Version: 0.001

Update: 

"""
import sys, unittest, os, os.path, traceback

from wwpdb.api.facade.ConfigInfo          import ConfigInfo
from wwpdb.utils.rcsb.DataFile            import DataFile
from wwpdb.utils.rcsb.RcsbDpUtil          import RcsbDpUtil


class RcsbDpUtilTests(unittest.TestCase):
    def setUp(self):
        cI=ConfigInfo('DEV')
        self.__testFilePath=cI.get('DP_TEST_FILE_PATH')
        self.__testFileCif=cI.get('DP_TEST_FILE_CIF')
        self.__testFileCifEps=cI.get('DP_TEST_FILE_CIFEPS')        
        self.__tmpPath=cI.get('TMP_PATH')
        #
        self.__rcsbAppsPath=cI.get('SITE_RCSB_APPS_PATH')
        self.lfh=sys.stdout
            
    def tearDown(self):
        pass

    def testCifToPdb(self): 
        """
        """
        self.lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtil(tmpPath=self.__tmpPath,rcsbPath=self.__rcsbPath,verbose=True)
            cifPath=os.path.join(self.__testFilePath,self.__testFileCif)
            dp.imp(cifPath)
            dp.op("cif2pdb")
            dp.exp("myTest1.pdb.gz")
            dp.expLog("myLog1.log.gz")    

        except:
            traceback.print_exc(file=sys.stdout)
            self.fail()

    def testCifEpsToPdb(self): 
        """
        """
        self.lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtil(tmpPath=self.__tmpPath,verbose=True)
            cifPath=os.path.join(self.__testFilePath,self.__testFileCifEps)
            dp.imp(cifPath)
            dp.op("cif2pdb")
            dp.exp("myTest2.pdb.gz")
            dp.expLog("myLog2.log.gz")    

        except:
            traceback.print_exc(file=sys.stdout)
            self.fail()

    def suite():
        return unittest.makeSuite(RcsbDpUtilTests,'test')

if __name__ == '__main__':
    unittest.main()

