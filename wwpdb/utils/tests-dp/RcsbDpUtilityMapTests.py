##
#
# File:    RcsbDpUtilityMapTests.py
# Author:  J. Westbrook
# Date:    May 27,2014
# Version: 0.001
#
# Update:
#  16-Jul-2014 jdw  add tests for ligand maps and omit maps
#  16-Oct-2018 jdw  adapt for Py2/3 and Python packaging
##
"""
Test cases for map production and structure factor reflection file validation -

"""

import logging
import os
import platform
import sys
import unittest

HERE = os.path.abspath(os.path.dirname(__file__))
TOPDIR = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
try:
    TESTOUTPUT = os.path.join(HERE, 'test-output', platform.python_version())
    if not os.path.exists(TESTOUTPUT):
        os.makedirs(TESTOUTPUT)
    mockTopPath = os.path.join(TOPDIR, 'wwpdb', 'mock-data')
    from wwpdb.utils.testing.SiteConfigSetup import SiteConfigSetup
    SiteConfigSetup().setupEnvironment(TESTOUTPUT, mockTopPath)
except Exception:
    pass

from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId
from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class RcsbDpUtilityMapTests(unittest.TestCase):

    def setUp(self):
        self.__siteId = getSiteId(defaultSiteId=None)
        logger.info("\nTesting with site environment for:  %s\n" % self.__siteId)
        #
        self.__tmpPath = os.path.join(HERE, 'test-output')
        self.__cI = ConfigInfo(self.__siteId)
        self.__testFilePath = os.path.join(TOPDIR, 'wwpdb', 'mock-data', 'dp-utils')
        #
        self.__testFileValidateXyz = "1cbs.cif"
        self.__testFileValidateSf = "1cbs-sf.cif"

        self.__testValidateIdList = ["1cbs", "3of4", "3oqp"]
        #
        self.__testFileMtzBad = "mtz-bad.mtz"
        self.__testFileMtzGood = "mtz-good.mtz"

        self.__testFileMtzRunaway = "bad-runaway.mtz"
        self.__testFileXyzRunaway = "bad-runaway.cif"

    def tearDown(self):
        pass

    def testAnnotMapCalc(self):
        """  Test create density maps --
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            for pdbId in self.__testValidateIdList:
                of2fofc = pdbId + "_map-2fofc_P1.map"
                offofc = pdbId + "_map-fofc_P1.map"

                testFileXyz = pdbId + ".cif"
                testFileSf = pdbId + "-sf.cif"

                dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
                dp.setDebugMode()
                xyzPath = os.path.join(self.__testFilePath, testFileXyz)
                sfPath = os.path.join(self.__testFilePath, testFileSf)
                dp.imp(xyzPath)
                dp.addInput(name="sf_file_path", value=sfPath)
                dp.op("annot-make-maps")
                dp.expLog(pdbId + "-annot-make-maps.log")
                dp.expList(dstPathList=[of2fofc, offofc])
                # dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotOmitMapCalc(self):
        """  Test create density maps --
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            for pdbId in self.__testValidateIdList:
                of2fofc = pdbId + "_map-omit-2fofc_P1.map"
                offofc = pdbId + "_map-omit-fofc_P1.map"

                testFileXyz = pdbId + ".cif"
                testFileSf = pdbId + "-sf.cif"

                dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
                dp.setDebugMode()
                xyzPath = os.path.join(self.__testFilePath, testFileXyz)
                sfPath = os.path.join(self.__testFilePath, testFileSf)
                dp.imp(xyzPath)
                dp.addInput(name="sf_file_path", value=sfPath)
                dp.op("annot-make-maps")
                dp.expLog(pdbId + "-annot-make-maps.log")
                dp.expList(dstPathList=[of2fofc, offofc])
                # dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotLigandMapCalc(self):
        """  Test create non-polymer local density maps --
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            for pdbId in ['3of4']:

                testFileXyz = pdbId + ".cif"
                testFileSf = pdbId + "-sf.cif"
                #
                dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
                dp.setDebugMode(flag=True)
                xyzPath = os.path.join(self.__testFilePath, testFileXyz)
                sfPath = os.path.join(self.__testFilePath, testFileSf)
                #
                outDataPath = os.path.join(self.__tmpPath, 'np-cc-maps')
                outIndexPath = os.path.join(self.__tmpPath, 'np-cc-maps', 'np-cc-maps-index.cif')
                #
                dp.imp(xyzPath)
                dp.addInput(name="sf_file_path", value=sfPath)
                dp.addInput(name="output_data_path", value=outDataPath)
                dp.addInput(name="output_index_path", value=outIndexPath)
                dp.op("annot-make-ligand-maps")
                dp.expLog(pdbId + "-annot-make-ligand-maps.log")
                #
                if (False):
                    dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
                    dp.setDebugMode(flag=True)
                    xyzPath = os.path.join(self.__testFilePath, testFileXyz)
                    sfPath = os.path.join(self.__testFilePath, testFileSf)
                    #
                    outDataPath = os.path.join(self.__tmpPath, 'np-cc-omit-maps')
                    outIndexPath = os.path.join(self.__tmpPath, 'np-cc-omit-maps', 'np-cc-omit-maps-index.cif')
                    #
                    dp.imp(xyzPath)
                    dp.addInput(name="omit_map", value=True)
                    dp.addInput(name="sf_file_path", value=sfPath)
                    dp.addInput(name="output_data_path", value=outDataPath)
                    dp.addInput(name="output_index_path", value=outIndexPath)
                    dp.op("annot-make-ligand-maps")
                    dp.expLog(pdbId + "-annot-make-ligand-omit-maps.log")

                    #
                    # This application
                    # dp.cleanup()

        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotDccReport(self):
        """  Test create DCC report -
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            ofn = "dcc-report.cif"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            dp.setDebugMode()
            xyzPath = os.path.join(self.__testFilePath, self.__testFileValidateXyz)
            sfPath = os.path.join(self.__testFilePath, self.__testFileValidateSf)
            dp.imp(xyzPath)
            dp.addInput(name="sf_file_path", value=sfPath)
            dp.op("annot-dcc-report")
            dp.expLog("dcc-report.log")
            dp.exp(ofn)
            # dp.expList(dstPathList=[ofpdf,ofxml])
            dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotMtz2PdbxGood(self):
        """  Test mtz to pdbx conversion  (good mtz)
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            diagfn = "sf-convert-diags.cif"
            ciffn = "sf-convert-datafile.cif"
            dmpfn = "sf-convert-mtzdmp.log"
            #
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            dp.setDebugMode()
            mtzPath = os.path.join(self.__testFilePath, self.__testFileMtzGood)
            dp.imp(mtzPath)
            dp.setTimeout(15)
            dp.op("annot-sf-convert")
            dp.expLog("sf-convert.log")
            dp.expList(dstPathList=[ciffn, diagfn, dmpfn])
            # dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotMtz2PdbxBad(self):
        """  Test mtz to pdbx conversion
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            diagfn = "sf-convert-diags-bad.cif"
            ciffn = "sf-convert-datafile-bad.cif"
            dmpfn = "sf-convert-mtzdmp-bad.log"
            #
            #self.__testFileMtzRunaway  = "bad-runaway.mtz"
            #self.__testFileXyzRunaway  = "bad-runaway.cif"
            #
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            mtzPath = os.path.join(self.__testFilePath, self.__testFileMtzBad)
            dp.imp(mtzPath)
            # xyzPath=os.path.join(self.__testFilePath,self.__testFileXyzBad)
            dp.setTimeout(15)
            # dp.addInput(name="xyz_file_path",value=xyzPath)
            dp.op("annot-sf-convert")
            dp.expLog("sf-convert-bad.log")
            dp.expList(dstPathList=[ciffn, diagfn, dmpfn])
            # dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotMtz2PdbxBadTimeout(self):
        """  Test mtz to pdbx conversion
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            diagfn = "sf-convert-diags-bad-runaway.cif"
            ciffn = "sf-convert-datafile-bad-runaway.cif"
            dmpfn = "sf-convert-mtzdmp-bad-runaway.log"
            #
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            dp.setDebugMode()
            mtzPath = os.path.join(self.__testFilePath, self.__testFileMtzRunaway)
            dp.imp(mtzPath)
            dp.setTimeout(15)
            dp.op("annot-sf-convert")
            dp.expLog("sf-convert-runaway.log")
            dp.expList(dstPathList=[ciffn, diagfn, dmpfn])
            # dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()


def suiteMapCalcTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityMapTests("testAnnotMapCalc"))
    suiteSelect.addTest(RcsbDpUtilityMapTests("testAnnotOmitMapCalc"))
    # suiteSelect.addTest(RcsbDpUtilityMapTests("testAnnotLigandMapCalc"))
    return suiteSelect


def suiteLigandMapCalcTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityMapTests("testAnnotLigandMapCalc"))
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
    doAll = True
    if (doAll):
        mySuite = suiteMapCalcTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)

        mySuite = suiteAnnotDccTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)

        mySuite = suiteLigandMapCalcTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)
    else:
        pass

    #
    mySuite = suiteLigandMapCalcTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)

    mySuite = suiteLigandMapCalcTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)
