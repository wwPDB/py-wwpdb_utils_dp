"""
Unit test For local development test only. 
Must set $CCP4 env before run, i.e. activate CCP4 setting.
For OneDep testing, please use the unit test in py-wwpdb_utils_dp/tests/RcsbDpUtilityMetalTests.py
"""

import os
import sys
import unittest
import os
import json

DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DIR = os.path.dirname(DIR)
TEST_DATA_DIR = os.path.join(TEST_DIR, "test_data")
TEST_TEMP_DIR = os.path.join(TEST_DIR, "temp")
METAL_DIR = os.path.dirname(TEST_DIR)

sys.path.insert(0, METAL_DIR)
print(sys.path)

class TestRunMetalCoord(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test1(self):
        l_command = [sys.executable, "-m", "wwpdb.utils.dp.metal.metalcoord.processMetalCoordUpdate"]
        l_command.extend(["--input", os.path.join(TEST_DATA_DIR,"0KA.cif")])
        l_command.extend(["--pdb", os.path.join(TEST_DATA_DIR, "4DHV-internal.cif")])
        command = " ".join(l_command)
        print(command)

        try:
            os.makedirs(TEST_TEMP_DIR, exist_ok=True)
        except Exception as e:
            print("cannot create workdir: %s with error %s", TEST_TEMP_DIR, e)

        os.chdir(TEST_TEMP_DIR)
        os.system(command)

        fp_metalcoord_json = os.path.join(TEST_TEMP_DIR, "metalcoord/metalcoord_report.json")
        self.assertTrue(os.path.exists(fp_metalcoord_json))  # test file exist

        with open(fp_metalcoord_json) as f:
            data = json.load(f)
            self.assertTrue(data)  # test file is not empty


if __name__ == "__main__":
    unittest.main()
