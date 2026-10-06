##
# File:    DensityWrapperTests.py
#
# Update:
##
"""
Hermetic unit tests for wwpdb.utils.dp.DensityWrapper.  RcsbDpUtility is mocked.

"""

import contextlib
import io
import logging
import os
import shutil
import sys
import tempfile
import unittest
from typing import Optional
from unittest import mock

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.abspath(__file__)))
    import commonsetup  # noqa: F401 pylint: disable=import-error,unused-import
else:
    from . import commonsetup  # noqa: F401 pylint: disable=unused-import

from wwpdb.utils.dp import DensityWrapper as DensityWrapperModule
from wwpdb.utils.dp.DensityWrapper import DensityWrapper

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

PATCHTARGET = "wwpdb.utils.dp.DensityWrapper.RcsbDpUtility"


def _touch(pth: Optional[str]) -> None:
    if pth:
        with open(pth, "w") as ofh:
            ofh.write("bcif")


class DensityWrapperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__workDir = tempfile.mkdtemp()
        self.__out = os.path.join(self.__workDir, "out.bcif")
        self.__savedLevel = logger.level

    def tearDown(self) -> None:
        logger.setLevel(self.__savedLevel)
        shutil.rmtree(self.__workDir, ignore_errors=True)

    def testDefaultSiteId(self) -> None:
        with mock.patch("wwpdb.utils.dp.DensityWrapper.getSiteId", return_value="DEFSITE") as mockSite, mock.patch(PATCHTARGET) as mockDp:
            dw = DensityWrapper()
            dw.convert_em_volume("in.map", self.__out, self.__workDir)
        mockSite.assert_called_once_with()
        mockDp.assert_called_once_with(tmpPath=self.__workDir, siteId="DEFSITE", verbose=True)

    def testXraySuccess(self) -> None:
        dw = DensityWrapper(site_id="MYSITE")
        with mock.patch(PATCHTARGET) as mockDp:
            mockDp.return_value.exp.side_effect = _touch
            ok = dw.convert_xray_density_map("model.cif", "2fofc.cif", "fofc.cif", self.__out, self.__workDir)
        self.assertTrue(ok)
        mockDp.assert_called_once_with(tmpPath=self.__workDir, siteId="MYSITE", verbose=True)
        dp = mockDp.return_value
        dp.imp.assert_called_once_with("model.cif")
        self.assertEqual(
            dp.addInput.call_args_list,
            [mock.call(name="two_fofc_cif", value="2fofc.cif", type="file"), mock.call(name="one_fofc_cif", value="fofc.cif", type="file")],
        )
        dp.op.assert_called_once_with("xray-density-bcif")
        dp.exp.assert_called_once_with(self.__out)
        dp.cleanup.assert_called_once_with()

    def testXrayNoOutput(self) -> None:
        dw = DensityWrapper(site_id="MYSITE")
        with mock.patch(PATCHTARGET) as mockDp:
            self.assertFalse(dw.convert_xray_density_map("model.cif", "2fofc.cif", "fofc.cif", self.__out, self.__workDir))
            self.assertFalse(dw.convert_xray_density_map("model.cif", "2fofc.cif", "fofc.cif", None, self.__workDir))
        self.assertEqual(mockDp.return_value.cleanup.call_count, 2)

    def testEmSuccess(self) -> None:
        dw = DensityWrapper(site_id="MYSITE")
        with mock.patch(PATCHTARGET) as mockDp:
            mockDp.return_value.exp.side_effect = _touch
            ok = dw.convert_em_volume("in.map", self.__out, self.__workDir)
        self.assertTrue(ok)
        dp = mockDp.return_value
        dp.imp.assert_called_once_with("in.map")
        dp.addInput.assert_not_called()
        dp.op.assert_called_once_with("em-density-bcif")
        dp.exp.assert_called_once_with(self.__out)
        dp.cleanup.assert_called_once_with()

    def testEmNoOutput(self) -> None:
        dw = DensityWrapper(site_id="MYSITE")
        with mock.patch(PATCHTARGET):
            self.assertFalse(dw.convert_em_volume("in.map", self.__out, self.__workDir))
            self.assertFalse(dw.convert_em_volume("in.map", "", self.__workDir))

    def testMainEm(self) -> None:
        argv = ["DensityWrapper.py", "--em_map", "in.map", "--binary_map_out", self.__out, "--debug"]
        with mock.patch.object(sys, "argv", argv), mock.patch("wwpdb.utils.dp.DensityWrapper.DensityWrapper") as mockDw:
            DensityWrapperModule.main()
        conv = mockDw.return_value.convert_em_volume
        conv.assert_called_once()
        kwargs = conv.call_args[1]
        self.assertEqual(kwargs["in_em_volume"], "in.map")
        self.assertEqual(kwargs["out_binary_volume"], self.__out)
        # Temporary working directory removed after use
        self.assertFalse(os.path.exists(kwargs["working_dir"]))
        self.assertEqual(logger.level, logging.DEBUG)

    def testMainNoEm(self) -> None:
        argv = ["DensityWrapper.py", "--binary_map_out", self.__out]
        with mock.patch.object(sys, "argv", argv), mock.patch("wwpdb.utils.dp.DensityWrapper.DensityWrapper") as mockDw:
            DensityWrapperModule.main()
        mockDw.return_value.convert_em_volume.assert_not_called()

    def testMainMissingRequired(self) -> None:
        err = io.StringIO()
        with mock.patch.object(sys, "argv", ["DensityWrapper.py"]), contextlib.redirect_stderr(err), self.assertRaises(SystemExit):
            DensityWrapperModule.main()
        self.assertIn("--binary_map_out", err.getvalue())


if __name__ == "__main__":
    unittest.main()
