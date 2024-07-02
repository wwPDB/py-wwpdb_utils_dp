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
import shutil
import unittest
import tempfile

from unittest.mock import patch

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
        logger.info("\nTesting with site environment for:  %s\n Temppath is %s", self.__siteId, self.__tmpPath)
        #
        self.__testFilePath = os.path.join(TOPDIR, "wwpdb", "mock-data", "MODELS")
        self.__testFileCif = "1ac5_updated.cif"
    
    def tearDown(self):
        # if os.path.exists(self.__tmpPath):
        #     shutil.rmtree(self.__tmpPath)
        pass

    @patch("wwpdb.utils.dp.pcm.pcm_util.mmcifHandling.get_latest_model")
    def testOutputFiles(self, glm_mock):
        glm_mock.return_value = os.path.join(self.__testFilePath, self.__testFileCif)

        output_mmcif = os.path.join(self.__tmpPath, "1ac5_mod.cif")
        output_csv = os.path.join(self.__tmpPath, "missing_data.csv")
        pcm = ProteinModificationUtil(dep_id="D_1000000001", output_cif=output_mmcif, output_csv=output_csv)
        pcm.run()

        with open(output_mmcif, "r") as f:
            content = f.read()
            self.assertTrue("_pdbx_modification_feature" in content)
            self.assertTrue("_pdbx_entry_details" in content)
        
        with open(output_csv, "r") as f:
            content = f.readlines()
            self.assertTrue("Comp_id,Modified_residue_id,Type,Category,Position,Polypeptide_position,Comp_id_linking_atom,Modified_residue_id_linking_atom,First_instance_model_db_code" in content[0])
            self.assertTrue("NAG,ASN,missing,missing,missing,missing,C1,ND2,1AC5" in content[-1])

    def testMissingModel(self):
        with self.assertRaises(FileNotFoundError):
            ProteinModificationUtil(dep_id="D_1000000001", output_cif="", output_csv="")


if __name__ == "__main__":
    # Run all tests --
    unittest.main()
