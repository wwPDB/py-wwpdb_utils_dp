##
# File:    PdbxChemShiftReportTests.py
#
##
"""
Hermetic tests for PdbxChemShiftReport
"""

import logging
import os
import shutil
import tempfile
import unittest

from mmcif.api.DataCategory import DataCategory
from mmcif.api.PdbxContainers import DataContainer
from mmcif.io.PdbxWriter import PdbxWriter

from wwpdb.utils.dp.PdbxChemShiftReport import PdbxChemShiftReport

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class PdbxChemShiftReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmpdir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.__tmpdir, ignore_errors=True)

    def __write(self, fname: str, c0: DataContainer) -> str:
        fpath = os.path.join(self.__tmpdir, fname)
        with open(fpath, "w") as ofh:
            PdbxWriter(ofh).write([c0])
        return fpath

    def testFullReport(self) -> None:
        c0 = DataContainer("report")
        cat = DataCategory("pdbx_shift_check")
        cat.appendAttribute("status")
        cat.append(["warning"])
        c0.append(cat)

        cat = DataCategory("pdbx_shift_check_warning_message")
        cat.appendAttribute("ordinal")
        cat.appendAttribute("text")
        cat.append(["1", "first warning"])
        cat.append(["2", "second warning"])
        c0.append(cat)

        cat = DataCategory("pdbx_shift_check_error_message")
        cat.appendAttribute("ordinal")
        cat.appendAttribute("text")
        cat.append(["1", "an error"])
        c0.append(cat)

        fpath = self.__write("full.cif", c0)
        rpt = PdbxChemShiftReport(fpath, verbose=True)
        self.assertEqual(rpt.getStatus(), ["warning"])
        self.assertEqual(rpt.getWarnings(), ["first warning", "second warning"])
        self.assertEqual(rpt.getErrors(), ["an error"])

    def testMissingCategoriesAndAttributes(self) -> None:
        c0 = DataContainer("report")
        cat = DataCategory("pdbx_shift_check")
        # status attribute is absent
        cat.appendAttribute("other")
        cat.append(["x"])
        c0.append(cat)
        fpath = self.__write("partial.cif", c0)
        rpt = PdbxChemShiftReport(fpath)
        self.assertEqual(rpt.getStatus(), [])
        self.assertEqual(rpt.getWarnings(), [])
        self.assertEqual(rpt.getErrors(), [])

    def testMissingFile(self) -> None:
        rpt = PdbxChemShiftReport(os.path.join(self.__tmpdir, "missing.cif"))
        self.assertEqual(rpt.getStatus(), [])
        self.assertEqual(rpt.getWarnings(), [])
        self.assertEqual(rpt.getErrors(), [])


if __name__ == "__main__":
    unittest.main()
