##
# File:    CentreOfMassUnitTests.py
#
# Update:
##
"""
Hermetic unit tests for wwpdb.utils.dp.CentreOfMass (gemmi based calculation, no site tools needed)

"""

import argparse
import contextlib
import io
import logging
import os
import shutil
import sys
import tempfile
import unittest
from typing import List, Optional
from unittest import mock

import gemmi
from mmcif.io.IoAdapterCore import IoAdapterCore

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.abspath(__file__)))
    from commonsetup import TOPDIR  # pylint: disable=import-error
else:
    from .commonsetup import TOPDIR

from wwpdb.utils.dp import CentreOfMass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class CentreOfMassUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__workDir = tempfile.mkdtemp()
        self.__modelPath = os.path.join(TOPDIR, "wwpdb", "mock-data", "MODELS", "4pdr.cif")
        self.__savedLevel = logger.level

    def tearDown(self) -> None:
        logger.setLevel(self.__savedLevel)
        shutil.rmtree(self.__workDir, ignore_errors=True)

    def __writeWithout(self, catNames: List[str], fileName: str) -> str:
        """Write a copy of the test model with the named categories removed"""
        ioObj = IoAdapterCore()
        containerList = ioObj.readFile(self.__modelPath)
        for catName in catNames:
            containerList[0].remove(catName)
        outPath = os.path.join(self.__workDir, fileName)
        self.assertTrue(ioObj.writeFile(outPath, containerList))
        return outPath

    def __readStruct(self, filePath: str) -> Optional[List[str]]:
        """Returns entry_id and center of mass values from struct category"""
        ioObj = IoAdapterCore()
        containerList = ioObj.readFile(filePath)
        catObj = containerList[0].getObj("struct")
        if catObj is None:
            return None
        return [
            str(catObj.getValue("entry_id", 0)),
            str(catObj.getValue("pdbx_center_of_mass_x", 0)),
            str(catObj.getValue("pdbx_center_of_mass_y", 0)),
            str(catObj.getValue("pdbx_center_of_mass_z", 0)),
        ]

    def __expectedCom(self) -> gemmi.Position:  # pylint: disable=no-member
        block = gemmi.cif.read(self.__modelPath)[0]  # pylint: disable=no-member
        com = CentreOfMass.get_center_of_mass(block)
        self.assertIsInstance(com, gemmi.Position)  # pylint: disable=no-member
        return com  # type: ignore[no-any-return]

    def testGetCenterOfMass(self) -> None:
        com = self.__expectedCom()
        self.assertAlmostEqual(com.x, -6.4795, places=3)
        self.assertAlmostEqual(com.y, -9.588, places=2)
        self.assertAlmostEqual(com.z, 0.144, places=2)

    def testGetCenterOfMassNoModel(self) -> None:
        block = gemmi.cif.read_string("data_test\n_entry.id TEST\n")[0]  # pylint: disable=no-member
        self.assertFalse(CentreOfMass.get_center_of_mass(block))

    def testGetDepositionIds(self) -> None:
        listPath = os.path.join(self.__workDir, "ids.txt")
        with open(listPath, "w") as ofh:
            ofh.write("D_1000000001\n  D_1000000002  \n")
        self.assertEqual(CentreOfMass.get_deposition_ids(listPath), ["D_1000000001", "D_1000000002"])

    def testGetModelFile(self) -> None:
        with mock.patch("wwpdb.utils.dp.CentreOfMass.PathInfo") as mockPi:
            mockPi.return_value.getModelPdbxFilePath.return_value = "/some/path/model.cif"
            ret = CentreOfMass.get_model_file("D_1000000001", "latest", siteId="MYSITE")
        self.assertEqual(ret, "/some/path/model.cif")
        self.assertEqual(mockPi.call_args[0][0], "MYSITE")
        mockPi.return_value.getModelPdbxFilePath.assert_called_once_with(dataSetId="D_1000000001", fileSource="archive", versionId="latest", mileStone=None)

    def testGetModelFileDefaultSite(self) -> None:
        with mock.patch("wwpdb.utils.dp.CentreOfMass.PathInfo") as mockPi, mock.patch("wwpdb.utils.dp.CentreOfMass.getSiteId", return_value="DEFSITE"):
            mockPi.return_value.getModelPdbxFilePath.return_value = "/x.cif"
            ret = CentreOfMass.get_model_file("D_1", "next", mileStone="review")
        self.assertEqual(ret, "/x.cif")
        self.assertEqual(mockPi.call_args[0][0], "DEFSITE")
        mockPi.return_value.getModelPdbxFilePath.assert_called_once_with(dataSetId="D_1", fileSource="archive", versionId="next", mileStone="review")

    def testProcessEntry(self) -> None:
        outPath = os.path.join(self.__workDir, "out.cif")
        self.assertEqual(CentreOfMass.process_entry(self.__modelPath, outPath), 0)
        vals = self.__readStruct(outPath)
        self.assertIsNotNone(vals)
        assert vals is not None
        com = self.__expectedCom()
        self.assertEqual(vals[0], "4PDR")
        self.assertAlmostEqual(float(vals[1]), com.x, places=3)
        self.assertAlmostEqual(float(vals[2]), com.y, places=3)
        self.assertAlmostEqual(float(vals[3]), com.z, places=3)

    def testProcessEntryRerun(self) -> None:
        """Running on an output file that already has the items replaces them"""
        outPath1 = os.path.join(self.__workDir, "out1.cif")
        outPath2 = os.path.join(self.__workDir, "out2.cif")
        self.assertEqual(CentreOfMass.process_entry(self.__modelPath, outPath1), 0)
        self.assertEqual(CentreOfMass.process_entry(outPath1, outPath2), 0)
        self.assertEqual(self.__readStruct(outPath1), self.__readStruct(outPath2))

    def testProcessEntryNoStruct(self) -> None:
        inPath = self.__writeWithout(["struct"], "nostruct.cif")
        outPath = os.path.join(self.__workDir, "out.cif")
        self.assertEqual(CentreOfMass.process_entry(inPath, outPath), 0)
        vals = self.__readStruct(outPath)
        assert vals is not None
        self.assertEqual(vals[0], "4PDR")
        com = self.__expectedCom()
        self.assertAlmostEqual(float(vals[1]), com.x, places=3)

    def testProcessEntryNoStructNoEntry(self) -> None:
        inPath = self.__writeWithout(["struct", "entry"], "noentry.cif")
        outPath = os.path.join(self.__workDir, "out.cif")
        self.assertEqual(CentreOfMass.process_entry(inPath, outPath), 0)
        vals = self.__readStruct(outPath)
        assert vals is not None
        self.assertEqual(vals[0], "XXXX")

    def testProcessEntryMissingFile(self) -> None:
        outPath = os.path.join(self.__workDir, "out.cif")
        self.assertEqual(CentreOfMass.process_entry(os.path.join(self.__workDir, "missing.cif"), outPath), 1)
        self.assertFalse(os.path.exists(outPath))

    def testProcessEntryNoCoordinates(self) -> None:
        inPath = os.path.join(self.__workDir, "nocoord.cif")
        with open(inPath, "w") as ofh:
            ofh.write("data_test\n_entry.id TEST\n")
        outPath = os.path.join(self.__workDir, "out.cif")
        self.assertEqual(CentreOfMass.process_entry(inPath, outPath), 1)
        self.assertFalse(os.path.exists(outPath))

    def testProcessEntryIoReadFailure(self) -> None:
        outPath = os.path.join(self.__workDir, "out.cif")
        with mock.patch("wwpdb.utils.dp.CentreOfMass.IoAdapterCore") as mockIo:
            mockIo.return_value.readFile.side_effect = OSError("cannot read")
            self.assertEqual(CentreOfMass.process_entry(self.__modelPath, outPath), 1)

    def testProcessEntryIoReadEmpty(self) -> None:
        outPath = os.path.join(self.__workDir, "out.cif")
        with mock.patch("wwpdb.utils.dp.CentreOfMass.IoAdapterCore") as mockIo:
            mockIo.return_value.readFile.return_value = []
            self.assertEqual(CentreOfMass.process_entry(self.__modelPath, outPath), 1)
            mockIo.return_value.writeFile.assert_not_called()

    def testProcessEntryWriteReturnsFalse(self) -> None:
        outPath = os.path.join(self.__workDir, "out.cif")
        realCl = IoAdapterCore().readFile(self.__modelPath)
        with mock.patch("wwpdb.utils.dp.CentreOfMass.IoAdapterCore") as mockIo:
            mockIo.return_value.readFile.return_value = realCl
            mockIo.return_value.writeFile.return_value = False
            self.assertEqual(CentreOfMass.process_entry(self.__modelPath, outPath), 1)
            mockIo.return_value.writeFile.assert_called_once_with(outPath, realCl)

    def testProcessEntryWriteRaises(self) -> None:
        outPath = os.path.join(self.__workDir, "out.cif")
        realCl = IoAdapterCore().readFile(self.__modelPath)
        with mock.patch("wwpdb.utils.dp.CentreOfMass.IoAdapterCore") as mockIo:
            mockIo.return_value.readFile.return_value = realCl
            mockIo.return_value.writeFile.side_effect = OSError("disk full")
            self.assertEqual(CentreOfMass.process_entry(self.__modelPath, outPath), 1)

    def __makeListArgs(self, depIds: List[str]) -> argparse.Namespace:
        listPath = os.path.join(self.__workDir, "ids.txt")
        with open(listPath, "w") as ofh:
            ofh.write("\n".join(depIds) + "\n")
        return argparse.Namespace(list=listPath, model_file_in=None, model_file_out=None)

    def __fakeModelFile(
        self,
        depid: str,
        version_id: str,
        mileStone: Optional[str] = None,  # noqa: ARG002 pylint: disable=unused-argument
        siteId: Optional[str] = None,  # noqa: ARG002 pylint: disable=unused-argument
    ) -> str:
        if version_id == "next":
            return os.path.join(self.__workDir, "%s_next.cif" % depid)
        if depid == "D_GOOD":
            return self.__modelPath
        return os.path.join(self.__workDir, "%s_missing.cif" % depid)

    def testCalculateForList(self) -> None:
        args = self.__makeListArgs(["D_GOOD", "D_BAD"])
        with mock.patch("wwpdb.utils.dp.CentreOfMass.get_model_file", side_effect=self.__fakeModelFile) as mockGmf:
            failed = CentreOfMass.calculate_for_list(args, siteId="SITE1")
        self.assertEqual(failed, ["D_BAD"])
        self.assertTrue(os.path.exists(os.path.join(self.__workDir, "D_GOOD_next.cif")))
        self.assertFalse(os.path.exists(os.path.join(self.__workDir, "D_BAD_next.cif")))
        self.assertEqual(mockGmf.call_count, 4)
        mockGmf.assert_any_call("D_GOOD", "latest", siteId="SITE1")
        mockGmf.assert_any_call("D_BAD", "next", siteId="SITE1")

    def testMainListFailure(self) -> None:
        args = self.__makeListArgs(["D_GOOD", "D_BAD"])
        with mock.patch("wwpdb.utils.dp.CentreOfMass.get_model_file", side_effect=self.__fakeModelFile):
            self.assertEqual(CentreOfMass.main(args), 1)

    def testMainListSuccess(self) -> None:
        args = self.__makeListArgs(["D_GOOD"])
        with mock.patch("wwpdb.utils.dp.CentreOfMass.get_model_file", side_effect=self.__fakeModelFile):
            self.assertEqual(CentreOfMass.main(args), 0)
        self.assertTrue(os.path.exists(os.path.join(self.__workDir, "D_GOOD_next.cif")))

    def testMainSingleFile(self) -> None:
        outPath = os.path.join(self.__workDir, "single.cif")
        args = argparse.Namespace(list=None, model_file_in=self.__modelPath, model_file_out=outPath)
        self.assertEqual(CentreOfMass.main(args), 0)
        self.assertIsNotNone(self.__readStruct(outPath))

    def testMainSingleFileFailureStillZero(self) -> None:
        """calculate_for_file only logs failures - main returns 0 for an existing but unusable input"""
        inPath = os.path.join(self.__workDir, "nocoord.cif")
        with open(inPath, "w") as ofh:
            ofh.write("data_test\n_entry.id TEST\n")
        outPath = os.path.join(self.__workDir, "single.cif")
        args = argparse.Namespace(list=None, model_file_in=inPath, model_file_out=outPath)
        self.assertEqual(CentreOfMass.main(args), 0)
        self.assertFalse(os.path.exists(outPath))

    def testMainMissingInput(self) -> None:
        args = argparse.Namespace(list=None, model_file_in=os.path.join(self.__workDir, "missing.cif"), model_file_out="out.cif")
        self.assertEqual(CentreOfMass.main(args), 1)

    def testParseArgs(self) -> None:
        argv = ["CentreOfMass.py", "-i", self.__modelPath, "-o", "out.cif", "-log", "DEBUG"]
        with mock.patch.object(sys, "argv", argv), mock.patch("wwpdb.utils.dp.CentreOfMass.main") as mockMain:
            CentreOfMass.parse_args()
        mockMain.assert_called_once()
        args = mockMain.call_args[0][0]
        self.assertEqual(args.model_file_in, self.__modelPath)
        self.assertEqual(args.model_file_out, "out.cif")
        self.assertIsNone(args.list)
        self.assertEqual(logger.level, logging.DEBUG)

    def testParseArgsNoArguments(self) -> None:
        out = io.StringIO()
        with mock.patch.object(sys, "argv", ["CentreOfMass.py"]), mock.patch("wwpdb.utils.dp.CentreOfMass.main") as mockMain, contextlib.redirect_stdout(out):
            with self.assertRaises(SystemExit):
                CentreOfMass.parse_args()
        mockMain.assert_not_called()
        self.assertIn("--model-file-in", out.getvalue())


if __name__ == "__main__":
    unittest.main()
