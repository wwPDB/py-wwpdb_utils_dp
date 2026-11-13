##
# File:    MetalCoordinationUtilityTests.py
#
# Update:
##
"""
Hermetic unit tests for wwpdb.utils.dp.MetalCoordinationUtility.

RcsbDpUtility is replaced by a mock, so neither FindGeo nor MetalCoord (nor any site tool) is run.
"""

import io
import json
import logging
import os
import shutil
import tempfile
import unittest
from typing import Any, Callable, Dict, List, Optional, Tuple
from unittest import mock

from wwpdb.utils.dp.MetalCoordinationUtility import MetalCoordinationUtility

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logger = logging.getLogger()

_PATCH_TARGET = "wwpdb.utils.dp.MetalCoordinationUtility.RcsbDpUtility"

_FINDGEO_SITE: Dict[str, Any] = {
    "chain": "A",
    "residue": "ZN",
    "sequence": 1,
    "icode": "?",
    "metal": "ZN",
    "altloc": ".",
    "metalElement": "Zn",
    "coordination": 4,
    "class": "Tetrahedral",
    "tag": "Regular",
    "class_generic": "tetrahedral",
    "class_abbr": "tet",
    "coordination_number_allowed": "YES",
    "descriptor": "desc",
    "sphere": [
        {"chain": "A", "residue": "CYS", "sequence": 10, "icode": "?", "name": "SG", "altloc": ".", "element": "S", "operator": "1_555"},
        {"chain": "A", "residue": "HIS", "sequence": 12, "name": "NE2", "element": "N"},
    ],
}

_METALCOORD_SITES: List[Dict[str, Any]] = [
    {
        "chain": "A",
        "residue": "ZN",
        "sequence": "1",
        "icode": "",
        "metal": "ZN",
        "altloc": "",
        "metalElement": "Zn",
        "coordination": "5",
        "class": "Square pyramid",
        "tag": "Distorted",
        "class_generic": "square-pyramidal",
        "class_abbr": "spy",
        "coordination_number_allowed": "YES",
        "descriptor": "?",
    },
    # no class information -> skipped
    {"chain": "A", "residue": "ZN", "sequence": "1", "icode": "", "metal": "ZN", "altloc": "", "class": "", "class_generic": "?"},
    # site not listed in the atom list -> not written
    {"chain": "C", "residue": "FE", "sequence": "2", "icode": "", "metal": "FE", "altloc": "", "class": "Octahedral", "tag": "Regular"},
]

_EXPECTED_ANNOTATION = [
    "coord_1|A|ZN|1||ZN||Zn|4|Tetrahedral|regular|tetrahedral|tet|FindGeo|Expected|desc",
    "sphere_1_1|A|CYS|10||SG||S|1_555|1",
    "sphere_1_2|A|HIS|12||NE2||N||2",
    "coord_2|A|ZN|1||ZN||Zn|5|Square pyramid|distorted|square-pyramidal|spy|MetalCoord|Unexpected|",
]


def _writeJson(path: str, obj: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f)


def _readLines(path: str) -> List[str]:
    with open(path, encoding="utf-8") as f:
        return [line for line in f.read().split("\n") if line]


class MetalCoordinationUtilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmp = tempfile.mkdtemp()
        self.__lfh = io.StringIO()
        self.__model = os.path.join(self.__tmp, "model.cif")
        with open(self.__model, "w", encoding="utf-8") as f:
            f.write("data_x\n")
        self.__fgOut = os.path.join(self.__tmp, "findgeo.json")
        self.__mcOut = os.path.join(self.__tmp, "metalcoord.json")
        self.__annot = os.path.join(self.__tmp, "annot.txt")
        self.__atomFile = os.path.join(self.__tmp, "atoms.txt")
        with open(self.__atomFile, "w", encoding="utf-8") as f:
            f.write("A ZN 1 ? ZN ?\n\n  B FE 2 ? FE ?  \nA ZN 1 ? ZN2 ?\n")

    def tearDown(self) -> None:
        shutil.rmtree(self.__tmp, ignore_errors=True)

    def __util(self, annot: Optional[str] = None) -> MetalCoordinationUtility:
        mcu = MetalCoordinationUtility(wrkPath=self.__tmp, siteId="TEST", verbose=True, log=self.__lfh)
        mcu.setModelCoordinatesFilePath(self.__model)
        mcu.setFindGeoOutputFilePath(self.__fgOut)
        mcu.setMetalCoordOutputFilePath(self.__mcOut)
        if annot is not None:
            mcu.setMetalAnnotationOutputFilePath(annot)
        return mcu

    # -- input handling --

    def testLigandInfoMissingFile(self) -> None:
        mcu = MetalCoordinationUtility(log=self.__lfh)
        mcu.setPolyAtomicMetalLigandInfoWithFilePath(os.path.join(self.__tmp, "nope.txt"))
        mcu.setPolyAtomicMetalLigandInfoWithFilePath(None)
        self.assertEqual(self.__lfh.getvalue().count("file does not exist"), 2)

    def testLigandInfoEmptyFile(self) -> None:
        empty = os.path.join(self.__tmp, "empty.txt")
        with open(empty, "w", encoding="utf-8") as f:
            f.write("\n  \n")
        mcu = MetalCoordinationUtility(log=self.__lfh)
        mcu.setPolyAtomicMetalLigandInfoWithFilePath(empty)
        self.assertIn("does not contain metal-containing residue", self.__lfh.getvalue())

    def testLigandInfoPopulatesIdList(self) -> None:
        ccIdList: List[str] = ["ZN"]
        mcu = MetalCoordinationUtility(log=self.__lfh)
        mcu.setPolyAtomicMetalLigandIdList(ccIdList)
        mcu.setPolyAtomicMetalLigandInfoWithFilePath(self.__atomFile)
        # The list given to setPolyAtomicMetalLigandIdList() is extended in place with unique residue names
        self.assertEqual(ccIdList, ["ZN", "FE"])

    def testSettersLog(self) -> None:
        self.__util(annot=self.__annot)
        out = self.__lfh.getvalue()
        self.assertIn("FindGeoOutputFilePath=%s" % self.__fgOut, out)
        self.assertIn("MetalCoordOutputFilePath=%s" % self.__mcOut, out)
        self.assertIn("MetalAnnotationOutputFilePath=%s" % self.__annot, out)

    # -- run() --

    def testRunMissingInfo(self) -> None:
        mcu = MetalCoordinationUtility(log=self.__lfh)
        with mock.patch(_PATCH_TARGET) as mDp:
            self.assertFalse(mcu.run())
        mDp.assert_not_called()
        out = self.__lfh.getvalue()
        self.assertIn("input model coordinates file path is not defined", out)
        self.assertIn("ligand Ids list is not defined", out)
        self.assertIn("'FindGeo' software is not defined", out)
        self.assertIn("'MetalCoord' software is not defined", out)

    def __fakeDp(self, results: Dict[str, Any], opRet: int = 0) -> Tuple[List[mock.MagicMock], Callable[..., mock.MagicMock]]:
        """Return (list collecting the mock RcsbDpUtility instances, factory); results maps op name to json content"""
        created: List[mock.MagicMock] = []

        def factory(**kwargs: Any) -> mock.MagicMock:
            inst = mock.MagicMock()
            inst.ctor_kwargs = kwargs
            state: Dict[str, str] = {}

            def op(name: str) -> int:
                state["op"] = name
                return opRet

            def exp(path: str) -> None:
                content = results.get(state["op"])
                if content is not None:
                    _writeJson(path, content)

            inst.op.side_effect = op
            inst.exp.side_effect = exp
            created.append(inst)
            return inst

        return created, factory

    def testRunSingleLigand(self) -> None:
        # stale outputs are removed before running
        _writeJson(self.__fgOut, ["stale"])
        _writeJson(self.__mcOut, ["stale"])
        created, factory = self.__fakeDp({"metal-findgeo": [_FINDGEO_SITE], "metal-metalcoord-stats": []})
        mcu = self.__util()
        mcu.setPolyAtomicMetalLigandIdList(["ZN"])
        with mock.patch(_PATCH_TARGET, side_effect=factory):
            self.assertTrue(mcu.run())
        self.assertEqual(len(created), 2)
        fg = created[0]
        mc = created[1]
        self.assertEqual(fg.ctor_kwargs, {"tmpPath": self.__tmp, "siteId": "TEST", "verbose": True, "log": self.__lfh})
        fg.imp.assert_called_once_with(self.__model)
        fg.addInput.assert_not_called()
        fg.op.assert_called_once_with("metal-findgeo")
        fg.exp.assert_called_once_with(self.__fgOut)
        fg.cleanup.assert_called_once_with()
        mc.addInput.assert_called_once_with(name="ligands", value="ZN")
        mc.op.assert_called_once_with("metal-metalcoord-stats")
        # empty json -> session directory kept
        mc.cleanup.assert_not_called()
        with open(self.__fgOut, encoding="utf-8") as f:
            self.assertEqual(json.load(f), [_FINDGEO_SITE])

    def testRunMultiLigandNoTimeoutFilter(self) -> None:
        created, factory = self.__fakeDp({}, opRet=0)
        mcu = self.__util()
        mcu.setPolyAtomicMetalLigandIdList(["ZN", "FE"])
        with mock.patch(_PATCH_TARGET, side_effect=factory):
            self.assertTrue(mcu.run(noTimeOutFlag=True, regularFilter="-regular"))
        fg = created[0]
        mc = created[1]
        fg.addInput.assert_called_once_with(name="timeout", value=36000)
        fg.op.assert_called_once_with("metal-findgeo-regular")
        mc.addInput.assert_has_calls([mock.call(name="ligands", value=["ZN", "FE"]), mock.call(name="timeout", value=36000)])
        mc.op.assert_called_once_with("metal-metalcoord-stats-regular")
        # no output produced
        self.assertFalse(os.path.exists(self.__fgOut))
        mc.cleanup.assert_not_called()

    def testRunOpFailure(self) -> None:
        created, factory = self.__fakeDp({"metal-findgeo": [_FINDGEO_SITE]}, opRet=1)
        mcu = self.__util()
        mcu.setPolyAtomicMetalLigandIdList(["ZN"])
        with mock.patch(_PATCH_TARGET, side_effect=factory):
            self.assertTrue(mcu.run())
        for inst in created:
            inst.exp.assert_not_called()
            inst.cleanup.assert_not_called()

    # -- readJsonOutputFiles() --

    def __prepared(self, annot: Optional[str]) -> MetalCoordinationUtility:
        mcu = self.__util(annot=annot)
        mcu.setPolyAtomicMetalLigandInfoWithFilePath(self.__atomFile)
        return mcu

    def testReadJsonOutputFiles(self) -> None:
        _writeJson(self.__fgOut, [_FINDGEO_SITE])
        _writeJson(self.__mcOut, _METALCOORD_SITES)
        with open(self.__annot, "w", encoding="utf-8") as f:
            f.write("stale\n")
        mcu = self.__prepared(self.__annot)
        mcu.readJsonOutputFiles()
        self.assertEqual(_readLines(self.__annot), _EXPECTED_ANNOTATION)

    def testReadJsonDefaultAnnotationPath(self) -> None:
        _writeJson(self.__fgOut, [_FINDGEO_SITE])
        mcu = self.__prepared(None)
        mcu.readJsonOutputFiles()
        default = os.path.join(self.__tmp, "D_xxxxxxxxxx.annotation.txt")
        self.assertEqual(_readLines(default), _EXPECTED_ANNOTATION[:3])

    def testReadJsonNoResults(self) -> None:
        _writeJson(self.__fgOut, [])
        _writeJson(self.__mcOut, {"error": "execution-error", "details": "x"})
        mcu = self.__prepared(self.__annot)
        mcu.readJsonOutputFiles()
        self.assertFalse(os.path.exists(self.__annot))
        out = self.__lfh.getvalue()
        self.assertIn("Run FindGeo failed: empty json output file", out)
        self.assertIn("Run MetalCoord failed: execution-error", out)
        self.assertIn("Missing metal coordination annotation", out)

    def testReadJsonInvalidJson(self) -> None:
        with open(self.__fgOut, "w", encoding="utf-8") as f:
            f.write("{bad")
        mcu = self.__prepared(self.__annot)
        mcu.readJsonOutputFiles()
        self.assertFalse(os.path.exists(self.__annot))
        self.assertIn("readJsonOutputFiles() - Expecting property name", self.__lfh.getvalue())

    # -- runUpdate() --

    def testRunUpdateMissingPaths(self) -> None:
        mcu = self.__util()
        with mock.patch(_PATCH_TARGET) as mDp:
            mcu.runUpdate()
            mcu.runUpdate(pdbxPath="a.cif")
        mDp.assert_not_called()

    def testRunUpdateRunFails(self) -> None:
        mcu = MetalCoordinationUtility(log=self.__lfh)
        with mock.patch(_PATCH_TARGET) as mDp:
            mcu.runUpdate(pdbxPath="a.cif", csvPath="b.csv")
        mDp.assert_not_called()

    def testRunUpdateNoAnnotation(self) -> None:
        created, factory = self.__fakeDp({"metal-findgeo": [], "metal-metalcoord-stats": []})
        mcu = self.__prepared(self.__annot)
        with mock.patch(_PATCH_TARGET, side_effect=factory):
            mcu.runUpdate(pdbxPath="a.cif", csvPath="b.csv")
        # only the two program runs; no merge step
        self.assertEqual(len(created), 2)

    def testRunUpdateMerge(self) -> None:
        created, factory = self.__fakeDp({"metal-findgeo": [_FINDGEO_SITE], "metal-metalcoord-stats": {"error": "timeout", "details": "t"}})
        mcu = self.__prepared(self.__annot)
        pdbx = os.path.join(self.__tmp, "out.cif")
        csv = os.path.join(self.__tmp, "out.csv")
        with mock.patch(_PATCH_TARGET, side_effect=factory):
            mcu.runUpdate(pdbxPath=pdbx, csvPath=csv, noTimeOut=True)
        self.assertEqual(len(created), 3)
        merge = created[2]
        merge.imp.assert_called_once_with(self.__model)
        expectedCalls = [mock.call(name="metal_coordination_file_path", value=self.__annot, type="file"), mock.call(name="add_timeout_skip", value="add")]
        merge.addInput.assert_has_calls(expectedCalls)
        merge.op.assert_called_once_with("annot-merge-metal-coordination")
        merge.expList.assert_called_once_with(dstPathList=[pdbx, csv])
        merge.cleanup.assert_called_once_with()
        self.assertEqual(_readLines(self.__annot), _EXPECTED_ANNOTATION[:3])

    def testRunUpdateMergeNoTimeout(self) -> None:
        created, factory = self.__fakeDp({"metal-findgeo": [_FINDGEO_SITE], "metal-metalcoord-stats": _METALCOORD_SITES})
        mcu = self.__prepared(self.__annot)
        with mock.patch(_PATCH_TARGET, side_effect=factory):
            mcu.runUpdate(pdbxPath="a.cif", csvPath="b.csv")
        merge = created[2]
        merge.addInput.assert_called_once_with(name="metal_coordination_file_path", value=self.__annot, type="file")


if __name__ == "__main__":
    unittest.main()
