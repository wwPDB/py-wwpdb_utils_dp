import logging
import json
import os
import shutil
import sys
import unittest

from wwpdb.utils.config.ConfigInfo import getSiteId
from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility

DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DATA_DIR = os.path.join(DIR, "test_files")
TEST_OUTPUT_DIR = os.path.join(DIR, "test_output")  # for debugging, activate cleanup when deployed 
if not os.path.exists(TEST_OUTPUT_DIR):
    os.makedirs(TEST_OUTPUT_DIR)
        
log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s - %(funcName)s:%(lineno)d - %(message)s')
c_handler = logging.StreamHandler()
c_handler.setLevel(logging.DEBUG)
c_handler.setFormatter(log_format)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(c_handler)


class TestFindGeo(unittest.TestCase):
    def setUp(self):
        self.__siteId = getSiteId()
        self.__sessionPath = TEST_OUTPUT_DIR
        self.__verbose = False
        self.__lfh = sys.stderr
        
        self.dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)

        self.fp_in = os.path.join(TEST_DATA_DIR, "4DHV-internal.cif")
        self.fp_out = os.path.join(TEST_OUTPUT_DIR, "4DHV-metal-findgeo.json")
        
    def tearDown(self):
        # shutil.rmtree(TEST_OUTPUT_DIR, ignore_errors=True)
        pass

    def test(self):
        self.dp.setDebugMode(flag=True)
        self.dp.imp(self.fp_in)
        logger.info("test input filepath: %s", self.fp_in)
        
        # self.dp.addInput(name="excluded-donors", value="H")  # for checking carbon-metal interaction
        # self.dp.addInput(name="excluded-metals", value="Mg,Ca")  # exlcuding a list of metal elements
        # self.dp.addInput(name="metal", value="Fe")  # run on a specific metal element only
        # self.dp.addInput(name="threshold", value="2.9")  # extend the default 2.8 range search
        # self.dp.addInput(name="workdir", value="/tmp")  # output findgeo temporary calculation data to a folder other than the default "./findgeo"
        
        rt = self.dp.op("metal-findgeo")
        logger.info("run FindGeo on %s with return code %s", self.fp_in, rt)
        self.assertEqual(rt, 0)
        
        try:
            self.dp.exp(self.fp_out)
            logger.info("test output filepath: %s", self.fp_out)
            self.assertTrue(os.path.exists(self.fp_out))  # check if test file exists

            with open(self.fp_out) as f:
                data = json.load(f)
                self.assertTrue(data)  # check if test file is empty
                
        except Exception as e:
            logger.exception("Failed to export: %s", e)
            raise

class TestMetalCoordStats(unittest.TestCase):
    def setUp(self):
        self.__siteId = getSiteId()
        self.__sessionPath = TEST_OUTPUT_DIR
        self.__verbose = False
        self.__lfh = sys.stderr
        
        self.dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)

        self.fp_in = os.path.join(TEST_DATA_DIR, "4DHV-internal.cif")
        self.fp_out = os.path.join(TEST_OUTPUT_DIR, "4DHV-metal-metalcoord.json")
        
    def tearDown(self):
        # shutil.rmtree(TEST_OUTPUT_DIR, ignore_errors=True)
        pass

    def test(self):
        self.dp.setDebugMode(flag=True)
        self.dp.imp(self.fp_in)
        logger.info("test input filepath: %s", self.fp_in)
        
        self.dp.addInput(name="ligand", value="0KA")  # CCD ID of the metal ligand to check on    
        # self.dp.addInput(name="max_size", value="2000")  # Maximum sample size for reference statistics.
        # self.dp.addInput(name="threshold", value="0.2")  # Procrustes distance threshold for finding COD reference.
        # self.dp.addInput(name="workdir", value="/tmp")  # output to a folder other than the default "./metalcoord"
        # self.dp.addInput(name="pdb", value="4DHV")  # PDB code or pdb file as input
        # self.dp.addInput(name="metalcoord_exe", value="")  # MetalCoord executable file, only use for testing new versions
        
        rt = self.dp.op("metal-metalcoord-stats")
        logger.info("run MetalCoord on ligand 0KA in file %s with return code %s", self.fp_in, rt)
        self.assertEqual(rt, 0)
        
        try:
            self.dp.exp(self.fp_out)
            logger.info("test output filepath: %s", self.fp_out)
            self.assertTrue(os.path.exists(self.fp_out))  # check if test file exists

            with open(self.fp_out) as f:
                data = json.load(f)
                self.assertTrue(data)  # check if test file is empty
                
        except Exception as e:
            logger.exception("Failed to export: %s", e)
            raise

class TestMetalCoordUpdate(unittest.TestCase):
    def setUp(self):
        self.__siteId = getSiteId()
        self.__sessionPath = TEST_OUTPUT_DIR
        self.__verbose = False
        self.__lfh = sys.stderr
        
        self.dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)

        self.fp_in_ccd = os.path.join(TEST_DATA_DIR, "0KA.cif")
        self.fp_in_pdb = os.path.join(TEST_DATA_DIR, "4DHV-internal.cif")
        self.fp_out = os.path.join(TEST_OUTPUT_DIR, "4DHV-metal-metalcoord.json")
        
    def tearDown(self):
        # shutil.rmtree(TEST_OUTPUT_DIR, ignore_errors=True)
        pass

    def test(self):
        self.dp.setDebugMode(flag=True)
        self.dp.imp(self.fp_in_ccd)
        logger.info("test input filepath: %s", self.fp_in_ccd)
        
        self.dp.addInput(name="pdb", value=os.path.join(TEST_DATA_DIR, "4DHV-internal.cif"))  # PDB code or pdb file as reference   
        # self.dp.addInput(name="acedrg_exe", value="")  # Acedrg executable file, only use for testing new versions
        # self.dp.addInput(name="metalcoord_exe", value="")  # MetalCoord executable file, only use for testing new versions
        # self.dp.addInput(name="servalcat_exe", value="")   # Servalcat executable file, only use for testing new versions
        # self.dp.addInput(name="workdir", value="/tmp")  # Directory to write outputs. Default is metalcoord subfolder in the current folder
        # self.dp.addInput(name="threshold", value="0.2")  # Procrustes distance threshold for finding COD reference.
        
        rt = self.dp.op("metal-metalcoord-update")
        logger.info("run MetalCoord on ligand file %s with return code %s", self.fp_in_ccd, rt)
        self.assertEqual(rt, 0)
        
        try:
            self.dp.exp(self.fp_out)
            logger.info("test output filepath: %s", self.fp_out)
            self.assertTrue(os.path.exists(self.fp_out))  # check if test file exists

            with open(self.fp_out) as f:
                data = json.load(f)
                self.assertTrue(data)  # check if test file is empty
                
        except Exception as e:
            logger.exception("Failed to export: %s", e)
            raise

        try:
            self.dp.expList(["ligand.cif","metal.json"])               
        except Exception as e:
            logger.exception("Failed to export: %s", e)
            raise

def suite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # suite.addTests(loader.loadTestsFromTestCase(TestFindGeo))
    # suite.addTests(loader.loadTestsFromTestCase(TestMetalCoordStats))
    suite.addTests(loader.loadTestsFromTestCase(TestMetalCoordUpdate))

    return suite


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite())
