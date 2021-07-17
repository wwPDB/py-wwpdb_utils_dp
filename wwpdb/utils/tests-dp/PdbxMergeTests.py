##
# File:    RcsbDpUtilityEmTests.py
# Author:  J. Westbrook
# Date:    May 26,2014
# Version: 0.001
#
# Update:

##
"""
Test cases for EM map annotation tools --

"""
import logging
import unittest
import os

from mmcif.api.DataCategory import DataCategory
from mmcif.api.PdbxContainers import DataContainer
from mmcif.io.PdbxReader import PdbxReader
from mmcif.io.PdbxWriter import PdbxWriter

if __package__ is None or __package__ == "":
    import sys
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT  # pylint: disable=import-error
else:
    from .commonsetup import TESTOUTPUT

from wwpdb.utils.dp.PdbxMergeCategory import PdbxMergeCategory

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class PdbxMergeTests(unittest.TestCase):
    def setUp(self):
        pass

    @staticmethod
    def _createfile1(pathout):
        my_data_list = []

        cur_container = DataContainer("myblock")

        acat = DataCategory("pdbx_item_enumeration")
        acat.appendAttribute("name")
        acat.appendAttribute("value")
        acat.appendAttribute("detail")
        acat.append(("1", "2", "3"))

        cur_container.append(acat)

        acat = DataCategory("exptl")
        acat.appendAttribute("absorpt_coefficient_mu")
        acat.appendAttribute("entry_id")
        acat.appendAttribute("method")
        acat.appendAttribute("details")
        acat.append(("?", "D_12345", "X-RAY DIFFRACTION", "some details"))

        cur_container.append(acat)

        acat = DataCategory("struct")
        acat.appendAttribute("title")
        acat.appendAttribute("pdbx_descriptor")
        acat.append(("Start title", "Start Descriptor"))

        cur_container.append(acat)

        my_data_list.append(cur_container)

        # Second block
        cur_container = DataContainer("secondblock")

        acat = DataCategory("pdbx_item_enumeration")
        acat.appendAttribute("name")
        acat.appendAttribute("value")
        acat.appendAttribute("detail")
        acat.append(("3", "2", "1"))

        cur_container.append(acat)

        my_data_list.append(cur_container)

        with open(pathout, "w") as ofh:
            pdbxw = PdbxWriter(ofh)
            pdbxw.setAlignmentFlag(flag=True)
            pdbxw.write(my_data_list)

    @staticmethod
    def _createfile2(pathout):
        my_data_list = []

        cur_container = DataContainer("test")

        acat = DataCategory("new")
        acat.appendAttribute("item")
        acat.append(("1",))

        cur_container.append(acat)

        acat = DataCategory("second_category")
        acat.appendAttribute("row")
        acat.appendAttribute("rowb")
        acat.append(("1", "2"))

        cur_container.append(acat)

        acat = DataCategory("third")
        acat.appendAttribute("id")
        acat.appendAttribute("val")
        acat.append(("1", "a"))
        acat.append(("2", "b"))
        acat.append(("3", "c"))

        cur_container.append(acat)

        acat = DataCategory("exptl")
        acat.appendAttribute("method")
        acat.appendAttribute("entry_id")
        acat.append(("NEW", "something"))

        cur_container.append(acat)

        acat = DataCategory("struct")
        acat.appendAttribute("new")
        acat.appendAttribute("pdbx_descriptor")
        acat.append(("Something to add", "Override descriptor"))

        cur_container.append(acat)

        my_data_list.append(cur_container)

        with open(pathout, "w") as ofh:
            pdbxw = PdbxWriter(ofh)
            pdbxw.setAlignmentFlag(flag=True)
            pdbxw.write(my_data_list)

    def _testmerge(self, pathin):
        with open(pathin, "r") as ifh:
            pdbxr = PdbxReader(ifh)
            dlist = []
            pdbxr.read(dlist)
            # Two blocks
            self.assertEqual(len(dlist), 2, "Two blocks in merge")

            block = dlist[0]

            # Merge
            cat = block.getObj("struct")
            self.assertIsNotNone(cat, "Missing struct category")
            self.assertEqual(cat.getRowCount(), 1, "Should only have a single row")
            rd = cat.getRowItemDict(0)
            # print(rd)
            self.assertEqual(rd, {"_struct.title": "Start title", "_struct.pdbx_descriptor": "Override descriptor", "_struct.new": "Something to add"}, "struct category mismatch")

            # Merge
            cat = block.getObj("exptl")
            self.assertIsNotNone(cat, "Missing exptl category")
            self.assertEqual(cat.getRowCount(), 1, "Should only have a single row")
            rd = cat.getRowItemDict(0)
            # print(rd)
            self.assertEqual(
                rd, {"_exptl.method": "NEW", "_exptl.entry_id": "something", "_exptl.absorpt_coefficient_mu": "?", "_exptl.details": "some details"}, "exptl category mismatch"
            )

            # Replace category non-existant
            cat = block.getObj("third")
            self.assertIsNotNone(cat, "Missing third category")
            self.assertEqual(cat.getRowCount(), 3, "Should only have a single row")
            rd = cat.getRowItemDict(0)
            self.assertEqual(rd, {"_third.id": "1", "_third.val": "a"}, "third category mismatch")
            rd = cat.getRowItemDict(1)
            self.assertEqual(rd, {"_third.id": "2", "_third.val": "b"}, "third category mismatch")

    def testMerge(self):
        f1name = os.path.join(TESTOUTPUT, "test_merge1.cif")
        self._createfile1(f1name)

        f2name = os.path.join(TESTOUTPUT, "test_merge2.cif")
        self._createfile2(f2name)

        f3name = os.path.join(TESTOUTPUT, "test_merge3.cif")

        if os.path.exists(f3name):
            os.unlink(f3name)

        pm = PdbxMergeCategory()
        self.assertTrue(pm.merge(f1name, f2name, f3name, ["struct", "exptl"], ["third"]), "Merge failed")

        self._testmerge(f3name)


if __name__ == "__main__":
    # Run all tests --
    unittest.main()
