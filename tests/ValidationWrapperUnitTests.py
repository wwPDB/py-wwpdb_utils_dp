##
# File:    ValidationWrapperUnitTests.py
#
# Update:
##
"""
Hermetic unit tests for wwpdb.utils.dp.ValidationWrapper.  The underlying RcsbDpUtility operations and
the map coefficient conversion are mocked, so no validation tools are needed.

"""

import logging
import os
import shutil
import sys
import tempfile
import unittest
from typing import Any, Iterator, List, Optional, Tuple
from unittest import mock

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.abspath(__file__)))
    from commonsetup import TOPDIR  # pylint: disable=import-error
else:
    from .commonsetup import TOPDIR

from wwpdb.utils.config.ConfigInfo import getSiteId

from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility
from wwpdb.utils.dp.ValidationWrapper import ValidationWrapper, ValidationWrapperOp

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

PSMTARGET = "wwpdb.utils.dp.ValidationWrapper.PdbxSFMapCoefficients"


def _fakeExpList(dstPathList: Optional[List[str]] = None) -> bool:
    """Stand in for RcsbDpUtility.expList - produces the last requested file (the mtz)"""
    if dstPathList:
        with open(dstPathList[-1], "w") as ofh:
            ofh.write("MTZ")
    return True


def _fakeWriteCoef(fopathout: str, twofopathout: str, entry_id: str = "xxxx") -> bool:
    for pth, kind in [(fopathout, "fo"), (twofopathout, "2fo")]:
        with open(pth, "w") as ofh:
            ofh.write("data_%s_%s\n" % (entry_id, kind))
    return True


class ValidationWrapperUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmpPath = tempfile.mkdtemp()
        self.__outDir = tempfile.mkdtemp()
        self.__modelPath = os.path.join(TOPDIR, "wwpdb", "mock-data", "MODELS", "4pdr.cif")
        self.__siteId = getSiteId()
        # pdf, xml, fullpdf, png, svg, imagetar, cif, fo, 2fo
        self.__dstList = [os.path.join(self.__outDir, f) for f in ["v.pdf", "v.xml", "vf.pdf", "v.png", "v.svg", "v.tar", "v.cif", "fo.cif", "2fo.cif"]]

    def tearDown(self) -> None:
        shutil.rmtree(self.__tmpPath, ignore_errors=True)
        shutil.rmtree(self.__outDir, ignore_errors=True)

    def __wrapper(self) -> ValidationWrapper:
        return ValidationWrapper(tmpPath=self.__tmpPath, siteId=self.__siteId)

    def __writeModel(self, content: str) -> str:
        pth = os.path.join(self.__outDir, "model.cif")
        with open(pth, "w") as ofh:
            ofh.write(content)
        return pth

    def testOpUnknown(self) -> None:
        vw = self.__wrapper()
        with mock.patch.object(RcsbDpUtility, "op") as mockOp:
            self.assertFalse(vw.op("annot-cif2pdb"))
        mockOp.assert_not_called()

    def testOpPassThrough(self) -> None:
        opNames: List[ValidationWrapperOp] = ["annot-wwpdb-validate-all", "annot-wwpdb-validate-all-v2"]
        for opName in opNames:
            vw = self.__wrapper()
            with mock.patch.object(RcsbDpUtility, "op", return_value=0) as mockOp:
                self.assertEqual(vw.op(opName), 0)
            mockOp.assert_called_once_with(opName)

    def testOpSfMapsToV2(self) -> None:
        vw = self.__wrapper()
        with mock.patch.object(RcsbDpUtility, "op", return_value=0) as mockOp:
            self.assertEqual(vw.op("annot-wwpdb-validate-all-sf"), 0)
        mockOp.assert_called_once_with("annot-wwpdb-validate-all-v2")

    def testExpListPassThrough(self) -> None:
        vw = self.__wrapper()
        with mock.patch.object(RcsbDpUtility, "op", return_value=0), mock.patch.object(RcsbDpUtility, "expList", return_value=True) as mockExp:
            vw.op("annot-wwpdb-validate-all")
            self.assertTrue(vw.expList(["a.pdf", "b.xml"]))
            self.assertTrue(vw.expList())
        self.assertEqual(mockExp.call_args_list, [mock.call(["a.pdf", "b.xml"]), mock.call([])])

    def testImpCopiesToWorkingDir(self) -> None:
        vw = self.__wrapper()
        vw.imp(self.__modelPath)
        wrkDir = vw.getWorkingDir()
        if wrkDir is None:
            self.fail("working directory not set")
        self.assertTrue(wrkDir.startswith(self.__tmpPath))
        self.assertTrue(len(os.listdir(wrkDir)) > 0)

    def __runSf(self, modelPath: str, readOk: bool = True, hasCoef: bool = True, makeMtz: bool = True) -> Tuple[Any, mock.MagicMock, mock.MagicMock]:
        vw = self.__wrapper()
        vw.imp(modelPath)
        expSide = _fakeExpList if makeMtz else None
        with mock.patch.object(RcsbDpUtility, "op", return_value=0), mock.patch(PSMTARGET) as mockPsm:
            with mock.patch.object(RcsbDpUtility, "expList", side_effect=expSide, return_value=True) as mockExp:
                psm = mockPsm.return_value
                psm.read_mtz_sf.return_value = readOk
                psm.has_map_coeff.return_value = hasCoef
                psm.write_mmcif_coef.side_effect = _fakeWriteCoef
                vw.op("annot-wwpdb-validate-all-sf")
                ret = vw.expList(dstPathList=self.__dstList)
        # Check base call
        mockExp.assert_called_once()
        baseList = mockExp.call_args[0][0]
        self.assertEqual(baseList[0:7], self.__dstList[0:7])
        wrkDir = vw.getWorkingDir()
        if wrkDir is None:
            self.fail("working directory not set")
        self.assertEqual(baseList[7], os.path.join(wrkDir, "mapcoef.mtz"))
        return ret, mockPsm, psm

    def __outputs(self) -> Iterator[Optional[str]]:
        for pth in self.__dstList[7:]:
            if os.path.exists(pth):
                with open(pth) as ifh:
                    yield ifh.read()
            else:
                yield None

    def testExpListSf(self) -> None:
        ret, mockPsm, psm = self.__runSf(self.__modelPath)
        self.assertTrue(ret)
        mockPsm.assert_called_once_with(siteid=self.__siteId, tmppath=self.__tmpPath)
        psm.read_mtz_sf.assert_called_once()
        self.assertTrue(psm.read_mtz_sf.call_args[0][0].endswith("mapcoef.mtz"))
        self.assertEqual(psm.write_mmcif_coef.call_args[1]["entry_id"], "4pdr")
        self.assertEqual(list(self.__outputs()), ["data_4pdr_fo\n", "data_4pdr_2fo\n"])

    def testExpListSfNoMtz(self) -> None:
        ret, mockPsm, _psm = self.__runSf(self.__modelPath, makeMtz=False)
        self.assertFalse(ret)
        mockPsm.assert_not_called()
        self.assertEqual(list(self.__outputs()), [None, None])

    def testExpListSfReadFails(self) -> None:
        ret, _mockPsm, psm = self.__runSf(self.__modelPath, readOk=False)
        self.assertFalse(ret)
        psm.has_map_coeff.assert_not_called()
        psm.write_mmcif_coef.assert_not_called()
        self.assertEqual(list(self.__outputs()), [None, None])

    def testExpListSfNoCoefficients(self) -> None:
        ret, _mockPsm, psm = self.__runSf(self.__modelPath, hasCoef=False)
        self.assertFalse(ret)
        psm.write_mmcif_coef.assert_not_called()
        self.assertEqual(list(self.__outputs()), [None, None])

    def testExpListSfWriteProducesNothing(self) -> None:
        vw = self.__wrapper()
        vw.imp(self.__modelPath)
        with mock.patch.object(RcsbDpUtility, "op", return_value=0), mock.patch(PSMTARGET) as mockPsm:
            with mock.patch.object(RcsbDpUtility, "expList", side_effect=_fakeExpList):
                mockPsm.return_value.read_mtz_sf.return_value = True
                mockPsm.return_value.has_map_coeff.return_value = True
                mockPsm.return_value.write_mmcif_coef.return_value = False
                vw.op("annot-wwpdb-validate-all-sf")
                self.assertFalse(vw.expList(dstPathList=self.__dstList))
        self.assertEqual(list(self.__outputs()), [None, None])

    def testExpListSfNoDatabase2(self) -> None:
        model = self.__writeModel("data_test\n_entry.id TEST\n")
        ret, _mockPsm, psm = self.__runSf(model)
        self.assertTrue(ret)
        self.assertEqual(psm.write_mmcif_coef.call_args[1]["entry_id"], "xxxx")

    def testExpListSfUnassignedPdbId(self) -> None:
        model = self.__writeModel("data_test\nloop_\n_database_2.database_id\n_database_2.database_code\nPDB ?\nWWPDB D_1000000001\n")
        ret, _mockPsm, psm = self.__runSf(model)
        self.assertTrue(ret)
        self.assertEqual(psm.write_mmcif_coef.call_args[1]["entry_id"], "xxxx")

    def testExpListSfNoPdbRow(self) -> None:
        model = self.__writeModel("data_test\nloop_\n_database_2.database_id\n_database_2.database_code\nWWPDB D_1000000001\nEMDB EMD-1234\n")
        ret, _mockPsm, psm = self.__runSf(model)
        self.assertTrue(ret)
        self.assertEqual(psm.write_mmcif_coef.call_args[1]["entry_id"], "xxxx")


if __name__ == "__main__":
    unittest.main()
