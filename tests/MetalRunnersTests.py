##
# File:    MetalRunnersTests.py
# Date:    2026-10-06
#
##
"""
Hermetic unit tests for the metal tool wrappers:

    wwpdb.utils.dp.metal.metalcoord.runAcedrg
    wwpdb.utils.dp.metal.metalcoord.runMetalCoord
    wwpdb.utils.dp.metal.metalcoord.runServalcat
    wwpdb.utils.dp.metal.findgeo.runFindGeo

No external binaries are executed: "executables" are empty placeholder files in a temporary
directory, and the run_command() name bound in each wrapper module is patched.

At runtime the wrappers import run_command via a sys.path entry for the metal_util directory
(i.e. as the top-level module "run_command"), so the base exception classes they catch must be
taken from that same module object. This file mirrors that import scheme.
"""

import logging
import os
import shutil
import sys
import tempfile
import unittest
from typing import TYPE_CHECKING, Any, Dict, List
from unittest import mock

from wwpdb.utils.dp.metal.findgeo import runFindGeo as rfg_module
from wwpdb.utils.dp.metal.findgeo.runFindGeo import FindGeoCommandExecutionError, FindGeoCommandTimeoutError, RunFindGeo, ValidateParametersError
from wwpdb.utils.dp.metal.metalcoord import runAcedrg as rag_module
from wwpdb.utils.dp.metal.metalcoord import runMetalCoord as rmc_module
from wwpdb.utils.dp.metal.metalcoord import runServalcat as rsc_module
from wwpdb.utils.dp.metal.metalcoord.runAcedrg import AcedrgCommandExecutionError, AcedrgCommandTimeoutError, AcedrgParametersError, RunAcedrg
from wwpdb.utils.dp.metal.metalcoord.runMetalCoord import (
    MetalCoordCommandExecutionError,
    MetalCoordCommandTimeoutError,
    MetalCoordParametersError,
    RunMetalCoord,
)
from wwpdb.utils.dp.metal.metalcoord.runServalcat import RunServalcat, ServalcatCommandExecutionError, ServalcatCommandTimeoutError, ServalcatParametersError

if TYPE_CHECKING:
    from wwpdb.utils.dp.metal.metal_util.run_command import MetalCommandExecutionError, MetalCommandTimeoutError
else:
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(rag_module.__file__))), "metal_util"))
    from run_command import MetalCommandExecutionError, MetalCommandTimeoutError  # noqa: E402 pylint: disable=import-error

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class _TempDirMixin(unittest.TestCase):
    """Common temporary directory handling"""

    def setUp(self) -> None:
        self.tmpDir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpDir, ignore_errors=True)

    def touch(self, *parts: str) -> str:
        fp = os.path.join(self.tmpDir, *parts)
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        with open(fp, "w", encoding="utf-8") as ofh:
            ofh.write("")
        return fp


