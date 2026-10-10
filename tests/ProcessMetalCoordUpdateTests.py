##
# File:    ProcessMetalCoordUpdateTests.py
#
# Update:
##
"""
Hermetic unit tests for wwpdb.utils.dp.metal.metalcoord.processMetalCoordUpdate.

Acedrg, MetalCoord and Servalcat are never invoked: their Run* wrappers are replaced by mocks at
the module level. callClean() is exercised for real against small generated mmCIF files.
"""

import atexit
import json
import logging
import os
import shutil
import sys
import tempfile
import unittest
from typing import Any, Dict, List, Optional, Tuple
from unittest import mock

from mmcif.io.IoAdapterCore import IoAdapterCore

# processMetalCoordUpdate calls setup_logger(log_dir=".") at import time, which creates a log file in
# the current directory. Import from inside a scratch directory so that the repository is not littered.
_LOGDIR = tempfile.mkdtemp(prefix="metalcoord_log_")
atexit.register(shutil.rmtree, _LOGDIR, True)
_CWD = os.getcwd()
os.chdir(_LOGDIR)
try:
    from wwpdb.utils.dp.metal.metalcoord import processMetalCoordUpdate as pmcu  # noqa: E402
finally:
    os.chdir(_CWD)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logger = logging.getLogger()


def _exc(name: str) -> Any:
    """Return the exception class exactly as bound in the module under test at runtime.

    The module imports its collaborators through sys.path-relative names (e.g. ``metalcoord.runMetalCoord``),
    so these classes are distinct from the ``wwpdb.utils.dp.metal...`` ones and must be taken from the module itself.
    """
    cls = vars(pmcu)[name]
    assert issubclass(cls, Exception)
    return cls


_ATOM_CIF = """data_comp_list
loop_
_chem_comp.id
_chem_comp.name
LIG 'test ligand'
#
data_comp_LIG
loop_
_chem_comp_atom.comp_id
_chem_comp_atom.atom_id
_chem_comp_atom.type_symbol
_chem_comp_atom.charge
_chem_comp_atom.pdbx_model_Cartn_x_ideal
_chem_comp_atom.pdbx_model_Cartn_y_ideal
_chem_comp_atom.pdbx_model_Cartn_z_ideal
LIG ZN1 ZN 0 1.0 2.0 3.0
LIG CO1 CO 0 4.0 5.0 6.0
LIG C1 C 0 7.0 8.0 9.0
#
"""

_NOATOM_CIF = """data_comp_list
loop_
_chem_comp.id
_chem_comp.name
LIG 'test ligand'
#
data_comp_LIG
_chem_comp.id LIG
#
"""

_ONEBLOCK_CIF = """data_comp_LIG
_chem_comp.id LIG
#
"""


def _write(path: str, text: str) -> str:
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def _readJson(path: str) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _site(chain: str, klass: str = "Tetrahedral", tag: str = "Regular", allowed: str = "YES", exception: str = "NO") -> Dict[str, Any]:
    return {"chain": chain, "class": klass, "tag": tag, "coordination_number_allowed": allowed, "class_in_exception": exception}


class _Base(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)


class CallAcedrgTests(_Base):
    def testSuccess(self) -> None:
        out = os.path.join(self.tmp, "acedrg")
        _write(out + ".cif", "data_x\n")
        d_args = {"out": out}
        with mock.patch.object(pmcu, "RunAcedrg") as mRun:
            self.assertEqual(pmcu.callAcedrg(d_args), out + ".cif")
        mRun.assert_called_once_with(d_args)
        mRun.return_value.run.assert_called_once_with()

    def testNoOutput(self) -> None:
        with mock.patch.object(pmcu, "RunAcedrg"):
            self.assertIsNone(pmcu.callAcedrg({"out": os.path.join(self.tmp, "acedrg")}))

    def testErrors(self) -> None:
        with mock.patch.object(pmcu, "RunAcedrg", side_effect=_exc("AcedrgParametersError")({"mmcif": "missing"})):
            self.assertIsNone(pmcu.callAcedrg({"out": "x"}))
        for exc in (_exc("AcedrgCommandTimeoutError")(["acedrg"], code=-1), _exc("AcedrgCommandExecutionError")(["acedrg"], code=1)):
            with mock.patch.object(pmcu, "RunAcedrg") as mRun:
                mRun.return_value.run.side_effect = exc
                self.assertIsNone(pmcu.callAcedrg({"out": "x"}))


