##
#
# File:    RcsbDpUtilityNMRTests.py
# Author:  J. Westbrook
# Date:    Sept 12,2014
# Version: 0.001
#
# Updates:
#   16-Oct-2018  jdw   adapt for Py2/3 and Python packaging
##
"""
Test cases for reading, concatenating and obtaining diagnostics about chemical shift files --

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
from wwpdb.utils.dp.PdbxChemShiftReport import PdbxChemShiftReport
from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility


logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class RcsbDpUtilityNMRTests(unittest.TestCase):

    def setUp(self):
        self.__lfh = sys.stderr
        self.__verbose = True
        # Pick up site information from the environment or failover to the development site id.
        self.__siteId = getSiteId(defaultSiteId=None)
        logger.info("\nTesting with site environment for:  %s\n" % self.__siteId)
        #
        self.__cI = ConfigInfo(self.__siteId)

        self.__testFilePath = os.path.join(TOPDIR, 'wwpdb', 'mock-data', 'dp-utils')
        self.__tmpPath = os.path.join(HERE, 'test-output')
        #
        self.__testFileStarCs = '2MMZ-cs.str'
        self.__testFileNmrModel = '2MMZ.cif'
        self.__testFileNmrModelAlt = '1MM0.cif'
        self.__testFileNmrMr = '2MMZ.mr'
        self.__testConcatCS = '2mmz-cs-file-full-2.cif'

        #

    def tearDown(self):
        pass

    def testAnnotCSCheck(self):
        """  Test CS file check
                             'nmr-cs-check-report'         :  (['html'], 'nmr-cs-check-report'),
                             'nmr-cs-xyz-check-report'     :  (['html'], 'nmr-cs-xyz-check-report'),
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of = "cs-file-check.html"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath = os.path.join(self.__testFilePath, self.__testFileStarCs)
            dp.imp(inpPath)
            dp.op("annot-chem-shift-check")
            dp.expLog("annot-cs-file-check.log")
            dp.exp(of)
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotCSCoordCheck(self):
        """  Test CS + Coordindate file check
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of = "cs-coord-file-check.html"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath = os.path.join(self.__testFilePath, self.__testFileStarCs)
            #
            xyzPath = os.path.abspath(os.path.join(self.__testFilePath, self.__testFileNmrModel))
            dp.imp(inpPath)
            dp.addInput(name="coordinate_file_path", value=xyzPath)
            dp.op("annot-chem-shift-coord-check")
            dp.expLog("annot-cs-coord-file-check.log")
            dp.exp(of)
            # dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testUploadShiftOneCheck(self):
        """  Test upload check of one CS file  ---   upload single file
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            dp.setDebugMode(flag=True)
            inpPath = os.path.join(self.__testFilePath, self.__testFileStarCs)
            outPath = "output-cs-file-full.cif"
            chkPath = "cs-diag-upload-check-1.cif"
            dp.addInput(name="chemical_shifts_file_path_list", value=[inpPath])
            dp.addInput(name="chemical_shifts_auth_file_name_list", value=['cs_file_1'])
            dp.addInput(name="chemical_shifts_upload_check_file_path", value=chkPath)

            dp.op("annot-chem-shifts-upload-check")
            dp.expLog("annot-chem-shifts-upload-check.log")
            dp.exp(outPath)
            # dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testUploadShiftListCheck(self):
        """  Test upload check of one CS file  ---  Upload multiple files
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            dp.setDebugMode(flag=True)
            inpPath = os.path.join(self.__testFilePath, self.__testFileStarCs)
            outPath = "output-cs-file-full-2.cif"
            chkPath = "cs-diag-upload-check-2.cif"
            dp.addInput(name="chemical_shifts_file_path_list", value=[inpPath, inpPath])
            dp.addInput(name="chemical_shifts_auth_file_name_list", value=['cs_file_1', 'cs_file_2'])
            dp.addInput(name="chemical_shifts_upload_check_file_path", value=chkPath)

            dp.op("annot-chem-shifts-upload-check")
            dp.expLog("annot-chem-shifts-upload-check-2.log")
            dp.exp(outPath)
            # dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testChemicalShiftCoordinateCheck(self):
        """  Test upload check of one CS file  ---   Using a PDB Archive STAR file -- (Does not work)
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            dp.setDebugMode(flag=True)
            inpPath = os.path.join(self.__testFilePath, self.__testFileStarCs)
            xyzPath = os.path.abspath(os.path.join(self.__testFilePath, self.__testFileNmrModel))
            outPath = "output-cs-file.cif"
            chkPath = "cs-diag-atom-name-check.cif"
            dp.imp(inpPath)
            dp.addInput(name="coordinate_file_path", value=xyzPath)
            dp.addInput(name="chemical_shifts_coord_check_file_path", value=chkPath)

            dp.op("annot-chem-shifts-atom-name-check")
            dp.expLog("annot-chem-shifts-atom-name-check.log")
            dp.exp(outPath)
            # dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testChemicalShiftCoordinateCheck2(self):
        """  Test upload check of one CS file  ---  Using a processed chemical shift file
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            dp.setDebugMode(flag=True)
            inpPath = os.path.join(self.__testFilePath, self.__testConcatCS)
            xyzPath = os.path.abspath(os.path.join(self.__testFilePath, self.__testFileNmrModel))
            outPath = "output-cs-file-concat.cif"
            chkPath = "cs-diag-atom-name-check-concat.cif"
            dp.imp(inpPath)
            dp.addInput(name="coordinate_file_path", value=xyzPath)
            dp.addInput(name="chemical_shifts_coord_check_file_path", value=chkPath)

            dp.op("annot-chem-shifts-atom-name-check")
            dp.expLog("annot-chem-shifts-atom-name-check-concat.log")
            dp.exp(outPath)
            # dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testChemicalShiftCoordinateCheck2Alt(self):
        """  Test upload check of one CS file  --- Using the wrong model to generate errors
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            dp.setDebugMode(flag=True)
            inpPath = os.path.join(self.__testFilePath, self.__testConcatCS)
            xyzPath = os.path.abspath(os.path.join(self.__testFilePath, self.__testFileNmrModelAlt))
            outPath = "output-cs-file-concat-alt.cif"
            chkPath = "cs-diag-atom-name-check-concat-alt.cif"
            dp.imp(inpPath)
            dp.addInput(name="coordinate_file_path", value=xyzPath)
            dp.addInput(name="chemical_shifts_coord_check_file_path", value=chkPath)

            dp.op("annot-chem-shifts-atom-name-check")
            dp.expLog("annot-chem-shifts-atom-name-check-concat-alt.log")
            dp.exp(outPath)
            #
            if os.access(chkPath, os.R_OK):
                csr = PdbxChemShiftReport(inputPath=chkPath, verbose=self.__verbose, log=self.__lfh)
                status = csr.getStatus()
                logger.info("Status code: %s\n" % status)
                warnings = csr.getWarnings()
                logger.info("\n\nWarning count : %d\n %s\n" % (len(warnings), ('\n').join(warnings)))
                #
                errors = csr.getErrors()
                logger.info("\n\nError count : %d\n %s\n" % (len(errors), ('\n').join(errors)))
            #
            # dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()


def suiteAnnotBmrbNmrTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityNMRTests("testAnnotCSCheck"))
    suiteSelect.addTest(RcsbDpUtilityNMRTests("testAnnotCSCoordCheck"))
    return suiteSelect


def suiteAnnotNmrTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityNMRTests("testUploadShiftOneCheck"))
    suiteSelect.addTest(RcsbDpUtilityNMRTests("testUploadShiftListCheck"))
    suiteSelect.addTest(RcsbDpUtilityNMRTests("testChemicalShiftCoordinateCheck"))
    suiteSelect.addTest(RcsbDpUtilityNMRTests("testChemicalShiftCoordinateCheck2"))
    suiteSelect.addTest(RcsbDpUtilityNMRTests("testChemicalShiftCoordinateCheck2Alt"))

    return suiteSelect


if __name__ == '__main__':
    #

    mySuite = suiteAnnotBmrbNmrTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)

    mySuite = suiteAnnotNmrTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)