# --------------------------------------------------------------------------------------------
class RunAcedrgTests(_TempDirMixin):
    def __args(self) -> Dict[str, Any]:
        return {"acedrg_exe": self.touch("bin", "acedrg_local"), "mmcif": self.touch("in.cif"), "out": os.path.join(self.tmpDir, "out_root"), "timeout": 30}

    def testValidExplicitExe(self) -> None:
        d_args = self.__args()
        rag = RunAcedrg(d_args)
        self.assertEqual(rag.d_args["acedrg_exe"], d_args["acedrg_exe"])

    def testCcp4Exe(self) -> None:
        d_args = self.__args()
        d_args["acedrg_exe"] = None
        ccp4Exe = self.touch("ccp4", "bin", "acedrg")
        with mock.patch.dict(os.environ, {"CCP4": os.path.join(self.tmpDir, "ccp4")}):
            rag = RunAcedrg(d_args)
        self.assertEqual(rag.d_args["acedrg_exe"], ccp4Exe)

    def testCcp4ExeMissing(self) -> None:
        d_args = self.__args()
        d_args["acedrg_exe"] = None
        with mock.patch.dict(os.environ, {"CCP4": os.path.join(self.tmpDir, "noccp4")}), self.assertRaises(AcedrgParametersError) as ctx:
            RunAcedrg(d_args)
        self.assertIn("CCP4 Acedrg executable not found", ctx.exception.errors["acedrg_exe"])

    def testNoCcp4Env(self) -> None:
        d_args = self.__args()
        d_args["acedrg_exe"] = ""
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CCP4", None)
            with self.assertRaises(AcedrgParametersError) as ctx:
                RunAcedrg(d_args)
        self.assertIn("'CCP4' is missing", ctx.exception.errors["acedrg_exe"])

    def testExplicitMissingAndNoInput(self) -> None:
        d_args = self.__args()
        d_args["acedrg_exe"] = os.path.join(self.tmpDir, "nope")
        d_args["mmcif"] = os.path.join(self.tmpDir, "nope.cif")
        with self.assertRaises(AcedrgParametersError) as ctx:
            RunAcedrg(d_args)
        self.assertEqual(set(ctx.exception.errors.keys()), {"acedrg_exe", "mmcif"})
        self.assertIn("nope.cif", str(ctx.exception))

    def testRunCommand(self) -> None:
        d_args = self.__args()
        rag = RunAcedrg(d_args)
        with mock.patch.object(rag_module, "run_command", return_value="acedrg ok") as mrun:
            out = rag.run()
        self.assertEqual(out, "acedrg ok")
        mrun.assert_called_once_with([d_args["acedrg_exe"], "--mmcif", d_args["mmcif"], "--out", d_args["out"], "--noProt"], 30)

    def testRunNoTimeoutKey(self) -> None:
        d_args = self.__args()
        del d_args["timeout"]
        rag = RunAcedrg(d_args)
        with mock.patch.object(rag_module, "run_command", return_value="") as mrun:
            rag.run()
        self.assertIsNone(mrun.call_args[0][1])

    def testRunTimeout(self) -> None:
        rag = RunAcedrg(self.__args())
        with mock.patch.object(rag_module, "run_command", side_effect=MetalCommandTimeoutError(["x"], None, stderr="Command timed out")):
            with self.assertRaises(AcedrgCommandTimeoutError) as ctx:
                rag.run()
        self.assertIn("timed out after 30 seconds", str(ctx.exception))
        self.assertIsInstance(ctx.exception, MetalCommandTimeoutError)

    def testRunExecutionError(self) -> None:
        rag = RunAcedrg(self.__args())
        with mock.patch.object(rag_module, "run_command", side_effect=MetalCommandExecutionError(["x"], 1, stderr="bad")):
            with self.assertRaises(AcedrgCommandExecutionError) as ctx:
                rag.run()
        self.assertNotIsInstance(ctx.exception, AcedrgCommandTimeoutError)
        self.assertIn("Acedrg command execution error", str(ctx.exception))


