##
# File:    PathInfoTests.py
# Date:    26-Feb-2013
#
# Updates:
#   27-Aug-2013  jdw verify after milestone addition to api.
#   28-Jun-2014  jdw add template examples
##
"""
Skeleton examples for creating standard file names for sequence resources and data files.

 **** A file source must be created to support these examples  ****

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"


import sys
import unittest
import traceback

from wwpdb.api.facade.ConfigInfo import getSiteId
from wwpdb.utils.rcsb.PathInfo import PathInfo


class PathInfoTests(unittest.TestCase):

    def setUp(self):
        #
        self.__verbose = True
        self.__lfh = sys.stdout
        self.__siteId = getSiteId(defaultSiteId='WWPDB_DEPLOY_TEST')

    def tearDown(self):
        pass

    def testGetStandardPaths(self):
        """ Test getting standard file names within session paths.
        """
        self.__lfh.write("\n------------------------ ")
        self.__lfh.write("Starting test function  %s" % sys._getframe().f_code.co_name)
        self.__lfh.write(" -------------------------\n")
        try:
            # fileSource, id, partionId, versionId
            tests = [('archive', "D_1000000000", None, 1, 'latest'),
                     ('archive', "D_1000000000", None, 'latest', 'latest'),
                     ('archive', "D_1000000000", None, 'next', 'latest'),
                     ('archive', "D_1000000000", None, 'previous', 'latest')]
            eId='1'
            for (fs, dataSetId, wfInst, pId, vId) in tests:
                self.__lfh.write("\n\n----------------------------------\n")
                self.__lfh.write("File source %s dataSetId %s  partno  %s wfInst %s version %s\n" % (fs, dataSetId, pId, wfInst, vId))

                pI = PathInfo(siteId=self.__siteId, sessionPath=".", verbose=self.__verbose, log=self.__lfh)
                #
                fp = pI.getModelPdbxFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
                self.__lfh.write("Model path (PDBx):   %s\n" % fp)

                fp = pI.getModelPdbxFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId, mileStone='deposit')
                self.__lfh.write("Model path (deposit) (PDBx):   %s\n" % fp)

                fp = pI.getModelPdbxFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId, mileStone='upload')
                self.__lfh.write("Model path (upload) (PDBx):   %s\n" % fp)

                fp = pI.getModelPdbFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
                self.__lfh.write("Model path (PDB):    %s\n" % fp)

                fp = pI.getPolyLinkFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
                self.__lfh.write("Link dist  (PDBx):   %s\n" % fp)

                fp = pI.getSequenceStatsFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
                self.__lfh.write("Sequence stats (PIC):   %s\n" % fp)

                fp = pI.getReferenceSequenceFilePath(dataSetId, entityId=eId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
                self.__lfh.write("Reference match entity %s (PDBx):   %s\n" % (eId, fp))

                fp = pI.getSequenceAssignmentFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
                self.__lfh.write("Sequence assignment (PDBx):   %s\n" % fp)

                fp = pI.getFilePath(dataSetId, wfInstanceId=wfInst, contentType='seqdb-match', formatType='pdbx', fileSource=fs, versionId=vId, partNumber=pId, mileStone=None)
                self.__lfh.write("Sequence match (getFilePath) (PDBx):   %s\n" % fp)
                #

                ft = pI.getFilePathVersionTemplate(dataSetId, wfInstanceId=wfInst, contentType='em-volume', formatType='map', fileSource="archive", partNumber=pId, mileStone=None)
                self.__lfh.write("EM volume version template:   %r\n" % ft)
                ft = pI.getFilePathPartitionTemplate(dataSetId, wfInstanceId=wfInst, contentType='em-mask', formatType='map', fileSource="archive", mileStone=None)
                self.__lfh.write("EM mask partition template:   %r\n" % ft)
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()


def suiteStandardPathTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(PathInfoTests("testGetStandardPaths"))
    return suiteSelect


if __name__ == '__main__':
    if (True):
        mySuite = suiteStandardPathTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)
