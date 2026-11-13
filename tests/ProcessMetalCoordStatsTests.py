##
# File:    ProcessMetalCoordStatsTests.py
#
# Update:
##
"""
Hermetic unit tests for wwpdb.utils.dp.metal.metalcoord.processMetalCoordStats.

MetalCoord is never invoked: RunMetalCoord and ParseMetalCoord are replaced by mocks at the
module level, and all outputs are written to temporary directories.
"""

import atexit
import json
import logging
import os
import shutil
import sys
import tempfile
import unittest
from typing import Any, Dict, List
from unittest import mock

# processMetalCoordStats calls setup_logger(log_dir=".") at import time, which creates a log file in
# the current directory. Import from inside a scratch directory so that the repository is not littered.
_LOGDIR = tempfile.mkdtemp(prefix="metalcoord_log_")
atexit.register(shutil.rmtree, _LOGDIR, True)
_CWD = os.getcwd()
os.chdir(_LOGDIR)
try:
    from wwpdb.utils.dp.metal.metalcoord import processMetalCoordStats as pmcs  # noqa: E402
finally:
    os.chdir(_CWD)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logger = logging.getLogger()


def _exc(name: str) -> Any:
    """Return the exception class exactly as bound in the module under test at runtime.

    The module imports its collaborators through sys.path-relative names (e.g. ``metalcoord.runMetalCoord``),
    so these classes are distinct from the ``wwpdb.utils.dp.metal...`` ones and must be taken from the module itself.
    """
    cls = vars(pmcs)[name]
    assert issubclass(cls, Exception)
    return cls


def _readJson(path: str) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _site(chain: str, klass: str = "Tetrahedral", tag: str = "Regular", allowed: str = "YES", exception: str = "NO") -> Dict[str, Any]:
    return {"chain": chain, "class": klass, "tag": tag, "coordination_number_allowed": allowed, "class_in_exception": exception}


class ProcessMetalCoordStatsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmp = tempfile.mkdtemp()
        self.__wrk = os.path.join(self.__tmp, "mc")
        os.makedirs(self.__wrk)
        self.__report = os.path.join(self.__wrk, "metalcoord_report.json")
        self.__argv = ["processMetalCoordStats.py", "--ligands", "0KA,NCO", "--pdb", "4DHV.cif", "--workdir", self.__wrk]
        self.__runArgs: List[Dict[str, Any]] = []

    def tearDown(self) -> None:
        shutil.rmtree(self.__tmp, ignore_errors=True)

    def __fakeRunMetalCoord(self, writeOutput: bool = True) -> Any:
        def factory(d_args: Dict[str, Any]) -> mock.MagicMock:
            self.__runArgs.append(dict(d_args))
            inst = mock.MagicMock()

            def run() -> str:
                if writeOutput:
                    with open(os.path.join(d_args["workdir"], d_args["ligand"] + ".json"), "w", encoding="utf-8") as f:
                        f.write("{}")
                return "ok"

            inst.run.side_effect = run
            return inst

        return factory

    def __runMain(self, argv: List[str], sites: List[Dict[str, Any]]) -> mock.MagicMock:
        with mock.patch.object(sys, "argv", argv), mock.patch.object(pmcs, "RunMetalCoord", side_effect=self.__fakeRunMetalCoord()), mock.patch.object(
            pmcs, "ParseMetalCoord"
        ) as mParse:
            mParse.return_value.l_sites = sites
            pmcs.main()
        return mParse

    def testMainNoFilter(self) -> None:
        sites = [_site("A"), _site("B", tag="Distorted")]
        mParse = self.__runMain(self.__argv, sites)
        self.assertEqual([a["ligand"] for a in self.__runArgs], ["0KA", "NCO"])
        first = self.__runArgs[0]
        self.assertEqual(first["pdb"], "4DHV.cif")
        self.assertEqual(first["workdir"], self.__wrk)
        self.assertEqual(first["max_size"], 100)
        self.assertEqual(first["threshold"], 0.3)
        self.assertEqual(first["timeout"], 3600)
        self.assertIsNone(first["metalcoord_exe"])
        readPaths = [c[0][0] for c in mParse.return_value.read.call_args_list]
        self.assertEqual(readPaths, [os.path.join(self.__wrk, "0KA.json"), os.path.join(self.__wrk, "NCO.json")])
        self.assertEqual(mParse.return_value.parse.call_count, 2)
        self.assertEqual(_readJson(self.__report), sites)

    def testMainFilter(self) -> None:
        sites = [
            _site("A"),
            _site("B", klass=" "),
            _site("C", tag="Irregular"),
            _site("D", allowed="NO"),
            _site("E", exception="YES"),
        ]
        self.__runMain(self.__argv + ["--filter", "--max_size", "5", "--threshold", "0.5", "--timeout", "7"], sites)  # noqa: RUF005
        self.assertEqual(self.__runArgs[0]["max_size"], 5)
        self.assertEqual(self.__runArgs[0]["threshold"], 0.5)
        self.assertEqual(self.__runArgs[0]["timeout"], 7)
        self.assertEqual([d["chain"] for d in _readJson(self.__report)], ["A"])

    def testParametersError(self) -> None:
        err = _exc("MetalCoordParametersError")({"pdb": "bad"})
        with mock.patch.object(sys, "argv", self.__argv), mock.patch.object(pmcs, "RunMetalCoord", side_effect=err):
            with self.assertRaises(SystemExit) as cm:
                pmcs.main()
        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(_readJson(self.__report), {"error": "parameters-error", "details": {"pdb": "bad"}})

    def testTimeout(self) -> None:
        with mock.patch.object(sys, "argv", self.__argv), mock.patch.object(pmcs, "RunMetalCoord") as mRun:
            mRun.return_value.run.side_effect = _exc("MetalCoordCommandTimeoutError")(["metalCoord"], code=-1)
            with self.assertRaises(SystemExit):
                pmcs.main()
        mRun.return_value.setInputMode.assert_called_with("stats")
        self.assertEqual(_readJson(self.__report)["error"], "timeout")

    def testExecutionError(self) -> None:
        with mock.patch.object(sys, "argv", self.__argv), mock.patch.object(pmcs, "RunMetalCoord") as mRun:
            mRun.return_value.run.side_effect = _exc("MetalCoordCommandExecutionError")(["metalCoord"], code=1, stderr="oops")
            with self.assertRaises(SystemExit):
                pmcs.main()
        d = _readJson(self.__report)
        self.assertEqual(d["error"], "execution-error")
        self.assertIn("oops", d["details"])

    def testMissingOutput(self) -> None:
        with mock.patch.object(sys, "argv", self.__argv), mock.patch.object(pmcs, "RunMetalCoord", side_effect=self.__fakeRunMetalCoord(writeOutput=False)):
            with self.assertRaises(SystemExit):
                pmcs.main()
        d = _readJson(self.__report)
        self.assertEqual(d["error"], "unexpected-error")
        self.assertIn("0KA", d["details"])

    def testParseError(self) -> None:
        with mock.patch.object(sys, "argv", self.__argv), mock.patch.object(pmcs, "RunMetalCoord", side_effect=self.__fakeRunMetalCoord()), mock.patch.object(
            pmcs, "ParseMetalCoord"
        ) as mParse:
            mParse.return_value.parse.side_effect = _exc("MetalCoordParseError")("cannot parse")
            with self.assertRaises(SystemExit):
                pmcs.main()
        d = _readJson(self.__report)
        self.assertEqual(d["error"], "unexpected-error")
        self.assertIn("cannot parse", d["details"])


if __name__ == "__main__":
    unittest.main()