# --------------------------------------------------------------------------------------------
class RunServalcatTests(_TempDirMixin):
    def __args(self) -> Dict[str, Any]:
        return {"servalcat_exe": self.touch("bin", "servalcat_local"), "update_dictionary": self.touch("dict.cif"), "output_prefix": "pref", "timeout": 40}

    def testValidExplicitExe(self) -> None:
        d_args = self.__args()
        self.assertEqual(RunServalcat(d_args).d_args["servalcat_exe"], d_args["servalcat_exe"])

    def testCcp4Exe(self) -> None:
        d_args = self.__args()
        d_args["servalcat_exe"] = None
        ccp4Exe = self.touch("ccp4", "bin", "servalcat")
        with mock.patch.dict(os.environ, {"CCP4": os.path.join(self.tmpDir, "ccp4")}):
            rsc = RunServalcat(d_args)
        self.assertEqual(rsc.d_args["servalcat_exe"], ccp4Exe)

    def testCcp4ExeMissing(self) -> None:
        d_args = self.__args()
        d_args["servalcat_exe"] = None
        with mock.patch.dict(os.environ, {"CCP4": os.path.join(self.tmpDir, "noccp4")}), self.assertRaises(ServalcatParametersError) as ctx:
            RunServalcat(d_args)
        self.assertIn("CCP4 Servalcat executable not found", ctx.exception.errors["servalcat_exe"])

    def testNoCcp4Env(self) -> None:
        d_args = self.__args()
        d_args["servalcat_exe"] = None
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CCP4", None)
            with self.assertRaises(ServalcatParametersError) as ctx:
                RunServalcat(d_args)
        self.assertIn("'CCP4' is missing", ctx.exception.errors["servalcat_exe"])

    def testExplicitMissingAndNoDictionary(self) -> None:
        d_args = self.__args()
        d_args["servalcat_exe"] = os.path.join(self.tmpDir, "nope")
        d_args["update_dictionary"] = os.path.join(self.tmpDir, "nope.cif")
        with self.assertRaises(ServalcatParametersError) as ctx:
            RunServalcat(d_args)
        self.assertEqual(set(ctx.exception.errors.keys()), {"servalcat_exe", "update_dictionary"})

    def testRunCommand(self) -> None:
        d_args = self.__args()
        rsc = RunServalcat(d_args)
        with mock.patch.object(rsc_module, "run_command", return_value="servalcat ok") as mrun:
            out = rsc.run()
        self.assertEqual(out, "servalcat ok")
        expected = [d_args["servalcat_exe"], "refine_geom", "--update_dictionary", d_args["update_dictionary"], "--output_prefix", "pref"]
        mrun.assert_called_once_with(expected, 40)

    def testRunTimeout(self) -> None:
        rsc = RunServalcat(self.__args())
        with mock.patch.object(rsc_module, "run_command", side_effect=MetalCommandTimeoutError(["x"])):
            with self.assertRaises(ServalcatCommandTimeoutError) as ctx:
                rsc.run()
        self.assertIn("timed out after 40 seconds", str(ctx.exception))

    def testRunExecutionError(self) -> None:
        rsc = RunServalcat(self.__args())
        with mock.patch.object(rsc_module, "run_command", side_effect=MetalCommandExecutionError(["x"], 2)):
            with self.assertRaises(ServalcatCommandExecutionError) as ctx:
                rsc.run()
        self.assertNotIsInstance(ctx.exception, ServalcatCommandTimeoutError)
        self.assertIn("Servalcat command execution error", str(ctx.exception))


