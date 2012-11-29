##
# File: CvsAdmin.py
# Orig: 09-April-2011  j. Westbrook
#
# Updates:
# 12-April-2011 jdw Revision checkout
# 27-Nov-2012   jdw Rename as CvsAdmin() and change logging to wwPDB style 
# 27-Nov-2012   jdw Add update and commit operations
# 29-Nov-2012   jdw Refactor to separate operations for maintaining a working
#                   copy of a project (cvs sandbox) and operations 
#                   which are independent of a working copy.
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
import tempfile,shutil

class  CvsWrapperBase(object):
    """Core wrapper class for opertations on cvs administrative operations on repositories.
    
    """
    def __init__(self,tmpPath="./",verbose=True,log=sys.stderr):
        self.__tmpPath=tmpPath
        #
        self.__verbose=verbose
        self.__lfh=log
        self.__debug=True
        
        self._repositoryHost=None
        self._repositoryPath=None
        self._cvsUser=None
        self._cvsPassword=None
        self._cvsRoot=None
        #
        self._wrkPath=None
        self._cvsInfoFileName ="cvsInfo.txt"
        self._cvsErrorFileName="cvsError.txt"
        self.__outputFilePath=None
        self.__errorFilePath=None
    
    def setRepositoryPath(self,host,path):
        self._repositoryHost=host
        self._repositoryPath=path

    def setAuthInfo(self,user,password):
        self._cvsUser=user
        self._cvsPassword=password

    def _getRedirect(self,fileNameOut="myLog.log",fileNameErr="myLog.log", append=False):
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
            
    def _runCvsCommand(self,myCommand):
        retcode=-100
        try:
            self.__lfh.write("Command: %s\n" % myCommand)
            
            #if (self.__debug):
            #    self.__lfh.write("+CvsAdmin(_runCvsCommand) command: %s\n" % myCommand)
            
            retcode = subprocess.call(myCommand, shell=True)
            if retcode < 0:
                self.__lfh.write("Child was terminated by signal %r\n" % retcode)
                #if self.__verbose:
                #    self.__lfh.write("+CvsAdmin(_runCvsCommand) Child was terminated by signal %r\n" % retcode)
                return False
            else:
                self.__lfh.write("Child was terminated by signal %r\n" % retcode)
                #if self.__verbose:
                #    self.__lfh.write("+CvsAdmin(_runCvsCommand) Child was terminated by signal %r\n" % retcode)                
                return True
        except OSError, e:
            self.__lfh.write("cvs command exception: %r\n" % retcode)
            #if self.__verbose:
            #    self.__lfh.write("+CvsAdmin(_runCvsCommand) Execution failed: %r\n" % e)
            return False

    def _setCvsRoot(self):
        try:
            self._cvsRoot=":pserver:" + self._cvsUser + ":" + self._cvsPassword + "@" + \
                            self._repositoryHost + ":" + self._repositoryPath
            return True
        except:
            return False

    def _getOutputFilePath(self):
        self.__outputFilePath=os.path.join(self._wrkPath,self._cvsInfoFileName)
        return self.__outputFilePath

    def _getErrorFilePath(self):
        self.__errorFilePath=os.path.join(self._wrkPath,self._cvsErrorFileName)
        return self.__errorFilePath        
        
    def _getOutputText(self):
        text=""
        try:
            filePath=self.__outputFilePath
            return self.__getTextFile(filePath)            
        except:
            pass

        return text

    def _getErrorText(self):
        text=""
        try:
            filePath=self.__errorFilePath
            return self.__getTextFile(filePath)
        except:
            pass
        
        return text


    def __getTextFile(self,filePath):
        text=""
        try:
            ifh=open(filePath,'r')
            text=ifh.read()
        except:
            pass
        
        return text

    def _makeTempWorkingDir(self):
        if (self.__tmpPath != None and os.path.isdir(self.__tmpPath)):
            self._wrkPath = os.path.abspath( tempfile.mkdtemp('tmpdir','tmpCVS',self.__tmpPath))
            
        else:
            self._wrkPath = os.path.abspath( tempfile.mkdtemp('tmpdir','tmpCVS') )
        
        if self.__verbose:
            self.__lfh.write("Working directory path set to  %r\n" % self._wrkPath)            

    def cleanup(self):
        """Cleanup any temporary files and directories created by this class.
        """
        return shutil.rmtree(self._wrkPath)
        


