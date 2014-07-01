##
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

import sys, unittest, os, os.path, traceback, json,math

from wwpdb.api.facade.ConfigInfo          import ConfigInfo,getSiteId
from wwpdb.utils.rcsb.RcsbDpUtility       import RcsbDpUtility
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


class RcsbDpUtilityEmTests(unittest.TestCase):
    def setUp(self):
        self.__lfh=sys.stderr        
        # Pick up site information from the environment or failover to the development site id.
        self.__siteId=getSiteId(defaultSiteId='WWPDB_DEPLOY_TEST')
        self.__lfh.write("\nTesting with site environment for:  %s\n" % self.__siteId)
        #
        self.__tmpPath         = './rcsb-tmp-dir'        
        cI=ConfigInfo(self.__siteId)
        
        self.__testFilePath  ='./data'
        self.__testMapNormal = "normal.map"
        self.__testMapSpider = "testmap.spi"
        #
        # Brian's protein dna complex 3IYD
        self.__testMapEmd = 'emd_5127.map'


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


    def testReadMapHeader(self): 
        """  Test read map header -- export JSON packet and plot density distribution -
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            #
            inpPath=os.path.join(self.__testFilePath,self.__testMapNormal)
            of=self.__testMapNormal+"_map-header-data_P1.json"
            dp.imp(inpPath)
            dp.op("annot-read-map-header")
            dp.expLog("annot-read-map-header.log")
            dp.exp(of)            
            dp.cleanup()
            #
            mD=json.load(open(of,'r'))
            self.__lfh.write("Map header keys: %r\n" % mD.keys())
            self.__lfh.write("Map header: %r\n" % mD.items())

            self.__lfh.write("Input  header keys: %r\n" % mD['input_header'].keys())
            self.__lfh.write("Output header keys: %r\n" % mD['output_header'].keys())
            #
            x = mD['input_histogram_categories']
            y = mD['input_histogram_values']
            logy=[]
            for v in y:
                if float(v) <= 0.0:
                    logy.append(math.log10(.1))
                else:
                    logy.append(math.log10(float(v)))

            #
            width = float(x[-1] - x[0])/float(len(x))
            #width = 2.0

            plt.bar( x, y, width, color="r", log=True)
            plt.title('Map density distribution')
            plt.ylabel( 'Voxels (log(10))' )
            plt.xlabel( 'Density' )
            
            plotFileName = "map-density-plot.png" 
            plt.savefig( plotFileName, format="png" )

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
    suiteSelect.addTest(RcsbDpUtilityEmTests("testReadMapHeader"))    
    #suiteSelect.addTest(RcsbDpUtilityEmTests("testMapFix"))    
    #suiteSelect.addTest(RcsbDpUtilityEmTests("testEm2EmSpider"))    
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

    mySuite=suiteAnnotEmTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)