# --------------------------------------------------------------------------------------------
class RunMetalCoordTests(_TempDirMixin):
    def __args(self) -> Dict[str, Any]:
        return {
            "metalcoord_exe": self.touch("bin", "metalCoord_local"),
            "ligand": "zn",
            "pdb": "4DHV",
            "workdir": os.path.join(self.tmpDir, "work"),
            "max_size": 100,
            "threshold": 0.1,
            "timeout": 50,
            "input": None,
        }

    def testValidArgsCreatesWorkdir(self) -> None:
        d_args = self.__args()
        rmc = RunMetalCoord(d_args)
        self.assertTrue(os.path.isdir(d_args["workdir"]))
        self.assertIsNone(rmc.mode)

    def testValidPdbFileAndInput(self) -> None:
        d_args = self.__args()
        d_args["pdb"] = self.touch("model.cif")
        d_args["input"] = self.touch("acedrg.cif")
        d_args["ligand"] = "AB12C"
        RunMetalCoord(d_args)

    def testPdbTwelveCharacterId(self) -> None:
        d_args = self.__args()
        d_args["pdb"] = "pdb00004dhvx"
        RunMetalCoord(d_args)
        # Current behavior: an extended PDB ID containing "_" fails the isalnum() check
        d_args["pdb"] = "pdb_00004dhv"
        with self.assertRaises(MetalCoordParametersError) as ctx:
            RunMetalCoord(d_args)
        self.assertEqual(set(ctx.exception.errors.keys()), {"pdb"})

    def testCcp4Exe(self) -> None:
        d_args = self.__args()
        d_args["metalcoord_exe"] = None
        ccp4Exe = self.touch("ccp4", "bin", "metalCoord")
        with mock.patch.dict(os.environ, {"CCP4": os.path.join(self.tmpDir, "ccp4")}):
            rmc = RunMetalCoord(d_args)
        self.assertEqual(rmc.d_args["metalcoord_exe"], ccp4Exe)

    def testCcp4ExeMissing(self) -> None:
        d_args = self.__args()
        d_args["metalcoord_exe"] = None
        with mock.patch.dict(os.environ, {"CCP4": os.path.join(self.tmpDir, "noccp4")}), self.assertRaises(MetalCoordParametersError) as ctx:
            RunMetalCoord(d_args)
        self.assertIn("CCP4 MetalCoord executable not found", ctx.exception.errors["metalcoord_exe"])

    def testNoCcp4Env(self) -> None:
        d_args = self.__args()
        d_args["metalcoord_exe"] = None
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CCP4", None)
            with self.assertRaises(MetalCoordParametersError) as ctx:
                RunMetalCoord(d_args)
        self.assertIn("'CCP4' is missing", ctx.exception.errors["metalcoord_exe"])

    def testAllInvalid(self) -> None:
        blocker = self.touch("blocker")
        d_args = self.__args()
        d_args.update(
            {
                "metalcoord_exe": os.path.join(self.tmpDir, "nope"),
                "pdb": "not-a-pdb",
                "ligand": "TOOLONG",
                "max_size": 5,
                "input": os.path.join(self.tmpDir, "missing.cif"),
                "threshold": -1,
                "workdir": os.path.join(blocker, "sub"),
            }
        )
        with self.assertRaises(MetalCoordParametersError) as ctx:
            RunMetalCoord(d_args)
        self.assertEqual(set(ctx.exception.errors.keys()), {"metalcoord_exe", "pdb", "ligand", "max_size", "input", "threshold", "workdir"})

    def testInvalidTypes(self) -> None:
        d_args = self.__args()
        d_args.update({"ligand": "A-B", "max_size": "100", "threshold": "0.1"})
        with self.assertRaises(MetalCoordParametersError) as ctx:
            RunMetalCoord(d_args)
        self.assertEqual(set(ctx.exception.errors.keys()), {"ligand", "max_size", "threshold"})

    def testRunNoMode(self) -> None:
        rmc = RunMetalCoord(self.__args())
        with mock.patch.object(rmc_module, "run_command") as mrun:
            self.assertIsNone(rmc.run())
        mrun.assert_not_called()

    def testRunStats(self) -> None:
        d_args = self.__args()
        rmc = RunMetalCoord(d_args)
        rmc.setInputMode("stats")
        self.assertEqual(rmc.mode, "stats")
        with mock.patch.object(rmc_module, "run_command", return_value="stats ok") as mrun:
            out = rmc.run()
        self.assertEqual(out, "stats ok")
        expected: List[str] = [
            d_args["metalcoord_exe"],
            "stats",
            "--ligand",
            "ZN",
            "--pdb",
            "4DHV",
            "--max_size",
            "100",
            "--threshold",
            "0.1",
            "--output",
            os.path.join(d_args["workdir"], "zn.json"),
        ]
        mrun.assert_called_once_with(expected, 50)

    def testRunUpdateWithModel(self) -> None:
        d_args = self.__args()
        d_args["input"] = self.touch("acedrg.cif")
        rmc = RunMetalCoord(d_args)
        rmc.setInputMode("update")
        with mock.patch.object(rmc_module, "run_command", return_value="update ok") as mrun:
            out = rmc.run()
        self.assertEqual(out, "update ok")
        expected = [
            d_args["metalcoord_exe"],
            "update",
            "--input",
            d_args["input"],
            "--output",
            os.path.join(d_args["workdir"], "metalcoord.cif"),
            "--threshold",
            "0.1",
            "--pdb",
            "4DHV",
        ]
        mrun.assert_called_once_with(expected, 50)

    def testRunUpdateMostCommon(self) -> None:
        d_args = self.__args()
        d_args["input"] = self.touch("acedrg.cif")
        d_args["pdb"] = None
        rmc = RunMetalCoord(d_args)
        rmc.setInputMode("update")
        with mock.patch.object(rmc_module, "run_command", return_value="") as mrun:
            rmc.run()
        cmd = mrun.call_args[0][0]
        self.assertEqual(cmd[-3:], ["--cif", "--cl", "most_common"])
        self.assertNotIn("--pdb", cmd)

    def testRunStatsErrors(self) -> None:
        rmc = RunMetalCoord(self.__args())
        rmc.setInputMode("stats")
        with mock.patch.object(rmc_module, "run_command", side_effect=MetalCommandTimeoutError(["x"])):
            with self.assertRaises(MetalCoordCommandTimeoutError) as ctx:
                rmc.run()
        self.assertIn("stats command timed out after 50 seconds", str(ctx.exception))
        with mock.patch.object(rmc_module, "run_command", side_effect=MetalCommandExecutionError(["x"], 1)):
            with self.assertRaises(MetalCoordCommandExecutionError) as ctx2:
                rmc.run()
        self.assertIn("stats command execution error", str(ctx2.exception))
        with mock.patch.object(rmc_module, "run_command", side_effect=RuntimeError("kaboom")):
            with self.assertRaises(MetalCoordCommandExecutionError) as ctx3:
                rmc.run()
        self.assertIn("Unexpected error while running MetalCoord stats command: kaboom", str(ctx3.exception))

    def testRunUpdateErrors(self) -> None:
        d_args = self.__args()
        d_args["input"] = self.touch("acedrg.cif")
        rmc = RunMetalCoord(d_args)
        rmc.setInputMode("update")
        with mock.patch.object(rmc_module, "run_command", side_effect=MetalCommandTimeoutError(["x"])):
            with self.assertRaises(MetalCoordCommandTimeoutError) as ctx:
                rmc.run()
        self.assertIn("update command timed out after 50 seconds", str(ctx.exception))
        with mock.patch.object(rmc_module, "run_command", side_effect=MetalCommandExecutionError(["x"], 1)):
            with self.assertRaises(MetalCoordCommandExecutionError) as ctx2:
                rmc.run()
        self.assertIn("update command execution error", str(ctx2.exception))
        with mock.patch.object(rmc_module, "run_command", side_effect=RuntimeError("kaboom")):
            with self.assertRaises(MetalCoordCommandExecutionError) as ctx3:
                rmc.run()
        self.assertIn("Unexpected error while running MetalCoord update command: kaboom", str(ctx3.exception))


