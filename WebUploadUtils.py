##
# File:  WebUploadUtils.py
# Date:  28-Feb-2013 
#
# Updates:
#  28-Feb-2013   jdw imported common functions from WebApp(*).py  modules.
#  03-Mar-2013   jdw catch unicode type in empty file request. 
#  28-Feb-2104   jdw add rename and file extension methods
##
"""
Utilities to manage  web application upload tasks.
     
"""
__docformat__ = "restructuredtext en"
__author__    = "John Westbrook"
__email__     = "jwest@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.09"

import sys, os, types, string, traceback, shutil


class WebUploadUtils(object):
    """
     This class encapsulates all of the web application upload tasks.
     
    """
    def __init__(self,reqObj=None, verbose=False,log=sys.stderr):

        self.__reqObj=reqObj
        self.__verbose=verbose        
        self.__lfh=log
        #
        self.__debug=False        
        #
        self.__sessionObj  = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sessionObj.getPath()
        #
        if (self.__verbose):
            self.__lfh.write("+WebUploadUtils.__setup() - session id   %s\n" % (self.__sessionObj.getId()))
            self.__lfh.write("+WebUploadUtils.__setup() - session path %s\n" % (self.__sessionPath))


    def isFileUpload(self,fileTag='file'):
        """ Generic check for the existence of request paramenter "fileTag=".
        """ 
        # Gracefully exit if no file is provide in the request object - 
        fs=self.__reqObj.getRawValue(fileTag)

        if (self.__debug):
            self.__lfh.write("+WebUploadUtils.isFileUpLoad() fs  %r\n" % fs)

        if ((fs is None) or (type(fs) == types.StringType) or (type(fs) == types.UnicodeType) ):
            return False
        return True

    def copyToSession(self,fileTag='file',sessionFileName=None, uncompress=True ):
        """  Copy uploaded file identified form element name 'fileTag' to the current session directory.

             File is copied to user uploaded file or to the sessionFileName if this is provided.
        """
        #
        if (self.__verbose):
            self.__lfh.write("+WebUploadUtils.copyToSession() - operation started\n")
        
        #
        try:
            fs=self.__reqObj.getRawValue(fileTag)
            if (self.__verbose):
                self.__lfh.write("+WebUploadUtils.copyToSession() - upload file descriptor fs =     %r\n" % fs)
                self.__lfh.write("+WebUploadUtils.copyToSession() - upload file descriptor fs =     %s\n" % fs)
            #formRequestFileName = str(fs.filename).strip().lower()
            formRequestFileName = str(fs.filename).strip()

            #
            if (formRequestFileName.find('\\') != -1) :
                uploadInputFilefName=ntpath.basename(formRequestFileName)
            else:
                uploadInputFileName=os.path.basename(formRequestFileName)

            #
            # Copy uploaded file in session directory 
            #
            if sessionFileName is not None:
                sessionInputFileName=sessionFileName
            else:
                sessionInputFileName=uploadInputFileName
                
            sessionInputFilePath=os.path.join(self.__sessionPath,sessionInputFileName)                

            if (self.__verbose):
                self.__lfh.write("+WebUploadUtils.copyToSession() - user request file name     %s\n" % fs.filename)
                self.__lfh.write("+WebUploadUtils.copyToSession() - upload input file name     %s\n" % uploadInputFileName)
                self.__lfh.write("+WebUploadUtils.copyToSession() - session target file path   %s\n" % sessionInputFilePath)                
                self.__lfh.write("+WebUploadUtils.copyToSession() - session target file name   %s\n" % sessionInputFileName)                
            #
            ofh=open(sessionInputFilePath,'w')
            ofh.write(fs.file.read())
            ofh.close()
            #
            if (uncompress and sessionInputFilePath.endswith(".gz")):
                if (self.__verbose):
                    self.__lfh.write("+WebUploadUtils.copyToSession() uncompressing file %s\n" % str(sessionInputFilePath) )
                self.__copyGzip(sessionInputFilePath,sessionInputFilePath[:-3])
                sessionInputFileName=sessionInputFileName[:-3]

            if (self.__verbose):
                self.__lfh.write("+WebUploadUtils.copyToSession() Uploaded file %s\n" % str(sessionInputFileName) )
            #
            return sessionInputFileName
        except:
            if (self.__verbose):
                self.__lfh.write("+WebUploadUtils.copyToSession() File upload processing failed\n")
                traceback.print_exc(file=self.__lfh)                            
            return None

    def renameSessionFile(self,srcFileName,dstFileName):
        try:
            srcPath=os.path.join(self.__sessionPath,srcFileName)
            dstPath=os.path.join(self.__sessionPath,dstFileName)
            shutil.copyfile(srcPath,dstPath)
            return True
        except:
            return False
        

    def getFileExtension(self,fileName):
        """ Return the file extension (basename.ext).
        """
        fExt=None
        if fileName is None or len(fileName) < 1:
            return fExt
        fL=str(fileName).split('.')
        if len(fL)>1:
            fExt=fL[-1]
        return fExt

    def perceiveIdentifier(self,fileName):
        """ Return the file identifier and identifier type if these can be deduced from 
            the input file name.   Returned values are in uppercase. 
        """
        #
        #
        fId=None
        fType=None
        if fileName is None or len(fileName) < 1:
            return fId,fType

        (head,tail)=os.path.splitext(str(fileName))
        headLC=head.upper()
        if headLC.startswith('RCSB'):
            fId = head
            fType='RCSB'
        elif headLC.startswith('D_'):
            fId = head
            fType="WF_ARCHIVE"
            # 
            # Look for
            #
            fields=head.split('_')
            if len(fields) > 1:
                fId='_'.join(fields[:2])
        elif headLC.startswith('W_'):
            fId=head
            fType="WF_INSTANCE"
        else:
            fId=head
            fType="UNKNOWN"
            if (self.__verbose):
                self.__lfh.write("+WebUploadUtils.copyToSession() using non-standard identifier %r for %r\n" % (head,str(fileName) ) )

        if (self.__verbose):
            self.__lfh.write("+WebUploadUtils.copyToSession() using identifier fId %r and fType %r \n" % (fId,fType ) )

        return fId,fType


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