class  CvsAdmin(CvsWrapperBase):
    """Wrapper class for opertations on cvs administrative operations on repositories.
    """
    def __init__(self,tmpPath="./",verbose=True,log=sys.stderr):
        super(CvsAdmin,self).__init__(tmpPath=tmpPath,verbose=verbose,log=log)
        self.__tmpPath=tmpPath
        #
        self.__verbose=verbose
        self.__lfh=log
        self.__debug=True


    def getHistory(self,cvsPath):
        """ Return the history text for project files identified by cvsPath in the
            current repository.
        """
        text=""
        cmd = self.__getHistoryCmd(cvsPath)
        if cmd is not None:
            ok=self._runCvsCommand(myCommand=cmd)
            text=self._getOutputText()
            
        return text

    def getRevisionList(self,cvsPath):
        """ Return a list of tuples containing the revision identifiers for the input file.

            Return data has the for [(RevId, A/M, timeStamp),...] where A=Added and M=Modified.  
        """
        revList=[]
        cmd = self.__getHistoryCmd(cvsPath)
        if cmd is not None:
            ok=self._runCvsCommand(myCommand=cmd)
            revList=self.__extractRevisions()
        return revList


    def checkOutFile(self,cvsPath,outPath,revId=None):
        """ Perform CVS checkout operation for the project files identified by the input cvsPath
            subject to the input revision identifier.

            Files that are checked out are then subsequently copied to outPath.

            Note that outPath will not be a CVS working copy (sandbox) after this operation.
        """ 
        text=""
        (pth,fn)=os.path.split(cvsPath)
        self.__lfh.write("Cvs directory %s   target file name %s\n" % (pth,fn))
        if len(fn) > 0:
            cmd = self.__getCheckOutCmd(cvsPath,outPath,revId)
            if cmd is not None:
                ok=self._runCvsCommand(myCommand=cmd)
                text=self._getErrorText()
        else:
            pass
        return text
    
    def __getHistoryCmd(self,cvsPath):
        if self._wrkPath is None:
            self._makeTempWorkingDir()
        outPath=self._getOutputFilePath()
        errPath=self._getErrorFilePath()
        if self._setCvsRoot():
            cmd="cvs -d " +  self._cvsRoot  + " history -a -x AM " + cvsPath + self._getRedirect(fileNameOut=outPath,fileNameErr=errPath)
        else:
            cmd=None
        return cmd

    def __getCheckOutCmd(self,cvsPath,outPath,revId=None):
        if self._wrkPath is None:
            self._makeTempWorkingDir()
        errPath=self._getErrorFilePath()
        (pth,fn)=os.path.split(cvsPath)
        self.__lfh.write("CVS directory %s  target file name %s\n" % (pth,fn))
        lclPath=os.path.join(self._wrkPath,fn)
        #
        #
        if self._setCvsRoot():
            if revId is None:
                rS=" "
                cmd="cvs -d " +  self._cvsRoot  + " co -d " + self._wrkPath + " " + cvsPath +  \
                     self._getRedirect(fileNameOut=errPath,fileNameErr=errPath) + ' ; '  + \
                     " mv -f  " + lclPath + " " + outPath + self._getRedirect(fileNameOut=errPath,fileNameErr=errPath,append=True) + ' ; ' 
            else:
                rS=" -r " + revId + " "
                cmd="cvs -d " +  self._cvsRoot  + " co -d " + self._wrkPath + rS +  " " + cvsPath + \
                     self._getRedirect(fileNameOut=errPath,fileNameErr=errPath) + ' ; '  + \
                     " mv -f  " + lclPath + " " + outPath + self._getRedirect(fileNameOut=errPath,fileNameErr=errPath,append=True) + ' ; ' 
        else:
            cmd=None
        return cmd

    def __extractRevisions(self):
        """Extract revisions details from the last history command.
        """
        revList=[]
        try:
            fName=self._getOutputFilePath()
            self.__lfh.write("Reading revisions from %r\n" % fName)            
            ifh=open(fName,'r')
            for line in ifh.readlines():
                fields=line[:-1].split()
                typeCode=str(fields[0])
                revId=str(fields[5])
                timeStamp= str( fields[1] + ':' + fields[2] )
                revList.append((revId,typeCode,timeStamp))
        except:
            self.__lfh.write("Extracting revision list for : %s\n" % fName)            
            pass

        revList.reverse()        
        self.__lfh.write("Ordered revision list %r\n" % revList)
        
        return revList



