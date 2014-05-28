##
#
# File:    RcsbDpUtilityEmTests.py
# Author:  J. Westbrook
# Date:    May 26,2014
# Version: 0.001
#
# Update:

##
"""
Test cases for EM map annotation tools --  

"""

import sys, unittest, os, os.path, traceback

from wwpdb.api.facade.ConfigInfo          import ConfigInfo,getSiteId
from wwpdb.utils.rcsb.RcsbDpUtility       import RcsbDpUtility


class RcsbDpUtilityEmTests(unittest.TestCase):
    def setUp(self):
        self.__lfh=sys.stderr        
        # Pick up site information from the environment or failover to the development site id.
        self.__siteId=getSiteId(defaultSiteId='WWPDB_DEPLOY_TEST')
        self.__lfh.write("\nTesting with site environment for:  %s\n" % self.__siteId)
        #
        self.__tmpPath         = './rcsb-tmp-dir'        
        cI=ConfigInfo(self.__siteId)
        
        self.__testMapNormal = "normal.map"
        self.__testMapSpider = "testmap.spi"


    def tearDown(self):
        pass


    def testMapFix(self): 
        """  Test mapfix utility
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            #
            inpPath=os.path.join(self.__testFilePath,self.__testMapNormal)
            of=self.__testMapNormal+"-fix.map"
            dp.imp(inpPath)
            dp.op("mapfix-big")
            dp.expLog("mapfix-big.log")
            dp.exp(of)            
            #dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testEm2EmSpider(self): 
        """  Test mapfix utility
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:

            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            #
            inpPath=os.path.join(self.__testFilePath,self.__testMapSpider)
            of=self.__testMapSpider+"-spider-cnv.map"
            dp.imp(inpPath)
            pixelSize=2.54
            dp.addInput(name="pixel-spacing-x",value=pixelSize)
            dp.addInput(name="pixel-spacing-y",value=pixelSize)
            dp.addInput(name="pixel-spacing-z",value=pixelSize)
            dp.op("em2em-spider")
            dp.expLog("em2em-spider.log")
            dp.exp(of)            
            #dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

def suiteAnnotEmTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityEmTests("testMapFix"))    
    suiteSelect.addTest(RcsbDpUtilityEmTests("testEm2EmSpider"))    
    return suiteSelect        



if __name__ == '__main__':
    # Run all tests -- 
    # unittest.main()
    #
    doAll=False
    if (doAll):

        mySuite=suiteAnnotEmTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)

    else:
        pass


    mySuite=suiteMapCalcTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)        
