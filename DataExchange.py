##
# File:  DataExchange.py
# Date:  19-Sep-2012
#
# Updates:
#
#  28-Feb-2013 jdw incorporate PathInfo() class
#  05-Mar-2013 jdw fetch() should not strip version information for output files.
#  08-Mar-2013 jdw add method to separately set path for 'session' storage.
##
"""
Import and export annotation data files between session and workflow storage.
     
"""
__docformat__ = "restructuredtext en"
__author__    = "John Westbrook"
__email__     = "jwest@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.09"

import sys, os, string, shutil, traceback, glob

from wwpdb.api.facade.ConfigInfo              import ConfigInfo
from wwpdb.api.facade.DataReference           import DataFileReference
from wwpdb.utils.rcsb.PathInfo                import PathInfo

class DataExchange(object):
    """
     This class encapsulates all of the data exchange operations
     required to move data annotation data files between session
     and workflow storage.     
     
    """
    def __init__(self,reqObj=None, depDataSetId=None, wfInstanceId=None, fileSource='archive', verbose=False,log=sys.stderr):

        self.__reqObj=reqObj
        self.__depDataSetId=depDataSetId
        self.__wfInstanceId=wfInstanceId        
        self.__fileSource=fileSource
        self.__verbose=verbose        
        self.__lfh=log
        #
        self.__debug=False        
        #
        self.__sessionObj  = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sessionObj.getPath()
        self.__siteId=self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__cI = ConfigInfo(self.__siteId)

        
        #
        if (self.__verbose):
            self.__lfh.write("+DataExchange.__setup() - session id   %s\n" % (self.__sessionObj.getId()))
            self.__lfh.write("+DataExchange.__setup() - session path %s\n" % (self.__sessionObj.getPath()))
            
            self.__lfh.write("+DataExchange.__setup() - data set %s  instance %s file source %s\n" %
                             (self.__depDataSetId, self.__wfInstanceId,self.__fileSource))


    def setInputSessionPath(self,inputSessionPath=None):
        """  Override the path to files with fileSource="session"
        """
        self.__inputSessionPath=inputSessionPath

    def purgeLogs(self):
        archivePath=self.__cI.get('SITE_ARCHIVE_STORAGE_PATH')
        dirPath=os.path.join(archivePath,'archive',self.__depDataSetId,'log')
        if self.__verbose:
            self.__lfh.write("+DataExchange.purgeLogs() - purging logs in directory  %s\n" % (dirPath))

        if (os.access(dirPath,os.W_OK)):
            fpattern=os.path.join(dirPath,"*log")
            if self.__verbose:
                self.__lfh.write("+DataExchange.purgeLogs() - purging pattern is %s\n" % (fpattern))
            
            pthList=glob.glob(fpattern)
            if self.__verbose:
                self.__lfh.write("+DataExchange.purgeLogs() candidate path length is %d\n" % len(pthList))
            #
            for pth in pthList:
                try:
                    os.remove(pth)
                except:
                    pass
            #
        return pthList

    def reversePurge(self,contentType,formatType="pdbx",partitionNumber=1):
        fn=self.__getArchiveFileName(contentType=contentType,formatType=formatType,version="none",partitionNumber=partitionNumber)

        archivePath=self.__cI.get('SITE_ARCHIVE_STORAGE_PATH')
        dirPath=os.path.join(archivePath,'archive',self.__depDataSetId)
        if self.__verbose:
            self.__lfh.write("+DataExchange.__setup() - purging in directory  %s\n" % (dirPath))

        if len(dirPath) < 2:
            return []
        fpattern=os.path.join(dirPath,fn+".V*")
        if self.__verbose:
            self.__lfh.write("+DataExchange.__setup() - purging pattern is %s\n" % (fpattern))
            
        pthList=glob.glob(fpattern)
        if self.__verbose:
            self.__lfh.write("+DataExchange.__reversePurge() candidate length is %d\n" % len(pthList))
        #
        fList=[]
        for pth in pthList:
            if not pth.endswith(".V1"):
                fList.append(pth)

        for pth in fList:
            try:
                os.remove(pth)
            except:
                pass
            #
        return fList

            
    def removeWorkflowDir(self):
        if ((self.__depDataSetId is not None) and self.__depDataSetId.startswith("D_") and (len(self.__depDataSetId) > 7)):
            workflowPath=self.__cI.get('SITE_WORKFLOW_STORAGE_PATH')
            dirPath=os.path.join(workflowPath,'workflow',self.__depDataSetId)
            if (os.access(dirPath,os.W_OK)):            
                shutil.rmtree(dirPath)
                return True
            else:
                return False
        else:
            return False
            
           
            
    def createArchiveDir(self,purgeFlag=True):
        """ Create new the archive directory if this is needed.

        """

        if (self.__verbose):
            self.__lfh.write("+DataExchange.export() creating archive directory for data set %s\n" % self.__depDataSetId)

        try:
            archivePath=self.__cI.get('SITE_ARCHIVE_STORAGE_PATH')
            dirPath=os.path.join(archivePath,'archive',self.__depDataSetId)
            
            if (not os.access(dirPath,os.W_OK)):
                if (self.__verbose):
                    self.__lfh.write("+DataExchange.createArchiveDir() creating archive directory path %s\n" % dirPath)
                os.makedirs(dirPath)
                return True                
            else:
                if purgeFlag:
                    if (self.__verbose):
                        self.__lfh.write("+DataExchange.export() existing archive directory path purged: %s\n" % dirPath)                    
                    shutil.rmtree(dirPath)
                    os.makedirs(dirPath)
                    return True
                else:
                    if (self.__verbose):
                        self.__lfh.write("+DataExchange.export() archive directory exists: %s\n" % dirPath)
                    return False
        except:
            if self.__verbose:
                traceback.print_exc(file=self.__lfh)                
            return False



    def fetch(self,contentType,formatType,version="latest",partitionNumber=1):
        """ Copy the input content object into the current session directory (session naming semantics follow source file object)

            Return the full path of the copied file or None

        """
        inpFilePath=self.__getFilePath(fileSource=self.__fileSource,contentType=contentType,formatType=formatType,version=version,partitionNumber=partitionNumber)
        if (self.__verbose):
            self.__lfh.write("+DataExchange.fetch() source type %s format %s version %s path %s\n" % (contentType,formatType,version,inpFilePath))

        try:
            if (os.access(inpFilePath,os.R_OK)):
                (dirPath,fileName)=os.path.split(inpFilePath)
                # trim of the trailing version - 
                #lastIdx=tfileName.rfind(".V")
                #if lastIdx > 0:
                #    fileName=tfileName[:lastIdx]
                #else:
                #    fileName=tfileName
                outFilePath = os.path.join(self.__sessionPath,fileName)
                if (self.__verbose):
                    self.__lfh.write("+DataExchange.fetch() destination file path %s\n" % outFilePath)
                shutil.copyfile(inpFilePath,outFilePath)                    
                return outFilePath
            else:
                if (self.__verbose):
                    self.__lfh.write("+DataExchange.fetch() missing input file at path %s\n" % inpFilePath)                
                return None
        except:
            if self.__verbose:
                traceback.print_exc(file=self.__lfh)            
            return None


    def export(self,inpFilePath,contentType,formatType,version="latest",partitionNumber=1):
        """ Copy input file to workflow instance or archival storage.

            Return True on success or False otherwise.

        """
        outFilePath=self.__getFilePath(fileSource=self.__fileSource,contentType=contentType,formatType=formatType,version=version,partitionNumber=partitionNumber)
        if (self.__verbose):
            self.__lfh.write("+DataExchange.export() destination type %s format %s version %s path %s\n" % (contentType,formatType,version,outFilePath))

        try:
            if (os.access(inpFilePath,os.R_OK)):
                if (self.__verbose):
                    self.__lfh.write("+DataExchange.export() destination file path %s\n" % outFilePath)
                if inpFilePath.endswith(".gz"):
                    self.__copyGzip(inpFilePath,outFilePath)
                else:
                    shutil.copyfile(inpFilePath,outFilePath)                    
                return True
            else:
                if (self.__verbose):
                    self.__lfh.write("+DataExchange.export() missing input file at path %s\n" % inpFilePath)                
                return False
        except:
            if self.__verbose:
                traceback.print_exc(file=self.__lfh)                            
            return False


    def __copyGzip(self,inpFilePath,outFilePath):
        """
        """
        try:
            cmd=" gzip -cd  %s > %s " % (inpFilePath,outFilePath)
            os.system(cmd)
            return True
        except:
            if self.__verbose:
                traceback.print_exc(file=self.__lfh)                            
            return False            
            

    def copyToSession(self,contentType,formatType,version="latest",partitionNumber=1):
        """ Copy the input content object into the session directory using archive naming conventions less version details.

            Return the full path of the session file or None

        """
        inpFilePath=self.__getFilePath(fileSource=self.__fileSource,contentType=contentType,formatType=formatType,version=version,partitionNumber=partitionNumber)
        if (self.__verbose):
            self.__lfh.write("+DataExchange.copyToSession() source file type %s format %s version %s path %s\n" % (contentType,formatType,version,inpFilePath))

        try:
            if (os.access(inpFilePath,os.R_OK)):
                fn=self.__getArchiveFileName(contentType,formatType,version="none",partitionNumber=partitionNumber)
                outFilePath=os.path.join(self.__sessionPath,fn)
                if (self.__verbose):
                    self.__lfh.write("+DataExchange.copyToSession() session destination file path %s\n" % outFilePath)
                shutil.copyfile(inpFilePath,outFilePath)                    
                return outFilePath
            else:
                if (self.__verbose):
                    self.__lfh.write("+DataExchange.copyToSession() missing input file at path %s\n" % inpFilePath)                
                return None
        except:
            if self.__verbose:
                traceback.print_exc(file=self.__lfh)                            
            return None

    def updateArchiveFromSession(self,contentType,formatType,version="next",partitionNumber=1):
        """ Copy the input content object from the session directory stored using  archive naming conventions less version details
            to archive storage.

            Return the full path of the archive file or None

        """
        fn=self.__getArchiveFileName(contentType,formatType,version="none",partitionNumber=partitionNumber)
        inpFilePath=os.path.join(self.__sessionPath,fn)
        if (self.__verbose):
            self.__lfh.write("+DataExchange.updateArchiveDromSession() source file type %s format %s path %s\n" % (contentType,formatType,inpFilePath))

        try:
            if (os.access(inpFilePath,os.R_OK)):
                outFilePath=self.__getFilePath(fileSource="archive",contentType=contentType,formatType=formatType,version=version,partitionNumber=partitionNumber)                
                if (self.__verbose):
                    self.__lfh.write("+DataExchange.updateArchiveFromSession() archive destination file path %s\n" % outFilePath)
                shutil.copyfile(inpFilePath,outFilePath)                    
                return outFilePath
            else:
                if (self.__verbose):
                    self.__lfh.write("+DataExchange.updateArchiveFrom() missing session input file at path %s\n" % inpFilePath)                
                return None
        except:
            if self.__verbose:
                traceback.print_exc(file=self.__lfh)                            
            return None

    ##

    ##
    def __getArchiveFileName(self,contentType="model",formatType="pdbx",version="latest",partitionNumber=1):

        (d,f)=self.__targetFilePath(fileSource="archive",contentType=contentType,formatType=formatType,version=version,partitionNumber=partitionNumber)
        return f

    def __getInstanceFileName(self,contentType="model",formatType="pdbx",version="latest",partitionNumber=1):
        (d,f)=self.__targetFilePath(fileSource="wf-instance",contentType=contentType,formatType=formatType,version=version,partitionNumber=partitionNumber)
        return f    
        



    def __getFilePath(self,fileSource="archive",contentType="model",formatType="pdbx",version="latest",partitionNumber=1):
        """ Return the file path for the input content object if this is valid. If the file path
            cannot be verified return None.

        """         
        pI = PathInfo(siteId=self.__siteId, sessionPath=self.__sessionPath, verbose=self.__verbose, log=self.__lfh)       
        if fileSource=='session' and self.__inputSessionPath is not None:
            pI.setSessionPath(self.__inputSessionPath)
        fP=pI.getFilePath(dataSetId=self.__depDataSetId,
                                 wfInstanceId=self.__wfInstanceId,
                                 contentType=contentType,
                                 formatType=formatType,
                                 fileSource=fileSource,
                                 versionId=version,
                                 partNumber=partitionNumber)
        return fP

    


    def __targetFilePath(self,fileSource="archive",contentType="model",formatType="pdbx",version="latest",partitionNumber=1):
        """ Return the file path for the input content object if this is valid. If the file path
            cannot be verified return None.

        """  
        pI = PathInfo(siteId=self.__siteId, sessionPath=self.__sessionPath, verbose=self.__verbose, log=self.__lfh)
        if fileSource=='session' and self.__inputSessionPath is not None:
            pI.setSessionPath(self.__inputSessionPath)              
        fP=pI.getFilePath(dataSetId=self.__depDataSetId,
                                 wfInstanceId=self.__wfInstanceId,
                                 contentType=contentType,
                                 formatType=formatType,
                                 fileSource=fileSource,
                                 versionId=version,
                                 partNumber=partitionNumber)
        #
        try:
            return os.path.split(fP)
        except:
            return (None,None)

