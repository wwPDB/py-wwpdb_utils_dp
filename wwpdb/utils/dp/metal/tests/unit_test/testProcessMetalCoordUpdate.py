"""
Unit test For local development test only.
Must set $CCP4 env before run, i.e. activate CCP4 setting.
For OneDep testing, please use the unit test in py-wwpdb_utils_dp/tests/RcsbDpUtilityMetalTests.py
"""

import os
import sys
import unittest

DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DIR = os.path.dirname(DIR)
TEST_DATA_DIR = os.path.join(TEST_DIR, "test_data")
TEST_TEMP_DIR = os.path.join(TEST_DIR, "test_output")
METAL_DIR = os.path.dirname(TEST_DIR)

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
        self.b_standalone_metalcoord = True

    def tearDown(self):
        pass

    def run_test(self, ccd_id, pdb_id):
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
        l_command.extend([sys.executable, os.path.join(METAL_DIR, "metalcoord", "processMetalCoordUpdate.py")])
        l_command.extend(["--input", os.path.join(TEST_DATA_DIR, f"{ccd_id}.cif")])
        if pdb_id:
            l_command.extend(["--pdb", os.path.join(TEST_DATA_DIR, f"{pdb_id}-internal.cif")])
        if self.b_standalone_metalcoord:
            metalcoord_exe = "/Users/chenghua/Projects/RunMetalCoord/py-run_metalCoord/venv/bin/metalCoord"
            l_command.extend(["--metalcoord_exe", metalcoord_exe])
        command = " ".join(l_command)
        print(command)

        folder = os.path.join(TEST_TEMP_DIR, f"{ccd_id}-MetalCoord-update")
        try:
            os.makedirs(folder, exist_ok=True)
        except Exception as e:  # noqa: BLE001
            print("cannot create workdir: %s with error %s", folder, e)

        os.chdir(folder)
        os.system(command)

        fp_metalcoord_json = os.path.join(folder, "metalcoord/metalcoord_report.json")
        self.assertTrue(os.path.exists(fp_metalcoord_json))  # test file exist

        self.assertTrue(os.path.isfile(fp_metalcoord_json), f"Expected {fp_metalcoord_json} to be a file")  # test is a file

        fp_final = os.path.join(folder, "metalcoord/clean.cif")
        self.assertTrue(os.path.exists(fp_final))  # test file exist
        self.assertTrue(os.path.isfile(fp_final), f"Expected {fp_final} to be a file")  # test is a file

    def test1(self):
        self.run_test("0KA", "4DHV")

    def test2(self):
        self.run_test("HEM", None)


if __name__ == "__main__":
    unittest.main()
