##
#
# File:    RcsbDpUtilityTests.py
# Author:  j. westbrook
# Date:    9-Sep-2010
# Version: 0.001
#
# Update:
#  Sep 10, 2010 jdw -  Added test cases for chemical component applications.
#                      Cleaned up error reporting .
#
#  Jun 23, 2011 jdw - Update examples -- verify configuration --  site_id = WWPDB_DEV tested 
##
"""
Test cases from 

"""

import sys, unittest, os, os.path, traceback

from wwpdb.api.facade.ConfigInfo          import ConfigInfo
from wwpdb.utils.rcsb.DataFile            import DataFile
from wwpdb.utils.rcsb.RcsbDpUtility       import RcsbDpUtility


class RcsbDpUtilityTests(unittest.TestCase):
    def setUp(self):
        self.__siteId='WWPDB_DEV'
        cI=ConfigInfo(self.__siteId)
        self.__testFilePath    =cI.get('DP_TEST_FILE_PATH')
        self.__testFileCif     =cI.get('DP_TEST_FILE_CIF')
        self.__testFileCifEps1 =cI.get('DP_TEST_FILE_CIFEPS')
        self.__testFileCifEps2 =cI.get('DP_TEST_FILE_CIFEPS_2')
        self.__tmpPath         =cI.get('TMP_PATH')
        self.__lfh=sys.stderr
            
    def tearDown(self):
        pass

    def testCifToPdb(self): 
        """
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath,siteId=self.__siteId,verbose=True)
            cifPath=os.path.join(self.__testFilePath,self.__testFileCif)
            dp.imp(cifPath)
            dp.op("cif2pdb")
            dp.exp("myTest1.pdb.gz")
            dp.expLog("myLog1.log.gz")    
            dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testChemCompAssign(self): 
        """   Test with no links
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath,siteId=self.__siteId,verbose=True)
            dp.setWorkingDir('tmp-assign')
            cifPath=os.path.join(self.__testFilePath,self.__testFileCifEps2)
            (head,tail) = os.path.split(cifPath)
            (id,ext) = os.path.splitext(tail)
            link_file_path=os.path.join(self.__testFilePath,id+"-cc-link.cif")
            dp.addInput(name="id",value=id)
            dp.addInput(name="cc_link_file_path",value=link_file_path,type='file')
            dp.imp(cifPath)
            dp.op("chem-comp-assign")
            dp.exp("chem-comp-assign.cif.gz")
            dp.expLog("chem-comp-assign.log.gz")
            dp.cleanup()

        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testChemCompInstanceUpdate(self): 
        """   Test with no links
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath,siteId=self.__siteId,verbose=True)
            dp.setWorkingDir('tmp-update')
            cifPath=os.path.join(self.__testFilePath,self.__testFileCifEps2)
            (head,tail) = os.path.split(cifPath)
            (id,ext) = os.path.splitext(tail)
            assign_file_path=os.path.join(self.__testFilePath,id+"-cc-assign.cif")
            dp.addInput(name="cc_assign_file_path",value=assign_file_path,type='file')
            dp.imp(cifPath)
            dp.op("chem-comp-instance-update")
            dp.exp(id+"-cc-instance-update.cif.gz")
            dp.expLog("chem-comp-update.log.gz")
            dp.cleanup()

        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testChemCompLink(self): 
        """
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath,siteId=self.__siteId,verbose=True)
            cifPath=os.path.join(self.__testFilePath,self.__testFileCifEps2)
            dp.imp(cifPath)
            dp.op("chem-comp-link")
            dp.exp("chem-comp-link.cif.gz")
            dp.expLog("chem-comp-link.log.gz")    
            dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()


    def testCifEpsToPdb(self): 
        """
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            cifPath=os.path.join(self.__testFilePath,self.__testFileCifEps1)
            dp.imp(cifPath)
            dp.op("cif2pdb")
            dp.exp("myTest2.pdb.gz")
            dp.expLog("myLog2.log.gz")    
            dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def suite():
        return unittest.makeSuite(RcsbDpUtilityTests,'test')

if __name__ == '__main__':
    unittest.main()

