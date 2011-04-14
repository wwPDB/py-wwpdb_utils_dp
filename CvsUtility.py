##
# File: CvsUtility.py
# Date: 09-April-2011  j. Westbrook
#
# Updates:
# 12-April-2011 jdw Revision checkout
##
"""
Wrapper class for opertations on cvs repositories.

Methods are provided to manage archiving of chemical component data files.

"""
__docformat__ = "restructuredtext en"
__author__    = "John Westbrook"
__email__     = "jwest@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.001"


import sys,os,subprocess
import tempfile,shutil,logging

class  CvsWrapper(object):
    """Wrapper class for opertations on cvs repositories.

    """
    def __init__(self,tmpPath="./"):
        self.__tmpPath=tmpPath
        self.__verbose=None
        self.__lfh=None
        self.__logger=logging.getLogger("wwpdb.utils.rcsb.CvsWrapper")
        self.__logger.info("Created instance of CvsWrapper\n")
        #
        self.__debug=True        
        self.__repositoryHost=None
        self.__repositoryPath=None
        self.__cvsUser=None
        self.__cvsPassword=None
        self.__cvsRoot=None
        #
        self.__wrkPath=None
        self.__cvsInfoFileName ="cvsInfo.txt"
        self.__cvsErrorFileName="cvsError.txt"
    
    def setRepositoryPath(self,host,path):
        self.__repositoryHost=host
        self.__repositoryPath=path

    def setAuthInfo(self,user,password):
        self.__cvsUser=user
        self.__cvsPassword=password

    def getHistory(self,cvsPath):
        text=""
        cmd = self.__getHistoryCmd(cvsPath)
        if cmd is not None:
            ok=self.__runCvsCommand(myCommand=cmd)
            text=self.__getOutputText()
            
        return text

    def getRevisionList(self,cvsPath):
        """ Return a list of tuples containing the revision identifiers for the input file.

            Return data has the for [(RevId, A/M, timeStamp),...] where A=Added and M=Modified.  
        """
        revList=[]
        cmd = self.__getHistoryCmd(cvsPath)
        if cmd is not None:
            ok=self.__runCvsCommand(myCommand=cmd)
            revList=self.__extractRevisions()
        return revList

    def cleanup(self):
        """Cleanup temporary files and directories
        """
        return shutil.rmtree(self.__wrkPath)

    def checkOutFile(self,cvsPath,outPath,revId=None):
        text=""
        (pth,fn)=os.path.split(cvsPath)
        self.__logger.info("Cvs directory %s   target file name %s\n" % (pth,fn))
        if len(fn) > 0:
            cmd = self.__getCheckOutCmd(cvsPath,outPath,revId)
            if cmd is not None:
                ok=self.__runCvsCommand(myCommand=cmd)
                text=self.__getErrorText()
        else:
            pass
        return text
    
    def __getHistoryCmd(self,cvsPath):
        if self.__wrkPath is None:
            self.__makeTempWorkingDir()
        outPath=os.path.join(self.__wrkPath,self.__cvsInfoFileName)
        errPath=os.path.join(self.__wrkPath,self.__cvsErrorFileName)
        if self.__setCvsRoot():
            cmd="cvs -d " +  self.__cvsRoot  + " history -a -x AM " + cvsPath + self.__getRedirect(fileNameOut=outPath,fileNameErr=errPath)
        else:
            cmd=None
        return cmd

    def __getCheckOutCmd(self,cvsPath,outPath,revId=None):
        if self.__wrkPath is None:
            self.__makeTempWorkingDir()
        errPath=os.path.join(self.__wrkPath,self.__cvsErrorFileName)
        #
        (pth,fn)=os.path.split(cvsPath)
        self.__logger.info("CVS directory %s  target file name %s\n" % (pth,fn))
        lclPath=os.path.join(self.__wrkPath,fn)
        #
        #
        if self.__setCvsRoot():
            if revId is None:
                rS=" "
                cmd="cvs -d " +  self.__cvsRoot  + " co -d " + self.__wrkPath + " " + cvsPath +  \
                     self.__getRedirect(fileNameOut=errPath,fileNameErr=errPath) + ' ; '  + \
                     " mv -f  " + lclPath + " " + outPath + self.__getRedirect(fileNameOut=errPath,fileNameErr=errPath,append=True) + ' ; ' 
            else:
                rS=" -r " + revId + " "
                cmd="cvs -d " +  self.__cvsRoot  + " co -d " + self.__wrkPath + rS +  " " + cvsPath + \
                     self.__getRedirect(fileNameOut=errPath,fileNameErr=errPath) + ' ; '  + \
                     " mv -f  " + lclPath + " " + outPath + self.__getRedirect(fileNameOut=errPath,fileNameErr=errPath,append=True) + ' ; ' 
        else:
            cmd=None
        return cmd

    def __getRedirect(self,fileNameOut="myLog.log",fileNameErr="myLog.log", append=False):
        if append:
            if fileNameOut == fileNameErr:
                oReDir=" >> " + fileNameOut + " 2>&1 "
            else:
                oReDir=" >> " + fileNameOut + " 2>> " + fileNameErr
        else:
            if fileNameOut == fileNameErr:
                oReDir=" > " + fileNameOut + " 2>&1 "
            else:
                oReDir=" > " + fileNameOut + " 2> " + fileNameErr
            

        return oReDir
            
    def __runCvsCommand(self,myCommand):
        retcode=-100
        try:
            self.__logger.info("Command: %s\n" % myCommand)
            
            #if (self.__debug):
            #    self.__lfh.write("+CvsWrapper(__runCvsCommand) command: %s\n" % myCommand)
            
            retcode = subprocess.call(myCommand, shell=True)
            if retcode < 0:
                self.__logger.info("Child was terminated by signal %r\n" % retcode)
                #if self.__verbose:
                #    self.__lfh.write("+CvsWrapper(__runCvsCommand) Child was terminated by signal %r\n" % retcode)
                return False
            else:
                self.__logger.info("Child was terminated by signal %r\n" % retcode)
                #if self.__verbose:
                #    self.__lfh.write("+CvsWrapper(__runCvsCommand) Child was terminated by signal %r\n" % retcode)                
                return True
        except OSError, e:
            self.__logger.exception("cvs command exception: %r\n" % retcode)
            #if self.__verbose:
            #    self.__lfh.write("+CvsWrapper(__runCvsCommand) Execution failed: %r\n" % e)
            return False

        
    def __setCvsRoot(self):
        try:
            self.__cvsRoot=":pserver:" + self.__cvsUser + ":" + self.__cvsPassword + "@" + \
                            self.__repositoryHost + ":" + self.__repositoryPath
            return True
        except:
            return False
        
    
    def __extractRevisions(self):
        """Extract revisions details from the last history command.
        """
        revList=[]
        try:
            fName=os.path.join(self.__wrkPath,self.__cvsInfoFileName)
            ifh=open(fName,'r')
            for line in ifh.readlines():
                fields=line[:-1].split()
                typeCode=str(fields[0])
                revId=str(fields[5])
                timeStamp= str( fields[1] + ':' + fields[2] )
                revList.append((revId,typeCode,timeStamp))
        except:
            self.__logger.exception("Extracting revision list for : %s\n" % fName)            
            pass
        
        return revList

    def __getOutputText(self):
        text=""
        try:
            fPath=os.path.join(self.__wrkPath,self.__cvsInfoFileName)
            ifh=open(fPath,'r')
            text=ifh.read()
        except:
            self.__logger.exception("Execption reading cvs output file: %s\n" % fPath)
        
        return text

    def __getErrorText(self):
        text=""
        try:
            fName=os.path.join(self.__wrkPath,self.__cvsErrorFileName)
            ifh=open(fName,'r')
            text=ifh.read()
        except:
            pass
        
        return text

    def __makeTempWorkingDir(self):
        if (self.__tmpPath != None and os.path.isdir(self.__tmpPath)):
            self.__wrkPath = tempfile.mkdtemp('tmpdir','rcsbCVS',self.__tmpPath)
        else:
            self.__wrkPath = tempfile.mkdtemp('tmpdir','rcsbCVS')
        self.__logger.info("Working directory path set to  %r\n" % self.__wrkPath)            


