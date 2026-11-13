##
# File:    ProcessFindGeoTests.py
#
# Update:
##
"""
Hermetic unit tests for wwpdb.utils.dp.metal.findgeo.processFindGeo.

The FindGeo executable is never invoked: RunFindGeo and ParseFindGeo are replaced by mocks
at the module level, and all outputs are written to temporary directories.
"""

import atexit
import json
import logging
import os
import shutil
import sys
import tempfile
import unittest
from typing import Any, Dict, List, Optional
from unittest import mock

# processFindGeo calls setup_logger(log_dir=".") at import time, which creates a log file in the
# current directory. Import from inside a scratch directory so that the repository is not littered.
_LOGDIR = tempfile.mkdtemp(prefix="findgeo_log_")
atexit.register(shutil.rmtree, _LOGDIR, True)
_CWD = os.getcwd()
os.chdir(_LOGDIR)
try:
    from wwpdb.utils.dp.metal.findgeo import processFindGeo as pfg  # noqa: E402
finally:
    os.chdir(_CWD)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logger = logging.getLogger()


def _exc(name: str) -> Any:
    """Return the exception class exactly as bound in the module under test at runtime.

    The module imports its collaborators through sys.path-relative names (e.g. ``metalcoord.runMetalCoord``),
    so these classes are distinct from the ``wwpdb.utils.dp.metal...`` ones and must be taken from the module itself.
    """
    cls = vars(pfg)[name]
    assert issubclass(cls, Exception)
    return cls


def _site(
    metal: str = "ZN1",
    tag: str = "Regular",
    allowed: str = "YES",
    coordination: Any = "4",
    rmsd: Any = "0.1",
    carbon_metal: str = "YES",
    klass: str = "Tetrahedral",
    chain: str = "A",
) -> Dict[str, Any]:
    return {
        "residue": "ZN",
        "metal": metal,
        "chain": chain,
        "sequence": "1",
        "icode": "",
        "altloc": "",
        "tag": tag,
        "coordination_number_allowed": allowed,
        "coordination": coordination,
        "rmsd": rmsd,
        "carbon_metal": carbon_metal,
        "class": klass,
    }


def _writeJson(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f)


def _readJson(path: str) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class ReadJsonTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmp = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.__tmp, ignore_errors=True)

    def testReadValid(self) -> None:
        fp = os.path.join(self.__tmp, "a.json")
        _writeJson(fp, [{"a": 1}])
        self.assertEqual(pfg.readJson(fp), [{"a": 1}])

    def testReadMissing(self) -> None:
        with self.assertRaises(_exc("jsonValidationError")) as cm:
            pfg.readJson(os.path.join(self.__tmp, "missing.json"))
        self.assertIn("not found", str(cm.exception))

    def testReadInvalid(self) -> None:
        fp = os.path.join(self.__tmp, "bad.json")
        with open(fp, "w", encoding="utf-8") as f:
            f.write("{not json")
        with self.assertRaises(_exc("jsonValidationError")) as cm:
            pfg.readJson(fp)
        self.assertIn("Invalid JSON", str(cm.exception))

    def testReadDirectory(self) -> None:
        # Opening a directory raises an OSError subclass (IsADirectoryError)
        with self.assertRaises(_exc("jsonValidationError")) as cm:
            pfg.readJson(self.__tmp)
        self.assertIn("Error reading file", str(cm.exception))

    def testReadUnexpected(self) -> None:
        fp = os.path.join(self.__tmp, "a.json")
        _writeJson(fp, [])
        with mock.patch("json.load", side_effect=RuntimeError("boom")), self.assertRaises(_exc("jsonValidationError")) as cm:
            pfg.readJson(fp)
        self.assertIn("Unexpected error", str(cm.exception))


