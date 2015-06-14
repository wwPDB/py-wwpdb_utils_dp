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
        self.__milestoneL = []
        self.__milestoneL.append(None)
        self.__milestoneL.extend(self.__cI.get('CONTENT_MILESTONE_LIST'))
        self.__cTBD = self.__cI.get('CONTENT_TYPE_BASE_DICTIONARY')
        self.__cTD = self.__cI.get('CONTENT_TYPE_DICTIONARY')
        self.__cTL = sorted(self.__cTBD.keys())
        self.__cTypesOtherL = ['assembly-assign',
                               'assembly-model',
                               'assembly-model-xyz',
                               'assembly-report',
                               'chem-comp-assign',
                               'chem-comp-assign-details',
                               'chem-comp-assign-final',
                               'chem-comp-depositor-info',
                               'chem-comp-link',
                               'component-image',
                               'dcc-report',
                               'dict-check-report',
                               'dict-check-report-r4',
                               'format-check-report',
                               'geometry-check-report',
                               'merge-xyz-report',
                               'misc-check-report',
                               'notes-from-annotator',
                               'polymer-linkage-distances',
                               'polymer-linkage-report',
                               'secondary-structure-topology',
                               'seq-align-data',
                               'seq-assign',
                               'seq-data-stats',
                               'seqdb-match',
                               'sequence-fasta',
                               'sf-convert-report',
                               'site-assign',
                               'special-position-report',
                               'validation-data',
                               'validation-report',
                               'validation-report-depositor',
                               'validation-report-full',
                               'validation-report-slider'
                               ]

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

    def __getPurgeInfo(self, purgeType='exp'):
        ''' Return the list of content type data to be purged -

            return [{fileSource,contentType,formatType,mileStone,purgeType},]
        '''
        rL = []
        if purgeType in ['exp']:
            for ct in ['model']:
                for fs in ['archive', 'deposit']:
                    for fm in ['pdbx', 'pdb']:
                        for milestone in self.__milestoneL:
                            rL.append({'fileSource': fs, 'contentType': ct, 'formatType': fm, 'mileStone': milestone, 'purgeType': 'exp'})
            for ct in ['structure-factors']:
                for fs in ['archive', 'deposit']:
                    for fm in ['pdbx', 'mtz']:
                        for milestone in self.__milestoneL:
                            rL.append({'fileSource': fs, 'contentType': ct, 'formatType': fm, 'mileStone': milestone, 'purgeType': 'exp'})
        elif purgeType in ['other', 'report']:
            for ct in self.__cTypesOtherL:
                for fs in ['archive', 'deposit']:
                    for fm in self.__cTD[ct][0]:
                        for milestone in self.__milestoneL:
                            rL.append({'fileSource': fs, 'contentType': ct, 'formatType': fm, 'mileStone': milestone, 'purgeType': 'other'})
        return rL

    def testPurgeProductionList(self):
        """
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            idList = self.__getIdList(self.__idList)
            dm = DataMaintenance(siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            for id in idList:
                for pType in ['exp', 'other']:
                    pTL = self.__getPurgeInfo(purgeType=pType)
                    for pT in pTL:
                        latest, rmL, gzL = dm.getPurgeCandidates(id,
                                                                 wfInstanceId=None,
                                                                 fileSource=pT['fileSource'],
                                                                 contentType=pT['contentType'],
                                                                 formatType=pT['formatType'],
                                                                 partitionNumber='1',
                                                                 mileStone=pT['mileStone'],
                                                                 purgeType=pT['purgeType'])
                        if latest is None:
                            continue
                        self.__lfh.write("\n+testPurgeCandidatesList - id %13s cType %s LATEST version %s\n" % (id, pT['contentType'], latest))
                        for ii, p in enumerate(rmL):
                            self.__lfh.write("+testPurgeCandidateList- %4d  rm - %r\n" % (ii, p))
                        for ii, p in enumerate(gzL):
                            self.__lfh.write("+testPurgeCandidateList- %4d  gz - %r\n" % (ii, p))
        except:
            traceback.print_exc(file=sys.stdout)
            self.fail()

    def testPurgeCandidatesList(self):
        """
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            idList = self.__getIdList(self.__idList)
            dm = DataMaintenance(siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            for id in idList:
                latest, rmL, gzL = dm.getPurgeCandidates(id, wfInstanceId=None, fileSource="archive",
                                                         contentType="model", formatType="pdbx", partitionNumber='1', mileStone=None)
                self.__lfh.write("\n\n+testPurgeCandidatesList - id %s LATEST version %s\n" % (id, latest))
                for ii, p in enumerate(rmL):
                    self.__lfh.write("+testPurgeCandidateList- %r  rm - %r\n" % (ii, p))
                for ii, p in enumerate(gzL):
                    self.__lfh.write("+testPurgeCandidateList- %r  gz - %r\n" % (ii, p))
            self.__lfh.write('%s\n' % '\n'.join(self.__cTL))

        except:
            traceback.print_exc(file=sys.stdout)
            self.fail()

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
                self.__lfh.write("\n\n+testVersionList- id %s file list\n" % (id))
                for ii, p in enumerate(pL):
                    self.__lfh.write("+testVersionList- %r  %r\n" % (ii, p))
        except:
            traceback.print_exc(file=sys.stdout)
            self.fail()


def suiteMiscTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(DataMaintenanceTests("testVersionList"))
    suiteSelect.addTest(DataMaintenanceTests("testPurgeCandidatesList"))
    return suiteSelect


def suiteProductionTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(DataMaintenanceTests("testPurgeProductionList"))
    return suiteSelect

if __name__ == '__main__':
    # Run all tests --
    # unittest.main()
    #
    if (False):
        mySuite = suiteMiscTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)

        mySuite = suiteProductionTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)

    mySuite = suiteProductionTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)
