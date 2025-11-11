"""
Unit test For local development test only.
Must set java_exe and findgeo_jar with hardcoded paths.
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


class TestRunFindGeo(unittest.TestCase):
    """
    Unit test class for running the FindGeo process and validating its output.
    This class sets up the environment to run the FindGeo tool either in a OneDep environment or a local development environment.
    It constructs the appropriate command to execute the FindGeo process, runs it, and verifies that the expected output file
    (`findgeo_report.json`) is generated and contains data.
    Test Methods:
        - test: Runs the FindGeo process with specified parameters, checks for the existence of the output JSON file,
            and asserts that the file is not empty.
    Setup and Teardown:
        - setUp: Placeholder for setup operations before each test.
        - tearDown: Placeholder for cleanup operations after each test.
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test(self):
        onedep_package_dir = os.getenv("PACKAGE_DIR", None)
        if onedep_package_dir:
            print("Test in OneDep environment")
            java_exe = os.path.join(onedep_package_dir, "java", "jre", "bin", "java")
            findgeo_jar = os.path.join(onedep_package_dir, "metallo", "FindGeo", "FindGeo.jar")
        else:
            print("Test in local development environment")
            java_exe = "/usr/local/opt/openjdk/bin/java"
            findgeo_jar = "/Users/chenghua/Projects/RunFindGeo/py-run_findgeo/packages/FindGeo/FindGeo-1.1.jar"
        l_command = [sys.executable, "-m", "wwpdb.utils.dp.metal.findgeo.processFindGeo"]
        l_command.extend(["--java-exe", java_exe])
        l_command.extend(["--findgeo-jar", findgeo_jar])
        l_command.extend(["--pdb", "4DHV"])
        command = " ".join(l_command)
        print(command)

        try:
            os.makedirs(TEST_TEMP_DIR, exist_ok=True)
        except Exception as e:
            print("cannot create workdir: %s with error %s", TEST_TEMP_DIR, e)

        os.chdir(TEST_TEMP_DIR)
        os.system(command)

        fp_findgeo_json = os.path.join(TEST_TEMP_DIR, "findgeo/findgeo_report.json")
        self.assertTrue(os.path.exists(fp_findgeo_json))  # test file exist

        with open(fp_findgeo_json) as f:
            data = json.load(f)
            self.assertTrue(data)  # test file is not empty


if __name__ == "__main__":
    unittest.main()
