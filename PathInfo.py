##
# File:  PathInfo.py
# Date:  25-Feb-2013
#
# Updated:
#  26-Feb-2013  jdw   implement new session storage options in DataFileReference()
#  28-Feb-2013  jdw   move to generic path wwpdb.utils.rcsb.PathInfo()
#  28-Feb-2013  jdw   Add wrappers for more general purpose methods -  
#  04-Apr-2013  jdw   Add assembly assignment and map convenience methods
#  27-Aug-2013  jdw   Add optional parameters for content milestone variants [upload,deposit,annotate,...] 
## 
"""
Common methods for finding path information resource and data files in the wwPDB data processing
and annotation system.

"""
__docformat__ = "restructuredtext en"
__author__    = "John Westbrook"
__email__     = "jwest@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.07"

import sys, os, os.path
from wwpdb.api.facade.DataReference  import DataFileReference

class PathInfo(object):
    """ Common methods for finding path information for sequence resources and data files.

        In these methods the parameter contentType refers to a base content type. 

        The mileStone parameter is used to select the milestone variant in any convenience methods
        (e.g. model-deposit, model-upload, ... )

    """    
    def __init__(self, siteId="WWPDB_DEPLOY_TEST", sessionPath='.', verbose=False, log=sys.stderr):
        """ 
        """
        self.__verbose=verbose
        self.__lfh=log
        self.__debug=False
        self.__siteId=siteId
        self.__sessionPath = sessionPath
        #
    def setSessionPath(self,sessionPath):
        """  Set the top path that will be searched for files with fileSource='session'
        """
        self.__sessionPath=sessionPath
        
    def getModelPdbxFilePath(self,dataSetId,wfInstanceId=None,fileSource="archive",versionId="latest",mileStone=None):
        return self.__getStandardPath(dataSetId=dataSetId,
                                      wfInstanceId=wfInstanceId,
                                      fileSource=fileSource,
                                      versionId=versionId,
                                      contentTypeBase='model',
                                      formatType='pdbx',
                                      mileStone=mileStone)
    
    def getModelPdbFilePath(self,dataSetId,wfInstanceId=None,fileSource="archive",versionId="latest",mileStone=None):
        return self.__getStandardPath(dataSetId=dataSetId,
                                      wfInstanceId=wfInstanceId,
                                      fileSource=fileSource,
                                      versionId=versionId,
                                      contentTypeBase='model',
                                      formatType='pdb',
                                      mileStone=mileStone)
    
    def getPolyLinkFilePath(self,dataSetId,wfInstanceId=None,fileSource="archive",versionId="latest",mileStone=None):
        return self.__getStandardPath(dataSetId=dataSetId,
                                      wfInstanceId=wfInstanceId,
                                      fileSource=fileSource,
                                      versionId=versionId,
                                      contentTypeBase='polymer-linkage-distances',
                                      formatType='pdbx',
                                      mileStone=mileStone)

    def getSequenceStatsFilePath(self,dataSetId,wfInstanceId=None,fileSource="archive",versionId="latest",mileStone=None):
        return self.__getStandardPath(dataSetId=dataSetId,
                                      wfInstanceId=wfInstanceId,
                                      fileSource=fileSource,
                                      versionId=versionId,
                                      contentTypeBase='seq-data-stats',
                                      formatType='pic',
                                      mileStone=mileStone)


    def getSequenceAlignFilePath(self,dataSetId,wfInstanceId=None,fileSource="archive",versionId="latest",mileStone=None):
        return self.__getStandardPath(dataSetId=dataSetId,
                                      wfInstanceId=wfInstanceId,
                                      fileSource=fileSource,
                                      versionId=versionId,
                                      contentTypeBase='seq-align-data',
                                      formatType='pic',
                                      mileStone=mileStone)


    def getReferenceSequenceFilePath(self,dataSetId,entityId='1',wfInstanceId=None,fileSource="archive",versionId="latest",mileStone=None):
        return self.__getStandardPath(dataSetId=dataSetId,
                                      wfInstanceId=wfInstanceId,
                                      fileSource=fileSource,
                                      versionId=versionId,
                                      partNumber=entityId,
                                      contentTypeBase='seqdb-match',
                                      formatType='pdbx',
                                      mileStone=mileStone)

    def getSequenceAssignmentFilePath(self,dataSetId,wfInstanceId=None,fileSource="archive",versionId="latest",mileStone=None):
        return self.__getStandardPath(dataSetId=dataSetId,
                                      wfInstanceId=wfInstanceId,
                                      fileSource=fileSource,
                                      versionId=versionId,
                                      contentTypeBase='seq-assign',
                                      formatType='pdbx',
                                      mileStone=mileStone)

    def getAssemblyAssignmentFilePath(self,dataSetId,wfInstanceId=None,fileSource="archive",versionId="latest",mileStone=None):
        return self.__getStandardPath(dataSetId=dataSetId,
                                      wfInstanceId=wfInstanceId,
                                      fileSource=fileSource,
                                      versionId=versionId,
                                      contentTypeBase='assembly-assign',
                                      formatType='pdbx',
                                      mileStone=mileStone)

    def getBlastMatchFilePath(self,entityId,entityPart='1',wfInstanceId=None,fileSource="archive",versionId="latest",mileStone=None):
        return self.__getStandardPath(dataSetId=entityId,
                                      wfInstanceId=wfInstanceId,
                                      fileSource=fileSource,
                                      versionId=versionId,
                                      partNumber=entityPart,
                                      contentTypeBase='blast-match',
                                      formatType='xml',
                                      mileStone=mileStone)

    def getMap2fofcFilePath(self,entityId,entityPart='1',wfInstanceId=None,fileSource="archive",versionId="latest",mileStone=None):
        return self.__getStandardPath(dataSetId=entityId,
                                      wfInstanceId=wfInstanceId,
                                      fileSource=fileSource,
                                      versionId=versionId,
                                      partNumber=entityPart,
                                      contentTypeBase='map-2fofc',
                                      formatType='map',
                                      mileStone=mileStone)

    def getMapfofcFilePath(self,entityId,entityPart='1',wfInstanceId=None,fileSource="archive",versionId="latest",mileStone=None):
        return self.__getStandardPath(dataSetId=entityId,
                                      wfInstanceId=wfInstanceId,
                                      fileSource=fileSource,
                                      versionId=versionId,
                                      partNumber=entityPart,
                                      contentTypeBase='map-fofc',
                                      formatType='map',
                                      mileStone=mileStone)


    #
    def getFilePath(self,dataSetId,wfInstanceId=None,contentType=None,formatType=None,fileSource="archive",versionId="latest",partNumber='1',mileStone=None):
        return self.__getStandardPath(dataSetId=dataSetId,
                                      wfInstanceId=wfInstanceId,
                                      contentTypeBase=contentType,
                                      formatType=formatType,
                                      fileSource=fileSource,
                                      versionId=versionId,
                                      partNumber=partNumber,
                                      mileStone=mileStone)

    #
    def getFileName(self,dataSetId,wfInstanceId=None,contentType=None,formatType=None,fileSource="archive",versionId="latest",partNumber='1',mileStone=None):
        return os.path.basename(self.__getStandardPath(dataSetId=dataSetId,
                                                       wfInstanceId=wfInstanceId,
                                                       contentTypeBase=contentType,
                                                       formatType=formatType,
                                                       fileSource=fileSource,
                                                       versionId=versionId,
                                                       partNumber=partNumber,
                                                       mileStone=mileStone))
        
    def getDirPath(self,dataSetId,wfInstanceId=None,contentType=None,formatType=None,fileSource="archive",versionId="latest",partNumber='1',mileStone=None):
        return os.path.dirname(self.__getStandardPath(dataSetId=dataSetId,
                                                      wfInstanceId=wfInstanceId,
                                                      contentTypeBase=contentType,
                                                      formatType=formatType,
                                                      fileSource=fileSource,
                                                      versionId=versionId,
                                                      partNumber=partNumber,
                                                      mileStone=mileStone))
    


    def getcopyContentType(self,sourcePath,sourcePattern,destPath):
        fpattern=os.path.join(sourcePath,sourcePattern)
        pthList=[]        
        pthList=glob.glob(fpattern)        
        #
        fileList=[]
        for pth in pthList:
            (dirName,fileName)=os.path.split(pth)
            fileList.append(fileName)
            shutil.copyfile(pth,os.path.join(destPath,fileName))
        return fileList

    def __getStandardPath(self,dataSetId,wfInstanceId=None,contentTypeBase=None,formatType=None,fileSource="archive",versionId="latest",partNumber='1',mileStone=None):
        """   Get WF conforming path/file names.
        """                
        #
        if mileStone is not None:
            contentType = contentTypeBase + '-' + mileStone
        else:
            contentType = contentTypeBase
        #
        retPath=None
        if (fileSource in ['archive','wf-archive']):
            dfRef=DataFileReference(siteId=self.__siteId,verbose=self.__verbose,log=self.__lfh)
            dfRef.setDepositionDataSetId(dataSetId)
            dfRef.setStorageType('archive')
            dfRef.setContentTypeAndFormat(contentType,formatType)
            dfRef.setPartitionNumber(partNumber)
            dfRef.setVersionId(versionId)
        elif (fileSource =='wf-instance'):
            dfRef=DataFileReference(siteId=self.__siteId,verbose=self.__verbose,log=self.__lfh)
            dfRef.setDepositionDataSetId(dataSetId)
            dfRef.setWorkflowInstanceId(wfInstanceId)
            dfRef.setStorageType('wf-instance')
            dfRef.setContentTypeAndFormat(contentType,formatType)
            dfRef.setPartitionNumber(partNumber)
            dfRef.setVersionId(versionId) 
        elif (fileSource in ['session','wf-session']):
            dfRef=DataFileReference(siteId=self.__siteId,verbose=self.__verbose,log=self.__lfh)
            dfRef.setSessionPath(self.__sessionPath)
            dfRef.setSessionDataSetId(dataSetId)
            dfRef.setStorageType('session')
            dfRef.setContentTypeAndFormat(contentType,formatType)
            dfRef.setPartitionNumber(partNumber)
            dfRef.setVersionId(versionId)

        else:
            self.__lfh.write("+PathInfo.__getStandardPath() bad file source %s for id %s wf id %s\n" % (fileSource,dataSetId,wfInstanceId))
            return retPath

        if (dfRef.isReferenceValid()):                  
            dP=dfRef.getDirPathReference()
            fP=dfRef.getFilePathReference()
            retPath=fP
            if (self.__debug):                
                self.__lfh.write("+PathInfo.__getStandardPath() directory path: %s\n" % dP)
                self.__lfh.write("+PathInfo.__getStandardPath() file path:      %s\n" % fP)
        else:
            self.__lfh.write("+PathInfo.__getStandardPath() invalid file path for %s for id %s wf id %s\n" % (fileSource,dataSetId,wfInstanceId))

        #
        return retPath