class CallMetalCoordTests(_Base):
    def __files(self, cif: bool = True, js: bool = True) -> Tuple[str, str]:
        fcif = os.path.join(self.tmp, "metalcoord.cif")
        fjs = os.path.join(self.tmp, "metalcoord.cif.json")
        if cif:
            _write(fcif, "data_x\n")
        if js:
            _write(fjs, "{}")
        return fcif, fjs

    def testSuccess(self) -> None:
        fcif, fjs = self.__files()
        with mock.patch.object(pmcu, "RunMetalCoord") as mRun:
            self.assertEqual(pmcu.callMetalCoord({"workdir": self.tmp, "pdb": "x.cif"}), (fcif, fjs))
        mRun.return_value.setInputMode.assert_called_once_with("update")
        self.assertEqual(mRun.return_value.run.call_count, 1)

    def testRetryWithoutPdb(self) -> None:
        fcif, fjs = os.path.join(self.tmp, "metalcoord.cif"), os.path.join(self.tmp, "metalcoord.cif.json")
        calls: List[Optional[str]] = []

        with mock.patch.object(pmcu, "RunMetalCoord") as mRun:
            inst = mRun.return_value
            inst.d_args = {"pdb": "x.cif"}

            def run() -> str:
                calls.append(inst.d_args["pdb"])
                if len(calls) == 2:
                    self.__files()
                return ""

            inst.run.side_effect = run
            self.assertEqual(pmcu.callMetalCoord({"workdir": self.tmp, "pdb": "x.cif"}), (fcif, fjs))
        self.assertEqual(calls, ["x.cif", None])

    def testRetryErrors(self) -> None:
        for exc in (_exc("MetalCoordCommandTimeoutError")(["mc"], code=-1), _exc("MetalCoordCommandExecutionError")(["mc"], code=1)):
            with mock.patch.object(pmcu, "RunMetalCoord") as mRun:
                mRun.return_value.d_args = {}
                mRun.return_value.run.side_effect = ["", exc]
                self.assertEqual(pmcu.callMetalCoord({"workdir": self.tmp, "pdb": "x.cif"}), (None, None))

    def testNoCifNoPdb(self) -> None:
        with mock.patch.object(pmcu, "RunMetalCoord") as mRun:
            self.assertEqual(pmcu.callMetalCoord({"workdir": self.tmp, "pdb": None}), (None, None))
        self.assertEqual(mRun.return_value.run.call_count, 1)

    def testNoJson(self) -> None:
        self.__files(js=False)
        with mock.patch.object(pmcu, "RunMetalCoord"):
            self.assertEqual(pmcu.callMetalCoord({"workdir": self.tmp}), (None, None))

    def testErrors(self) -> None:
        with mock.patch.object(pmcu, "RunMetalCoord", side_effect=_exc("MetalCoordParametersError")({"input": "bad"})):
            self.assertEqual(pmcu.callMetalCoord({"workdir": self.tmp}), (None, None))
        for exc in (_exc("MetalCoordCommandTimeoutError")(["mc"], code=-1), _exc("MetalCoordCommandExecutionError")(["mc"], code=1)):
            with mock.patch.object(pmcu, "RunMetalCoord") as mRun:
                mRun.return_value.run.side_effect = exc
                self.assertEqual(pmcu.callMetalCoord({"workdir": self.tmp}), (None, None))


class CallServalcatTests(_Base):
    def testSuccess(self) -> None:
        prefix = os.path.join(self.tmp, "servalcat")
        _write(prefix + "_updated.cif", "data_x\n")
        with mock.patch.object(pmcu, "RunServalcat") as mRun:
            self.assertEqual(pmcu.callServalcat({"output_prefix": prefix}), prefix + "_updated.cif")
        mRun.return_value.run.assert_called_once_with()

    def testNoOutput(self) -> None:
        with mock.patch.object(pmcu, "RunServalcat"):
            self.assertIsNone(pmcu.callServalcat({"output_prefix": os.path.join(self.tmp, "servalcat")}))

    def testErrors(self) -> None:
        with mock.patch.object(pmcu, "RunServalcat", side_effect=_exc("ServalcatParametersError")({"x": "y"})):
            self.assertIsNone(pmcu.callServalcat({"output_prefix": "p"}))
        for exc in (_exc("ServalcatCommandTimeoutError")(["s"], code=-1), _exc("ServalcatCommandExecutionError")(["s"], code=1)):
            with mock.patch.object(pmcu, "RunServalcat") as mRun:
                mRun.return_value.run.side_effect = exc
                self.assertIsNone(pmcu.callServalcat({"output_prefix": "p"}))


