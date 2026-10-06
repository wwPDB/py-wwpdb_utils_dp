##
# File:    PdbxModelComplexityUnitTests.py
#
##
"""
Hermetic tests for PdbxModelComplexity calculation logic
"""

import logging
import os
import shutil
import tempfile
import unittest
from typing import Any, Dict, List, Optional
from unittest import mock

from mmcif.api.DataCategory import DataCategory
from mmcif.api.PdbxContainers import DataContainer
from mmcif.io.IoAdapterCore import IoAdapterCore

from wwpdb.utils.dp.PdbxModelComplexity import PdbxModelCompletity, main

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class PdbxModelComplexityUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmpdir = tempfile.mkdtemp()
        self.__out = os.path.join(self.__tmpdir, "out.cif")

    def tearDown(self) -> None:
        shutil.rmtree(self.__tmpdir, ignore_errors=True)

    def __writeModel(
        self,
        entities: Optional[List[List[str]]] = None,
        entattr: Optional[List[str]] = None,
        oligo: Optional[str] = None,
    ) -> str:
        c0 = DataContainer("model")
        c0.append(DataCategory("struct", ["title"], [["test"]]))
        if entities is not None:
            if entattr is None:
                entattr = ["id", "type", "pdbx_number_of_molecules", "formula_weight"]
            c0.append(DataCategory("entity", entattr, entities))
        if oligo is not None:
            c0.append(DataCategory("pdbx_struct_assembly", ["id", "oligomeric_count"], [["1", oligo]]))
        fpath = os.path.join(self.__tmpdir, "model.cif")
        IoAdapterCore().writeFile(fpath, [c0])
        return fpath

    def __readOutput(self) -> Dict[str, Any]:
        cL = IoAdapterCore().readFile(self.__out)
        self.assertEqual(len(cL), 1)
        self.assertEqual(cL[0].getName(), "complexity")
        cat = cL[0].getObj("pdbx_complexity")
        ret: Dict[str, Any] = {att: cat.getValue(att, 0) for att in cat.getAttributeList()}
        return ret

    def testCalculate(self) -> None:
        ents = [
            ["1", "polymer", "2", "1000.0"],
            ["2", "non-polymer", "3", "100.0"],
            ["3", "water", "10", "18.0"],
        ]
        fpath = self.__writeModel(ents, oligo="4")
        pmc = PdbxModelCompletity(threshold=1000.0)
        self.assertTrue(pmc.calculate(fpath))
        pmc.write_output(self.__out)
        out = self.__readOutput()
        # polymer: 2 * 1000 * 4 = 8000; non-poly: 300 + 180 = 480
        self.assertEqual(out["is_complex"], "True")
        self.assertAlmostEqual(float(out["polymer_complexity"]), 8000.0)
        self.assertAlmostEqual(float(out["non_poly_complexity"]), 480.0)
        self.assertAlmostEqual(float(out["entry_complexity"]), 8480.0)
        self.assertEqual(out["complex_threshold"], "1.00e+03")

    def testNotComplexDefaultOligo(self) -> None:
        fpath = self.__writeModel([["1", "polymer", "1", "500.0"]])
        pmc = PdbxModelCompletity()
        self.assertTrue(pmc.calculate(fpath))
        pmc.write_output(self.__out)
        out = self.__readOutput()
        self.assertEqual(out["is_complex"], "False")
        self.assertAlmostEqual(float(out["entry_complexity"]), 500.0)
        self.assertEqual(out["complex_threshold"], "1.00e+06")

    def testBadOligoCount(self) -> None:
        fpath = self.__writeModel([["1", "polymer", "2", "10.0"]], oligo="abc")
        pmc = PdbxModelCompletity(threshold=1.0)
        self.assertTrue(pmc.calculate(fpath))
        pmc.write_output(self.__out)
        # Non-integer oligomeric_count falls back to 1
        self.assertAlmostEqual(float(self.__readOutput()["polymer_complexity"]), 20.0)

    def testMissingEntityAttribute(self) -> None:
        fpath = self.__writeModel([["1", "polymer", "2"]], entattr=["id", "type", "pdbx_number_of_molecules"])
        pmc = PdbxModelCompletity()
        self.assertFalse(pmc.calculate(fpath))

    def testNoEntity(self) -> None:
        """No entity category - succeeds with default output values"""
        fpath = self.__writeModel(None)
        pmc = PdbxModelCompletity(threshold=5.0)
        self.assertTrue(pmc.calculate(fpath))
        pmc.write_output(self.__out)
        out = self.__readOutput()
        self.assertEqual(out["is_complex"], "False")
        self.assertEqual(out["entry_complexity"], "0")
        self.assertEqual(out["polymer_complexity"], "0")
        self.assertEqual(out["non_poly_complexity"], "0")
        self.assertEqual(out["complex_threshold"], "5.00e+00")

    def testMissingFile(self) -> None:
        pmc = PdbxModelCompletity()
        self.assertFalse(pmc.calculate(os.path.join(self.__tmpdir, "missing.cif")))

    def testEmptyFile(self) -> None:
        emp = os.path.join(self.__tmpdir, "empty.cif")
        with open(emp, "w"):
            pass
        pmc = PdbxModelCompletity()
        self.assertFalse(pmc.calculate(emp))

    def testMainSuccess(self) -> None:
        fpath = self.__writeModel([["1", "polymer", "1", "50.0"]])
        argv = ["PdbxModelComplexity.py", "--model", fpath, "--output", self.__out, "--threshold", "10"]
        with mock.patch("sys.argv", argv), self.assertRaises(SystemExit) as cm:
            main()
        self.assertEqual(cm.exception.code, 0)
        out = self.__readOutput()
        self.assertEqual(out["is_complex"], "True")
        self.assertEqual(out["complex_threshold"], "1.00e+01")

    def testMainFailure(self) -> None:
        argv = ["PdbxModelComplexity.py", "--model", os.path.join(self.__tmpdir, "missing.cif"), "--output", self.__out]
        with mock.patch("sys.argv", argv), mock.patch("builtins.print") as mprint, self.assertRaises(SystemExit) as cm:
            main()
        self.assertEqual(cm.exception.code, 1)
        mprint.assert_called_once()
        self.assertFalse(os.path.exists(self.__out))


if __name__ == "__main__":
    unittest.main()
