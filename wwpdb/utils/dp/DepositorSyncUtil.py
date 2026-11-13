import sys
import traceback
from typing import Any, Optional, TextIO

from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility


class DepositorSyncUtil:
    # reqObj is a wwpdb.utils.session request object; that package is not a dependency here
    def __init__(self, reqObj: Any = None, verbose: bool = False, log: TextIO = sys.stderr) -> None:
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        self.__sObj: Any = None
        self.__sessionId: Optional[str] = None
        self.__sessionPath: Optional[str] = None
        self.__siteId = str(self.__reqObj.getValue("WWPDB_SITE_ID"))
        self.__getSession()

    def syncWithDatabase(self, depId: str, modelFilePath: str) -> None:
        self.__lfh.write("+DepositorSyncUtil.syncWithDatabase() - syncing depositor data in %s with database for %s\n" % (modelFilePath, depId))

        try:
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.addInput(name="depId", value=depId)
            dp.addInput(name="modelFilePath", value=modelFilePath)
            dp.op("sync-depositors")
            return
        except:  # noqa: E722 pylint: disable=bare-except
            self.__lfh.write("DepositorSyncUtil::syncWithDatabase(): failing, with exception.\n")
            traceback.print_exc(file=self.__lfh)

    def __getSession(self) -> None:
        """Join existing session or create new session as required."""
        self.__sObj = self.__reqObj.newSessionObj()
        self.__sessionId = self.__sObj.getId()
        self.__sessionPath = self.__sObj.getPath()
        if self.__verbose:
            self.__lfh.write("------------------------------------------------------\n")
            self.__lfh.write("+DepositorSyncUtil.__getSession() - creating/joining session %s\n" % self.__sessionId)
            self.__lfh.write("+DepositorSyncUtil.__getSession() - session path %s\n" % self.__sessionPath)
