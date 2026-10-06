##
# File:    PdbxStripCategoryTests.py
#
##
"""
Hermetic tests for PdbxStripCategory
"""

import logging
import os
import shutil
import tempfile
import unittest
from typing import List

from mmcif.api.DataCategory import DataCategory
from mmcif.api.PdbxContainers import DataContainer
from mmcif.io.PdbxReader import PdbxReader
from mmcif.io.PdbxWriter import PdbxWriter

from wwpdb.utils.dp.PdbxStripCategory import PdbxStripCategory

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class PdbxStripCategoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmpdir = tempfile.mkdtemp()
        self.__inp = os.path.join(self.__tmpdir, "in.cif")
        self.__out = os.path.join(self.__tmpdir, "out.cif")
        self.__writeInput(self.__inp)

    def tearDown(self) -> None:
        shutil.rmtree(self.__tmpdir, ignore_errors=True)

    @staticmethod
    def __writeInput(pathout: str) -> None:
        c0 = DataContainer("blk1")
        for cname in ["entry", "struct_conf", "pdbx_coord", "exptl"]:
            cat = DataCategory(cname)
            cat.appendAttribute("id")
            cat.append(["v_" + cname])
            c0.append(cat)
        c1 = DataContainer("blk2")
        cat = DataCategory("other")
        cat.appendAttribute("id")
        cat.append(["x"])
        c1.append(cat)
        with open(pathout, "w") as ofh:
            PdbxWriter(ofh).write([c0, c1])

    @staticmethod
    def __read(pathin: str) -> List[DataContainer]:
        cL: List[DataContainer] = []
        with open(pathin) as ifh:
            PdbxReader(ifh).read(cL)
        return cL

    def testStrip(self) -> None:
        ps = PdbxStripCategory(verbose=True)
        self.assertTrue(ps.strip(self.__inp, self.__out, ["struct_conf", "pdbx_coord", "notpresent"]))
        cL = self.__read(self.__out)
        # Only the first block is written
        self.assertEqual(len(cL), 1)
        self.assertEqual(cL[0].getName(), "blk1")
        self.assertEqual(cL[0].getObjNameList(), ["entry", "exptl"])
        self.assertEqual(cL[0].getObj("exptl").getValue("id", 0), "v_exptl")

    def testStripNoList(self) -> None:
        ps = PdbxStripCategory()
        self.assertTrue(ps.strip(self.__inp, self.__out))
        cL = self.__read(self.__out)
        self.assertEqual(len(cL), 1)
        self.assertEqual(cL[0].getObjNameList(), ["entry", "struct_conf", "pdbx_coord", "exptl"])

    def testMissingInput(self) -> None:
        ps = PdbxStripCategory()
        self.assertFalse(ps.strip(os.path.join(self.__tmpdir, "missing.cif"), self.__out, ["entry"]))
        self.assertFalse(os.path.exists(self.__out))

    def testEmptyInput(self) -> None:
        emp = os.path.join(self.__tmpdir, "empty.cif")
        with open(emp, "w"):
            pass
        ps = PdbxStripCategory()
        self.assertFalse(ps.strip(emp, self.__out))


if __name__ == "__main__":
    unittest.main()
