##
# File:    MetalRunCommandTests.py
# Date:    2026-10-06
#
##
"""
Hermetic unit tests for wwpdb.utils.dp.metal.metal_util.run_command.

subprocess.run is mocked for the failure paths; the success path runs the current Python
interpreter so no external binaries are required. Tests chdir into a temporary directory so
the default log directory created by setup_logger() does not land in the repository.
"""

import logging
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from typing import List
from unittest import mock

from wwpdb.utils.dp.metal.metal_util.run_command import MetalCommandExecutionError, MetalCommandTimeoutError, run_command, setup_logger

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _closeLogger(name: str) -> None:
    """Remove and close all handlers on the named logger"""
    lgr = logging.getLogger(name)
    for handler in list(lgr.handlers):
        lgr.removeHandler(handler)
        handler.close()


class MetalCommandErrorTests(unittest.TestCase):
    def testExecutionErrorMessageWithStderr(self) -> None:
        err = MetalCommandExecutionError(["prog", "-x"], 3, stderr="  bad thing \n", stdout="out")
        self.assertEqual(err.cmd, ["prog", "-x"])
        self.assertEqual(err.code, 3)
        self.assertEqual(err.stderr, "  bad thing \n")
        self.assertEqual(err.stdout, "out")
        self.assertEqual(str(err), "Command ['prog', '-x'] failed with exit code 3\nStderr:\nbad thing")

    def testExecutionErrorMessageWithoutStderr(self) -> None:
        err = MetalCommandExecutionError("prog")
        self.assertIsNone(err.code)
        self.assertIsNone(err.stderr)
        self.assertIsNone(err.stdout)
        self.assertEqual(str(err), "Command prog failed with exit code None")

    def testTimeoutIsExecutionError(self) -> None:
        err = MetalCommandTimeoutError(["prog"], None, stderr="Command timed out")
        self.assertIsInstance(err, MetalCommandExecutionError)
        self.assertIn("Command timed out", str(err))


class MetalSetupLoggerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmpDir = tempfile.mkdtemp()
        self.__names: List[str] = []

    def tearDown(self) -> None:
        for name in self.__names:
            _closeLogger(name)
        shutil.rmtree(self.__tmpDir, ignore_errors=True)

    def __newName(self) -> str:
        name = "metal_cmd_test_" + uuid.uuid4().hex
        self.__names.append(name)
        return name

    def testSetupLoggerDebug(self) -> None:
        name = self.__newName()
        logDir = os.path.join(self.__tmpDir, "logs")
        lgr = setup_logger(name=name, log_dir=logDir, b_debug=True)
        self.assertEqual(lgr.name, name)
        self.assertEqual(lgr.level, logging.DEBUG)
        self.assertTrue(os.path.isdir(logDir))
        fileHandlers = [h for h in lgr.handlers if isinstance(h, logging.FileHandler)]
        self.assertEqual(len(fileHandlers), 1)
        self.assertEqual(fileHandlers[0].level, logging.DEBUG)
        self.assertEqual(len(lgr.handlers), 2)
        logFiles = os.listdir(logDir)
        self.assertEqual(len(logFiles), 1)
        self.assertTrue(logFiles[0].startswith(name + "_"))
        self.assertTrue(logFiles[0].endswith(".log"))

    def testSetupLoggerInfoAndReuse(self) -> None:
        name = self.__newName()
        lgr = setup_logger(name=name, log_dir=self.__tmpDir, b_debug=False)
        fileHandlers = [h for h in lgr.handlers if isinstance(h, logging.FileHandler)]
        self.assertEqual(fileHandlers[0].level, logging.INFO)
        # A second call must not add more handlers
        lgr2 = setup_logger(name=name, log_dir=self.__tmpDir, b_debug=True)
        self.assertIs(lgr, lgr2)
        self.assertEqual(len(lgr2.handlers), 2)


class MetalRunCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__cwd = os.getcwd()
        self.__tmpDir = tempfile.mkdtemp()
        os.chdir(self.__tmpDir)
        self.__logger = logging.getLogger("metal_run_command_tests")

    def tearDown(self) -> None:
        _closeLogger("cmd")
        os.chdir(self.__cwd)
        shutil.rmtree(self.__tmpDir, ignore_errors=True)

    def testSuccessRealProcess(self) -> None:
        out = run_command([sys.executable, "-c", "print('hello metal')"], 60, self.__logger)
        self.assertEqual(out.strip(), "hello metal")

    def testSuccessMockedArgs(self) -> None:
        completed = subprocess.CompletedProcess(args=["prog"], returncode=0, stdout="ok\n", stderr="")
        with mock.patch.object(subprocess, "run", return_value=completed) as mrun:
            out = run_command(["prog", "a"], 17, self.__logger)
        self.assertEqual(out, "ok\n")
        mrun.assert_called_once_with(["prog", "a"], check=True, capture_output=True, text=True, timeout=17)

    def testDefaultLoggerCreated(self) -> None:
        completed = subprocess.CompletedProcess(args=["prog"], returncode=0, stdout="x", stderr="")
        with mock.patch.object(subprocess, "run", return_value=completed):
            out = run_command(["prog"], 5)
        self.assertEqual(out, "x")
        # default setup_logger() writes to ./metal_command_logs, which is in the temp dir
        self.assertTrue(os.path.isdir(os.path.join(self.__tmpDir, "metal_command_logs")))

    def testBinaryNotFound(self) -> None:
        missing = os.path.join(self.__tmpDir, "no_such_binary_xyz")
        with self.assertRaises(MetalCommandExecutionError) as ctx:
            run_command([missing], 5, self.__logger)
        self.assertNotIsInstance(ctx.exception, MetalCommandTimeoutError)
        self.assertIsNone(ctx.exception.code)
        self.assertEqual(ctx.exception.cmd, [missing])
        self.assertIsInstance(ctx.exception.__cause__, FileNotFoundError)

    def testCalledProcessError(self) -> None:
        exc = subprocess.CalledProcessError(2, ["prog", "x"], output="partial out\n", stderr="boom\n")
        with mock.patch.object(subprocess, "run", side_effect=exc), self.assertRaises(MetalCommandExecutionError) as ctx:
            run_command(["prog", "x"], 5, self.__logger)
        self.assertEqual(ctx.exception.code, 2)
        self.assertEqual(ctx.exception.cmd, ["prog", "x"])
        self.assertEqual(ctx.exception.stderr, "boom\n")
        self.assertEqual(ctx.exception.stdout, "partial out\n")
        self.assertIn("boom", str(ctx.exception))

    def testCalledProcessErrorNoOutput(self) -> None:
        exc = subprocess.CalledProcessError(1, ["prog"])
        with mock.patch.object(subprocess, "run", side_effect=exc), self.assertRaises(MetalCommandExecutionError) as ctx:
            run_command(["prog"], 5, self.__logger)
        self.assertEqual(ctx.exception.code, 1)
        self.assertIsNone(ctx.exception.stderr)

    def testTimeout(self) -> None:
        exc = subprocess.TimeoutExpired(["prog"], 1, output="some out", stderr="some err")
        with mock.patch.object(subprocess, "run", side_effect=exc), self.assertRaises(MetalCommandTimeoutError) as ctx:
            run_command(["prog"], 1, self.__logger)
        self.assertEqual(ctx.exception.stderr, "Command timed out")
        self.assertIsNone(ctx.exception.code)
        self.assertEqual(ctx.exception.cmd, ["prog"])

    def testTimeoutNoOutput(self) -> None:
        exc = subprocess.TimeoutExpired(["prog"], 1)
        with mock.patch.object(subprocess, "run", side_effect=exc), self.assertRaises(MetalCommandTimeoutError):
            run_command(["prog"], 1, self.__logger)

    def testUnexpectedError(self) -> None:
        with mock.patch.object(subprocess, "run", side_effect=ValueError("weird")), self.assertRaises(MetalCommandExecutionError) as ctx:
            run_command(["prog"], 1, self.__logger)
        self.assertNotIsInstance(ctx.exception, MetalCommandTimeoutError)
        self.assertEqual(ctx.exception.stderr, "weird")
        self.assertIsInstance(ctx.exception.__cause__, ValueError)


if __name__ == "__main__":
    unittest.main()
