"""
Unit test For local development test only.
Must set $CCP4 env before run, i.e. activate CCP4 setting.
For OneDep testing, please use the unit test in py-wwpdb_utils_dp/tests/RcsbDpUtilityMetalTests.py
"""

import os
import sys
import unittest
import json

DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DIR = os.path.dirname(DIR)
TEST_DATA_DIR = os.path.join(TEST_DIR, "test_data")
TEST_TEMP_DIR = os.path.join(TEST_DIR, "test_output")

sys.path.insert(0, TEST_DIR)


class TestRunMetalCoord(unittest.TestCase):
    """
    Unit test class for verifying the metal coordination update process.
    Methods
    -------
    - setUp():
        Prepare the test environment. Currently a placeholder.
    - tearDown():
        Clean up after tests. Currently a placeholder.
    - test():
        Executes the metal coordination update workflow:
        - Sets up CCP4 environment variables.
        - Constructs and runs the command for processing metal coordination.
        - Checks for the existence and validity of output files:
            - `metalcoord_report.json`
            - `servalcat_updated.cif`
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test(self):
        l_command = []
        ccp4_dir = os.getenv("CCP4", None)
        if ccp4_dir:
            print("Found CCP4 env at %s" % ccp4_dir)
        else:
            print("Setup CCP4")
            onedep_package_dir = os.getenv("PACKAGE_DIR", None)
            if onedep_package_dir:
                print("Test in OneDep environment")
                ccp4_dir = os.path.join(onedep_package_dir, "metallo", "ccp4-9")
            else:
                print("Test in local development")
                ccp4_dir = "/Applications/ccp4-9"
            l_command.append(f"source {ccp4_dir}/bin/ccp4.setup-sh;")
        l_command.extend([sys.executable, "-m", "wwpdb.utils.dp.metal.metalcoord.processMetalCoordUpdate"])
        l_command.extend(["--input", os.path.join(TEST_DATA_DIR, "0KA.cif")])
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

        fp_metalcoord_json = os.path.join(TEST_TEMP_DIR, "metalcoord/servalcat_updated.cif")
        self.assertTrue(os.path.exists(fp_metalcoord_json))  # test file exist


if __name__ == "__main__":
    unittest.main()
