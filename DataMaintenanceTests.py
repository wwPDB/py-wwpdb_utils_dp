"""

File:    DataMaintenanceTests.py
Author:  jdw
Date:    13-June-2015
Version: 0.001

"""
import sys
import unittest
import os
import os.path
import traceback

from wwpdb.api.facade.ConfigInfo import ConfigInfo, getSiteId
from wwpdb.utils.rcsb.DataFile import DataFile
from wwpdb.utils.rcsb.DataMaintenance import DataMaintenance


class DataMaintenanceTests(unittest.TestCase):

    def setUp(self):
        self.__lfh = sys.stderr
        self.__verbose = True
        self.__siteId = getSiteId(defaultSiteId='WWPDB_DEPLOY_TEST')
        self.__lfh.write("\nTesting with site environment for:  %s\n" % self.__siteId)
        self.__cI = ConfigInfo(self.__siteId)
        # must be set --
        self.__idList = "RELEASED.LIST"

    def tearDown(self):
        pass

    def __getIdList(self, fPath):
        ifh = open(fPath, 'r')
        fL = []
        #  D_10 00 00 00 01
        for line in ifh:
            tId = line[:-1]
            if len(tId) == 12 and tId.startswith("D_"):
                fL.append(tId)
        ifh.close()
        return fL

    def testVersionList(self):
        """
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            idList = self.__getIdList(self.__idList)
            dm = DataMaintenance(siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            for id in idList:
                pL = dm.getVersionFileList(id, wfInstanceId=None, fileSource="archive",
                                           contentType="model", formatType="pdbx", partitionNumber='1', mileStone=None)
                self.__lfh.write("+testVersionList- id %s file list\n" % (id))
                for ii, p in enumerate(pL):
                    self.__lfh.write("+testVersionList- %r  %r\n" % (ii, p))
        except:
            traceback.print_exc(file=sys.stdout)
            self.fail()


def suiteMiscTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(DataMaintenanceTests("testVersionList"))
    return suiteSelect


if __name__ == '__main__':
    # Run all tests --
    # unittest.main()
    #
    mySuite = suiteMiscTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)
