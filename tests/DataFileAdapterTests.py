##
# File:    DataFileAdapterTests.py
#
# Update:
##
"""
Hermetic unit tests for wwpdb.utils.dp.DataFileAdapter.  RcsbDpUtility is mocked so the
sequence of operations and arguments can be verified without the annotation tools.

"""

import io
import logging
import os
import shutil
import sys
import tempfile
import unittest
from typing import Any, Callable, List
from unittest import mock

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.abspath(__file__)))
    import commonsetup  # noqa: F401 pylint: disable=import-error,unused-import
else:
    from . import commonsetup  # noqa: F401 pylint: disable=unused-import

from wwpdb.utils.dp.DataFileAdapter import DataFileAdapter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

PATCHTARGET = "wwpdb.utils.dp.DataFileAdapter.RcsbDpUtility"


class DataFileAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__sessionPath = tempfile.mkdtemp()
        self.__siteId = "TEST_SITE"
        self.__reqObj = mock.Mock()
        self.__reqObj.getValue.side_effect = lambda key: self.__siteId if key == "WWPDB_SITE_ID" else ""
        self.__reqObj.getSessionObj.return_value.getPath.return_value = self.__sessionPath
        self.__lfh = io.StringIO()

    def tearDown(self) -> None:
        shutil.rmtree(self.__sessionPath, ignore_errors=True)

    def __adapter(self, verbose: bool = False) -> DataFileAdapter:
        return DataFileAdapter(self.__reqObj, verbose=verbose, log=self.__lfh)

    def __checkConstruct(self, mockDp: mock.MagicMock) -> None:
        mockDp.assert_called_once_with(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=False, log=self.__lfh)

    def __opNames(self, mockDp: mock.MagicMock) -> List[str]:
        return [c[0][0] for c in mockDp.return_value.op.call_args_list]

    def __checkSimple(self, func: Callable[..., Any], args: List[Any], expectOp: str, expectLog: str) -> mock.MagicMock:
        """Runs a simple conversion and checks the common imp/op/expLog/exp sequence"""
        with mock.patch(PATCHTARGET) as mockDp:
            ok = func(*args)
        self.assertTrue(ok)
        self.__checkConstruct(mockDp)
        dp = mockDp.return_value
        dp.imp.assert_called_once_with("in.cif")
        dp.op.assert_called_once_with(expectOp)
        dp.expLog.assert_called_once_with(os.path.join(self.__sessionPath, expectLog))
        dp.exp.assert_called_once_with("out.cif")
        # debug is always on - so cleanup never called
        dp.cleanup.assert_not_called()
        return mockDp

    def __checkFailure(self, func: Callable[..., Any], args: List[Any]) -> None:
        with mock.patch(PATCHTARGET) as mockDp:
            mockDp.return_value.op.side_effect = RuntimeError("tool failure")
            ok = func(*args)
        self.assertFalse(ok)
        self.assertIn("tool failure", self.__lfh.getvalue())

    def testPdbx2NmrStar(self) -> None:
        dfa = self.__adapter()
        mockDp = self.__checkSimple(dfa.pdbx2nmrstar, ["in.cif", "out.cif"], "annot-pdbx2nmrstar", "annot-pdbx2nmrstar.log")
        mockDp.return_value.addInput.assert_not_called()

    def testPdbx2NmrStarPdbId(self) -> None:
        dfa = self.__adapter()
        mockDp = self.__checkSimple(dfa.pdbx2nmrstar, ["in.cif", "out.cif", "1abc"], "annot-pdbx2nmrstar", "annot-pdbx2nmrstar.log")
        mockDp.return_value.addInput.assert_called_once_with(name="pdb_id", value="1abc", type="param")

    def testPdbx2NmrStarFail(self) -> None:
        self.__checkFailure(self.__adapter().pdbx2nmrstar, ["in.cif", "out.cif"])

    def testRcsb2Pdbx(self) -> None:
        dfa = self.__adapter()
        self.__checkSimple(dfa.rcsb2Pdbx, ["in.cif", "out.cif"], "annot-rcsb2pdbx", "annot-rcsb2pdbx.log")
        self.__checkSimple(dfa.rcsb2Pdbx, ["in.cif", "out.cif", True], "annot-rcsb2pdbx-strip", "annot-rcsb2pdbx.log")
        self.__checkSimple(dfa.rcsb2Pdbx, ["in.cif", "out.cif", True, True], "annot-rcsb2pdbx-strip-plus-entity", "annot-rcsb2pdbx.log")
        # Entity flag ignored without strip
        self.__checkSimple(dfa.rcsb2Pdbx, ["in.cif", "out.cif", False, True], "annot-rcsb2pdbx", "annot-rcsb2pdbx.log")

    def testRcsb2PdbxFail(self) -> None:
        self.__checkFailure(self.__adapter().rcsb2Pdbx, ["in.cif", "out.cif"])

    def testRcsb2PdbxWithPdbId(self) -> None:
        dfa = self.__adapter()
        self.__checkSimple(dfa.rcsb2PdbxWithPdbId, ["in.cif", "out.cif"], "annot-rcsb2pdbx-withpdbid", "annot-rcsb2pdbx.log")

    def testRcsb2PdbxWithPdbIdFail(self) -> None:
        self.__checkFailure(self.__adapter().rcsb2PdbxWithPdbId, ["in.cif", "out.cif"])

    def testRcsb2PdbxWithPdbIdAlt(self) -> None:
        dfa = self.__adapter()
        self.__checkSimple(dfa.rcsb2PdbxWithPdbIdAlt, ["in.cif", "out.cif"], "annot-rcsb2pdbx-alt", "annot-rcsb2pdbxalt.log")

    def testRcsb2PdbxWithPdbIdAltFail(self) -> None:
        self.__checkFailure(self.__adapter().rcsb2PdbxWithPdbIdAlt, ["in.cif", "out.cif"])

    def testRcsbEps2Pdbx(self) -> None:
        dfa = self.__adapter()
        self.__checkSimple(dfa.rcsbEps2Pdbx, ["in.cif", "out.cif"], "annot-cif2cif", "annot-rcsbeps2pdbx.log")
        self.__checkSimple(dfa.rcsbEps2Pdbx, ["in.cif", "out.cif", True], "annot-rcsbeps2pdbx-strip", "annot-rcsbeps2pdbx.log")
        self.__checkSimple(dfa.rcsbEps2Pdbx, ["in.cif", "out.cif", True, True], "annot-rcsbeps2pdbx-strip-plus-entity", "annot-rcsbeps2pdbx.log")

    def testRcsbEps2PdbxFail(self) -> None:
        self.__checkFailure(self.__adapter().rcsbEps2Pdbx, ["in.cif", "out.cif"])

    def testCif2Pdb(self) -> None:
        self.__checkSimple(self.__adapter().cif2Pdb, ["in.cif", "out.cif"], "annot-cif2pdb", "annot-cif2pdb.log")

    def testCif2PdbFail(self) -> None:
        self.__checkFailure(self.__adapter().cif2Pdb, ["in.cif", "out.cif"])

    def testCif2Pdbx(self) -> None:
        self.__checkSimple(self.__adapter().cif2Pdbx, ["in.cif", "out.cif"], "cif2pdbx-public", "annot-cif2pdbx.log")

    def testCif2PdbxFail(self) -> None:
        self.__checkFailure(self.__adapter().cif2Pdbx, ["in.cif", "out.cif"])

    def testModelConvertToPdbxMissingArgs(self) -> None:
        dfa = self.__adapter(verbose=True)
        with mock.patch(PATCHTARGET) as mockDp:
            self.assertFalse(dfa.modelConvertToPdbx(filePath=None, pdbxFilePath="out.cif"))
            self.assertFalse(dfa.modelConvertToPdbx(filePath="in.cif", pdbxFilePath=None))
            self.assertFalse(dfa.modelConvertToPdbx(filePath="in.cif", fileType="unknown-type", pdbxFilePath="out.cif"))
        mockDp.assert_not_called()
        self.assertIn("modelConvertToPdbx", self.__lfh.getvalue())

    def testModelConvertToPdbxCopy(self) -> None:
        dfa = self.__adapter()
        inPath = os.path.join(self.__sessionPath, "in.cif")
        with open(inPath, "w") as ofh:
            ofh.write("data_test\n_entry.id TEST\n")
        for fileType in ["pdbx-mmcif", "pdbx", "pdbx-cif"]:
            outPath = os.path.join(self.__sessionPath, "out-%s.cif" % fileType)
            with mock.patch(PATCHTARGET) as mockDp:
                self.assertTrue(dfa.modelConvertToPdbx(filePath=inPath, fileType=fileType, pdbxFilePath=outPath))
            mockDp.assert_not_called()
            with open(outPath) as ifh:
                self.assertEqual(ifh.read(), "data_test\n_entry.id TEST\n")
        # Same source and destination - no copy needed
        self.assertTrue(dfa.modelConvertToPdbx(filePath=inPath, fileType="pdbx", pdbxFilePath=inPath))

    def testModelConvertToPdbxCopyFailure(self) -> None:
        dfa = self.__adapter()
        missing = os.path.join(self.__sessionPath, "missing.cif")
        self.assertFalse(dfa.modelConvertToPdbx(filePath=missing, fileType="pdbx", pdbxFilePath=os.path.join(self.__sessionPath, "out.cif")))
        self.assertIn("Traceback", self.__lfh.getvalue())

    def testModelConvertToPdbxConversions(self) -> None:
        dfa = self.__adapter()
        expected = {
            "rcsb-mmcif": "annot-rcsb2pdbx",
            "rcsb-mmcif-strip": "annot-rcsb2pdbx-strip",
            "rcsb-cifeps": "annot-cif2cif",
            "rcsb-cifeps-strip": "annot-rcsbeps2pdbx-strip",
        }
        for fileType, opName in expected.items():
            with mock.patch(PATCHTARGET) as mockDp:
                self.assertTrue(dfa.modelConvertToPdbx(filePath="in.cif", fileType=fileType, pdbxFilePath="out.cif"))
            self.assertEqual(self.__opNames(mockDp), [opName])
            mockDp.return_value.exp.assert_called_once_with("out.cif")

    def testModelConvertToPdbxConversionFails(self) -> None:
        dfa = self.__adapter()
        with mock.patch(PATCHTARGET) as mockDp:
            mockDp.return_value.exp.side_effect = OSError("no output")
            self.assertFalse(dfa.modelConvertToPdbx(filePath="in.cif", fileType="rcsb-mmcif", pdbxFilePath="out.cif"))

    def testPdbx2Assemblies(self) -> None:
        dfa = self.__adapter(verbose=True)
        resDir = tempfile.mkdtemp()
        outDir = tempfile.mkdtemp()
        try:
            res1 = os.path.join(resDir, "1abc-assembly-1.cif")
            res2 = os.path.join(resDir, "1abc-assembly-2.cif")
            for pth in [res1, res2]:
                with open(pth, "w") as ofh:
                    ofh.write("data_%s\n" % os.path.basename(pth))
            missing = os.path.join(resDir, "not-there.cif")
            with mock.patch(PATCHTARGET) as mockDp:
                mockDp.return_value.getResultPathList.return_value = [res1, missing, res2]
                ok = dfa.pdbx2Assemblies("D_1000000001", "in.cif", outPath=outDir, indexFilePath="index.txt")
            self.assertTrue(ok)
            dp = mockDp.return_value
            dp.imp.assert_called_once_with("in.cif")
            expectedCalls = [
                mock.call(name="deposition_data_set_id", value="D_1000000001", type="param"),
                mock.call(name="index_file_path", value="index.txt", type="param"),
            ]
            dp.addInput.assert_has_calls(expectedCalls)
            dp.op.assert_called_once_with("annot-gen-assem-pdbx")
            dp.expLog.assert_called_once_with(os.path.join(self.__sessionPath, "pdbx-assembly.log"))
            self.assertEqual(sorted(os.listdir(outDir)), ["1abc-assembly-1.cif", "1abc-assembly-2.cif"])
            self.assertIn("assembly output paths", self.__lfh.getvalue())
        finally:
            shutil.rmtree(resDir, ignore_errors=True)
            shutil.rmtree(outDir, ignore_errors=True)

    def testPdbx2AssembliesNoOptional(self) -> None:
        dfa = self.__adapter()
        with mock.patch(PATCHTARGET) as mockDp:
            mockDp.return_value.getResultPathList.return_value = []
            self.assertTrue(dfa.pdbx2Assemblies(None, "in.cif"))
        mockDp.return_value.addInput.assert_not_called()
        self.assertEqual(self.__lfh.getvalue(), "")

    def testPdbx2AssembliesFail(self) -> None:
        dfa = self.__adapter()
        with mock.patch(PATCHTARGET) as mockDp:
            mockDp.return_value.op.side_effect = RuntimeError("assembly failure")
            self.assertFalse(dfa.pdbx2Assemblies("D_1", "in.cif"))
        self.assertIn("pdbx2Assemblies() - failing for input file path in.cif", self.__lfh.getvalue())

    def testMtz2Pdbx(self) -> None:
        dfa = self.__adapter()
        with mock.patch(PATCHTARGET) as mockDp:
            ok = dfa.mtz2Pdbx("in.mtz", "out-sf.cif", pdbxFilePath="model.cif", logFilePath="diag.log", dumpFilePath="dump.log", timeout=30)
        self.assertTrue(ok)
        self.__checkConstruct(mockDp)
        dp = mockDp.return_value
        dp.imp.assert_called_once_with("in.mtz")
        dp.setTimeout.assert_called_once_with(30)
        dp.addInput.assert_called_once_with(name="xyz_file_path", value="model.cif")
        dp.op.assert_called_once_with("annot-sf-convert")
        dp.expLog.assert_called_once_with("diag.log")
        dp.expList.assert_called_once_with(dstPathList=["out-sf.cif", "diag.log", "dump.log"])
        dp.cleanup.assert_not_called()

    def testMtz2PdbxDefaults(self) -> None:
        dfa = self.__adapter()
        with mock.patch(PATCHTARGET) as mockDp:
            ok = dfa.mtz2Pdbx("in.mtz", "out-sf.cif")
        self.assertTrue(ok)
        dp = mockDp.return_value
        dp.setTimeout.assert_called_once_with(120)
        dp.addInput.assert_not_called()
        dp.expLog.assert_called_once_with(None)
        dp.expList.assert_called_once_with(dstPathList=["out-sf.cif", "sf-convert-diags.cif", "sf-convert-mtzdmp.log"])

    def testMtz2PdbxFail(self) -> None:
        dfa = self.__adapter()
        with mock.patch(PATCHTARGET) as mockDp:
            mockDp.return_value.op.side_effect = RuntimeError("sf failure")
            self.assertFalse(dfa.mtz2Pdbx("in.mtz", "out-sf.cif"))
        self.assertIn("mtz2Pdbx() - failing for mtz file path in.mtz output path out-sf.cif", self.__lfh.getvalue())


if __name__ == "__main__":
    unittest.main()
