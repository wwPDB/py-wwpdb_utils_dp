##
#
# File:    RcsbDpUtilityPisaTests.py
# Author:  J. Westbrook
# Date:    June 20,2012
# Version: 0.001
#
# Update:
#   28-Aug-2012  jdw   test with latest tools deployment using site_id WWPDB_DEPLOY_TEST
#   16-Oct-2018  jdw   adapt for Py2/3 and Python packaging
##
"""
Test cases for assembly calculation using both PDBx/mmCIF and PDB form input data files -

"""
import logging
import os
import platform
import sys
import unittest

if __package__ is None or __package__ == '':
    import sys
    from os import path
    sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
    from commonsetup import TESTOUTPUT, TOPDIR, toolsmissing
else:
    from .commonsetup import TESTOUTPUT, TOPDIR, toolsmissing

from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId
from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility


logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)


@unittest.skipIf(toolsmissing, "Tools not available for testing")
@unittest.skipIf(toolsmissing, "Tools not available for testing")
class RcsbDpUtilityTests(unittest.TestCase):

    def setUp(self):
        # Pick up site information from the environment or failover to the development site id.
        self.__siteId = getSiteId(defaultSiteId=None)
        logger.info("\nTesting with site environment for:  %s\n" % self.__siteId)
        #
        self.__cI = ConfigInfo(self.__siteId)
        self.__testFilePath = os.path.join(TOPDIR, 'wwpdb', 'mock-data', 'dp-utils')
        self.__tmpPath = TESTOUTPUT
        #
        self.__testFilePdbPisa = '3rer.pdb'
        self.__testFileCifPisa = '3rer.cif'
        #
        logger.info("\nTest file path %s\n" % (self.__testFilePath))
        logger.info("\nCIF  file path %s\n" % (self.__testFileCifPisa))

    def tearDown(self):
        pass

    def testPisaAnalysisPdb(self):
        """
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            pdbPath = os.path.join(self.__testFilePath, self.__testFilePdbPisa)
            dp.imp(pdbPath)
            dp.addInput(name="pisa_session_name", value="session_3re3_pdb")
            dp.op("pisa-analysis")
            dp.expLog("pisa-anal-pdb.log.gz")
            dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testPisaAnalysisCif(self):
        """
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            cifPath = os.path.join(self.__testFilePath, self.__testFileCifPisa)
            dp.imp(cifPath)
            dp.addInput(name="pisa_session_name", value="session_test_cif")
            dp.op("pisa-analysis")
            dp.expLog("pisa-anal-cif.log.gz")
            dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testPisaAssemblyReportXmlCif(self):
        """
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            fPath = os.path.join(self.__testFilePath, self.__testFileCifPisa)
            dp.imp(fPath)
            dp.addInput(name="pisa_session_name", value="session_test_cif")
            dp.op("pisa-analysis")
            dp.expLog("pisa-anal-assembly-cif.log")
            dp.op("pisa-assembly-report-xml")
            dp.exp("pisa-assembly-report-cif.xml")
            dp.expLog("pisa-report-xml-cif.log")
            #
            dp.op("pisa-interface-report-xml")
            dp.exp("pisa-interface-report-cif.xml")
            dp.expLog("pisa-interface-report-xml-cif.log")
            dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testPisaAssemblyReportXmlPdb(self):
        """
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            fPath = os.path.join(self.__testFilePath, self.__testFilePdbPisa)
            dp.imp(fPath)
            dp.addInput(name="pisa_session_name", value="session_3re3_cif")
            dp.op("pisa-analysis")
            dp.expLog("pisa-anal-assembly-pdb.log.gz")
            dp.op("pisa-assembly-report-xml")
            dp.exp("pisa-assembly-report-pdb.xml")
            dp.expLog("pisa-report-xml-pdb.log.gz")
            dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testPisaAssemblyDownloadModelCif(self):
        """
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            fPath = os.path.join(self.__testFilePath, self.__testFileCifPisa)
            dp.imp(fPath)
            dp.addInput(name="pisa_session_name", value="session_3re3_cif")
            dp.op("pisa-analysis")
            dp.expLog("pisa-anal-assembly-cif.log.gz")
            dp.op("pisa-assembly-report-xml")
            dp.exp("pisa-assembly-report-cif.xml")
            dp.expLog("pisa-report-xml-cif.log.gz")
            #
            for assemId in ['1', '2', '3', '4', '5']:
                dp.addInput(name="pisa_assembly_id", value=assemId)
                oFileName = '3rer-assembly-' + assemId + '.cif.gz'
                oLogName = '3rer-assembly-' + assemId + '-cif.log.gz'
                dp.op("pisa-assembly-coordinates-cif")
                dp.exp(oFileName)
                dp.expLog(oLogName)
            dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testPisaAssemblyDownloadModelPdb(self):
        """
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            fPath = os.path.join(self.__testFilePath, self.__testFileCifPisa)
            dp.imp(fPath)
            dp.addInput(name="pisa_session_name", value="session_3re3_cif")
            dp.op("pisa-analysis")
            dp.expLog("pisa-anal-assembly-cif.log.gz")
            dp.op("pisa-assembly-report-xml")
            dp.exp("pisa-assembly-report-cif.xml")
            dp.expLog("pisa-report-xml-cif.log.gz")
            #
            for assemId in ['1', '2', '3', '4', '5']:
                dp.addInput(name="pisa_assembly_id", value=assemId)
                oFileName = '3rer-assembly-' + assemId + '.pdb.gz'
                oLogName = '3rer-assembly-' + assemId + '-pdb.log.gz'
                dp.op("pisa-assembly-coordinates-pdb")
                dp.exp(oFileName)
                dp.expLog(oLogName)
            dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testPisaAssemblyMergeModelCif(self):
        """
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            fPath = os.path.join(self.__testFilePath, self.__testFileCifPisa)
            assignPath = os.path.join(self.__testFilePath, "3rer_assembly_assign_P1.cif")
            dp.imp(fPath)
            dp.addInput(name="pisa_session_name", value="session_3re3-cif")
            dp.op("pisa-analysis")
            dp.op("pisa-assembly-report-xml")
            dp.exp("pisa-assembly-report-cif.xml")
            #
            cifPath = os.path.join(self.__testFilePath, self.__testFileCifPisa)
            dp.imp(cifPath)
            #
            # assignmentFile      = self.__inputParamDict['pisa_assembly_assignment_file_path']
            #
            dp.addInput(name="pisa_assembly_file_path", value="pisa-assembly-report-cif.xml", type="file")
            dp.addInput(name="pisa_assembly_assignment_file_path", value=assignPath, type="file")
            dp.op("pisa-assembly-merge-cif")
            dp.exp("3rer-updated.cif.gz")
            dp.expLog("3rer-updated-cif.log.gz")
            # dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()


def suitePisaTestsCif():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityTests("testPisaAnalysisCif"))
    suiteSelect.addTest(RcsbDpUtilityTests("testPisaAssemblyReportXmlCif"))
    suiteSelect.addTest(RcsbDpUtilityTests("testPisaAssemblyDownloadModelCif"))
    suiteSelect.addTest(RcsbDpUtilityTests("testPisaAssemblyMergeModelCif"))
    return suiteSelect


def suitePisaTestsPdb():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityTests("testPisaAnalysisPdb"))
    suiteSelect.addTest(RcsbDpUtilityTests("testPisaAssemblyReportXmlPdb"))
    suiteSelect.addTest(RcsbDpUtilityTests("testPisaAssemblyDownloadModelPdb"))

    return suiteSelect


if __name__ == '__main__':
    #
    if (False):
        mySuite = suitePisaTestsPdb()
        unittest.TextTestRunner(verbosity=2).run(mySuite)
    #
    mySuite = suitePisaTestsCif()
    unittest.TextTestRunner(verbosity=2).run(mySuite)
