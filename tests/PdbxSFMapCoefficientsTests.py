##
# File:    PdbxSFMapCoefficientsTests.py
#
##
"""
Hermetic tests for PdbxSFMapCoefficients - RcsbDpUtility is mocked for MTZ conversion
"""

import logging
import os
import shutil
import tempfile
import unittest
from typing import Any, List, Optional
from unittest import mock

from mmcif.api.DataCategory import DataCategory
from mmcif.api.PdbxContainers import DataContainer
from mmcif.io.IoAdapterCore import IoAdapterCore

if __package__ is None or __package__ == "":
    import sys
    from os import path

    sys.path.append(path.dirname(path.abspath(__file__)))
    from commonsetup import TESTOUTPUT  # pylint: disable=import-error,unused-import  # noqa: F401
else:
    from .commonsetup import TESTOUTPUT  # noqa: F401  # pylint: disable=unused-import

from wwpdb.utils.config.ConfigInfo import getSiteId

from wwpdb.utils.dp.PdbxSFMapCoefficients import PdbxSFMapCoefficients

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

ALLREFLN = ["index_h", "index_k", "index_l", "fom", "pdbx_DELFWT", "pdbx_DELPHWT", "pdbx_FWT", "pdbx_PHWT", "F_meas_au"]


class PdbxSFMapCoefficientsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmpdir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.__tmpdir, ignore_errors=True)

    def __writeSf(self, fname: str, reflnattr: Optional[List[str]] = None, withrefln: bool = True) -> str:
        if reflnattr is None:
            reflnattr = ALLREFLN
        c0 = DataContainer("r1abcsf")

        cat = DataCategory("entry", ["id"], [["1ABC"]])
        c0.append(cat)
        cat = DataCategory("cell", ["entry_id", "length_a"], [["1ABC", "10.0"]])
        c0.append(cat)
        cat = DataCategory("symmetry", ["entry_id", "space_group_name_H-M"], [["1ABC", "P 1"]])
        c0.append(cat)
        cat = DataCategory("audit", ["revision_id"], [["1"]])
        c0.append(cat)
        cat = DataCategory("exptl_crystal", ["id"], [["1"]])
        c0.append(cat)
        if withrefln:
            rows = [[str(i + j) for j in range(len(reflnattr))] for i in range(3)]
            cat = DataCategory("refln", list(reflnattr), rows)
            c0.append(cat)

        fpath = os.path.join(self.__tmpdir, fname)
        IoAdapterCore().writeFile(fpath, [c0])
        return fpath

    @staticmethod
    def __read(fpath: str) -> List[Any]:
        ret: List[Any] = IoAdapterCore().readFile(fpath)
        return ret

    def testHasMapCoeffAndWrite(self) -> None:
        sfin = self.__writeSf("sf.cif")
        sfc = PdbxSFMapCoefficients(tmppath=self.__tmpdir)
        self.assertFalse(sfc.has_map_coeff())
        self.assertTrue(sfc.read_mmcif_sf(sfin))
        self.assertTrue(sfc.has_map_coeff())

        fo = os.path.join(self.__tmpdir, "fo.cif")
        twofo = os.path.join(self.__tmpdir, "2fo.cif")
        self.assertTrue(sfc.write_mmcif_coef(fo, twofo, entry_id="9XYZ"))

        for fpath, coef, keep, drop in [
            (fo, "fo", ["pdbx_DELFWT", "pdbx_DELPHWT"], ["pdbx_FWT", "pdbx_PHWT"]),
            (twofo, "2fo", ["pdbx_FWT", "pdbx_PHWT"], ["pdbx_DELFWT", "pdbx_DELPHWT"]),
        ]:
            cL = self.__read(fpath)
            self.assertEqual(len(cL), 1)
            b0 = cL[0]
            self.assertEqual(b0.getName(), "9XYZ" + coef)
            self.assertEqual(b0.getObjNameList(), ["entry", "cell", "symmetry", "refln"])
            self.assertEqual(b0.getObj("entry").getValue("id", 0), "9XYZ")
            self.assertEqual(b0.getObj("cell").getValue("entry_id", 0), "9XYZ")
            self.assertEqual(b0.getObj("symmetry").getValue("entry_id", 0), "9XYZ")
            refln = b0.getObj("refln")
            self.assertEqual(refln.getAttributeList(), ["index_h", "index_k", "index_l", "fom"] + keep)  # noqa: RUF005
            for att in drop + ["F_meas_au"]:  # noqa: RUF005
                self.assertNotIn(att, refln.getAttributeList())
            self.assertEqual(refln.getRowCount(), 3)

        # Original data is not modified by writing
        self.assertTrue(sfc.has_map_coeff())

    def testDefaultEntryId(self) -> None:
        sfc = PdbxSFMapCoefficients(tmppath=self.__tmpdir)
        self.assertTrue(sfc.read_mmcif_sf(self.__writeSf("sf.cif")))
        fo = os.path.join(self.__tmpdir, "fo.cif")
        twofo = os.path.join(self.__tmpdir, "2fo.cif")
        self.assertTrue(sfc.write_mmcif_coef(fo, twofo))
        self.assertEqual(self.__read(fo)[0].getName(), "xxxxfo")
        self.assertEqual(self.__read(twofo)[0].getName(), "xxxx2fo")

    def testMissingAttribute(self) -> None:
        sfc = PdbxSFMapCoefficients()
        self.assertTrue(sfc.read_mmcif_sf(self.__writeSf("sf.cif", reflnattr=["index_h", "index_k", "index_l", "fom", "pdbx_FWT"])))
        self.assertFalse(sfc.has_map_coeff())

    def testNoRefln(self) -> None:
        sfc = PdbxSFMapCoefficients()
        self.assertTrue(sfc.read_mmcif_sf(self.__writeSf("sf.cif", withrefln=False)))
        self.assertFalse(sfc.has_map_coeff())

    def testEmptyFile(self) -> None:
        emp = os.path.join(self.__tmpdir, "empty.cif")
        with open(emp, "w"):
            pass
        sfc = PdbxSFMapCoefficients()
        self.assertTrue(sfc.read_mmcif_sf(emp))
        self.assertFalse(sfc.has_map_coeff())

    def testReadFailure(self) -> None:
        sfc = PdbxSFMapCoefficients()
        with mock.patch("wwpdb.utils.dp.PdbxSFMapCoefficients.IoAdapterCore") as mio:
            mio.return_value.readFile.side_effect = OSError("bad")
            self.assertFalse(sfc.read_mmcif_sf("/nonexistent.cif"))
        self.assertFalse(sfc.has_map_coeff())

    def __runMtz(self, produce: bool, cleanup: bool, tmppath: Optional[str]) -> bool:
        sfsrc = self.__writeSf("src.cif")

        def fakeExpList(dstPathList: List[str]) -> bool:
            if produce:
                shutil.copyfile(sfsrc, dstPathList[0])
            return True

        sfc = PdbxSFMapCoefficients(siteid="TESTSITE", tmppath=tmppath, cleanup=cleanup)
        with mock.patch("wwpdb.utils.dp.PdbxSFMapCoefficients.RcsbDpUtility") as mdp:
            inst = mdp.return_value
            inst.expList.side_effect = fakeExpList
            ret: bool = sfc.read_mtz_sf("/path/in.mtz")

        mdp.assert_called_once_with(siteId=getSiteId("TESTSITE"), tmpPath=tmppath)
        inst.imp.assert_called_once_with("/path/in.mtz")
        inst.op.assert_called_once_with("annot-sf-convert")
        self.assertEqual(inst.expLog.call_count, 1)
        if cleanup:
            inst.cleanup.assert_called_once_with()
        else:
            inst.cleanup.assert_not_called()
        if ret:
            self.assertTrue(sfc.has_map_coeff())
        return ret

    def testMtzSuccessCleanup(self) -> None:
        workroot = os.path.join(self.__tmpdir, "work")
        os.makedirs(workroot)
        self.assertTrue(self.__runMtz(produce=True, cleanup=True, tmppath=workroot))
        # Work directory removed
        self.assertEqual(os.listdir(workroot), [])

    def testMtzSuccessNoCleanup(self) -> None:
        workroot = os.path.join(self.__tmpdir, "work")
        os.makedirs(workroot)
        self.assertTrue(self.__runMtz(produce=True, cleanup=False, tmppath=workroot))
        dirs = os.listdir(workroot)
        self.assertEqual(len(dirs), 1)
        self.assertTrue(dirs[0].startswith("rcsb-"))
        self.assertTrue(os.path.exists(os.path.join(workroot, dirs[0], "sf-convert-datafile.cif")))

    def testMtzFailureNoTmpPath(self) -> None:
        self.assertFalse(self.__runMtz(produce=False, cleanup=True, tmppath=None))


if __name__ == "__main__":
    unittest.main()
