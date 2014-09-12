##
#
# File:    RcsbDpUtilityNMRTests.py
# Author:  J. Westbrook
# Date:    Sept 12,2014
# Version: 0.001
#
# Updates:
##
"""
Test cases from 

"""

import sys, unittest, os, os.path, traceback

from wwpdb.api.facade.ConfigInfo          import ConfigInfo,getSiteId
from wwpdb.utils.rcsb.DataFile            import DataFile
from wwpdb.utils.rcsb.RcsbDpUtility       import RcsbDpUtility

from wwpdb.api.facade.WfDataObject  import WfDataObject



class RcsbDpUtilityAnnotTests(unittest.TestCase):
    def setUp(self):
        self.__lfh=sys.stderr        
        # Pick up site information from the environment or failover to the development site id.
        self.__siteId=getSiteId(defaultSiteId='WWPDB_DEPLOY_TEST')
        self.__lfh.write("\nTesting with site environment for:  %s\n" % self.__siteId)
        #
        self.__tmpPath         = './rcsb-tmp-dir'        
        cI=ConfigInfo(self.__siteId)
        
        self.__testFilePath       = './data'
        #
        self.__testFileStarCs    = '2MMZ_cs.str'
        self.__testFileNmrModel  = '2MMZ.cif'
        #
        self.__testNmrModel      = '2MMZ.cif'
        self.__testNmrMr         = '2MMZ.mr'
        self.__testNmrCsFullStar = '2MMZ_cs.str'
        
        #

    def tearDown(self):
        pass


    def testAnnotCSCheck(self): 
        """  Test CS file check
                             'nmr-cs-check-report'         :  (['html'], 'nmr-cs-check-report'),
                             'nmr-cs-xyz-check-report'     :  (['html'], 'nmr-cs-xyz-check-report'),
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of="cs-file-check.html"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath=os.path.join(self.__testFilePath,self.__testFileStarCs)
            dp.imp(inpPath)
            dp.op("annot-chem-shift-check")
            dp.expLog("annot-cs-file-check.log")
            dp.exp(of)            
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()


    def testAnnotCSCoordCheck(self): 
        """  Test CS + Coordindate file check
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of="cs-coord-file-check.html"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath=os.path.join(self.__testFilePath,self.__testFileStarCs)
            #
            xyzPath=os.path.abspath(os.path.join(self.__testFilePath,self.__testFileNmrModel))
            dp.imp(inpPath)
            dp.addInput(name="coordinate_file_path",value=xyzPath)            
            dp.op("annot-chem-shift-coord-check")
            dp.expLog("annot-cs-coord-file-check.log")
            dp.exp(of)            
            #dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()


def suiteAnnotNMRTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotCSCheck"))
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotCSCoordCheck"))
    return suiteSelect        



if __name__ == '__main__':
    #
    doAll=False
    if (doAll):
        mySuite=suiteAnnotNMRTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)    


    else:
        pass

    mySuite=suiteAnnotNMRTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)    

