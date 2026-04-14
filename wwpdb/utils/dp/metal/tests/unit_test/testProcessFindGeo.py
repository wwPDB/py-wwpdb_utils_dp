"""
Unit test For local development test only.
Must set java_exe and findgeo_jar with hardcoded paths.
For OneDep testing, please use the unit test in py-wwpdb_utils_dp/tests/RcsbDpUtilityMetalTests.py
"""

import json
import os
import sys
import unittest

DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DIR = os.path.dirname(DIR)
TEST_DATA_DIR = os.path.join(TEST_DIR, "test_data")
TEST_TEMP_DIR = os.path.join(TEST_DIR, "test_output")
METAL_DIR = os.path.dirname(TEST_DIR)

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

    def testInternalFile(self):
        onedep_package_dir = os.getenv("PACKAGE_DIR", None)
        if onedep_package_dir:
            print("Test in OneDep environment")
            java_exe = os.path.join(onedep_package_dir, "java", "jre", "bin", "java")
            findgeo_jar = os.path.join(onedep_package_dir, "metallo", "FindGeo", "FindGeo.jar")
        else:
            print("Test in local development environment")
            java_exe = "/usr/local/opt/openjdk/bin/java"
            findgeo_jar = "/Users/chenghua/Projects/RunFindGeo/py-run_findgeo/packages/FindGeo/FindGeo-1.1.jar"
        l_command = [sys.executable, os.path.join(METAL_DIR, "findgeo", "processFindGeo.py")]
        l_command.extend(["--java-exe", java_exe])
        l_command.extend(["--findgeo-jar", findgeo_jar])
        l_command.extend(["--input", os.path.join(TEST_DATA_DIR, "8D3M-internal.cif")])
        l_command.append("--compare")
        folder = "findgeo_8D3M_internal_compare_all_geometry"
        l_command.extend(["--workdir", folder])
        command = " ".join(l_command)
        print(command)

        try:
            os.makedirs(TEST_TEMP_DIR, exist_ok=True)
        except Exception as e:
            print("cannot create workdir: %s with error %s", TEST_TEMP_DIR, e)

        os.chdir(TEST_TEMP_DIR)
        os.system(command)

        fp_findgeo_json = os.path.join(TEST_TEMP_DIR, folder, "findgeo_report.json")
        self.assertTrue(os.path.exists(fp_findgeo_json))  # test file exist

        with open(fp_findgeo_json) as f:
            data = json.load(f)
            self.assertTrue(data)  # test file is not empty

    def testPdbId(self):
        onedep_package_dir = os.getenv("PACKAGE_DIR", None)
        if onedep_package_dir:
            print("Test in OneDep environment")
            java_exe = os.path.join(onedep_package_dir, "java", "jre", "bin", "java")
            findgeo_jar = os.path.join(onedep_package_dir, "metallo", "FindGeo", "FindGeo.jar")
        else:
            print("Test in local development environment")
            java_exe = "/usr/local/opt/openjdk/bin/java"
            findgeo_jar = "/Users/chenghua/Projects/RunFindGeo/py-run_findgeo/packages/FindGeo/FindGeo-1.1.jar"
        l_command = [sys.executable, os.path.join(METAL_DIR, "findgeo", "processFindGeo.py")]
        l_command.extend(["--java-exe", java_exe])
        l_command.extend(["--findgeo-jar", findgeo_jar])
        l_command.extend(["--pdb", "4DHV"])
        l_command.append("--compare")
        folder = "findgeo_4DHV_public_compare_all_geometry"
        l_command.extend(["--workdir", folder])
        command = " ".join(l_command)
        print(command)

        try:
            os.makedirs(TEST_TEMP_DIR, exist_ok=True)
        except Exception as e:
            print("cannot create workdir: %s with error %s", TEST_TEMP_DIR, e)

        os.chdir(TEST_TEMP_DIR)
        os.system(command)

        fp_findgeo_json = os.path.join(TEST_TEMP_DIR, folder, "findgeo_report.json")
        self.assertTrue(os.path.exists(fp_findgeo_json))  # test file exist

        with open(fp_findgeo_json) as f:
            data = json.load(f)
            self.assertTrue(data)  # test file is not empty

    def testInternalFileFiltered(self):
        onedep_package_dir = os.getenv("PACKAGE_DIR", None)
        if onedep_package_dir:
            print("Test in OneDep environment")
            java_exe = os.path.join(onedep_package_dir, "java", "jre", "bin", "java")
            findgeo_jar = os.path.join(onedep_package_dir, "metallo", "FindGeo", "FindGeo.jar")
        else:
            print("Test in local development environment")
            java_exe = "/usr/local/opt/openjdk/bin/java"
            findgeo_jar = "/Users/chenghua/Projects/RunFindGeo/py-run_findgeo/packages/FindGeo/FindGeo-1.1.jar"
        l_command = [sys.executable, os.path.join(METAL_DIR, "findgeo", "processFindGeo.py")]
        l_command.extend(["--java-exe", java_exe])
        l_command.extend(["--findgeo-jar", findgeo_jar])
        l_command.extend(["--input", os.path.join(TEST_DATA_DIR, "8D3M-internal.cif")])
        l_command.append("--compare")
        l_command.append("--filter")
        folder = "findgeo_8D3M_internal_compare_regular_geometry"
        l_command.extend(["--workdir", folder])
        command = " ".join(l_command)
        print(command)

        try:
            os.makedirs(TEST_TEMP_DIR, exist_ok=True)
        except Exception as e:
            print("cannot create workdir: %s with error %s", TEST_TEMP_DIR, e)

        os.chdir(TEST_TEMP_DIR)
        os.system(command)

        fp_findgeo_json = os.path.join(TEST_TEMP_DIR, folder, "findgeo_report.json")
        self.assertTrue(os.path.exists(fp_findgeo_json))  # test file exist

        with open(fp_findgeo_json) as f:
            data = json.load(f)
            self.assertFalse(data)  # test file is not empty

    def testPdbIdFiltered(self):
        onedep_package_dir = os.getenv("PACKAGE_DIR", None)
        if onedep_package_dir:
            print("Test in OneDep environment")
            java_exe = os.path.join(onedep_package_dir, "java", "jre", "bin", "java")
            findgeo_jar = os.path.join(onedep_package_dir, "metallo", "FindGeo", "FindGeo.jar")
        else:
            print("Test in local development environment")
            java_exe = "/usr/local/opt/openjdk/bin/java"
            findgeo_jar = "/Users/chenghua/Projects/RunFindGeo/py-run_findgeo/packages/FindGeo/FindGeo-1.1.jar"
        l_command = [sys.executable, os.path.join(METAL_DIR, "findgeo", "processFindGeo.py")]
        l_command.extend(["--java-exe", java_exe])
        l_command.extend(["--findgeo-jar", findgeo_jar])
        l_command.extend(["--pdb", "4DHV"])
        l_command.append("--compare")
        l_command.append("--filter")
        folder = "findgeo_4DHV_public_compare_regular_geometry"
        l_command.extend(["--workdir", folder])
        command = " ".join(l_command)
        print(command)

        try:
            os.makedirs(TEST_TEMP_DIR, exist_ok=True)
        except Exception as e:
            print("cannot create workdir: %s with error %s", TEST_TEMP_DIR, e)

        os.chdir(TEST_TEMP_DIR)
        os.system(command)

        fp_findgeo_json = os.path.join(TEST_TEMP_DIR, folder, "findgeo_report.json")
        self.assertTrue(os.path.exists(fp_findgeo_json))  # test file exist

        with open(fp_findgeo_json) as f:
            data = json.load(f)
            self.assertTrue(data)  # test file is not empty


    def testTimeout(self):
        onedep_package_dir = os.getenv("PACKAGE_DIR", None)
        if onedep_package_dir:
            print("Test in OneDep environment")
            java_exe = os.path.join(onedep_package_dir, "java", "jre", "bin", "java")
            findgeo_jar = os.path.join(onedep_package_dir, "metallo", "FindGeo", "FindGeo.jar")
        else:
            print("Test in local development environment")
            java_exe = "/usr/local/opt/openjdk/bin/java"
            findgeo_jar = "/Users/chenghua/Projects/RunFindGeo/py-run_findgeo/packages/FindGeo/FindGeo-1.1.jar"
        l_command = [sys.executable, os.path.join(METAL_DIR, "findgeo", "processFindGeo.py")]
        l_command.extend(["--java-exe", java_exe])
        l_command.extend(["--findgeo-jar", findgeo_jar])
        l_command.extend(["--input", os.path.join(TEST_DATA_DIR, "8D3M-internal.cif")])
        l_command.append("--compare")
        folder = "findgeo_8D3M_internal_compare_timeout"
        l_command.extend(["--workdir", folder])
        l_command.extend(["--timeout", "1"])
        command = " ".join(l_command)
        print(command)

        try:
            os.makedirs(TEST_TEMP_DIR, exist_ok=True)
        except Exception as e:
            print("cannot create workdir: %s with error %s", TEST_TEMP_DIR, e)

        os.chdir(TEST_TEMP_DIR)
        os.system(command)

        fp_findgeo_json = os.path.join(TEST_TEMP_DIR, folder, "findgeo_report.json")
        self.assertTrue(os.path.exists(fp_findgeo_json))  # test file exist

        with open(fp_findgeo_json) as f:
            data = json.load(f)
            self.assertTrue(data["error"] == "timeout")

    def testParameterError(self):
        onedep_package_dir = os.getenv("PACKAGE_DIR", None)
        if onedep_package_dir:
            print("Test in OneDep environment")
            java_exe = os.path.join(onedep_package_dir, "java", "jre", "bin", "java")
            findgeo_jar = os.path.join(onedep_package_dir, "metallo", "FindGeo", "FindGeo.jar")
        else:
            print("Test in local development environment")
            java_exe = "/usr/local/opt/openjdk/bin/java"
            findgeo_jar = "/Users/chenghua/Projects/RunFindGeo/py-run_findgeo/packages/FindGeo/FindGeo-1.1.jar"
        l_command = [sys.executable, os.path.join(METAL_DIR, "findgeo", "processFindGeo.py")]
        l_command.extend(["--java-exe", java_exe])
        l_command.extend(["--findgeo-jar", findgeo_jar])
        l_command.extend(["--input", os.path.join(TEST_DATA_DIR, "8D3M-internal.cif")])
        l_command.append("--compare")
        folder = "findgeo_8D3M_internal_compare_parameters_error"
        l_command.extend(["--workdir", folder])
        l_command.extend(["--format", "mmCIF"])  # use mmCIF format to cause execution error since FindGeo.jar does not support mmCIF input, which will cause execution error instead of timeout error
        command = " ".join(l_command)
        print(command)

        try:
            os.makedirs(TEST_TEMP_DIR, exist_ok=True)
        except Exception as e:
            print("cannot create workdir: %s with error %s", TEST_TEMP_DIR, e)

        os.chdir(TEST_TEMP_DIR)
        os.system(command)

        fp_findgeo_json = os.path.join(TEST_TEMP_DIR, folder, "findgeo_report.json")
        self.assertTrue(os.path.exists(fp_findgeo_json))  # test file exist

        with open(fp_findgeo_json) as f:
            data = json.load(f)
            self.assertTrue(data["error"] == "parameters-error")

    def testExecutionError(self):
        onedep_package_dir = os.getenv("PACKAGE_DIR", None)
        if onedep_package_dir:
            print("Test in OneDep environment")
            java_exe = os.path.join(onedep_package_dir, "java", "jre", "bin", "java")
            findgeo_jar = os.path.join(onedep_package_dir, "metallo", "FindGeo", "FindGeo.jar")
        else:
            print("Test in local development environment")
            java_exe = "/usr/local/opt/openjdk/bin/java"
            findgeo_jar = "/Users/chenghua/Projects/RunFindGeo/py-run_findgeo/packages/FindGeo/FindGeo-1.1.jar"
        l_command = [sys.executable, os.path.join(METAL_DIR, "findgeo", "processFindGeo.py")]
        l_command.extend(["--java-exe", java_exe])
        l_command.extend(["--findgeo-jar", findgeo_jar])
        l_command.extend(["--input", os.path.join(TEST_DATA_DIR, "8D3M-internal.cif")])
        l_command.append("--compare")
        folder = "findgeo_8D3M_internal_compare_execution_error"
        l_command.extend(["--workdir", folder])
        l_command.extend(["--metal", "A"])  # use invalid metal to cause execution error since FindGeo.jar does not support mmCIF input, which will cause execution error instead of timeout error
        command = " ".join(l_command)
        print(command)

        try:
            os.makedirs(TEST_TEMP_DIR, exist_ok=True)
        except Exception as e:
            print("cannot create workdir: %s with error %s", TEST_TEMP_DIR, e)

        os.chdir(TEST_TEMP_DIR)
        os.system(command)

        fp_findgeo_json = os.path.join(TEST_TEMP_DIR, folder, "findgeo_report.json")
        self.assertTrue(os.path.exists(fp_findgeo_json))  # test file exist

        with open(fp_findgeo_json) as f:
            data = json.load(f)
            self.assertTrue(data["error"] == "execution-error")

    def testPermissionError(self):
        onedep_package_dir = os.getenv("PACKAGE_DIR", None)
        if onedep_package_dir:
            print("Test in OneDep environment")
            java_exe = os.path.join(onedep_package_dir, "java", "jre", "bin", "java")
            findgeo_jar = os.path.join(onedep_package_dir, "metallo", "FindGeo", "FindGeo.jar")
        else:
            print("Test in local development environment")
            java_exe = "/usr/local/opt/openjdk/bin/java"
            findgeo_jar = "/Users/chenghua/Projects/RunFindGeo/py-run_findgeo/packages/FindGeo/FindGeo-1.1.jar"
        l_command = [sys.executable, os.path.join(METAL_DIR, "findgeo", "processFindGeo.py")]
        l_command.extend(["--java-exe", java_exe])
        l_command.extend(["--findgeo-jar", findgeo_jar])
        l_command.extend(["--input", os.path.join(TEST_DATA_DIR, "8D3M-internal.cif")])
        l_command.append("--compare")
        folder = "findgeo_8D3M_internal_compare_permission_error"
        l_command.extend(["--workdir", "/test1"])  # dangerous test to check execution permission error, local only test
        command = " ".join(l_command)
        print(command)

        try:
            os.makedirs(TEST_TEMP_DIR, exist_ok=True)
        except Exception as e:
            print("cannot create workdir: %s with error %s", TEST_TEMP_DIR, e)

        os.chdir(TEST_TEMP_DIR)
        rt = os.system(command)
        print("return code: ", rt)
        self.assertNotEqual(rt, 0)  # command should fail with non-zero exit code since workdir cannot be created

        fp_findgeo_json = os.path.join(TEST_TEMP_DIR, folder, "findgeo_report.json")
        self.assertFalse(os.path.exists(fp_findgeo_json))  # test file doesn't exist


if __name__ == "__main__":
    test_suite = unittest.TestSuite()
    test_suite.addTest(TestRunFindGeo("testInternalFile"))
    test_suite.addTest(TestRunFindGeo("testPdbId"))
    test_suite.addTest(TestRunFindGeo("testInternalFileFiltered"))
    test_suite.addTest(TestRunFindGeo("testPdbIdFiltered"))
    test_suite.addTest(TestRunFindGeo("testTimeout"))
    test_suite.addTest(TestRunFindGeo("testParameterError"))
    test_suite.addTest(TestRunFindGeo("testExecutionError"))
    # test_suite.addTest(TestRunFindGeo("testPermissionError"))
    unittest.TextTestRunner().run(test_suite)
