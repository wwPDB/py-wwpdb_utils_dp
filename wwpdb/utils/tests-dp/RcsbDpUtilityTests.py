##
# File:    RcsbDpUtilityTests.py
# Author:  j. westbrook
# Date:    9-Sep-2010
# Version: 0.001
#
# Update:
#  Sep 10, 2010 jdw -  Added test cases for chemical component applications.
#                      Cleaned up error reporting .
#  Jun 23, 2011 jdw -  Update examples -- verify configuration --  site_id = WWPDB_DEV tested
#  Apr 15, 2012 jdw -  Add PISA application tasks
#               jdw -  add cif check application
#  Aug 29, 2012 jdw -  check dependencies installed for site_id WWPDB_DEPLOY_TEST
#  16-Oct-2018  jdw -  adapt for Py2/3 and Python packaging
##
"""
Test cases from

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
    from commonsetup import TESTOUTPUT, TOPDIR, dictsmissing
else:
    from .commonsetup import TESTOUTPUT, TOPDIR, dictsmissing

from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId
from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class RcsbDpUtilityTests(unittest.TestCase):

    def setUp(self):
        self.__tmpPath = TESTOUTPUT
        #
        self.__siteId = getSiteId(defaultSiteId=None)
        logger.info("\nTesting with site environment for:  %s\n" % self.__siteId)
        #
        self.__cI = ConfigInfo(self.__siteId)
        self.__testFilePath = os.path.join(TOPDIR, 'wwpdb', 'mock-data', 'dp-utils')
        self.__testFileCif = '1xbb.cif'

    def tearDown(self):
        pass

    def testCifToPdb(self):
        """
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            cifPath = os.path.join(self.__testFilePath, self.__testFileCif)
            dp.imp(cifPath)
            dp.op("cif2pdb")
            dp.exp("myTest1.pdb.gz")
            dp.expLog("myLog1.log.gz")
            # dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    @unittest.skipIf(dictsmissing, "SITE_PDBX_DICTIONARY_NAME_DICT not in site-config")
    def testCifCheck(self):
        """
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            cifPath = os.path.join(self.__testFilePath, self.__testFileCif)
            dp.imp(cifPath)
            dp.op("check-cif")
            dp.exp("check-cif-diags.txt")
            dp.expLog("check-cif.log")
            # dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    @unittest.skipIf(dictsmissing, "SITE_PDBX_DICTIONARY_NAME_DICT not in site-config")
    def testCifCheckExt(self):
        """
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            for name in ['deposit', 'archive_current', 'archive_next']:
                dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
                cifPath = os.path.join(self.__testFilePath, self.__testFileCif)
                dp.imp(cifPath)
                dp.addInput(name='dictionary', value=name)
                dp.op("check-cif-ext")
                dp.exp("check-cif-diags-%s.txt" % name)
                dp.expLog("check-cif-%s.log" % name)
                # dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    @unittest.skipIf(dictsmissing, "SITE_PDBX_DICTIONARY_NAME_DICT not in site-config")
    def testCif2PdbxExt(self):
        """
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            for name in ['archive_next', 'archive_current']:
                dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
                cifPath = os.path.join(self.__testFilePath, self.__testFileCif)
                dp.imp(cifPath)
                dp.addInput(name='destination', value=name)
                dp.op("cif2pdbx-ext")
                dp.exp("cif2pdbx-ext-%s.cif" % name)
                dp.expLog("cif2pdbx-%s.log" % name)
                # dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()


def suiteMaxitTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityTests("testCifToPdb"))
    return suiteSelect


def suiteMiscTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityTests("testCifCheck"))
    suiteSelect.addTest(RcsbDpUtilityTests("testCifCheckExt"))
    suiteSelect.addTest(RcsbDpUtilityTests("testCif2PdbxExt"))
    return suiteSelect


if __name__ == '__main__':
    # Run all tests --
    # unittest.main()
    #
    mySuite = suiteMaxitTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)
    #
    mySuite = suiteMiscTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)
