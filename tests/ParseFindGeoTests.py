##
# File:    ParseFindGeoTests.py
# Date:    2026-10-06
#
##
"""
Hermetic unit tests for wwpdb.utils.dp.metal.findgeo.parseFindGeo.

A synthetic FindGeo output folder (one sub-folder per metal site containing findgeo.out and
findgeo.input) is generated in a temporary directory. Tests chdir into that directory because
the mmCIF parser may drop log files into the current working directory.
"""

import json
import logging
import os
import shutil
import tempfile
import unittest
from typing import List, Optional

from wwpdb.utils.dp.metal.findgeo.parseFindGeo import ParseFindGeo

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
    "rmsd",
    "coordination_number_allowed",
    "redox_active",
    "oxidation_state",
    "carbon_metal",
    "class_in_exception",
]

ATOM_SITE_ITEMS = [
    "group_PDB",
    "id",
    "type_symbol",
    "label_atom_id",
    "label_alt_id",
    "label_comp_id",
    "label_asym_id",
    "label_entity_id",
    "label_seq_id",
    "pdbx_PDB_ins_code",
    "Cartn_x",
    "Cartn_y",
    "Cartn_z",
    "occupancy",
    "B_iso_or_equiv",
    "auth_seq_id",
    "auth_comp_id",
    "auth_asym_id",
    "auth_atom_id",
    "pdbx_PDB_model_num",
]


def _findGeoOut(coordination: Optional[str], hits: List[str], best: Optional[str]) -> str:
    lines = ["FindGeo output", ""]
    if coordination is not None:
        lines.append("Coordination number: %s" % coordination)
    lines.append("Geometry - Tag | RMSD")
    lines.extend(hits)
    if best is not None:
        lines.append("Best geometry: %s" % best)
    return "\n".join(lines) + "\n"


def _cifInput(atomLabel: str, comp: str, chain: str, seq: str, authAsymItem: str = "auth_asym_id") -> str:
    items = [authAsymItem if it == "auth_asym_id" else it for it in ATOM_SITE_ITEMS]
    lines = ["data_findgeo", "#", "loop_"] + ["_atom_site.%s" % it for it in items]
    row = ["HETATM", "1", atomLabel, atomLabel, "B", comp, "C", "2", ".", "X", "1.000", "2.000", "3.000", "1.00", "20.00", seq, comp, chain, atomLabel, "1"]
    lines.append(" ".join(row))
    lines.append(" ".join(["ATOM", "2", "N", "N", ".", "HIS", "A", "1", "10", "?", "1.5", "2.5", "3.5", "1.00", "20.00", "10", "HIS", chain, "N", "1"]))  # noqa: FLY002
    lines.append("#")
    return "\n".join(lines) + "\n"


def _pdbInput(atomLabel: str, alt: str, comp: str, chain: str, seq: int, ins: str) -> str:
    fmt = "HETATM%5d %-4s%1s%3s %1s%4d%1s   %8.3f%8.3f%8.3f%6.2f%6.2f          %2s"
    line = fmt % (1, atomLabel, alt, comp, chain, seq, ins, 1.0, 2.0, 3.0, 1.0, 20.0, "ZN")
    return line + "\n"


class ParseFindGeoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__cwd = os.getcwd()
        self.__tmpDir = tempfile.mkdtemp()
        os.chdir(self.__tmpDir)
        self.__folder = os.path.join(self.__tmpDir, "findgeo")
        os.makedirs(self.__folder)

    def tearDown(self) -> None:
        os.chdir(self.__cwd)
        shutil.rmtree(self.__tmpDir, ignore_errors=True)

    def __addSite(self, name: str, outText: Optional[str], inputText: Optional[str]) -> str:
        siteDir = os.path.join(self.__folder, name)
        os.makedirs(siteDir)
        if outText is not None:
            with open(os.path.join(siteDir, "findgeo.out"), "w", encoding="utf-8") as ofh:
                ofh.write(outText)
        if inputText is not None:
            with open(os.path.join(siteDir, "findgeo.input"), "w", encoding="utf-8") as ofh:
                ofh.write(inputText)
        return siteDir

    def __writeFile(self, name: str, text: str) -> str:
        fp = os.path.join(self.__tmpDir, name)
        with open(fp, "w", encoding="utf-8") as ofh:
            ofh.write(text)
        return fp

    # ---- parseFindGeoOutPut ----

    def testOutRegular(self) -> None:
        fp = self.__writeFile(
            "r.out",
            _findGeoOut("4", ["TET - Tetrahedron | Regular | 0.123", "spl - square plane | Distorted | 0.456"], "Tetrahedron (Regular)"),
        )
        d = ParseFindGeo(self.__folder).parseFindGeoOutPut(fp)
        self.assertEqual(d, {"coordination": "4", "class_abbr": "TET", "class": "tetrahedron", "tag": "Regular", "rmsd": "0.123"})

    def testOutDistorted(self) -> None:
        fp = self.__writeFile(
            "d.out",
            _findGeoOut("4", ["TET - tetrahedron | Regular | 0.123", "SPL - square plane | Distorted | 0.456"], "square plane (Distorted)"),
        )
        d = ParseFindGeo(self.__folder).parseFindGeoOutPut(fp)
        self.assertIsNotNone(d)
        assert d is not None
        self.assertEqual(d["class"], "square plane")
        self.assertEqual(d["class_abbr"], "SPL")
        self.assertEqual(d["tag"], "Distorted")
        self.assertEqual(d["rmsd"], "0.456")

    def testOutIrregular(self) -> None:
        fp = self.__writeFile(
            "i.out",
            _findGeoOut(
                "5",
                ["TBP - trigonal bipyramid | Irregular | 1.900", "SPY - square pyramid | Irregular | 1.200", "XXX - other | Irregular | N/A"],
                "square pyramid (Irregular)",
            ),
        )
        d = ParseFindGeo(self.__folder).parseFindGeoOutPut(fp)
        self.assertEqual(d, {"coordination": "5", "class": "irregular", "class_abbr": "", "tag": "Irregular", "rmsd": "1.2"})

    def testOutIrregularNoNumericRmsd(self) -> None:
        fp = self.__writeFile("i2.out", _findGeoOut("5", ["XXX - other | Irregular | N/A"], "other (Irregular)"))
        d = ParseFindGeo(self.__folder).parseFindGeoOutPut(fp)
        self.assertIsNotNone(d)
        assert d is not None
        self.assertEqual(d["rmsd"], "")

    def testOutUndetected(self) -> None:
        fp = self.__writeFile("u.out", _findGeoOut("3", ["TRI - trigonal plane | Regular | 0.1"], "something odd"))
        d = ParseFindGeo(self.__folder).parseFindGeoOutPut(fp)
        self.assertEqual(d, {"coordination": "3", "class": "undetected", "class_abbr": "", "tag": "None", "rmsd": ""})

    def testOutMissingFile(self) -> None:
        d = ParseFindGeo(self.__folder).parseFindGeoOutPut(os.path.join(self.__tmpDir, "nope.out"))
        self.assertEqual(d, {})

    def testOutNoCoordination(self) -> None:
        fp = self.__writeFile("n1.out", _findGeoOut(None, ["TET - tetrahedron | Regular | 0.1"], "tetrahedron (Regular)"))
        self.assertIsNone(ParseFindGeo(self.__folder).parseFindGeoOutPut(fp))

    def testOutNoHits(self) -> None:
        fp = self.__writeFile("n2.out", "Coordination number: 4\nBest geometry: tetrahedron (Regular)\n")
        self.assertIsNone(ParseFindGeo(self.__folder).parseFindGeoOutPut(fp))

    def testOutNoBest(self) -> None:
        fp = self.__writeFile("n3.out", _findGeoOut("4", ["TET - tetrahedron | Regular | 0.1"], None))
        self.assertIsNone(ParseFindGeo(self.__folder).parseFindGeoOutPut(fp))

    def testOutBestNotInHits(self) -> None:
        fp = self.__writeFile("n4.out", _findGeoOut("4", ["TET - tetrahedron | Regular | 0.1"], "square plane (Regular)"))
        self.assertIsNone(ParseFindGeo(self.__folder).parseFindGeoOutPut(fp))

    # ---- input parsers ----

    def testPdbInput(self) -> None:
        fp = self.__writeFile("p.input", _pdbInput("ZN", "A", "ZN", "B", 301, "C"))
        t = ParseFindGeo(self.__folder, input_format="pdb").parseFindGeoPdbInput(fp)
        self.assertEqual(t, ("ZN", "ZN", "B", "301", "C", "A"))

    def testPdbInputShortLine(self) -> None:
        fp = self.__writeFile("p2.input", "HETATM    1 ZN   ZN A 301\n")
        self.assertEqual(ParseFindGeo(self.__folder, input_format="pdb").parseFindGeoPdbInput(fp), ())

    def testPdbInputNotAtom(self) -> None:
        fp = self.__writeFile("p3.input", "REMARK nothing here\n")
        self.assertEqual(ParseFindGeo(self.__folder, input_format="pdb").parseFindGeoPdbInput(fp), ())

    def testCifInputViaMmcif(self) -> None:
        fp = self.__writeFile("c.input", _cifInput("ZN", "ZN", "A", "301"))
        pfg = ParseFindGeo(self.__folder)
        d_row = pfg.parseMmcif(fp)
        self.assertEqual(d_row["auth_asym_id"], "A")
        t = pfg.parseFindGeoCifInput(fp)
        self.assertEqual(t, ("ZN", "ZN", "A", "301", "X", "B"))

    def testCifInputColumnGuessFallback(self) -> None:
        fp = self.__writeFile("c2.input", _cifInput("CU", "CU1", "D", "77", authAsymItem="auth_asym_xx"))
        pfg = ParseFindGeo(self.__folder)
        self.assertEqual(pfg.parseMmcif(fp), {})
        t = pfg.parseFindGeoCifInput(fp)
        self.assertEqual(t, ("CU1", "CU", "D", "77", "X", "B"))

    def testCifInputNoAtomSite(self) -> None:
        fp = self.__writeFile("c3.input", "data_x\n_entry.id X\n")
        pfg = ParseFindGeo(self.__folder)
        self.assertEqual(pfg.parseMmcif(fp), {})
        self.assertEqual(pfg.parseFindGeoCifInput(fp), ())

    def testCifInputUnreadable(self) -> None:
        fp = os.path.join(self.__tmpDir, "missing.input")
        self.assertEqual(ParseFindGeo(self.__folder).parseMmcif(fp), {})

    # ---- amend ----

    def testAmendRegular(self) -> None:
        d = ParseFindGeo(self.__folder).amend({"class": "tetrahedron", "metalElement": "Zn", "coordination": "4", "tag": "Regular"})
        self.assertEqual(d["class_generic"], "tetrahedral")
        self.assertEqual(d["coordination_number_allowed"], "YES")
        self.assertEqual(d["redox_active"], "N")
        self.assertEqual(d["oxidation_state"], "2")
        self.assertEqual(d["carbon_metal"], "NO")
        self.assertEqual(d["class_in_exception"], "NO")
        self.assertEqual(d["tag"], "Regular")

    def testAmendCoordinationNumberException(self) -> None:
        d = ParseFindGeo(self.__folder).amend({"class": "trigonal plane", "metalElement": "Zn", "coordination": "3", "tag": "Regular"})
        self.assertEqual(d["coordination_number_allowed"], "NO")
        self.assertEqual(d["tag"], "Coordination number exception")

    def testAmendClassException(self) -> None:
        d = ParseFindGeo(self.__folder).amend({"class": "square plane", "metalElement": "Mg", "coordination": "4", "tag": "Regular"})
        self.assertEqual(d["class_in_exception"], "YES")
        self.assertEqual(d["tag"], "Coordination class exception")

    def testAmendUnknownMetal(self) -> None:
        d = ParseFindGeo(self.__folder).amend({"class": "weird shape", "metalElement": "Xx", "coordination": "9", "tag": "Irregular"})
        self.assertEqual(d["class_generic"], "")
        self.assertEqual(d["coordination_number_allowed"], "")
        self.assertEqual(d["redox_active"], "")
        self.assertEqual(d["oxidation_state"], "")
        self.assertEqual(d["carbon_metal"], "NO")
        self.assertEqual(d["class_in_exception"], "NO")
        self.assertEqual(d["tag"], "Irregular")

    def testAmendCarbonMetal(self) -> None:
        d = ParseFindGeo(self.__folder).amend({"class": "octahedron", "metalElement": "Fe", "coordination": "6", "tag": "Distorted"})
        self.assertEqual(d["carbon_metal"], "YES")
        self.assertEqual(d["redox_active"], "Y")
        self.assertEqual(d["class_generic"], "octahedral")

    # ---- full folder parse ----

    def testParseFolderCif(self) -> None:
        self.__addSite(
            "ZN_301__A_ZN",
            _findGeoOut("4", ["TET - tetrahedron | Regular | 0.123"], "tetrahedron (Regular)"),
            _cifInput("ZN", "ZN", "A", "301"),
        )
        self.__addSite(
            "Fe_401__B_HEM",
            _findGeoOut("6", ["OCT - octahedron | Distorted | 0.500"], "octahedron (Distorted)"),
            _cifInput("FE", "HEM", "B", "401"),
        )
        # skipped entries
        os.makedirs(os.path.join(self.__folder, "data"))
        with open(os.path.join(self.__folder, "plain_file.txt"), "w", encoding="utf-8") as ofh:
            ofh.write("x")
        os.makedirs(os.path.join(self.__folder, "nounderscore"))
        self.__addSite("Cu_1__A_CU", None, None)  # no findgeo.out
        self.__addSite("Cu_2__A_CU", _findGeoOut("4", ["TET - tetrahedron | Regular | 0.1"], "tetrahedron (Regular)"), None)  # no input
        self.__addSite("Cu_3__A_CU", _findGeoOut(None, [], None), _cifInput("CU", "CU", "A", "3"))  # unparseable out
        self.__addSite("Cu_4__A_CU", _findGeoOut("4", ["TET - tetrahedron | Regular | 0.1"], "tetrahedron (Regular)"), "data_x\n_entry.id X\n")  # no atoms

        pfg = ParseFindGeo(self.__folder, input_format="cif")
        pfg.parse()
        self.assertEqual(len(pfg.l_sites), 2)
        byMetal = {s["metalElement"]: s for s in pfg.l_sites}
        self.assertEqual(set(byMetal.keys()), {"Zn", "Fe"})
        zn = byMetal["Zn"]
        self.assertEqual(list(zn.keys()), EXPECTED_KEY_ORDER)
        self.assertEqual(zn["metal"], "ZN")
        self.assertEqual(zn["chain"], "A")
        self.assertEqual(zn["residue"], "ZN")
        self.assertEqual(zn["sequence"], "301")
        self.assertEqual(zn["icode"], "X")
        self.assertEqual(zn["altloc"], "B")
        self.assertEqual(zn["class_generic"], "tetrahedral")
        self.assertEqual(zn["tag"], "Regular")
        self.assertEqual(byMetal["Fe"]["residue"], "HEM")
        self.assertEqual(byMetal["Fe"]["carbon_metal"], "YES")

        fpOut = os.path.join(self.__tmpDir, "report.json")
        pfg.report(fpOut)
        with open(fpOut, encoding="utf-8") as ifh:
            loaded = json.load(ifh)
        self.assertEqual(len(loaded), 2)
        self.assertEqual(list(loaded[0].keys()), EXPECTED_KEY_ORDER)

    def testParseFolderPdb(self) -> None:
        outText = _findGeoOut("4", ["TET - tetrahedron | Regular | 0.1"], "tetrahedron (Regular)")
        self.__addSite("ZN_301__A_ZN", outText, _pdbInput("ZN", " ", "ZN", "A", 301, " "))
        pfg = ParseFindGeo(self.__folder, input_format="pdb")
        pfg.parse()
        self.assertEqual(len(pfg.l_sites), 1)
        site = pfg.l_sites[0]
        self.assertEqual(site["metal"], "ZN")
        self.assertEqual(site["chain"], "A")
        self.assertEqual(site["sequence"], "301")
        self.assertEqual(site["icode"], " ")
        self.assertEqual(site["altloc"], " ")

    def testParseUnsupportedFormat(self) -> None:
        self.__addSite("ZN_301__A_ZN", _findGeoOut("4", ["TET - tetrahedron | Regular | 0.1"], "tetrahedron (Regular)"), _cifInput("ZN", "ZN", "A", "301"))
        pfg = ParseFindGeo(self.__folder, input_format="xyz")
        self.assertIsNone(pfg.parseOneSite("ZN_301__A_ZN"))
        pfg.parse()
        self.assertEqual(pfg.l_sites, [])

    def testParseEmptyFolder(self) -> None:
        pfg = ParseFindGeo(self.__folder)
        pfg.parse()
        self.assertEqual(pfg.l_sites, [])
        fpOut = os.path.join(self.__tmpDir, "empty.json")
        pfg.report(fpOut)
        with open(fpOut, encoding="utf-8") as ifh:
            self.assertEqual(json.load(ifh), [])


if __name__ == "__main__":
    unittest.main()