class  CvsSandBoxAdmin(CvsWrapperBase):
    """Wrapper class for opertations on cvs working directories (aka cvs sandboxes).

    """
    def __init__(self,tmpPath="./",verbose=True,log=sys.stderr):
        super(CvsSandBoxAdmin,self).__init__(tmpPath=tmpPath,verbose=verbose,log=log)
        self.__tmpPath=tmpPath
        #
        self.__verbose=verbose
        self.__lfh=log
        self.__debug=True
        #
        self.__sandBoxTopPath=None

    def setSandBoxTopPath(self,dirPath):
        """ Assign the path that contains or will contain the working copy of the cvs project.

            Must be an existing writable path.
            
        """
        if os.access(dirPath,os.W_OK):
            self.__sandBoxTopPath=dirPath
            return True
        else:
            return False

    def getSandBoxTopPath(self):
        return os.path.abspath(self.__sandBoxTopPath)


    def checkOut(self,projectPath=None,revId=None):
        """ Create CVS sandbox working copy of the input project path within the current repository.

        """
        if (self.__verbose):
            self.__lfh.write("Checking out CVS repository working path %s file path %s\n" %
                             (self.__sandBoxTopPath, projectPath))
        
        if (self.__sandBoxTopPath is not None and projectPath is not None):
            cmd = self.__getCheckOutProjectCmd(projectPath,revId=revId)
            if cmd is not None:
                ok=self._runCvsCommand(myCommand=cmd)
                text=self._getErrorText()
        else:
            pass
        return text
        
    def update(self,projectPath,prune=False):
        """ Update CVS sandbox working copy of the input project path.   The project path must
            correspond to an existing working copy of the repository.

        """
        if (self.__verbose):
            self.__lfh.write("Updating CVS repository working path %s project file path %s\n" %
                             (self.__sandBoxTopPath, projectPath))
        targetPath=os.path.join(self.__sandBoxTopPath,projectPath)
        if (os.access(targetPath,os.W_OK)):
            cmd = self.__getUpdateProjectCmd(projectPath,prune=prune)
            if cmd is not None:
                ok=self._runCvsCommand(myCommand=cmd)
                text=self._getErrorText()
        else:
            self.__lfh.write("+ERROR - cannot update project path %s\n" % targetPath)            

        return text

    def add(self,projectDir,relProjectPath):
        """ Add to CVS sandbox working copy the input project path.   The project path must
            correspond to an existing path in the local working copy.

        """
        if (self.__verbose):
            self.__lfh.write("Add %s to the CVS repository working in file path %s\n" %
                             (relProjectPath, os.path.join(self.__sandBoxTopPath,projectDir) ))
        targetPath=os.path.join(self.__sandBoxTopPath,projectDir,relProjectPath)
        if (os.access(targetPath,os.W_OK)):
            cmd = self.__getAddCommitCmd(projectDir,relProjectPath)
            if cmd is not None:
                ok=self._runCvsCommand(myCommand=cmd)
                text=self._getErrorText()
        else:
            self.__lfh.write("+ERROR - cannot add project path %s\n" % targetPath)            

        return text


    def remove(self,projectDir,relProjectPath):
        """ Remove from the CVS sandbox working copy the input project path.   The project path must
            correspond to an existing path in the local working copy.

        """
        if (self.__verbose):
            self.__lfh.write("Remove %s from the CVS repository working in file path %s\n" %
                             (relProjectPath,os.path.join(self.__sandBoxTopPath,projectDir)))
        targetPath=os.path.join(self.__sandBoxTopPath,projectDir,relProjectPath)
        if (os.access(targetPath,os.W_OK)):
            cmd = self.__getRemoveCommitCmd(projectDir,relProjectPath)
            if cmd is not None:
                ok=self._runCvsCommand(myCommand=cmd)
                text=self._getErrorText()
        else:
            self.__lfh.write("+ERROR - cannot remove project path %s\n" % targetPath)            

        return text


    def __getCheckOutProjectCmd(self, projectPath, revId=None):
        if self._wrkPath is None:
            self._makeTempWorkingDir()        
        errPath=self._getErrorFilePath()
        if self._setCvsRoot():
            cmd = " cd " + self.__sandBoxTopPath + " ; "
            if revId is None:
                cmd+="cvs -d " +  self._cvsRoot  + " co " + projectPath + \
                      self._getRedirect(fileNameOut=errPath,fileNameErr=errPath) + " ; "
            else:
                rS=" -r " + revId + " "
                cmd+="cvs -d " +  self._cvsRoot  + " co " +  rS + projectPath + \
                     self._getRedirect(fileNameOut=errPath,fileNameErr=errPath) + ' ; '
        else:
            cmd=None
        return cmd

    def __getUpdateProjectCmd(self, projectPath, prune=False):
        if self._wrkPath is None:
            self._makeTempWorkingDir()                
        errPath=self._getErrorFilePath()
        if self._setCvsRoot():
            if prune:
                pF=" -P "
            else:
                pF=" "
            targetPath=os.path.join(self.__sandBoxTopPath,projectPath)
            cmd = " cd " + targetPath + "; "
            cmd+="cvs -d " +  self._cvsRoot  + " update -d " + pF + \
                      self._getRedirect(fileNameOut=errPath,fileNameErr=errPath) + " ; "
        else:
            cmd=None
        return cmd


    def __getAddCommitCmd(self, projectDir, relProjectPath, message="Initial version"):
        if self._wrkPath is None:
            self._makeTempWorkingDir()        
        errPath=self._getErrorFilePath()
        if self._setCvsRoot():
            cmd = " cd " + os.path.join(self.__sandBoxTopPath,projectDir) + " ; "
            if message is not None and len(message) > 0:
                qm=' -m "'+message+'" '
            cmd+="cvs -d " +  self._cvsRoot  + " add " +  relProjectPath + \
                      self._getRedirect(fileNameOut=errPath,fileNameErr=errPath) + " ; "
            cmd+="cvs -d " +  self._cvsRoot  + " commit " + qm + relProjectPath + \
                  self._getRedirect(fileNameOut=errPath,fileNameErr=errPath,append=True) + ' ; '             
        else:
            cmd=None
        return cmd


    def __getRemoveCommitCmd(self, projectDir, relProjectPath, message="File removed"):
        if self._wrkPath is None:
            self._makeTempWorkingDir()        
        errPath=self._getErrorFilePath()
        if self._setCvsRoot():
            cmd = " cd " + os.path.join(self.__sandBoxTopPath,projectDir) + " ; "            
            if message is not None and len(message) > 0:
                qm=' -m "'+message+'" '
            cmd+="cvs -d " +  self._cvsRoot  + " remove -f " +  relProjectPath + \
                      self._getRedirect(fileNameOut=errPath,fileNameErr=errPath) + " ; "
            cmd+="cvs -d " +  self._cvsRoot  + " commit " + qm + relProjectPath + \
                  self._getRedirect(fileNameOut=errPath,fileNameErr=errPath,append=True) + ' ; '             
        else:
            cmd=None
        return cmd

