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
#  3-Dec-2012   jdw Add separate commit operations.
# 27-Jan-2013   jdw Provide return status and message text as returns for public methods
#                   in CvsSandBoxAdmin().
# 28-Jan-2013   jdw change __getCheckOutCmd() to avoid absolute path with 'co -d path' 
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


import sys,os,subprocess,traceback
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
            if self.__verbose:
                self.__lfh.write("+CvsWrapperBase._runCvsCommand Command: %s\n" % myCommand)
            
            # retcode = subprocess.call(myCommand, stdout=self.__lfh, stderr=self.__lfh, shell=True)
            retcode = subprocess.call(myCommand,  shell=True)            
            if retcode != 0:
                if self.__verbose:
                    self.__lfh.write("+CvsWrapperBase(_runCvsCommand) Child was terminated by signal %r\n" % retcode)
                return False
            else:
                if self.__verbose:
                    self.__lfh.write("+CvsWrapperBase(_runCvsCommand) Child was terminated by signal %r\n" % retcode)                
                return True
        except OSError, e:
            if self.__verbose:
                traceback.print_exc(file=self.__lfh)                                            
                self.__lfh.write("+CvsWrapperBase(_runCvsCommand) Execution failed: %r\n" % e)
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
            if self.__verbose:
                traceback.print_exc(file=self.__lfh)                                            
                self.__lfh.write("+CvsWrapperBase(_getOutputText) path %r\n" % self.__outputFilePath)                        

        return text

    def _getErrorText(self):
        text=""
        try:
            filePath=self.__errorFilePath
            return self.__getTextFile(filePath)
        except:
            if self.__verbose:
                traceback.print_exc(file=self.__lfh)                                            
                self.__lfh.write("+CvsWrapperBase(_getErrorText) path %r\n" % self.__errorFilePath)            
        
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
            self.__lfh.write("+CvsWrapperBase(_makeTempWorkingDir) Working directory path set to  %r\n" % self._wrkPath)

    def cleanup(self):
        """Cleanup any temporary files and directories created by this class.
        """
        if (self._wrkPath is not None and len(self._wrkPath) > 0):
            try:
                shutil.rmtree(self._wrkPath)
                return True
            except:
                return False
        else:
            return True
        


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
        ok=False
        cmd = self.__getHistoryCmd(cvsPath)
        if cmd is not None:
            ok=self._runCvsCommand(myCommand=cmd)
            text=self._getOutputText()
        else:
            text='History command failed with repository command processing error' 
            
        return (ok,text)

    def getRevisionList(self,cvsPath):
        """ Return a list of tuples containing the revision identifiers for the input file.

            Return data has the for [(RevId, A/M, timeStamp),...] where A=Added and M=Modified.  
        """
        revList=[]
        ok=False
        cmd = self.__getHistoryCmd(cvsPath)
        if cmd is not None:
            ok=self._runCvsCommand(myCommand=cmd)
            revList=self.__extractRevisions()
        else:
            text='Revision history command failed with repository command processing error'             

        return (ok,revList)

    def checkOutFile(self,cvsPath,outPath,revId=None):
        """ Perform CVS checkout operation for the project files identified by the input cvsPath
            subject to the input revision identifier.

            Files that are checked out are then subsequently copied to outPath.

            Note that outPath will not be a CVS working copy (sandbox) after this operation.
        """ 
        text=""
        ok=False
        (pth,fn)=os.path.split(cvsPath)
        if (self.__verbose):
            self.__lfh.write("+CvsAdmin(checkOutFile) Cvs directory %s   target file name %s\n" % (pth,fn))
        if len(fn) > 0:
            cmd = self.__getCheckOutCmd(cvsPath,outPath,revId)
            if cmd is not None:
                ok=self._runCvsCommand(myCommand=cmd)
                text=self._getErrorText()
            else:
                text='Check out failed with repository command processing error'                            
        else:
            self.__lfh.write("+ERROR - CvsAdmin(checkOutFile) cannot check out project path %s\n" % cvsPath)
            text='Check out failed with repository project path issue: %s' % cvsPath        

        return (ok,text)
    
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
        if (self.__verbose):
            self.__lfh.write("+CvsAdmin(__getCheckOutCmd) CVS directory %s  target file name %s\n" % (pth,fn))
        lclPath=os.path.join(self._wrkPath,cvsPath)
        outPathAbs=os.path.abspath(outPath)
        #
        #
        if self._setCvsRoot():
            if revId is None:
                rS=" "
                cmd="cd " + self._wrkPath + " ; cvs -d " +  self._cvsRoot  + " co "  + cvsPath +  \
                     self._getRedirect(fileNameOut=errPath,fileNameErr=errPath) + ' ; '  + \
                     " mv -f  " + lclPath + " " + outPathAbs + self._getRedirect(fileNameOut=errPath,fileNameErr=errPath,append=True) + ' ; '                 
                #cmd="cvs -d " +  self._cvsRoot  + " co -d " + self._wrkPath + " " + cvsPath +  \
                #     self._getRedirect(fileNameOut=errPath,fileNameErr=errPath) + ' ; '  + \
                #     " mv -f  " + lclPath + " " + outPath + self._getRedirect(fileNameOut=errPath,fileNameErr=errPath,append=True) + ' ; ' 
            else:
                rS=" -r " + revId + " "
                cmd="cd " + self._wrkPath + "; cvs -d " +  self._cvsRoot  + " co " + rS +  " " + cvsPath + \
                     self._getRedirect(fileNameOut=errPath,fileNameErr=errPath) + ' ; '  + \
                     " mv -f  " + lclPath + " " + outPathAbs + self._getRedirect(fileNameOut=errPath,fileNameErr=errPath,append=True) + ' ; '                 
                #cmd="cvs -d " +  self._cvsRoot  + " co -d " + self._wrkPath + rS +  " " + cvsPath + \
                #     self._getRedirect(fileNameOut=errPath,fileNameErr=errPath) + ' ; '  + \
                #     " mv -f  " + lclPath + " " + outPath + self._getRedirect(fileNameOut=errPath,fileNameErr=errPath,append=True) + ' ; ' 
        else:
            cmd=None
        return cmd

    def __extractRevisions(self):
        """Extract revisions details from the last history command.
        """
        revList=[]
        try:
            fName=self._getOutputFilePath()
            if (self.__verbose):            
                self.__lfh.write("+CvsAdmin(__extraRevisions) Reading revisions from %r\n" % fName)            
            ifh=open(fName,'r')
            for line in ifh.readlines():
                fields=line[:-1].split()
                typeCode=str(fields[0])
                revId=str(fields[5])
                timeStamp= str( fields[1] + ':' + fields[2] )
                revList.append((revId,typeCode,timeStamp))
        except:
            if (self.__verbose):
                self.__lfh.write("+CvsAdmin(__extraRevisions) Extracting revision list for : %s\n" % fName)            
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
            self.__lfh.write("\n+CvsSandBoxAdmin(checkOut) Checking out CVS repository working path %s project file path %s\n" %
                             (self.__sandBoxTopPath, projectPath))
        text=''
        ok=False
        if (self.__sandBoxTopPath is not None and projectPath is not None):
            cmd = self.__getCheckOutProjectCmd(projectPath,revId=revId)
            if (self.__verbose):
                self.__lfh.write("\n+CvsSandBoxAdmin(checkOut) checkout command %s\n" % cmd)
            if cmd is not None:
                ok=self._runCvsCommand(myCommand=cmd)
                text=self._getErrorText()
            else:
                text='Check out failed with repository command processing error'
        else:
            self.__lfh.write("+ERROR - CvsSandBoxAdmin(checkOut) cannot check out project path %s\n" % projectPath)
            text='Check out failed with repository project path issue: %s' % projectPath
        
        return (ok,text)
        
    def update(self,projectDir,relProjectPath='.',prune=False):
        """ Update CVS sandbox working copy of the input project path.   The project path must
            correspond to an existing working copy of the repository.

        """
        if (self.__verbose):
            self.__lfh.write("\n+CvsSandBoxAdmin(update) Updating CVS repository working path %s project %s relative file path %s\n" %
                             (self.__sandBoxTopPath, projectDir,relProjectPath))
        targetPath=os.path.join(self.__sandBoxTopPath,projectDir)
        text=''
        ok=False
        if (os.access(targetPath,os.W_OK)):
            cmd = self.__getUpdateCmd(projectDir,relProjectPath=relProjectPath,prune=prune)
            if (self.__verbose):
                self.__lfh.write("\n+CvsSandBoxAdmin(update) update command %s\n" % cmd)            
            if cmd is not None:
                ok=self._runCvsCommand(myCommand=cmd)
                text=self._getErrorText()
            else:
                text='Update failed with repository command processing error'
        else:
            text='Update failed with repository project path issue: %s' % targetPath            
            self.__lfh.write("+ERROR - CvsSandBoxAdmin(update) cannot update project path %s\n" % targetPath)            

        return (ok,text)

    def add(self,projectDir,relProjectPath):
        """ Add an new definition in CVS working direcotry in the input project path.   The project path must
            correspond to an existing file path in the local working copy.

        """
        if (self.__verbose):
            self.__lfh.write("\n+CvsSandBoxAdmin(add) Add %s to project %s in CVS repository working path %s\n" %
                             (relProjectPath, projectDir, self.__sandBoxTopPath ))
        targetPath=os.path.join(self.__sandBoxTopPath,projectDir,relProjectPath)
        text=''
        ok=False        
        if (os.access(targetPath,os.W_OK)):
            cmd = self.__getAddCommitCmd(projectDir,relProjectPath)
            if cmd is not None:
                ok=self._runCvsCommand(myCommand=cmd)
                text=self._getErrorText()
            else:
                text='Add failed with repository command processing error'                
        else:
            text='Add failed due with repository project path issue: %s' % targetPath                        
            self.__lfh.write("+ERROR - CvsSandBoxAdmin(add) cannot add project path %s\n" % targetPath)            

        return (ok,text)


    def commit(self,projectDir,relProjectPath):
        """ Commit changes in the input project/file path to the CVS repository. The project path must
            correspond to an existing path in the local working copy.

        """
        if (self.__verbose):
            self.__lfh.write("\n+CvsSandBoxAdmin(commit) Commit changes to %s in project %s in CVS repository working path %s\n" %
                             (relProjectPath, projectDir, self.__sandBoxTopPath ))
        targetPath=os.path.join(self.__sandBoxTopPath,projectDir,relProjectPath)
        text=''
        ok=False                
        if (os.access(targetPath,os.W_OK)):
            cmd = self.__getCommitCmd(projectDir,relProjectPath)
            if cmd is not None:
                ok=self._runCvsCommand(myCommand=cmd)
                text=self._getErrorText()
            else:
                text='Commit failed with repository command processing error'
        else:
            text='Commit failed due with repository project path issue: %s' % targetPath                                    
            self.__lfh.write("+ERROR - CvsSandBoxAdmin(commit) cannot commit project path %s\n" % targetPath)            

        return (ok,text)


    def remove(self,projectDir,relProjectPath):
        """ Remove from the CVS sandbox working copy the input project path.   The project path must
            correspond to an existing path in the local working copy.

        """
        if (self.__verbose):
            self.__lfh.write("\n+CvsSandBoxAdmin(remove) Remove %s from project %s in CVS repository working path %s\n" %
                             (relProjectPath,projectDir, self.__sandBoxTopPath))
        targetPath=os.path.join(self.__sandBoxTopPath,projectDir,relProjectPath)
        text=''
        ok=False                        
        if (os.access(targetPath,os.W_OK)):
            cmd = self.__getRemoveCommitCmd(projectDir,relProjectPath)
            if cmd is not None:
                ok=self._runCvsCommand(myCommand=cmd)
                text=self._getErrorText()
            else:
                text='Remove failed with repository command processing error'               
        else:
            text='Remove failed due with repository project path issue: %s' % targetPath                                                
            self.__lfh.write("+ERROR - CvsSandBoxAdmin(remove) cannot remove project path %s\n" % targetPath)            

        return (ok,text)

    def __getCheckOutProjectCmd(self, relProjectPath, revId=None):
        """ Return CVS command for checkout of a complete project from the current repository.
        """
        if self._wrkPath is None:
            self._makeTempWorkingDir()        
        errPath=self._getErrorFilePath()
        if self._setCvsRoot():
            cmd = " cd " + self.__sandBoxTopPath + " ; "
            if revId is None:
                cmd+="cvs -d " +  self._cvsRoot  + " co " + relProjectPath + \
                      self._getRedirect(fileNameOut=errPath,fileNameErr=errPath) + " ; "
            else:
                rS=" -r " + revId + " "
                cmd+="cvs -d " +  self._cvsRoot  + " co " +  rS + relProjectPath + \
                     self._getRedirect(fileNameOut=errPath,fileNameErr=errPath) + ' ; '
        else:
            cmd=None
        return cmd

    def __getUpdateProjectCmd(self, projectDir, prune=False):
        """ Return CVS command for updating a complete project working directory from current repository.
        """
        if self._wrkPath is None:
            self._makeTempWorkingDir()                
        errPath=self._getErrorFilePath()
        if self._setCvsRoot():
            if prune:
                pF=" -P "
            else:
                pF=" "
            targetPath=os.path.join(self.__sandBoxTopPath,projectDir)
            cmd = " cd " + targetPath + "; "
            cmd+="cvs -d " +  self._cvsRoot  + " update -C -d " + pF + \
                      self._getRedirect(fileNameOut=errPath,fileNameErr=errPath) + " ; "
        else:
            cmd=None
        return cmd

    def __getUpdateCmd(self, projectDir, relProjectPath, prune=False):
        """ Return CVS command for updating the input relative path within project working
            directory from current repository.
        """        
        if self._wrkPath is None:
            self._makeTempWorkingDir()                
        errPath=self._getErrorFilePath()
        if self._setCvsRoot():
            if prune:
                pF=" -P "
            else:
                pF=" "
            targetPath=os.path.join(self.__sandBoxTopPath,projectDir)
            cmd = " cd " + targetPath + "; "
            cmd+="cvs -d " +  self._cvsRoot  + " update -C -d " + pF + relProjectPath + \
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

    def __getCommitCmd(self, projectDir, relProjectPath, message="Automated update"):
        if self._wrkPath is None:
            self._makeTempWorkingDir()        
        errPath=self._getErrorFilePath()
        if self._setCvsRoot():
            cmd = " cd " + os.path.join(self.__sandBoxTopPath,projectDir) + " ; "
            if message is not None and len(message) > 0:
                qm=' -m "'+message+'" '
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