# --------------------------------------------------------------------------------------------
class RunFindGeoTests(_TempDirMixin):
    def __args(self) -> Dict[str, Any]:
        return {
            "excluded-donors": "C,H",
            "format": "cif",
            "input": self.touch("model.cif"),
            "metal": "all",
            "overwright": True,
            "pdb": None,
            "threshold": 2.8,
            "workdir": os.path.join(self.tmpDir, "findgeo"),
            "excluded-metals": "None",
            "java-exe": self.touch("bin", "java"),
            "findgeo-jar": self.touch("FindGeo.jar"),
            "timeout": 60,
        }

    def testValidDefaultCommand(self) -> None:
        d_args = self.__args()
        rfg = RunFindGeo(d_args)
        self.assertTrue(os.path.isdir(d_args["workdir"]))
        self.assertEqual(rfg.input, ["--input", d_args["input"]])
        with mock.patch.object(rfg_module, "run_command", return_value="fg ok") as mrun:
            out = rfg.run()
        self.assertEqual(out, "fg ok")
        expected = [
            d_args["java-exe"],
            "-jar",
            d_args["findgeo-jar"],
            "--input",
            d_args["input"],
            "--format",
            "cif",
            "--threshold",
            "2.8",
            "--workdir",
            d_args["workdir"],
            "--overwrite",
        ]
        mrun.assert_called_once_with(expected, 60)

    def testOptionalArgsCommand(self) -> None:
        d_args = self.__args()
        d_args.update({"input": None, "pdb": "1ABC", "metal": "Zn", "overwright": False, "excluded-donors": "C", "excluded-metals": "Mg,Ca", "format": "pdb"})
        rfg = RunFindGeo(d_args)
        self.assertEqual(rfg.input, ["--pdb", "1abc"])
        with mock.patch.object(rfg_module, "run_command", return_value="") as mrun:
            rfg.run()
        cmd = mrun.call_args[0][0]
        self.assertEqual(cmd[3:5], ["--pdb", "1abc"])
        self.assertIn("--format", cmd)
        self.assertEqual(cmd[cmd.index("--format") + 1], "pdb")
        self.assertEqual(cmd[cmd.index("--metal") + 1], "Zn")
        self.assertEqual(cmd[cmd.index("--excluded-donors") + 1], "C")
        self.assertEqual(cmd[cmd.index("--excluded-metals") + 1], "Mg,Ca")
        self.assertNotIn("--overwrite", cmd)

    def testMissingInputFallsBackToPdb(self) -> None:
        d_args = self.__args()
        d_args["input"] = os.path.join(self.tmpDir, "missing.cif")
        d_args["pdb"] = "pdb_00001abc"
        rfg = RunFindGeo(d_args)
        self.assertEqual(rfg.input, ["--pdb", "pdb_00001abc"])

    def testAllInvalid(self) -> None:
        blocker = self.touch("blocker")
        d_args = self.__args()
        d_args.update(
            {
                "java-exe": os.path.join(self.tmpDir, "nojava"),
                "findgeo-jar": os.path.join(self.tmpDir, "no.jar"),
                "format": "xyz",
                "metal": "Abc",
                "excluded-metals": "Mg,Cax",
                "threshold": 4.5,
                "workdir": os.path.join(blocker, "sub"),
                "input": None,
                "pdb": "12345",
            }
        )
        with self.assertRaises(ValidateParametersError) as ctx:
            RunFindGeo(d_args)
        self.assertEqual(set(ctx.exception.errors.keys()), {"java-exe", "findgeo-jar", "format", "metal", "excluded-metals", "threshold", "workdir", "pdb"})

    def testNoInputNoPdb(self) -> None:
        d_args = self.__args()
        d_args["input"] = None
        d_args["threshold"] = 1.0
        with self.assertRaises(ValidateParametersError) as ctx:
            RunFindGeo(d_args)
        self.assertEqual(set(ctx.exception.errors.keys()), {"input", "threshold"})

    def testRunTimeout(self) -> None:
        rfg = RunFindGeo(self.__args())
        with mock.patch.object(rfg_module, "run_command", side_effect=MetalCommandTimeoutError(["x"])):
            with self.assertRaises(FindGeoCommandTimeoutError) as ctx:
                rfg.run()
        self.assertIn("timed out after 60 seconds", str(ctx.exception))

    def testRunExecutionError(self) -> None:
        rfg = RunFindGeo(self.__args())
        with mock.patch.object(rfg_module, "run_command", side_effect=MetalCommandExecutionError(["x"], 3)):
            with self.assertRaises(FindGeoCommandExecutionError) as ctx:
                rfg.run()
        self.assertNotIsInstance(ctx.exception, FindGeoCommandTimeoutError)
        self.assertIn("FindGeo command execution error", str(ctx.exception))

    def testRunUnexpectedError(self) -> None:
        rfg = RunFindGeo(self.__args())
        with mock.patch.object(rfg_module, "run_command", side_effect=RuntimeError("kaboom")), self.assertRaises(FindGeoCommandExecutionError) as ctx:
            rfg.run()
        self.assertIn("Unexpected error when running FindGeo: kaboom", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
