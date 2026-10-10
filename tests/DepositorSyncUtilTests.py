##
# File:    DepositorSyncUtilTests.py
#
##
"""
Hermetic tests for DepositorSyncUtil - RcsbDpUtility is mocked
"""

import io
import logging
import unittest
from unittest import mock

if __package__ is None or __package__ == "":
    import sys
    from os import path

    sys.path.append(path.dirname(path.abspath(__file__)))
    from commonsetup import TESTOUTPUT  # pylint: disable=import-error,unused-import  # noqa: F401
else:
    from .commonsetup import TESTOUTPUT  # noqa: F401  # pylint: disable=unused-import

from wwpdb.utils.dp.DepositorSyncUtil import DepositorSyncUtil

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class DepositorSyncUtilTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__sObj = mock.Mock()
        self.__sObj.getId.return_value = "sess123"
        self.__sObj.getPath.return_value = "/some/session/path"
        self.__reqObj = mock.Mock()
        self.__reqObj.getValue.return_value = "TESTSITE"
        self.__reqObj.newSessionObj.return_value = self.__sObj

    def testInitVerbose(self) -> None:
        lfh = io.StringIO()
        DepositorSyncUtil(reqObj=self.__reqObj, verbose=True, log=lfh)
        self.__reqObj.getValue.assert_called_once_with("WWPDB_SITE_ID")
        self.__reqObj.newSessionObj.assert_called_once_with()
        out = lfh.getvalue()
        self.assertIn("creating/joining session sess123", out)
        self.assertIn("session path /some/session/path", out)

    def testInitQuiet(self) -> None:
        lfh = io.StringIO()
        DepositorSyncUtil(reqObj=self.__reqObj, verbose=False, log=lfh)
        self.assertEqual(lfh.getvalue(), "")

    def testSync(self) -> None:
        lfh = io.StringIO()
        with mock.patch("wwpdb.utils.dp.DepositorSyncUtil.RcsbDpUtility") as mdp:
            dsu = DepositorSyncUtil(reqObj=self.__reqObj, verbose=True, log=lfh)
            dsu.syncWithDatabase("D_1000000001", "/path/model.cif")

        mdp.assert_called_once_with(tmpPath="/some/session/path", siteId="TESTSITE", verbose=True, log=lfh)
        inst = mdp.return_value
        inst.addInput.assert_has_calls([mock.call(name="depId", value="D_1000000001"), mock.call(name="modelFilePath", value="/path/model.cif")])
        inst.op.assert_called_once_with("sync-depositors")
        self.assertIn("syncing depositor data in /path/model.cif with database for D_1000000001", lfh.getvalue())
        self.assertNotIn("failing", lfh.getvalue())

    def testSyncFailure(self) -> None:
        lfh = io.StringIO()
        with mock.patch("wwpdb.utils.dp.DepositorSyncUtil.RcsbDpUtility") as mdp:
            mdp.return_value.op.side_effect = RuntimeError("boom")
            dsu = DepositorSyncUtil(reqObj=self.__reqObj, verbose=False, log=lfh)
            # Must not raise
            dsu.syncWithDatabase("D_1", "/m.cif")
        out = lfh.getvalue()
        self.assertIn("failing, with exception", out)
        self.assertIn("RuntimeError: boom", out)


if __name__ == "__main__":
    unittest.main()