class CallCleanTests(_Base):
    def testClean(self) -> None:
        fp = _write(os.path.join(self.tmp, "servalcat_updated.cif"), _ATOM_CIF)
        out = pmcu.callClean(fp)
        self.assertEqual(out, os.path.join(self.tmp, "clean.cif"))
        assert out is not None
        l_dc = IoAdapterCore().readFile(out)
        self.assertEqual(len(l_dc), 2)
        cat = l_dc[1].getObj("chem_comp_atom")
        attrs = cat.getAttributeList()
        for a in ("model_Cartn_x", "model_Cartn_y", "model_Cartn_z"):
            self.assertIn(a, attrs)
        self.assertNotIn("pdbx_model_Cartn_x_ideal", attrs)
        charges = {cat.getValue("atom_id", i): cat.getValue("charge", i) for i in range(cat.getRowCount())}
        # Zn: not redox active -> oxidation state 2; Co: redox active -> '?'; C untouched
        self.assertEqual(charges, {"ZN1": "2", "CO1": "?", "C1": "0"})
        self.assertEqual(cat.getValue("model_Cartn_x", 0), "1.0")

    def testNoAtomCategory(self) -> None:
        fp = _write(os.path.join(self.tmp, "s.cif"), _NOATOM_CIF)
        self.assertIsNone(pmcu.callClean(fp))

    def testSingleBlock(self) -> None:
        fp = _write(os.path.join(self.tmp, "s.cif"), _ONEBLOCK_CIF)
        self.assertIsNone(pmcu.callClean(fp))

    def testEmptyFile(self) -> None:
        fp = _write(os.path.join(self.tmp, "s.cif"), "")
        self.assertIsNone(pmcu.callClean(fp))


class MainTests(_Base):
    def setUp(self) -> None:
        super().setUp()
        self.wrk = os.path.join(self.tmp, "mc")
        os.makedirs(self.wrk)
        self.report = os.path.join(self.wrk, "metalcoord_report.json")
        self.argv = ["processMetalCoordUpdate.py", "--input", "0KA.cif", "--pdb", "4DHV.cif", "--workdir", self.wrk, "--timeout", "9"]

    def __runMain(
        self,
        acedrg: Optional[str] = "acedrg.cif",
        metalcoord: Tuple[Optional[str], Optional[str]] = ("mc.cif", "mc.json"),
        servalcat: Optional[str] = "serv.cif",
        clean: Optional[str] = "clean.cif",
        sites: Optional[List[Dict[str, Any]]] = None,
        parseError: bool = False,
    ) -> Dict[str, mock.MagicMock]:
        with mock.patch.object(sys, "argv", self.argv), mock.patch.object(pmcu, "callAcedrg", return_value=acedrg) as mA:
            mM_patch = mock.patch.object(pmcu, "callMetalCoord", return_value=metalcoord)
            mS_patch = mock.patch.object(pmcu, "callServalcat", return_value=servalcat)
            with mM_patch as mM, mS_patch as mS:
                with mock.patch.object(pmcu, "callClean", return_value=clean) as mC, mock.patch.object(pmcu, "ParseMetalCoord") as mP:
                    mP.return_value.l_sites = sites if sites is not None else []
                    if parseError:
                        mP.return_value.read.side_effect = _exc("MetalCoordParseError")("broken")
                    pmcu.main()
        return {"acedrg": mA, "metalcoord": mM, "servalcat": mS, "clean": mC, "parse": mP}

    def testSuccessFilter(self) -> None:
        sites = [_site("A"), _site("B", klass=""), _site("C", tag="Distorted"), _site("D", allowed="NO"), _site("E", exception="YES")]
        mocks = self.__runMain(sites=sites)
        self.assertEqual(mocks["acedrg"].call_args[0][0], {"acedrg_exe": None, "mmcif": "0KA.cif", "out": os.path.join(self.wrk, "acedrg"), "timeout": 9})
        self.assertEqual(
            mocks["metalcoord"].call_args[0][0],
            {"metalcoord_exe": None, "workdir": self.wrk, "input": "acedrg.cif", "pdb": "4DHV.cif", "threshold": 0.3, "timeout": 9},
        )
        self.assertEqual(
            mocks["servalcat"].call_args[0][0],
            {"servalcat_exe": None, "update_dictionary": "mc.cif", "output_prefix": os.path.join(self.wrk, "servalcat"), "timeout": 9},
        )
        mocks["clean"].assert_called_once_with("serv.cif")
        mocks["parse"].return_value.read.assert_called_once_with("mc.json")
        self.assertEqual([d["chain"] for d in _readJson(self.report)], ["A"])

    def __assertExit(self, error: str, **kwargs: Any) -> None:
        with self.assertRaises(SystemExit) as cm:
            self.__runMain(**kwargs)
        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(_readJson(self.report)["error"], error)

    def testAcedrgFailed(self) -> None:
        self.__assertExit("acedrg-failed", acedrg=None)

    def testMetalCoordFailed(self) -> None:
        self.__assertExit("metalcoord-failed", metalcoord=(None, None))

    def testServalcatFailed(self) -> None:
        self.__assertExit("servalcat-failed", servalcat=None)

    def testCleanFailed(self) -> None:
        self.__assertExit("clean-failed", clean=None)

    def testParseFailed(self) -> None:
        self.__assertExit("unexpected-error", parseError=True)


if __name__ == "__main__":
    unittest.main()
