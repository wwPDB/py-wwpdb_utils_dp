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
        # self.dp.addInput(name="excluded-donors", value="H")  # for checking carbon-metal interaction
        # self.dp.addInput(name="excluded-metals", value="Mg,Ca")  # exlcuding a list of metal elements
        # self.dp.addInput(name="metal", value="Fe")  # run on a specific metal element only
        # self.dp.addInput(name="threshold", value="2.9")  # extend the default 2.8 range search
        # self.dp.addInput(name="workdir", value="/tmp")  # output metalcoord temporary calculation data to a folder other than the default "./metalcoord"
        
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

        
def suite():
    suite = unittest.TestSuite()
    # suite.addTest(unittest.makeSuite(TestFindGeo))
    suite.addTest(unittest.makeSuite(TestMetalCoordStats))
    return suite

if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite())
