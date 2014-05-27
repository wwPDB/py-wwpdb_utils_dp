##
#
# File:    RcsbDpUtilityMapTests.py
# Author:  J. Westbrook
# Date:    May 27,2014
# Version: 0.001
#
# Update:
##
"""
Test cases for map production and structure factor reflection file validation - 

"""

import sys, unittest, os, os.path, traceback

from wwpdb.api.facade.ConfigInfo          import ConfigInfo,getSiteId
from wwpdb.utils.rcsb.RcsbDpUtility       import RcsbDpUtility


class RcsbDpUtilityMapTests(unittest.TestCase):
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
        self.__testFileValidateXyz = "1cbs.cif"
        self.__testFileValidateSf  = "1cbs-sf.cif"
        self.__testValidateIdList  = ["1cbs","3of4","3oqp"]
        self.__testArchiveIdList  = [("D_900002","4EC0"),("D_600000","4F3R")]
        #
        self.__testFileCifSeq       = "RCSB095269_model_P1.cif.V1"
        self.__testFileSeqAssign    = "RCSB095269_seq-assign_P1.cif.V1"
        
        self.__testFileMtzBad  = "mtz-bad.mtz"
        self.__testFileMtzGood = "mtz-good.mtz"        

        self.__testFileMtzRunaway  = "bad-runaway.mtz"
        self.__testFileXyzRunaway  = "bad-runaway.cif"

    def tearDown(self):
        pass

    def testAnnotMapCalc(self): 
        """  Test create density maps --
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            for pdbId in ['1cbs','3of4','3oqp']:
                of2fofc=pdbId+"_2fofc.map"
                offofc=pdbId+"_fofc.map"

                testFileXyz=pdbId+".cif"
                testFileSf=pdbId+"-sf.cif"
                
                dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
                dp.setDebugMode()
                xyzPath=os.path.join(self.__testFilePath,testFileXyz)
                sfPath=os.path.join(self.__testFilePath,testFileSf)            
                dp.imp(xyzPath)
                dp.addInput(name="sf_file_path",value=sfPath)            
                dp.op("annot-make-maps")
                dp.expLog(pdbId+"-annot-make-maps.log")
                dp.expList(dstPathList=[of2fofc,offofc])
                #dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testAnnotLigandMapCalc(self): 
        """  Test create density maps --
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            for pdbId in ['2yn2']:
                #of2fofc=pdbId+"_2fofc.map"
                #offofc=pdbId+"_fofc.map"

                testFileXyz=pdbId+".cif"
                testFileSf=pdbId+"-sf.cif"
                
                dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True,log=self.__lfh)
                xyzPath=os.path.join(self.__testFilePath,testFileXyz)
                sfPath=os.path.join(self.__testFilePath,testFileSf)     
                outMapPath='.'
                outMapPathFull=os.path.abspath(outMapPath) 
                #
                dp.imp(xyzPath)
                dp.addInput(name="sf_file_path",value=sfPath)            
                dp.addInput(name="output_map_file_path",value=outMapPathFull)            
                dp.op("annot-make-ligand-maps")
                dp.expLog(pdbId+"-annot-make-ligand-maps.log")
                #dp.expList(dstPathList=[of2fofc,offofc])
                #dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testAnnotDccReport(self): 
        """  Test create DCC report -
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            ofn="dcc-report.cif"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            dp.setDebugMode()
            xyzPath=os.path.join(self.__testFilePath,self.__testFileValidateXyz)
            sfPath=os.path.join(self.__testFilePath,self.__testFileValidateSf)            
            dp.imp(xyzPath)
            dp.addInput(name="sf_file_path",value=sfPath)            
            dp.op("annot-dcc-report")
            dp.expLog("dcc-report.log")
            dp.exp(ofn)
            #dp.expList(dstPathList=[ofpdf,ofxml])
            dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testAnnotMtz2PdbxGood(self): 
        """  Test mtz to pdbx conversion  (good mtz)
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            diagfn="sf-convert-diags.cif"
            ciffn="sf-convert-datafile.cif"
            dmpfn="sf-convert-mtzdmp.log"
            #
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            dp.setDebugMode()
            mtzPath=os.path.join(self.__testFilePath,self.__testFileMtzGood)
            dp.imp(mtzPath)
            dp.setTimeout(15)
            dp.op("annot-sf-convert")
            dp.expLog("sf-convert.log")
            dp.expList(dstPathList=[ciffn,diagfn,dmpfn])
            #dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()


    def testAnnotMtz2PdbxBad(self): 
        """  Test mtz to pdbx conversion
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            diagfn="sf-convert-diags-bad.cif"
            ciffn="sf-convert-datafile-bad.cif"
            dmpfn="sf-convert-mtzdmp-bad.log"
            #
            #self.__testFileMtzRunaway  = "bad-runaway.mtz"
            #self.__testFileXyzRunaway  = "bad-runaway.cif"
            #
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            mtzPath=os.path.join(self.__testFilePath,self.__testFileMtzBad)
            dp.imp(mtzPath)
            #xyzPath=os.path.join(self.__testFilePath,self.__testFileXyzBad)
            dp.setTimeout(15)
            #dp.addInput(name="xyz_file_path",value=xyzPath)
            dp.op("annot-sf-convert")
            dp.expLog("sf-convert-bad.log")
            dp.expList(dstPathList=[ciffn,diagfn,dmpfn])
            #dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testAnnotMtz2PdbxBadTimeout(self): 
        """  Test mtz to pdbx conversion
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            diagfn="sf-convert-diags-bad-runaway.cif"
            ciffn="sf-convert-datafile-bad-runaway.cif"
            dmpfn="sf-convert-mtzdmp-bad-runaway.log"
            #
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            dp.setDebugMode()
            mtzPath=os.path.join(self.__testFilePath,self.__testFileMtzRunaway)
            dp.imp(mtzPath)
            dp.setTimeout(15)
            dp.op("annot-sf-convert")
            dp.expLog("sf-convert-runaway.log")
            dp.expList(dstPathList=[ciffn,diagfn,dmpfn])
            #dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()



def suiteMapCalcTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityMapTests("testAnnotMapCalc"))
    #suiteSelect.addTest(RcsbDpUtilityMapTests("testAnnotLigandMapCalc"))
    return suiteSelect    

def suiteAnnotDccTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityMapTests("testAnnotDccReport"))
    suiteSelect.addTest(RcsbDpUtilityMapTests("testAnnotMtz2PdbxGood"))
    suiteSelect.addTest(RcsbDpUtilityMapTests("testAnnotMtz2PdbxBad"))
    return suiteSelect        

if __name__ == '__main__':
    # Run all tests -- 
    #
    doAll=False
    if (doAll):

        mySuite=suiteMapCalcTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)        

        mySuite=suiteAnnotDccTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)

    else:
        pass


    mySuite=suiteMapCalcTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)        