class SiteCompareTests(unittest.TestCase):
    def testReadSites(self) -> None:
        d = pfg.readSites([_site(), {"metal": "X"}])
        self.assertIn(("ZN", "ZN1", "A", "1", "", ""), d)
        self.assertIn(("", "X", "", "", "", ""), d)
        self.assertEqual(len(d), 2)

    def testCompareRmsd(self) -> None:
        self.assertEqual(pfg.compareRmsd({"rmsd": "0.1"}, {"rmsd": "0.2"}), "exclude_carbon")
        self.assertEqual(pfg.compareRmsd({"rmsd": "0.2"}, {"rmsd": "0.2"}), "exclude_carbon")
        self.assertEqual(pfg.compareRmsd({"rmsd": "0.3"}, {"rmsd": "0.2"}), "include_carbon")
        # non-numeric values are treated as 99.0
        self.assertEqual(pfg.compareRmsd({"rmsd": "?"}, {"rmsd": "5"}), "include_carbon")
        self.assertEqual(pfg.compareRmsd({"rmsd": "5"}, {"rmsd": "?"}), "exclude_carbon")

    def __pick(self, exc: Optional[Dict[str, Any]], inc: Optional[Dict[str, Any]]) -> str:
        if exc is not None:
            exc["which"] = "exc"
        if inc is not None:
            inc["which"] = "inc"
        res = pfg.compareResults([exc] if exc else [], [inc] if inc else [])
        self.assertEqual(len(res), 1)
        return str(res[0]["which"])

    def testOnlyOne(self) -> None:
        self.assertEqual(self.__pick(_site(), None), "exc")
        self.assertEqual(self.__pick(None, _site()), "inc")
        # Carbon-metal bond not allowed -> include result discarded
        self.assertEqual(self.__pick(_site(tag="Irregular"), _site(carbon_metal="NO")), "exc")

    @unittest.expectedFailure
    def testCarbonNotAllowedAlone(self) -> None:
        # Suspected bug: when the only result is an include-carbon site with carbon_metal == "NO",
        # both candidates become empty and compareRmsd() raises TypeError on float(None).
        res = pfg.compareResults([], [_site(carbon_metal="NO")])
        self.assertEqual(res, [])

    @unittest.expectedFailure
    def testCompareRmsdMissing(self) -> None:
        # Suspected bug: docstring says missing values are treated as 99.0, but float(None) raises TypeError
        self.assertEqual(pfg.compareRmsd({}, {"rmsd": "1.0"}), "include_carbon")

    def testRegularPreferred(self) -> None:
        self.assertEqual(self.__pick(_site(tag="Regular"), _site(tag="Distorted")), "exc")
        self.assertEqual(self.__pick(_site(tag="Irregular"), _site(tag="Regular")), "inc")

    def testDistortedPreferred(self) -> None:
        self.assertEqual(self.__pick(_site(tag="Distorted"), _site(tag="Irregular")), "exc")
        self.assertEqual(self.__pick(_site(tag="Irregular"), _site(tag="Distorted")), "inc")

    def testBothRegularAllowed(self) -> None:
        self.assertEqual(self.__pick(_site(allowed="YES"), _site(allowed="NO")), "exc")
        self.assertEqual(self.__pick(_site(allowed="NO"), _site(allowed="YES")), "inc")
        # neither allowed -> rmsd
        self.assertEqual(self.__pick(_site(allowed="NO", rmsd="0.1"), _site(allowed="NO", rmsd="0.2")), "exc")
        self.assertEqual(self.__pick(_site(allowed="NO", rmsd="0.3"), _site(allowed="NO", rmsd="0.2")), "inc")

    def testBothAllowedCoordination(self) -> None:
        self.assertEqual(self.__pick(_site(coordination="5"), _site(coordination="4")), "exc")
        self.assertEqual(self.__pick(_site(coordination="4"), _site(coordination="6")), "inc")
        # non-numeric coordination treated as 0
        self.assertEqual(self.__pick(_site(coordination="x"), _site(coordination="4")), "inc")
        self.assertEqual(self.__pick(_site(coordination="4"), _site(coordination="?")), "exc")
        # same coordination -> rmsd
        self.assertEqual(self.__pick(_site(tag="Distorted", rmsd="0.1"), _site(tag="Distorted", rmsd="0.5")), "exc")
        self.assertEqual(self.__pick(_site(tag="Distorted", rmsd="0.9"), _site(tag="Distorted", rmsd="0.5")), "inc")

    def testBothIrregular(self) -> None:
        self.assertEqual(self.__pick(_site(tag="Irregular", allowed="YES"), _site(tag="Irregular", allowed="NO")), "exc")
        self.assertEqual(self.__pick(_site(tag="Irregular", allowed="NO"), _site(tag="Irregular", allowed="YES")), "inc")
        self.assertEqual(self.__pick(_site(tag="Irregular", rmsd="0.1"), _site(tag="Irregular", rmsd="0.2")), "exc")
        self.assertEqual(self.__pick(_site(tag="Irregular", rmsd="0.4"), _site(tag="Irregular", rmsd="0.2")), "inc")

    def testMultipleSites(self) -> None:
        res = pfg.compareResults([_site(chain="A"), _site(chain="B")], [_site(chain="C")])
        self.assertEqual(sorted(d["chain"] for d in res), ["A", "B", "C"])


class RunOneTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmp = tempfile.mkdtemp()
        self.__wrk = os.path.join(self.__tmp, "fg")
        os.makedirs(self.__wrk)
        self.__args: Dict[str, Any] = {"workdir": self.__wrk, "format": "cif", "timeout": 10}
        self.__report = os.path.join(self.__wrk, "findgeo_report.json")

    def tearDown(self) -> None:
        shutil.rmtree(self.__tmp, ignore_errors=True)

    def testSuccess(self) -> None:
        with mock.patch.object(pfg, "RunFindGeo") as mRun, mock.patch.object(pfg, "ParseFindGeo") as mParse:
            mRun.return_value.run.return_value = "stdout"
            self.assertTrue(pfg.runOne(self.__args))
        mRun.assert_called_once_with(self.__args)
        mParse.assert_called_once_with(self.__wrk, input_format="cif")
        mParse.return_value.parse.assert_called_once_with()
        mParse.return_value.report.assert_called_once_with(self.__report)

    def testParametersError(self) -> None:
        with mock.patch.object(pfg, "RunFindGeo", side_effect=_exc("ValidateParametersError")({"input": "bad"})):
            self.assertFalse(pfg.runOne(self.__args))
        self.assertEqual(_readJson(self.__report), {"error": "parameters-error", "details": {"input": "bad"}})

    def testTimeout(self) -> None:
        with mock.patch.object(pfg, "RunFindGeo") as mRun:
            mRun.return_value.run.side_effect = _exc("FindGeoCommandTimeoutError")(["java"], code=-1)
            self.assertFalse(pfg.runOne(self.__args))
        self.assertEqual(_readJson(self.__report), {"error": "timeout", "details": "Timeout after 10 seconds"})

    def testExecutionError(self) -> None:
        with mock.patch.object(pfg, "RunFindGeo") as mRun:
            mRun.return_value.run.side_effect = _exc("FindGeoCommandExecutionError")(["java"], code=2, stderr="bad")
            self.assertFalse(pfg.runOne(self.__args))
        d = _readJson(self.__report)
        self.assertEqual(d["error"], "execution-error")
        self.assertIn("bad", d["details"])


class RunCompareTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmp = tempfile.mkdtemp()
        self.__wrk = os.path.join(self.__tmp, "fg")
        self.__report = os.path.join(self.__wrk, "findgeo_report.json")
        self.__calls: List[Dict[str, Any]] = []

    def tearDown(self) -> None:
        shutil.rmtree(self.__tmp, ignore_errors=True)

    def __fakeRunOne(self, results: Dict[str, Any]) -> Any:
        """results maps workdir suffix to (return value, json content or None)"""

        def run(d_args: Dict[str, Any]) -> bool:
            self.__calls.append(d_args)
            suffix = "exclude" if d_args["workdir"].endswith("_exclude_carbon") else "include"
            ret, content = results[suffix]
            if content is not None:
                _writeJson(os.path.join(d_args["workdir"], "findgeo_report.json"), content)
            return bool(ret)

        return run

    def testDonorListsWithoutC(self) -> None:
        exc = [dict(_site(), which="exc")]
        inc = [dict(_site(tag="Irregular"), which="inc")]
        fake = self.__fakeRunOne({"exclude": (True, exc), "include": (True, inc)})
        with mock.patch.object(pfg, "runOne", side_effect=fake):
            self.assertTrue(pfg.runCompare({"workdir": self.__wrk, "excluded-donors": "H,D"}))
        self.assertEqual(self.__calls[0]["excluded-donors"], "C,H,D")
        self.assertEqual(self.__calls[0]["workdir"], self.__wrk + "_exclude_carbon")
        self.assertEqual(self.__calls[1]["excluded-donors"], "H,D")
        self.assertEqual(self.__calls[1]["workdir"], self.__wrk + "_include_carbon")
        res = _readJson(self.__report)
        self.assertEqual([d["which"] for d in res], ["exc"])

    def testDonorListsWithC(self) -> None:
        fake = self.__fakeRunOne({"exclude": (True, []), "include": (True, [])})
        with mock.patch.object(pfg, "runOne", side_effect=fake):
            self.assertTrue(pfg.runCompare({"workdir": self.__wrk, "excluded-donors": "H,C"}))
        self.assertEqual(self.__calls[0]["excluded-donors"], "H,C")
        self.assertEqual(self.__calls[1]["excluded-donors"], "H")
        self.assertEqual(_readJson(self.__report), [])

    def testFirstRunFailsWithReport(self) -> None:
        err = {"error": "timeout", "details": "x"}
        fake = self.__fakeRunOne({"exclude": (False, err), "include": (True, [])})
        with mock.patch.object(pfg, "runOne", side_effect=fake):
            self.assertFalse(pfg.runCompare({"workdir": self.__wrk, "excluded-donors": "H"}))
        self.assertEqual(len(self.__calls), 1)
        self.assertEqual(_readJson(self.__report), err)

    def testFirstRunFailsNoReport(self) -> None:
        fake = self.__fakeRunOne({"exclude": (False, None), "include": (True, [])})
        with mock.patch.object(pfg, "runOne", side_effect=fake):
            self.assertFalse(pfg.runCompare({"workdir": self.__wrk, "excluded-donors": "H"}))
        self.assertEqual(_readJson(self.__report)["error"], "json-error")

    def testSecondRunFailsWithReport(self) -> None:
        err = {"error": "execution-error", "details": "y"}
        fake = self.__fakeRunOne({"exclude": (True, []), "include": (False, err)})
        with mock.patch.object(pfg, "runOne", side_effect=fake):
            self.assertFalse(pfg.runCompare({"workdir": self.__wrk, "excluded-donors": "H"}))
        self.assertEqual(len(self.__calls), 2)
        self.assertEqual(_readJson(self.__report), err)

    def testSecondRunFailsNoReport(self) -> None:
        fake = self.__fakeRunOne({"exclude": (True, []), "include": (False, None)})
        with mock.patch.object(pfg, "runOne", side_effect=fake):
            self.assertFalse(pfg.runCompare({"workdir": self.__wrk, "excluded-donors": "H"}))
        self.assertEqual(_readJson(self.__report)["error"], "json-error")

    def testCannotCreateWorkdir(self) -> None:
        with mock.patch("os.makedirs", side_effect=OSError("denied")), mock.patch("sys.stderr"), self.assertRaises(SystemExit) as cm:
            pfg.runCompare({"workdir": self.__wrk, "excluded-donors": "H"})
        self.assertEqual(cm.exception.code, 1)


class MainTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmp = tempfile.mkdtemp()
        self.__wrk = os.path.join(self.__tmp, "fg")
        self.__report = os.path.join(self.__wrk, "findgeo_report.json")
        self.__baseArgv = ["processFindGeo.py", "--java-exe", "java", "--findgeo-jar", "fg.jar", "--input", "x.cif", "--workdir", self.__wrk]

    def tearDown(self) -> None:
        shutil.rmtree(self.__tmp, ignore_errors=True)

    def __writer(self, content: Any) -> Any:
        def run(d_args: Dict[str, Any]) -> bool:
            _writeJson(os.path.join(d_args["workdir"], "findgeo_report.json"), content)
            return True

        return run

    def testMainRunOneArgs(self) -> None:
        with mock.patch.object(sys, "argv", self.__baseArgv), mock.patch.object(pfg, "runOne", side_effect=self.__writer([_site()])) as mRun:
            pfg.main()
        d_args = mRun.call_args[0][0]
        self.assertEqual(d_args["excluded-donors"], "H,D")
        self.assertEqual(d_args["format"], "cif")
        self.assertEqual(d_args["input"], "x.cif")
        self.assertEqual(d_args["metal"], "All")
        self.assertTrue(d_args["overwright"])
        self.assertIsNone(d_args["pdb"])
        self.assertEqual(d_args["threshold"], 2.8)
        self.assertEqual(d_args["excluded-metals"], "None")
        self.assertEqual(d_args["java-exe"], "java")
        self.assertEqual(d_args["findgeo-jar"], "fg.jar")
        self.assertEqual(d_args["timeout"], 3600)
        # no filter -> report untouched
        self.assertEqual(_readJson(self.__report), [_site()])

    def testMainCompare(self) -> None:
        argv = self.__baseArgv + ["--compare-donors"]  # noqa: RUF005
        with mock.patch.object(sys, "argv", argv), mock.patch.object(pfg, "runOne") as mRun:
            with mock.patch.object(pfg, "runCompare", side_effect=self.__writer([])) as mCmp:
                pfg.main()
        mCmp.assert_called_once()
        mRun.assert_not_called()

    def testMainMissingReport(self) -> None:
        with mock.patch.object(sys, "argv", self.__baseArgv), mock.patch.object(pfg, "runOne", return_value=False), mock.patch("sys.stderr"):
            with self.assertRaises(SystemExit) as cm:
                pfg.main()
        self.assertEqual(cm.exception.code, 1)

    def testMainFilter(self) -> None:
        sites = [
            _site(chain="A"),
            _site(chain="B", klass="  "),
            _site(chain="C", tag="Distorted"),
            _site(chain="D", allowed="NO"),
            dict(_site(chain="E"), class_in_exception="YES"),
            dict(_site(chain="F"), class_in_exception="NO"),
        ]
        argv = self.__baseArgv + ["--filter"]  # noqa: RUF005
        with mock.patch.object(sys, "argv", argv), mock.patch.object(pfg, "runOne", side_effect=self.__writer(sites)):
            pfg.main()
        self.assertEqual([d["chain"] for d in _readJson(self.__report)], ["A", "F"])

    def testMainFilterNoChange(self) -> None:
        sites = [_site(chain="A")]
        argv = self.__baseArgv + ["--filter"]  # noqa: RUF005
        with mock.patch.object(sys, "argv", argv), mock.patch.object(pfg, "runOne", side_effect=self.__writer(sites)):
            pfg.main()
        self.assertEqual(_readJson(self.__report), sites)


if __name__ == "__main__":
    unittest.main()
