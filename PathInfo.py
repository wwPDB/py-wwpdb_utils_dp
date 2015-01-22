##
# File:  PathInfo.py
# Date:  25-Feb-2013  J. Westbrook
#
# Updated:
#  26-Feb-2013  jdw   implement new session storage options in DataFileReference()
#  28-Feb-2013  jdw   move to generic path wwpdb.utils.rcsb.PathInfo()
#  28-Feb-2013  jdw   Add wrappers for more general purpose methods -
#  04-Apr-2013  jdw   Add assembly assignment and map convenience methods
#  27-Aug-2013  jdw   Add optional parameters for content milestone variants [upload,deposit,annotate,...]
#  23-Dec-2013  jdw   Add support for file source 'session-download' as extension of file source session.
#  19-Apr-2014  jdw   add getPolyLinkReportFilePath()
#   9-May-2014  jdw   add entity/partition argument to getSequenceAlignFilePath()
# 25-Jun-2014   jdw   add convenience methods getEmVolumeFilePath() getEmMaskFilePath()
# 26-Jun-2014   jdw   correct parameter errors on blast-match and map methods, add omit-map methods
# 28-Jun-2014   jdw   add template methods for searching file versions and partitions
#  1-Jul-2014   jdw   fix initialization in __getPathWorker()
#  5-Jul-2014   jdw   add method getFilePathContentTypeTemplate()
#  7-Jul-2014   jdw   add method getStatusHistoryFilePath()
# 23-Aug-2014   jdw   add method getEmDepositVolumeParamsFilePath()
# 14-Sep-2014   jdw   add isValidFileName(fileName, requireVersion=True) and splitFileName(fileName)
# 24-Sep-2014   jdw   add getFileExtension(formatType)
##
"""
Common methods for finding path information for resource and data files in the wwPDB data processing
and annotation system.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import sys
import os
import os.path
import traceback
from wwpdb.api.facade.ConfigInfo import ConfigInfo
from wwpdb.api.facade.DataReference import DataFileReference, ReferenceFileComponents


class PathInfo(object):

    """ Common methods for finding path information for sequence resources and data files.

        In these methods the parameter contentType refers to a base content type.

        The mileStone parameter is used to select the milestone variant in any convenience methods
        (e.g. model-deposit, model-upload, ... )

    """

    def __init__(self, siteId="WWPDB_DEPLOY_TEST", sessionPath='.', verbose=False, log=sys.stderr):
        """
        """
        self.__verbose = verbose
        self.__lfh = log
        self.__debug = False
        self.__siteId = siteId
        self.__sessionPath = sessionPath
        self.__sessionDownloadPath = os.path.join(self.__sessionPath, "downloads")
        self.__cI = ConfigInfo(siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)

    def setDebugFlag(self, flag):
        self.__debug = flag

    def isValidFileName(self, fileName, requireVersion=True):
        """ Is the input file name project compliant ?
        """
        rfc = ReferenceFileComponents(verbose=self.__verbose, log=self.__lfh)
        if rfc.set(fileName=fileName):
            (dId, cT, cF, pN, vN) = rfc.get()
            if (requireVersion):
                if ((dId is None) or (cT is None) or (cF is None) or (pN is None) or (vN is None)):
                    return False
                else:
                    return True
            else:
                if ((dId is None) or (cT is None) or (cF is None) or (pN is None)):
                    return False
                else:
                    return True
        else:
            return False

    def getFileExtension(self, formatType):
        eD = self.__cI.get('FILE_FORMAT_EXTENSION_DICTIONARY')
        try:
            return eD[formatType]
        except:
            return None

    def splitFileName(self, fileName):
        """
        returns (depositionDataSetId, contentType, contentFormat, filePartionNumber, [versionId (int) or None])
        """
        try:
            rfc = ReferenceFileComponents(verbose=self.__verbose, log=self.__lfh)
            rfc.set(fileName=fileName)
            return rfc.get()
        except:
            return (None, None, None, None, None)

    #
    def setSessionPath(self, sessionPath):
        """  Set the top path that will be searched for files with fileSource='session'
        """
        self.__sessionPath = sessionPath
        self.__sessionDownloadPath = os.path.join(self.__sessionPath, "downloads")

    def getArchivePath(self, dataSetId):
        try:
            return os.path.join(self.__cI.get('SITE_ARCHIVE_STORAGE_PATH'), 'archive', dataSetId)
        except:
            return None

    def getInstancePath(self, dataSetId, wfInstanceId):
        try:
            return os.path.join(self.__cI.get('SITE_ARCHIVE_STORAGE_PATH'), 'workflow', dataSetId, 'instance', wfInstanceId)
        except:
            return None

    def getInstanceTopPath(self, dataSetId):
        try:
            return os.path.join(self.__cI.get('SITE_ARCHIVE_STORAGE_PATH'), 'workflow', dataSetId, 'instance')
        except:
            return None

    def getDepositPath(self, dataSetId):
        try:
            return os.path.join(self.__cI.get('SITE_ARCHIVE_STORAGE_PATH'), 'deposit', dataSetId)
        except:
            return None

    def getModelPdbxFilePath(self, dataSetId, wfInstanceId=None, fileSource="archive", versionId="latest", mileStone=None):
        return self.__getStandardPath(dataSetId=dataSetId,
                                      wfInstanceId=wfInstanceId,
                                      fileSource=fileSource,
                                      versionId=versionId,
                                      contentTypeBase='model',
                                      formatType='pdbx',
                                      mileStone=mileStone)

    def getModelPdbFilePath(self, dataSetId, wfInstanceId=None, fileSource="archive", versionId="latest", mileStone=None):
        return self.__getStandardPath(dataSetId=dataSetId,
                                      wfInstanceId=wfInstanceId,
                                      fileSource=fileSource,
                                      versionId=versionId,
                                      contentTypeBase='model',
                                      formatType='pdb',
                                      mileStone=mileStone)

    def getPolyLinkFilePath(self, dataSetId, wfInstanceId=None, fileSource="archive", versionId="latest", mileStone=None):
        return self.__getStandardPath(dataSetId=dataSetId,
                                      wfInstanceId=wfInstanceId,
                                      fileSource=fileSource,
                                      versionId=versionId,
                                      contentTypeBase='polymer-linkage-distances',
                                      formatType='pdbx',
                                      mileStone=mileStone)

    def getPolyLinkReportFilePath(self, dataSetId, wfInstanceId=None, fileSource="archive", versionId="latest", mileStone=None):
        return self.__getStandardPath(dataSetId=dataSetId,
                                      wfInstanceId=wfInstanceId,
                                      fileSource=fileSource,
                                      versionId=versionId,
                                      contentTypeBase='polymer-linkage-report',
                                      formatType='html',
                                      mileStone=mileStone)

    def getSequenceStatsFilePath(self, dataSetId, wfInstanceId=None, fileSource="archive", versionId="latest", mileStone=None):
        return self.__getStandardPath(dataSetId=dataSetId,
                                      wfInstanceId=wfInstanceId,
                                      fileSource=fileSource,
                                      versionId=versionId,
                                      contentTypeBase='seq-data-stats',
                                      formatType='pic',
                                      mileStone=mileStone)

    def getSequenceAlignFilePath(self, dataSetId, entityId='1', wfInstanceId=None, fileSource="archive", versionId="latest", mileStone=None):
        return self.__getStandardPath(dataSetId=dataSetId,
                                      wfInstanceId=wfInstanceId,
                                      fileSource=fileSource,
                                      versionId=versionId,
                                      contentTypeBase='seq-align-data',
                                      partNumber=entityId,
                                      formatType='pic',
                                      mileStone=mileStone)

    def getReferenceSequenceFilePath(self, dataSetId, entityId='1', wfInstanceId=None, fileSource="archive", versionId="latest", mileStone=None):
        return self.__getStandardPath(dataSetId=dataSetId,
                                      wfInstanceId=wfInstanceId,
                                      fileSource=fileSource,
                                      versionId=versionId,
                                      partNumber=entityId,
                                      contentTypeBase='seqdb-match',
                                      formatType='pdbx',
                                      mileStone=mileStone)

    def getSequenceAssignmentFilePath(self, dataSetId, wfInstanceId=None, fileSource="archive", versionId="latest", mileStone=None):
        return self.__getStandardPath(dataSetId=dataSetId,
                                      wfInstanceId=wfInstanceId,
                                      fileSource=fileSource,
                                      versionId=versionId,
                                      contentTypeBase='seq-assign',
                                      formatType='pdbx',
                                      mileStone=mileStone)

    def getAssemblyAssignmentFilePath(self, dataSetId, wfInstanceId=None, fileSource="archive", versionId="latest", mileStone=None):
        return self.__getStandardPath(dataSetId=dataSetId,
                                      wfInstanceId=wfInstanceId,
                                      fileSource=fileSource,
                                      versionId=versionId,
                                      contentTypeBase='assembly-assign',
                                      formatType='pdbx',
                                      mileStone=mileStone)

    def getBlastMatchFilePath(self, dataSetId, entityId='1', wfInstanceId=None, fileSource="archive", versionId="latest", mileStone=None):
        return self.__getStandardPath(dataSetId=dataSetId,
                                      wfInstanceId=wfInstanceId,
                                      fileSource=fileSource,
                                      versionId=versionId,
                                      partNumber=entityId,
                                      contentTypeBase='blast-match',
                                      formatType='xml',
                                      mileStone=mileStone)

    def getMap2fofcFilePath(self, dataSetId, wfInstanceId=None, fileSource="archive", versionId="latest", mileStone=None):
        return self.__getStandardPath(dataSetId=dataSetId,
                                      wfInstanceId=wfInstanceId,
                                      fileSource=fileSource,
                                      versionId=versionId,
                                      partNumber='1',
                                      contentTypeBase='map-2fofc',
                                      formatType='map',
                                      mileStone=mileStone)

    def getMapfofcFilePath(self, dataSetId, wfInstanceId=None, fileSource="archive", versionId="latest", mileStone=None):
        return self.__getStandardPath(dataSetId=entityId,
                                      wfInstanceId=wfInstanceId,
                                      fileSource=fileSource,
                                      versionId=versionId,
                                      partNumber='1',
                                      contentTypeBase='map-fofc',
                                      formatType='map',
                                      mileStone=mileStone)

    def getOmitMap2fofcFilePath(self, dataSetId, wfInstanceId=None, fileSource="archive", versionId="latest", mileStone=None):
        return self.__getStandardPath(dataSetId=dataSetId,
                                      wfInstanceId=wfInstanceId,
                                      fileSource=fileSource,
                                      versionId=versionId,
                                      partNumber='1',
                                      contentTypeBase='omit-map-2fofc',
                                      formatType='map',
                                      mileStone=mileStone)

    def getOmitMapfofcFilePath(self, dataSetId, wfInstanceId=None, fileSource="archive", versionId="latest", mileStone=None):
        return self.__getStandardPath(dataSetId=entityId,
                                      wfInstanceId=wfInstanceId,
                                      fileSource=fileSource,
                                      versionId=versionId,
                                      partNumber='1',
                                      contentTypeBase='omit-map-fofc',
                                      formatType='map',
                                      mileStone=mileStone)
    #

    def getEmVolumeFilePath(self, dataSetId, wfInstanceId=None, fileSource="archive", versionId="latest", mileStone=None):
        return self.__getStandardPath(dataSetId=entityId,
                                      wfInstanceId=wfInstanceId,
                                      fileSource=fileSource,
                                      versionId=versionId,
                                      partNumber='1',
                                      contentTypeBase='em-volume',
                                      formatType='map',
                                      mileStone=mileStone)

    def getEmMaskFilePath(self, dataSetId, maskNumber='1', wfInstanceId=None, fileSource="archive", versionId="latest", mileStone=None):
        return self.__getStandardPath(dataSetId=dataSetId,
                                      wfInstanceId=wfInstanceId,
                                      fileSource=fileSource,
                                      versionId=versionId,
                                      partNumber=maskNumber,
                                      contentTypeBase='em-mask',
                                      formatType='map',
                                      mileStone=mileStone)

    def getEmDepositVolumeParamsFilePath(self, dataSetId, maskNumber='1', wfInstanceId=None, fileSource="deposit", versionId="latest", mileStone=None):
        return self.__getStandardPath(dataSetId=dataSetId,
                                      wfInstanceId=wfInstanceId,
                                      fileSource=fileSource,
                                      versionId=versionId,
                                      partNumber=maskNumber,
                                      contentTypeBase='deposit-volume-params',
                                      formatType='pic',
                                      mileStone=mileStone)

    def getAuthChemcialShiftsFilePath(self, dataSetId, formatType='nmr-star', partNumber='next', wfInstanceId=None, fileSource="archive", versionId="latest", mileStone=None):
        return self.__getStandardPath(dataSetId=dataSetId,
                                      wfInstanceId=wfInstanceId,
                                      fileSource=fileSource,
                                      versionId=versionId,
                                      partNumber=partNumber,
                                      contentTypeBase='nmr-chemical-shifts-auth',
                                      formatType=formatType,
                                      mileStone=mileStone)

    def getChemcialShiftsFilePath(self, dataSetId, formatType='nmr-star', wfInstanceId=None, fileSource="archive", versionId="latest", mileStone=None):
        return self.__getStandardPath(dataSetId=dataSetId,
                                      wfInstanceId=wfInstanceId,
                                      fileSource=fileSource,
                                      versionId=versionId,
                                      partNumber='1',
                                      contentTypeBase='nmr-chemical-shifts',
                                      formatType=formatType,
                                      mileStone=mileStone)

    def getStatusHistoryFilePath(self, dataSetId, fileSource="archive", versionId="latest"):
        return self.__getStandardPath(dataSetId=dataSetId,
                                      wfInstanceId=None,
                                      fileSource=fileSource,
                                      versionId=versionId,
                                      partNumber='1',
                                      contentTypeBase='status-history',
                                      formatType='pdbx',
                                      mileStone=None)

    #
    def getFilePath(self, dataSetId, wfInstanceId=None, contentType=None, formatType=None, fileSource="archive", versionId="latest", partNumber='1', mileStone=None):
        return self.__getStandardPath(dataSetId=dataSetId,
                                      wfInstanceId=wfInstanceId,
                                      contentTypeBase=contentType,
                                      formatType=formatType,
                                      fileSource=fileSource,
                                      versionId=versionId,
                                      partNumber=partNumber,
                                      mileStone=mileStone)

    #
    def getFileName(self, dataSetId, wfInstanceId=None, contentType=None, formatType=None, fileSource="archive", versionId="latest", partNumber='1', mileStone=None):
        return os.path.basename(self.__getStandardPath(dataSetId=dataSetId,
                                                       wfInstanceId=wfInstanceId,
                                                       contentTypeBase=contentType,
                                                       formatType=formatType,
                                                       fileSource=fileSource,
                                                       versionId=versionId,
                                                       partNumber=partNumber,
                                                       mileStone=mileStone))

    def getDirPath(self, dataSetId, wfInstanceId=None, contentType=None, formatType=None, fileSource="archive", versionId="latest", partNumber='1', mileStone=None):
        return os.path.dirname(self.__getStandardPath(dataSetId=dataSetId,
                                                      wfInstanceId=wfInstanceId,
                                                      contentTypeBase=contentType,
                                                      formatType=formatType,
                                                      fileSource=fileSource,
                                                      versionId=versionId,
                                                      partNumber=partNumber,
                                                      mileStone=mileStone))

    def getWebDownloadPath(self, dataSetId, wfInstanceId=None, contentType=None, formatType=None, versionId="latest", partNumber='1', mileStone=None):
        fn = os.path.basename(self.__getStandardPath(dataSetId=dataSetId,
                                                     wfInstanceId=wfInstanceId,
                                                     contentTypeBase=contentType,
                                                     formatType=formatType,
                                                     fileSource='session-download',
                                                     versionId=versionId,
                                                     partNumber=partNumber,
                                                     mileStone=mileStone))
        (p, sId) = os.path.split(self.__sessionPath)
        return os.path.join('/sessions', sId, 'downloads', fn)

    def getFilePathVersionTemplate(self, dataSetId, wfInstanceId=None, contentType=None, formatType=None, fileSource="archive", partNumber='1', mileStone=None):
        fp, vt, pt, cct = self.__getPathWorker(dataSetId=dataSetId,
                                               wfInstanceId=wfInstanceId,
                                               contentTypeBase=contentType,
                                               formatType=formatType,
                                               fileSource=fileSource,
                                               versionId='none', partNumber=partNumber, mileStone=mileStone)
        return vt

    def getFilePathPartitionTemplate(self, dataSetId, wfInstanceId=None, contentType=None, formatType=None, fileSource="archive", mileStone=None):
        fp, vt, pt, cct = self.__getPathWorker(dataSetId=dataSetId,
                                               wfInstanceId=wfInstanceId,
                                               contentTypeBase=contentType,
                                               formatType=formatType,
                                               fileSource=fileSource,
                                               versionId='none',
                                               partNumber='1',
                                               mileStone=mileStone)
        return pt

    def getFilePathContentTypeTemplate(self, dataSetId, wfInstanceId=None, contentType=None, fileSource="archive"):
        fp, vt, pt, cct = self.__getPathWorker(dataSetId=dataSetId,
                                               wfInstanceId=wfInstanceId,
                                               contentTypeBase=contentType,
                                               formatType='any',
                                               fileSource=fileSource,
                                               versionId='none',
                                               partNumber='1',
                                               mileStone=None)
        return cct

    def __getStandardPath(self, dataSetId, wfInstanceId=None, contentTypeBase=None, formatType=None, fileSource="archive", versionId="latest", partNumber='1', mileStone=None):
        try:
            fP, vT, pT, ccT = self.__getPathWorker(dataSetId=dataSetId,
                                                   wfInstanceId=wfInstanceId,
                                                   contentTypeBase=contentTypeBase,
                                                   formatType=formatType,
                                                   fileSource=fileSource,
                                                   versionId=versionId,
                                                   partNumber=partNumber,
                                                   mileStone=mileStone)
        except:
            self.__lfh.write("+PathInfo.__getStandard() failing for %s id %s wf id %s\n" % (fileSource, dataSetId, wfInstanceId))
            traceback.print_exc(file=self.__lfh)
        return fP

    def __getPathWorker(self, dataSetId, wfInstanceId=None, contentTypeBase=None, formatType=None, fileSource="archive", versionId="latest", partNumber='1', mileStone=None):
        """   Return the path and templates corresponding to the input file typing arguments.

              Return:  <full file path>,<file path as a version template>,<file path as a partition template>
        """
        #
        try:
            if mileStone is not None:
                contentType = contentTypeBase + '-' + mileStone
            else:
                contentType = contentTypeBase
                #
            if (self.__debug):
                self.__lfh.write("+PathInfo.__getPathworker() file source %s for id %s wf id %s contentType %r formatType %r partNumber %r versionId %r\n" %
                                 (fileSource, dataSetId, wfInstanceId, contentType, formatType, partNumber, versionId))
            dfRef = DataFileReference(siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            if (fileSource in ['archive', 'wf-archive']):
                dfRef.setDepositionDataSetId(dataSetId)
                dfRef.setStorageType('archive')
                dfRef.setContentTypeAndFormat(contentType, formatType)
                dfRef.setPartitionNumber(partNumber)
                dfRef.setVersionId(versionId)
            elif (fileSource in ['deposit']):
                dfRef.setDepositionDataSetId(dataSetId)
                dfRef.setStorageType('deposit')
                dfRef.setContentTypeAndFormat(contentType, formatType)
                dfRef.setPartitionNumber(partNumber)
                dfRef.setVersionId(versionId)
            elif (fileSource == 'wf-instance'):
                dfRef.setDepositionDataSetId(dataSetId)
                dfRef.setWorkflowInstanceId(wfInstanceId)
                dfRef.setStorageType('wf-instance')
                dfRef.setContentTypeAndFormat(contentType, formatType)
                dfRef.setPartitionNumber(partNumber)
                dfRef.setVersionId(versionId)
            elif (fileSource in ['session', 'wf-session']):
                dfRef.setSessionPath(self.__sessionPath)
                dfRef.setSessionDataSetId(dataSetId)
                dfRef.setStorageType('session')
                dfRef.setContentTypeAndFormat(contentType, formatType)
                dfRef.setPartitionNumber(partNumber)
                dfRef.setVersionId(versionId)

            elif (fileSource in ['session-download']):
                dfRef.setSessionPath(self.__sessionDownloadPath)
                dfRef.setSessionDataSetId(dataSetId)
                dfRef.setStorageType('session')
                dfRef.setContentTypeAndFormat(contentType, formatType)
                dfRef.setPartitionNumber(partNumber)
                dfRef.setVersionId(versionId)
            else:
                self.__lfh.write("+PathInfo.__getPathworker() bad file source %s for id %s wf id %s contentType %r \n" %
                                 (fileSource, dataSetId, wfInstanceId, contentType))
                return None, None, None, None

            fP = None
            vT = None
            pT = None
            ctT = None
            if (dfRef.isReferenceValid()):
                fP = dfRef.getFilePathReference()
                dP = dfRef.getDirPathReference()
                pT = os.path.join(dP, dfRef.getPartitionNumberSearchTarget())
                vT = os.path.join(dP, dfRef.getVersionIdSearchTarget())
                ctT = os.path.join(dP, dfRef.getContentTypeSearchTarget())
                if (self.__debug):
                    self.__lfh.write("+PathInfo.__getPathworker() file path:                %s\n" % fP)
                    self.__lfh.write("+PathInfo.__getPathworker() partition search path:    %s\n" % pT)
                    self.__lfh.write("+PathInfo.__getPathworker() version search path:      %s\n" % vT)
                    self.__lfh.write("+PathInfo.__getPathworker() content type search path: %s\n" % ctT)
            else:
                dP = dfRef.getDirPathReference()
                ctT = os.path.join(dP, dfRef.getContentTypeSearchTarget())
                if (self.__debug):
                    self.__lfh.write("+PathInfo.__getPathworker() content type search path: %s\n" % ctT)
                #
            return fP, vT, pT, ctT
        except:
            if self.__verbose:
                self.__lfh.write("+PathInfo.__getPathWorker() failing for source %s id %s wf id %s contentType %r\n" %
                                 (fileSource, dataSetId, wfInstanceId, contentType))
                traceback.print_exc(file=self.__lfh)
            return None, None, None, None

    ###
    def __getcopyContentType(self, sourcePath, sourcePattern, destPath):
      """  internal method  -- not used --
      """
        fpattern = os.path.join(sourcePath, sourcePattern)
        pthList = []
        pthList = glob.glob(fpattern)
        #
        fileList = []
        for pth in pthList:
            (dirName, fileName) = os.path.split(pth)
            fileList.append(fileName)
            shutil.copyfile(pth, os.path.join(destPath, fileName))
        return fileList
