##
#
# File:    RcsbDpUtilitySeqTests.py
# Author:  J. Westbrook
# Date:    April 16, 2013
# Version: 0.001
#
# Update:
# 20-Apr-2013 jdw working on osx for blastp and blastn
# 16-Oct-2018  jdw   adapt for Py2/3 and Python packaging
##
"""
Test cases for sequence search  and entry fetch/extract operations --
"""

import logging
import os
import sys
import unittest

if __package__ is None or __package__ == '':
    from os import path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT, TOPDIR, toolsmissing
else:
    from .commonsetup import TESTOUTPUT, TOPDIR, toolsmissing

from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId
from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility


logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)


@unittest.skipIf(toolsmissing, "Tools not available for testing")
class RcsbDpUtilityTests(unittest.TestCase):

    def setUp(self):

        self.__siteId = getSiteId(defaultSiteId='WWPDB_DEPLOY_TEST')
        logger.info("\nTesting with site environment for:  %s\n" % self.__siteId)
        #
        self.__cI = ConfigInfo(self.__siteId)
        self.__tmpPath = TESTOUTPUT
        #
        self.__testFilePath = os.path.join(TOPDIR, 'wwpdb', 'mock-data', 'dp-utils')
        self.__testFileFastaP = os.path.join(self.__testFilePath, '1KIP.fasta')
        self.__testFileFastaN = os.path.join(self.__testFilePath, '2WDK.fasta')
        #
        logger.info("\nTest fasta protein file path %s\n" % (self.__testFileFastaP))
        logger.info("\nTest fasta RNA     file path %s\n" % (self.__testFileFastaN))

    def tearDown(self):
        pass

    def testProteinSequenceSearch(self):
        """
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            dp.imp(self.__testFileFastaP)
            dp.addInput(name="db_name", value="my_uniprot_all")
            dp.addInput(name="num_threads", value="4")
            dp.addInput(name="evalue", value="0.001")
            dp.op("seq-blastp")
            dp.expLog("seq-blastp.log")
            dp.exp("seq-blastp.xml")
            dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testRnaSequenceSearch(self):
        """
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            dp.imp(self.__testFileFastaN)
            dp.addInput(name="db_name", value="my_ncbi_nt")
            dp.addInput(name="num_threads", value="4")
            dp.addInput(name="evalue", value="0.001")
            dp.op("seq-blastn")
            dp.expLog("seq-blastn.log")
            dp.exp("seq-blastn.xml")
            dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()


def suiteSequenceSearchTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityTests("testProteinSequenceSearch"))
    suiteSelect.addTest(RcsbDpUtilityTests("testRnaSequenceSearch"))
    return suiteSelect


if __name__ == '__main__':
    #
    mySuite = suiteSequenceSearchTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)
