##
# Update:

##
"""
Test cases for SF Map coefficients

"""
import logging
import unittest
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)


if __package__ is None or __package__ == '':
    import sys
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT, TOPDIR, toolsmissing
else:
    from .commonsetup import TESTOUTPUT, TOPDIR, toolsmissing

from wwpdb.utils.dp.PdbxSFMapCoefficients import PdbxSFMapCoefficients


class PdbxSFTests(unittest.TestCase):
    def setUp(self):
        pass

    def testImport(self):
        p = PdbxSFMapCoefficients()

if __name__ == '__main__':
    # Run all tests --
    unittest.main()
