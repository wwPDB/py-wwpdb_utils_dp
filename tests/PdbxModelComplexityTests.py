##
# File:    PdbxModelComplexityTests.py
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
    from commonsetup import TESTOUTPUT, TOPDIR, modified_environ  # pylint: disable=import-error
else:
    from .commonsetup import TESTOUTPUT, TOPDIR, modified_environ

from mmcif.io.IoAdapterCore import IoAdapterCore

from wwpdb.utils.config.ConfigInfo import getSiteId
from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class ModelComplexityTests(unittest.TestCase):
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

    def testModelComplexity(self):
        """ """

        outfile = os.path.join(TESTOUTPUT, "complexity.cif")
        if os.path.exists(outfile):
            os.remove(outfile)

        with modified_environ(PYTHONPATH=TOPDIR):
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            cifPath = os.path.join(self.__testFilePath, self.__testFileCif)
            dp.imp(cifPath)

            dp.op("annot-complexity")
            dp.exp(outfile)
            dp.expLog(os.path.join(TESTOUTPUT, "complexity.log"))
        self.assertTrue(os.path.exists(outfile))
        self.assertFalse(self.getcomplex(outfile))

    def testModelComplexityThreshold(self):
        """Retrieve complexity with lower threshold"""

        outfile = os.path.join(TESTOUTPUT, "complexity2.cif")
        if os.path.exists(outfile):
            os.remove(outfile)

        with modified_environ(PYTHONPATH=TOPDIR):
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            cifPath = os.path.join(self.__testFilePath, self.__testFileCif)
            dp.imp(cifPath)
            dp.addInput("threshold", "1000")
            dp.op("annot-complexity")
            dp.exp(outfile)
            dp.expLog(os.path.join(TESTOUTPUT, "complexity2.log"))
        self.assertTrue(os.path.exists(outfile))
        self.assertTrue(self.getcomplex(outfile))

    def getcomplex(self, fpath):
        """Retrieve complexity"""
        io = IoAdapterCore()
        cL = io.readFile(fpath)
        self.assertIsInstance(cL, list)
        b0 = cL[0]
        cObj = b0.getObj("pdbx_complexity")
        comp = cObj.getValue("is_complex")
        ret = comp == "True"
        return ret


if __name__ == "__main__":
    # Run all tests --
    unittest.main()
