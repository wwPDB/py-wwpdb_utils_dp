##
# File:    COMTests.py
# Author:  E.Peisach
# Date:    2-Sep-2021
# Version: 0.001
#
# Update:
##
"""
Test cases for CentreOfMass calculation

"""

import logging
import os
import sys
import unittest

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.abspath(__file__)))
    from commonsetup import TESTOUTPUT, TOPDIR, toolsmissing  # pylint: disable=import-error
else:
    from .commonsetup import TESTOUTPUT, TOPDIR, toolsmissing

from wwpdb.utils.config.ConfigInfo import getSiteId

from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)


@unittest.skipIf(toolsmissing, "Cannot test COM without tools")
class COMTests(unittest.TestCase):
    def setUp(self):
        self.__tmpPath = TESTOUTPUT
        #
        self.__siteId = getSiteId(defaultSiteId=None)
        logger.info("\nTesting with site environment for:  %s\n", self.__siteId)
        #
        self.__testFilePath = os.path.join(TOPDIR, "wwpdb", "mock-data", "MODELS")
        self.__testFileCif = "1kip.cif"

    def tearDown(self):
        pass

    def testCifToPdb(self):
        """ """
        logger.info("\nStarting")
        dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
        cifPath = os.path.join(self.__testFilePath, self.__testFileCif)
        dp.imp(cifPath)
        dp.op("centre-of-mass")
        outfile = os.path.join(TESTOUTPUT, "com.cif")
        dp.exp(outfile)
        dp.expLog(os.path.join(TESTOUTPUT, "com.log"))
        self.assertTrue(os.path.exists(outfile))


if __name__ == "__main__":
    # Run all tests --
    unittest.main()
