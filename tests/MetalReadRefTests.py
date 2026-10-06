##
# File:    MetalReadRefTests.py
# Date:    2026-10-06
#
##
"""
Hermetic unit tests for wwpdb.utils.dp.metal.metal_util.readRef.

Exercises each reference reader against the bundled metal_ref CSV files and against small
synthetic CSV files (via a patched REF_PATH) to cover the NA-skip and duplicate-geometry paths.
"""

import io
import logging
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from typing import List
from unittest import mock

from wwpdb.utils.dp.metal.metal_util import readRef
from wwpdb.utils.dp.metal.metal_util.readRef import readRefCoordException, readRefCoordMap, readRefCoordNum, readRefMetalCarbon, readRefRedOx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class MetalReadRefBundledTests(unittest.TestCase):
    """Read the reference files shipped with the package"""

    def testRefPathExists(self) -> None:
        self.assertTrue(os.path.isdir(readRef.REF_PATH))
        self.assertEqual(os.path.basename(readRef.REF_PATH), "metal_ref")

    def testReadRefRedOx(self) -> None:
        d_redox, d_oxi = readRefRedOx()
        self.assertEqual(d_redox["Fe"], "Y")
        self.assertEqual(d_oxi["Fe"], "2,3")
        self.assertEqual(d_redox["Zn"], "N")
        self.assertEqual(d_oxi["Zn"], "2")
        self.assertEqual(set(d_redox.keys()), set(d_oxi.keys()))

    def testReadRefCoordNum(self) -> None:
        d_coord_num = readRefCoordNum()
        self.assertEqual(d_coord_num["Zn"], ["4", "5", "6"])
        self.assertEqual(d_coord_num["Be"], ["4"])
        for value in d_coord_num.values():
            self.assertIsInstance(value, list)

    def testReadRefCoordMapFindGeo(self) -> None:
        d_map = readRefCoordMap("FindGeo")
        self.assertEqual(d_map["tetrahedron"], {"abbr": "TET", "pdb_geom": "tetrahedral"})
        self.assertEqual(d_map["trigonal plane with a vacancy"], {"abbr": "TRV", "pdb_geom": "bent"})
        self.assertNotIn("na", d_map)

    def testReadRefCoordMapMetalCoord(self) -> None:
        d_map = readRefCoordMap("metalCoord")
        self.assertEqual(d_map["tetrahedral"], {"abbr": "TET", "pdb_geom": "tetrahedral"})
        self.assertEqual(d_map["capped-linear"], {"abbr": "CLN", "pdb_geom": "linear monocapped"})
        self.assertNotIn("na", d_map)

    def testReadRefCoordMapUnknownProgram(self) -> None:
        with self.assertRaises(KeyError):
            readRefCoordMap("NoSuchProgram")

    def testReadRefMetalCarbon(self) -> None:
        l_metal = readRefMetalCarbon()
        self.assertIn("Fe", l_metal)
        self.assertIn("Ru", l_metal)
        self.assertNotIn("Zn", l_metal)

    def testReadRefCoordException(self) -> None:
        d_exc = readRefCoordException()
        expected = {"Percent-threshold": "10", "Geometry-exclusion-FindGeo": "square plane", "Geometry-exclusion-MetalCoord": "square-planar"}
        self.assertEqual(d_exc["Mg"], expected)
        self.assertEqual(d_exc["Fe"]["Percent-threshold"], "15")
        self.assertEqual(d_exc["Zn"]["Geometry-exclusion-FindGeo"], "")


class MetalReadRefSyntheticTests(unittest.TestCase):
    """Read synthetic reference files from a temporary REF_PATH"""

    def setUp(self) -> None:
        self.__tmpDir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.__tmpDir, ignore_errors=True)

    def __write(self, name: str, lines: List[str]) -> None:
        with open(os.path.join(self.__tmpDir, name), "w", encoding="utf-8") as ofh:
            ofh.write("\n".join(lines) + "\n")

    def testCoordMapSkipsNaAndDuplicates(self) -> None:
        self.__write(
            "coord_classes_mapping_abbr.csv",
            [
                "CN,Abbreviation Prog,Name Prog,Name PDB",
                "2, lin , Linear ,LINEAR",
                "3,NA,NA,trigonal planar",
                "4,dup,linear,other",
                "4,tet,Tetrahedral,Tetrahedral",
            ],
        )
        buf = io.StringIO()
        with mock.patch.object(readRef, "REF_PATH", self.__tmpDir), redirect_stdout(buf):
            d_map = readRefCoordMap("Prog")
        self.assertEqual(d_map, {"linear": {"abbr": "LIN", "pdb_geom": "linear"}, "tetrahedral": {"abbr": "TET", "pdb_geom": "tetrahedral"}})
        self.assertIn("duplicate geometry", buf.getvalue())

    def testRedOxAndCoordNumStripping(self) -> None:
        self.__write("metal_oxidation_state.csv", ["Metals\tRedox active\tOxidation state", " Qq \t Y \t1,2"])
        self.__write("metal_coordination_number.csv", ["Metals\tCoordination numbers", " Qq \t 2,4 "])
        with mock.patch.object(readRef, "REF_PATH", self.__tmpDir):
            d_redox, d_oxi = readRefRedOx()
            d_cn = readRefCoordNum()
        self.assertEqual(d_redox, {"Qq": "Y"})
        self.assertEqual(d_oxi, {"Qq": "1,2"})
        self.assertEqual(d_cn, {"Qq": ["2", "4"]})

    def testMetalCarbonAndException(self) -> None:
        self.__write("carbon_metal_bond.csv", ["Metals\tccd_ids", " Qq \tAAA,BBB", "Xx\tCCC"])
        self.__write(
            "threshold_exception_ccd_annotation.csv",
            ["Element\tPercent-threshold\tGeometry-exclusion-FindGeo\tGeometry-exclusion-MetalCoord", "Qq\t 20 \t a b \t c-d "],
        )
        with mock.patch.object(readRef, "REF_PATH", self.__tmpDir):
            l_metal = readRefMetalCarbon()
            d_exc = readRefCoordException()
        self.assertEqual(l_metal, ["Qq", "Xx"])
        self.assertEqual(d_exc, {"Qq": {"Percent-threshold": "20", "Geometry-exclusion-FindGeo": "a b", "Geometry-exclusion-MetalCoord": "c-d"}})

    def testMissingFilesRaise(self) -> None:
        with mock.patch.object(readRef, "REF_PATH", self.__tmpDir):
            with self.assertRaises(FileNotFoundError):
                readRefRedOx()
            with self.assertRaises(FileNotFoundError):
                readRefCoordNum()
            with self.assertRaises(FileNotFoundError):
                readRefCoordMap("FindGeo")
            with self.assertRaises(FileNotFoundError):
                readRefMetalCarbon()
            with self.assertRaises(FileNotFoundError):
                readRefCoordException()

    def testMissingColumnRaises(self) -> None:
        self.__write("metal_coordination_number.csv", ["Metals\tWrong", "Zn\t4"])
        with mock.patch.object(readRef, "REF_PATH", self.__tmpDir), self.assertRaises(KeyError):
            readRefCoordNum()


if __name__ == "__main__":
    unittest.main()
