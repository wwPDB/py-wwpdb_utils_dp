##
# File:    ElectronDensityCommonUnitTests.py
#
# Update:
##
"""
Hermetic unit tests for wwpdb.utils.dp.electron_density.common_functions.  The node based
volume-server-query is replaced by a small python script.

"""

import json
import logging
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.abspath(__file__)))

from wwpdb.utils.dp.electron_density.common_functions import convert_mdb_to_binary_cif, run_command, run_command_and_check_output_file

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Fake volume-server-query: "query --jobs <json>" - writes output described in json
FAKE_QUERY = """import json, os, sys
with open(sys.argv[-1]) as ifh:
    jobs = json.load(ifh)
for job in jobs:
    with open(os.path.join(job["outputFolder"], job["outputFilename"]), "w") as ofh:
        ofh.write("bcif:" + job["source"]["name"] + ":" + str(job["params"]["detail"]))
"""

# Writes the current directory name to a file in that directory
FAKE_CWD = """import os
with open("cwd.txt", "w") as ofh:
    ofh.write(os.getcwd())
"""


class ElectronDensityCommonUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__workDir = tempfile.mkdtemp()
        self.__scriptDir = tempfile.mkdtemp()
        self.__outDir = tempfile.mkdtemp()
        self.__query = self.__writeScript("query.py", FAKE_QUERY)

    def tearDown(self) -> None:
        for dirPath in [self.__workDir, self.__scriptDir, self.__outDir]:
            shutil.rmtree(dirPath, ignore_errors=True)

    def __writeScript(self, name: str, content: str) -> str:
        pth = os.path.join(self.__scriptDir, name)
        with open(pth, "w") as ofh:
            ofh.write(content)
        return pth

    def testRunCommandSuccess(self) -> None:
        self.assertTrue(run_command("%s -c pass" % sys.executable, "ok"))

    def testRunCommandFailure(self) -> None:
        self.assertFalse(run_command("%s -c 'import sys; sys.exit(2)'" % sys.executable, "fail"))

    def testRunCommandMissingExecutable(self) -> None:
        self.assertFalse(run_command(os.path.join(self.__workDir, "no-such-program"), "missing"))

    def testRunCommandWorkdir(self) -> None:
        script = self.__writeScript("cwd.py", FAKE_CWD)
        self.assertTrue(run_command("%s %s" % (sys.executable, script), "cwd", workdir=self.__workDir))
        with open(os.path.join(self.__workDir, "cwd.txt")) as ifh:
            self.assertEqual(os.path.realpath(ifh.read()), os.path.realpath(self.__workDir))

    def testRunCommandOutputLogged(self) -> None:
        with mock.patch("wwpdb.utils.dp.electron_density.common_functions.subprocess.Popen") as mockPopen:
            mockPopen.return_value.communicate.return_value = ("some output", "some error")
            mockPopen.return_value.returncode = 0
            with self.assertLogs("wwpdb.utils.dp.electron_density.common_functions", level="INFO") as cm:
                self.assertTrue(run_command("prog arg1 'arg 2'", "logged"))
        mockPopen.assert_called_once_with(["prog", "arg1", "arg 2"])
        text = "\n".join(cm.output)
        self.assertIn("some output", text)
        self.assertIn("some error", text)
        self.assertIn("process worked: logged", text)

    def testRunCommandAndCheckOutput(self) -> None:
        outFile = os.path.join(self.__workDir, "made.txt")
        cmd = "%s -c \"open('made.txt', 'w').write('x')\"" % sys.executable
        self.assertTrue(run_command_and_check_output_file(cmd, "make", outFile, workdir=self.__workDir))
        self.assertFalse(run_command_and_check_output_file(cmd, "make", os.path.join(self.__workDir, "other.txt"), workdir=self.__workDir))

    def testRunCommandAndCheckOutputFailure(self) -> None:
        outFile = os.path.join(self.__workDir, "made.txt")
        with open(outFile, "w") as ofh:
            ofh.write("x")
        self.assertFalse(run_command_and_check_output_file("%s -c 'import sys; sys.exit(1)'" % sys.executable, "fail", outFile))
        self.assertFalse(run_command_and_check_output_file("", "fail", outFile))
        self.assertFalse(run_command_and_check_output_file("ls", "fail", ""))

    def testConvertMdbToBinaryCif(self) -> None:
        outFile = os.path.join(self.__outDir, "new", "sub", "map.bcif")
        mdb = os.path.join(self.__workDir, "in.mdb")
        ok = convert_mdb_to_binary_cif(sys.executable, self.__query, "my_map", "src", mdb, outFile, self.__workDir, detail=2)
        self.assertTrue(ok)
        with open(outFile) as ifh:
            self.assertEqual(ifh.read(), "bcif:my_map:2")
        with open(os.path.join(self.__workDir, "conversion.json")) as ifh:
            jobs = json.load(ifh)
        self.assertEqual(
            jobs,
            [
                {
                    "source": {"filename": mdb, "name": "my_map", "id": "src"},
                    "query": {"kind": "cell"},
                    "params": {"detail": 2, "asBinary": True},
                    "outputFolder": self.__workDir,
                    "outputFilename": "my_map_src-cell_d2.bcif",
                }
            ],
        )

    def testConvertMdbToBinaryCifDefaultDetail(self) -> None:
        outFile = os.path.join(self.__outDir, "map.bcif")
        self.assertTrue(convert_mdb_to_binary_cif(sys.executable, self.__query, "m", "s", "in.mdb", outFile, self.__workDir))
        self.assertTrue(os.path.exists(os.path.join(self.__workDir, "m_s-cell_d4.bcif")))
        with open(outFile) as ifh:
            self.assertEqual(ifh.read(), "bcif:m:4")

    def testConvertMdbToBinaryCifNoWorkingDir(self) -> None:
        """Without a working directory, the current directory is used"""
        outFile = os.path.join(self.__outDir, "map.bcif")
        savedCwd = os.getcwd()
        try:
            os.chdir(self.__workDir)
            ok = convert_mdb_to_binary_cif(sys.executable, self.__query, "m", "s", "in.mdb", outFile, None)
        finally:
            os.chdir(savedCwd)
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(os.path.join(self.__workDir, "conversion.json")))
        self.assertTrue(os.path.exists(outFile))

    def testConvertMdbToBinaryCifRelativeOutput(self) -> None:
        """An output file with no directory component is copied relative to the current directory"""
        savedCwd = os.getcwd()
        try:
            os.chdir(self.__outDir)
            ok = convert_mdb_to_binary_cif(sys.executable, self.__query, "m", "s", "in.mdb", "rel.bcif", self.__workDir)
        finally:
            os.chdir(savedCwd)
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(os.path.join(self.__outDir, "rel.bcif")))

    def testConvertMdbToBinaryCifFailure(self) -> None:
        failScript = self.__writeScript("fail.py", "import sys\nsys.exit(1)\n")
        outFile = os.path.join(self.__outDir, "map.bcif")
        self.assertFalse(convert_mdb_to_binary_cif(sys.executable, failScript, "m", "s", "in.mdb", outFile, self.__workDir))
        self.assertFalse(os.path.exists(outFile))


if __name__ == "__main__":
    unittest.main()
