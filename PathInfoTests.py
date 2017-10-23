##
# File:    PathInfoTests.py
# Date:    26-Feb-2013
#
# Updates:
#   27-Aug-2013  jdw verify after milestone addition to api.
#   28-Jun-2014  jdw add template examples
#   23-Oct-2017  jdw update logging
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


import time
import unittest

from wwpdb.api.facade.ConfigInfo import getSiteId
from wwpdb.utils.rcsb.PathInfo import PathInfo

import logging
FORMAT = '[%(levelname)s]-%(module)s.%(funcName)s: %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger()


class PathInfoTests(unittest.TestCase):

    def setUp(self):
        #
        self.__verbose = True
        self.__siteId = getSiteId(defaultSiteId=None)

        self.__startTime = time.time()
        logger.debug("Starting %s at %s" % (self.id(),
                                            time.strftime("%Y %m %d %H:%M:%S", time.localtime())))

    def tearDown(self):
        endTime = time.time()
        logger.debug("Completed %s at %s (%.4f seconds)\n" % (self.id(),
                                                              time.strftime("%Y %m %d %H:%M:%S", time.localtime()),
                                                              endTime - self.__startTime))

    def testGetStandardPaths(self):
        """ Test getting standard file names within session paths.
        """
        ok = True
        try:
            # fileSource, id, partionId, versionId
            tests = [('archive', "D_1000000000", None, 1, 'latest'),
                     ('archive', "D_1000000000", None, 'latest', 'latest'),
                     ('archive', "D_1000000000", None, 'next', 'latest'),
                     ('archive', "D_1000000000", None, 'previous', 'latest')]
            eId = '1'
            for (fs, dataSetId, wfInst, pId, vId) in tests:
                logger.debug("File source %s dataSetId %s  partno  %s wfInst %s version %s" % (fs, dataSetId, pId, wfInst, vId))

                pI = PathInfo(siteId=self.__siteId, sessionPath=".")
                #
                fp = pI.getModelPdbxFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
                logger.debug("Model path (PDBx):   %s" % fp)

                fp = pI.getModelPdbxFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId, mileStone='deposit')
                logger.debug("Model path (deposit) (PDBx):   %s" % fp)

                fp = pI.getModelPdbxFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId, mileStone='upload')
                logger.debug("Model path (upload) (PDBx):   %s" % fp)

                fp = pI.getModelPdbFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
                logger.debug("Model path (PDB):    %s" % fp)

                fp = pI.getPolyLinkFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
                logger.debug("Link dist  (PDBx):   %s" % fp)

                fp = pI.getSequenceStatsFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
                logger.debug("Sequence stats (PIC):   %s" % fp)

                fp = pI.getReferenceSequenceFilePath(dataSetId, entityId=eId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
                logger.debug("Reference match entity %s (PDBx):   %s" % (eId, fp))

                fp = pI.getSequenceAssignmentFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
                logger.debug("Sequence assignment (PDBx):   %s" % fp)

                fp = pI.getFilePath(dataSetId, wfInstanceId=wfInst, contentType='seqdb-match', formatType='pdbx', fileSource=fs, versionId=vId, partNumber=pId, mileStone=None)
                logger.debug("Sequence match (getFilePath) (PDBx):   %s" % fp)
                #

                ft = pI.getFilePathVersionTemplate(dataSetId, wfInstanceId=wfInst, contentType='em-volume', formatType='map', fileSource="archive", partNumber=pId, mileStone=None)
                logger.debug("EM volume version template:   %r" % ft)
                ft = pI.getFilePathPartitionTemplate(dataSetId, wfInstanceId=wfInst, contentType='em-mask-volume', formatType='map', fileSource="archive", mileStone=None)
                logger.debug("EM mask partition template:   %r" % ft)
            self.assertEqual(ok, True)
        except Exception as e:
            logger.exception("Failing with %r" % str(e))
            self.fail()


def suiteStandardPathTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(PathInfoTests("testGetStandardPaths"))
    return suiteSelect


if __name__ == '__main__':
    if (True):
        mySuite = suiteStandardPathTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)
