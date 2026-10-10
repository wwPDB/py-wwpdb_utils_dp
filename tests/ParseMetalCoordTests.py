##
# File:    ParseMetalCoordTests.py
# Date:    2026-10-06
#
##
"""
Hermetic unit tests for wwpdb.utils.dp.metal.metalcoord.parseMetalCoord.

Synthetic MetalCoord JSON output is written to a temporary directory and parsed against the
bundled metal_ref reference data.
"""

import json
import logging
import os
import shutil
import tempfile
import unittest
from typing import Any, Dict, List, Optional
from unittest import mock

from wwpdb.utils.dp.metal.metalcoord.parseMetalCoord import MetalCoordParseError, ParseMetalCoord

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

EXPECTED_KEY_ORDER = [
    "metal",
    "metalElement",
    "chain",
    "residue",
    "sequence",
    "icode",
    "altloc",
    "coordination",
    "class",
    "class_abbr",
    "class_generic",
    "tag",
    "procrustes",
    "count",
    "descriptor",
    "coordination_number_allowed",
    "redox_active",
    "oxidation_state",
    "carbon_metal",
    "class_in_exception",
    "sphere",
]


def _ligand(cls: str, abbr: str, procrustes: Any, coordination: int, order: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    return {
        "class": cls,
        "class_abr": abbr,
        "descriptor": "desc-" + cls,
        "procrustes": procrustes,
        "coordination": coordination,
        "count": 42,
        "order": order if order is not None else [{"name": "N1", "residue": "HIS"}],
        "base": [],
    }


def _site(metal: str, element: str, ligands: List[Dict[str, Any]], sequence: int = 301) -> Dict[str, Any]:
    return {
        "metal": metal,
        "metalElement": element,
        "chain": "A",
        "residue": "LIG",
        "sequence": sequence,
        "icode": ".",
        "altloc": "",
        "ligands": ligands,
    }


class ParseMetalCoordTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmpDir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.__tmpDir, ignore_errors=True)

    def __writeJson(self, data: Any, name: str = "mc.json") -> str:
        fp = os.path.join(self.__tmpDir, name)
        with open(fp, "w", encoding="utf-8") as ofh:
            json.dump(data, ofh)
        return fp

    def __parse(self, data: Any) -> ParseMetalCoord:
        pmc = ParseMetalCoord()
        pmc.read(self.__writeJson(data))
        pmc.parse()
        return pmc

    def testInit(self) -> None:
        pmc = ParseMetalCoord()
        self.assertIsNone(pmc.data)
        self.assertEqual(pmc.l_sites, [])
        self.assertIn("tetrahedral", pmc.d_coord_map)
        self.assertIn("Zn", pmc.d_coord_num)

    def testRegularSiteFullRecord(self) -> None:
        order = [{"name": "SG", "residue": "CYS"}]
        ligands = [_ligand("octahedral", "OCT", 0.5, 6), _ligand("tetrahedral", "TET", 0.05, 4, order), _ligand("square-planar", "SP", 11.0, 4)]
        data = [_site("ZN1", "Zn", ligands)]
        pmc = self.__parse(data)
        self.assertEqual(len(pmc.l_sites), 1)
        site = pmc.l_sites[0]
        self.assertEqual(list(site.keys()), EXPECTED_KEY_ORDER)
        self.assertEqual(site["metal"], "ZN1")
        self.assertEqual(site["class"], "tetrahedral")
        self.assertEqual(site["class_abbr"], "TET")
        self.assertEqual(site["class_generic"], "tetrahedral")
        self.assertEqual(site["descriptor"], "desc-tetrahedral")
        self.assertEqual(site["procrustes"], 0.05)
        self.assertEqual(site["coordination"], 4)
        self.assertEqual(site["count"], 42)
        self.assertEqual(site["sphere"], order)
        self.assertEqual(site["coordination_number_allowed"], "YES")
        self.assertEqual(site["tag"], "Regular")
        self.assertEqual(site["redox_active"], "N")
        self.assertEqual(site["oxidation_state"], "2")
        self.assertEqual(site["carbon_metal"], "NO")
        self.assertEqual(site["class_in_exception"], "NO")

    def testDistortedCarbonMetal(self) -> None:
        pmc = self.__parse([_site("FE1", "Fe", [_ligand("octahedral", "OCT", 0.5, 6)])])
        site = pmc.l_sites[0]
        self.assertEqual(site["tag"], "Distorted")
        self.assertEqual(site["class_generic"], "octahedral")
        self.assertEqual(site["redox_active"], "Y")
        self.assertEqual(site["oxidation_state"], "2,3")
        self.assertEqual(site["carbon_metal"], "YES")

    def testCoordinationNumberException(self) -> None:
        # Zn allows 4,5,6 -- coordination 3 is an exception for both regular and distorted scores
        pmc = self.__parse([_site("ZN1", "Zn", [_ligand("pyramid", "PYR", 0.1, 3)]), _site("ZN2", "Zn", [_ligand("pyramid", "PYR", 0.9, 3)], sequence=302)])
        for site in pmc.l_sites:
            self.assertEqual(site["coordination_number_allowed"], "NO")
            self.assertEqual(site["tag"], "Coordination number exception")

    def testClassException(self) -> None:
        # Mg excludes square-planar for MetalCoord
        data = [_site("MG1", "Mg", [_ligand("square-planar", "SP", 0.1, 4)]), _site("MG2", "Mg", [_ligand("square-planar", "SP", 0.5, 4)], sequence=2)]
        pmc = self.__parse(data)
        for site in pmc.l_sites:
            self.assertEqual(site["class_in_exception"], "YES")
            self.assertEqual(site["tag"], "Coordination class exception")

    def testMetalWithExceptionEntryButNotExcluded(self) -> None:
        pmc = self.__parse([_site("MG1", "Mg", [_ligand("octahedral", "OCT", 0.1, 6)])])
        self.assertEqual(pmc.l_sites[0]["class_in_exception"], "NO")
        self.assertEqual(pmc.l_sites[0]["tag"], "Regular")

    def testUnknownMetalAndClass(self) -> None:
        pmc = self.__parse([_site("XX1", "Xx", [_ligand("weird-shape", "WRD", 0.3, 7)])])
        site = pmc.l_sites[0]
        self.assertEqual(site["class_generic"], "")
        self.assertEqual(site["coordination_number_allowed"], "")
        self.assertEqual(site["redox_active"], "")
        self.assertEqual(site["oxidation_state"], "")
        self.assertEqual(site["carbon_metal"], "NO")
        self.assertEqual(site["class_in_exception"], "NO")
        self.assertEqual(site["tag"], "Distorted")

    def testNegativeProcrustes(self) -> None:
        pmc = self.__parse([_site("ZN1", "Zn", [_ligand("tetrahedral", "TET", -0.5, 4)])])
        self.assertEqual(pmc.l_sites[0]["tag"], "")

    def testNonNumericProcrustesInAmend(self) -> None:
        pmc = ParseMetalCoord()
        pmc.l_sites.append({"class": "tetrahedral", "metalElement": "Zn", "coordination": 4, "procrustes": "n/a"})
        pmc.amend()
        self.assertEqual(pmc.l_sites[0]["tag"], "")
        self.assertEqual(pmc.l_sites[0]["coordination_number_allowed"], "YES")

    def testMultipleSitesSortedKeys(self) -> None:
        data = [_site("ZN1", "Zn", [_ligand("tetrahedral", "TET", 0.1, 4)]), _site("CU1", "Cu", [_ligand("square-planar", "SP", 0.3, 4)], sequence=5)]
        pmc = self.__parse(data)
        self.assertEqual([s["metal"] for s in pmc.l_sites], ["ZN1", "CU1"])
        for site in pmc.l_sites:
            self.assertEqual(list(site.keys()), EXPECTED_KEY_ORDER)

    def testEmptyData(self) -> None:
        pmc = self.__parse([])
        self.assertEqual(pmc.data, [])
        self.assertEqual(pmc.l_sites, [])

    def testNoLigandBelowThresholdRaises(self) -> None:
        pmc = ParseMetalCoord()
        pmc.read(self.__writeJson([_site("ZN1", "Zn", [_ligand("tetrahedral", "TET", 12.0, 4)])]))
        with self.assertRaises(MetalCoordParseError):
            pmc.parse()

    def testMissingKeyRaises(self) -> None:
        pmc = ParseMetalCoord()
        pmc.read(self.__writeJson([{"metal": "ZN1"}]))
        with self.assertRaises(MetalCoordParseError) as ctx:
            pmc.parse()
        self.assertIn("unexpected error occurred during parsing", str(ctx.exception))

    def testReadFileNotFound(self) -> None:
        pmc = ParseMetalCoord()
        with self.assertRaises(MetalCoordParseError) as ctx:
            pmc.read(os.path.join(self.__tmpDir, "missing.json"))
        self.assertIn("File not found", str(ctx.exception))

    def testReadBadJson(self) -> None:
        fp = os.path.join(self.__tmpDir, "bad.json")
        with open(fp, "w", encoding="utf-8") as ofh:
            ofh.write("{not json")
        pmc = ParseMetalCoord()
        with self.assertRaises(MetalCoordParseError) as ctx:
            pmc.read(fp)
        self.assertIn("Failed to decode JSON", str(ctx.exception))

    def testReadPermissionDenied(self) -> None:
        fp = self.__writeJson([])
        pmc = ParseMetalCoord()
        with mock.patch("wwpdb.utils.dp.metal.metalcoord.parseMetalCoord.open", side_effect=PermissionError("denied"), create=True):
            with self.assertRaises(MetalCoordParseError) as ctx:
                pmc.read(fp)
        self.assertIn("Permission denied", str(ctx.exception))

    def testReadUnexpectedError(self) -> None:
        pmc = ParseMetalCoord()
        # An OSError that is neither FileNotFoundError nor PermissionError hits the generic handler
        with mock.patch("wwpdb.utils.dp.metal.metalcoord.parseMetalCoord.open", side_effect=OSError("odd"), create=True):
            with self.assertRaises(MetalCoordParseError) as ctx:
                pmc.read(self.__tmpDir)
        self.assertIn("unexpected error occurred while reading", str(ctx.exception))

    def testReport(self) -> None:
        pmc = self.__parse([_site("ZN1", "Zn", [_ligand("tetrahedral", "TET", 0.1, 4)])])
        fpOut = os.path.join(self.__tmpDir, "report.json")
        pmc.report(fpOut)
        with open(fpOut, encoding="utf-8") as ifh:
            content = ifh.read()
        loaded = json.loads(content)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["tag"], "Regular")
        self.assertEqual(list(loaded[0].keys()), EXPECTED_KEY_ORDER)


if __name__ == "__main__":
    unittest.main()
