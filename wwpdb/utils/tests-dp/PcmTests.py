##
# File:    COMTests.py
# Author:  E.Peisach
# Date:    2-Sep-2021
# Version: 0.001
#
# Update:
##
"""
Test cases for PCM calculation

"""
import logging
import os
import sys
import unittest
import tempfile

# if __package__ is None or __package__ == "":
#     from os import path

#     sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
#     from commonsetup import TESTOUTPUT, TOPDIR, toolsmissing  # pylint: disable=import-error
# else:
#     from .commonsetup import TESTOUTPUT, TOPDIR, toolsmissing
TESTOUTPUT = tempfile.mkdtemp()
HERE = os.path.abspath(os.path.dirname(__file__))
TOPDIR = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))

from wwpdb.utils.config.ConfigInfo import getSiteId
from wwpdb.utils.dp.pcm.pcm_util import ProteinModificationUtil

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class ProteinModificationTests(unittest.TestCase):
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

    def testMmcifOutput(self):
        output_mmcif = ""
        pcm = ProteinModificationUtil(dep_id="D_1000000001")
        pcm.create_modified_mmcif(output_path=output_mmcif)

        with open(output_mmcif, "r") as f:
            content = f.read()
            self.assertTrue("MODRES" in content)

    def testCsvOutput(self):
        output_csv = ""
        pcm = ProteinModificationUtil(dep_id="D_1000000001")
        pcm.create_missing_data_csv(output_path=output_csv)

        with open(output_csv, "r") as f:
            content = f.readlines()
            self.assertTrue(content[0] == "Dep_ID,Comp_id,Modified_residue_id,Type,Category,Position,Polypeptide_position,Comp_id_linking_atom,Modified_residue_id_linking_atom,First_instance_model_db_code")
            self.assertTrue(content[-1] == "")


if __name__ == "__main__":
    # Run all tests --
    unittest.main()
