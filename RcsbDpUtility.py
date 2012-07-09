##
# File: RcsbDpUtility.py
# Date: 09-Sep-2010
#
# Updates:
# 9-Sep-2010  jdw  Imported from RcsbDpUtils.py to avoid possible problems with existing code.
# 9-Sep-2010  jdw  Extension of RcsbDpUtil generalizing configuration information.
# 10-Sep-2010 jdw  Added new chemical component applications.
#                  Added methods of set additional input files and parameters.
# 14-Sep-2010 jdw  Clarify the roles of tmpDir and wrkDir.
#  5-Dec-2010 jdw  Add parameter for link_radii to bond distance calculation
#  5-Dec-2010 jdw  Add parameters for bond_radii and inst_id for chemical component batch assignment.
# 13-Dec-2010 jdw  Add additional explicit environment for cc-tools apps
# 01-Feb-2011 rps  Updated to accommodate "chem-comp-assign-validation" operation
# 16-Feb-2011 rps  "cif2cif-pdbx-skip-process" added to support creation of cif file amenable to load into jmol
# 03-May-2011 jdw update maxit operations
# 23-Jun-2011 jdw add hostname to differentiate temp/working directory -
# 27-Jun-2011 jdw revised configuration error reporting.  Added comp_path for maxit.
# 29-Jun-2011 jdw add additional configuration checks.
# 14-Jun-2012 jdw add user selection option for op="chem-comp-instance-update"
# 25-Jun-2012 jdw add new annotation methods from annotation-pack
#  3-Jul-2012 jdw add new sequence merge data application
#                         update command arguments for "chem-comp-instance-update"
#  4-Jul-2012 jdw add optional assembly analysis arguments 
##
"""
Wrapper class for data processing and chemical component utilities.

Initial RCSB version - adapted from file utils method collections.


"""
import sys, os, os.path, glob, time, datetime, shutil, tempfile
import socket

from wwpdb.utils.rcsb.DataFile    import DataFile
from wwpdb.api.facade.ConfigInfo  import ConfigInfo

class RcsbDpUtility(object):
    """ Wrapper class for data processing and chemical component utilities.
    """
    def __init__(self, tmpPath="/scratch", siteId="DEV",  verbose=False, log=sys.stderr):
        self.__verbose  = verbose
        self.__debug    = True
        self.__lfh      = log
        #
        # tmpPath is used (if it exists) to place working directories if these are not explicitly set.
        # This path is not used otherwise.
        #
        self.__tmpPath  = tmpPath
        self.__siteId   = siteId
        #
        # Working directory and file path details
        #
        # The working directory is where temporary files are stored by utility operations.
        # This can be set explicity via the self.setWorkingDir() method or will be created
        # as a temporary path dynamically as a subdirectory of self.__tmpDir.
        #
        self.__wrkPath        = None
        self.__sourceFileList = []
        self.__resultPathList = []                
        self.__inputParamDict  = {}
        #
        # List of known operations --- 
        self.__maxitOps = ["cif2cif","cif2cif-remove","cif2cif-ebi","cif2cif-pdbx","cif2cif-pdbx-skip-process","cif-rcsb2cif-pdbx",
                           "cif-seqed2cif-pdbx", "cif2pdb","pdb2cif","pdb2cif-ebi","switch-dna",
                           "cif2pdb-assembly","pdbx2pdb-assembly","pdbx2deriv"]
        self.__rcsbOps = [ "rename-atoms", "cif2pdbx", "pdbx2xml", "pdb2dssp", "pdb2stride",
                           "initial-version","poly-link-dist","chem-comp-link", "chem-comp-assign",
                           "chem-comp-assign-validation", "chem-comp-instance-update"]
        self.__pisaOps = ["pisa-analysis","pisa-assembly-report-xml","pisa-assembly-report-text",
                          "pisa-interface-report-xml","pisa-assembly-coordinates-pdb","pisa-assembly-coordinates-cif",
                          "pisa-assembly-coordinates-cif","pisa-assembly-merge-cif"]
        self.__annotationOps = ["annot-secondary-structure", "annot-link-ssbond", "annot-distant-solvent",
                                "annot-merge-struct-site","annot-reposition-solvent","annot-base-pair-info",
                                "annot-validation","annot-site"]

        #
        # Source, destination and logfile path details
        #
        self.__srcPath     = None
        self.__dstPath     = None
        self.__dstLogPath  = None
        self.__dstErrorPath  = None        
        #
        self.__stepOpList  = []
        self.__stepNo      = 0
        self.__stepNoSaved = None

        self.__cI=ConfigInfo(self.__siteId)        
        self.__initPath()

    def __getConfigPath(self, ky):
        try:
            pth =  os.path.abspath(self.__cI.get(ky))
            if (self.__debug): 
                self.__lfh.write("++INFO - site %s configuration for %s is %s\n" % (self.__siteId,ky,pth))            
        except:
            if (self.__verbose): 
                self.__lfh.write("++WARN - site %s configuration data missing for %s\n" % (self.__siteId,ky))
            pth = ''
        return pth

    def __initPath(self):
        """ Provide placeholder values for application specific path details
        """
        #
        self.__rcsbAppsPath  = None
        self.__localAppsPath = None
        self.__annotAppsPath = None
        self.__toolsPath = None        
        #
        
    def setRcsbAppsPath(self,fPath):
        """ Set or overwrite the configuration setting for __rcsbAppsPath.
        """ 
        if (fPath != None and os.path.isdir(fPath)):
            self.__rcsbAppsPath = os.path.abspath(fPath)

    def setAppsPath(self,fPath):
        """ Set or overwrite the configuration setting for __localAppsPath.
        """         
        if (fPath != None and os.path.isdir(fPath)):
            self.__localAppsPath = os.path.abspath(fPath)

    def saveResult(self):
        return(self.__stepNo)
    
    def useResult(self,stepNo):
        if (stepNo > 0 and stepNo <= self.__stepNo):
            self.__stepNoSaved = stepNo
            if (self.__verbose): 
                self.__lfh.write("++INFO - Using result from step %s\n" % self.__stepNoSaved)        
        
    def __makeTempWorkingDir(self):
        hostName=str(socket.gethostname()).split('.')[0]
        if ((hostName is not None) and (len(hostName) > 0)):
            suffix = '-' + hostName
        else:
            suffix = '-dir'

        prefix='rcsb-'
        if (self.__tmpPath != None and os.path.isdir(self.__tmpPath)):
            self.__wrkPath = tempfile.mkdtemp(suffix,prefix,self.__tmpPath)
        else:
            self.__wrkPath = tempfile.mkdtemp(suffix,prefix)            

        
    def setWorkingDir(self,dPath):
        if (not os.path.isdir(dPath)):
            os.makedirs(dPath,0755)
        if (os.access(dPath,os.F_OK)):
            self.__wrkPath = os.path.abspath(dPath)

    def getWorkingDir(self):
        return self.__wrkPath

    def setSource(self, fPath):
        if (os.access(fPath,os.F_OK)):
            self.__srcPath = os.path.abspath(fPath)
        else:
            self.__srcPath = None
        self.__stepNo      = 0

    def setDestination(self,fPath):
        self.__dstPath = os.path.abspath(fPath)

    def setErrorDestination(self,fPath):
        self.__dstErrorPath = os.path.abspath(fPath)

    def setLogDestination(self,fPath):
        self.__dstLogPath = os.path.abspath(fPath)
        
    def op(self,op):
        if (self.__srcPath == None): return

        if (self.__wrkPath == None):
            self.__makeTempWorkingDir()

        self.__stepOpList.append(op)
        
        if op in self.__maxitOps:
            self.__stepNo += 1            
            self.__maxitStep(op)
        elif op in self.__rcsbOps:
            self.__stepNo += 1            
            self.__rcsbStep(op)

        elif op in self.__pisaOps:
            self.__stepNo += 1            
            self.__pisaStep(op)

        elif op in self.__annotationOps:
            self.__stepNo += 1            
            self.__annotationStep(op)            

        else:
            self.__lfh.write("++ERROR - Unknown operation %s\n" % op)
        

    def __getSourceWrkFileList(self,stepNo):
        """Build a file containing the current list of source files.
        """
        fn = "input_file_list_"  + str(stepNo)
        if (self.__wrkPath != None):
            iPathList=os.path.join(self.__wrkPath,fn)
        else:
            iPathList= fn
        #
        ofh = open(iPathList,'w')        
        if (self.__sourceFileList == []):
            ofh.write("%s\n" % self.__getSourceWrkFile(self.__stepNo))
        else:
            for f in self.__sourceFileList == []:
                ofh.write("%s\n",f)
        ofh.close()
        #        
        return(iPathList)
    
    def __getSourceWrkFile(self,stepNo):
        return("input_file_"  + str(stepNo))

    def __getResultWrkFile(self,stepNo):        
        return("result_file_"  + str(stepNo))

    def __getLogWrkFile(self,stepNo):        
        return("log_file_"  + str(stepNo))

    def __getErrWrkFile(self,stepNo):        
        return("error_file_"  + str(stepNo))

    def __getTmpWrkFile(self,stepNo):        
        return("temp_file_"  + str(stepNo))                

    def __updateInputPath(self):
        """Shuffle the output from the previous step or a selected previous
           step as the input for the current operation.
        """
        #
        if (self.__stepNo > 1):
            if (self.__stepNoSaved != None ):
                return(self.__getResultWrkFile(self.__stepNoSaved) )
                self.__stepNoSaved = None
            else:
                return(self.__getResultWrkFile(self.__stepNo - 1))


    def __annotationStep(self, op):
        """ Internal method that performs a single annotation application operation.
        """
        #
        # Set application specific path details here -
        #
        self.__annotAppsPath  =  self.__getConfigPath('SITE_ANNOT_TOOLS_PATH')
        self.__toolsPath      =  self.__getConfigPath('SITE_TOOLS_PATH')        

        if self.__rcsbAppsPath is None:        
            self.__rcsbAppsPath  =  self.__getConfigPath('SITE_RCSB_APPS_PATH')        
        #
        # These may not be needed -- 
        self.__pdbxDictPath  =  self.__getConfigPath('SITE_PDBX_DICT_PATH')
        self.__pathDdlSdb      = os.path.join(self.__pdbxDictPath,"mmcif_ddl.sdb")
        self.__pathPdbxDictSdb = os.path.join(self.__pdbxDictPath,"mmcif_pdbx.sdb")
        self.__pathPdbxDictOdb = os.path.join(self.__pdbxDictPath,"mmcif_pdbx.odb")
        #
        #
        iPath=     self.__getSourceWrkFile(self.__stepNo)
        iPathList= self.__getSourceWrkFileList(self.__stepNo)
        oPath=     self.__getResultWrkFile(self.__stepNo)
        lPath=     self.__getLogWrkFile(self.__stepNo)
        ePath=     self.__getErrWrkFile(self.__stepNo)
        tPath=     self.__getTmpWrkFile(self.__stepNo)        
        #
        if (self.__wrkPath != None):
            ePathFull=os.path.join(self.__wrkPath, ePath)
            lPathFull=os.path.join(self.__wrkPath, lPath)
            tPathFull=os.path.join(self.__wrkPath, tPath)                                    
            cmd = "(cd " + self.__wrkPath
        else:
            ePathFull = ePath
            lPathFull = lPath
            tPathFull = tPath            
            cmd = "("
        #
        if (self.__stepNo > 1):
            pPath = self.__updateInputPath()
            if (os.access(pPath,os.F_OK)):            
                cmd += "; cp " + pPath + " "  + iPath
        #
        if (op == "annot-secondary-structure"):
            cmdPath =os.path.join(self.__annotAppsPath,"bin","GetSecondStruct")
            thisCmd  = " ; " + cmdPath                        
            cmd += " ; RCSBROOT=" + self.__rcsbAppsPath + " ; export RCSBROOT "            
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log " 
            #
            if  self.__inputParamDict.has_key('ss_topology_file_path'):
                topFilePath=self.__inputParamDict['ss_topology_file_path']                                
                cmd += " -support " + topFilePath
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            cmd += " ; cat annot-step.log " + " >> " + lPath
            
        elif (op == "annot-link-ssbond"):
            cmdPath =os.path.join(self.__annotAppsPath,"bin","GetLinkAndSSBond")
            thisCmd  = " ; " + cmdPath                        
            cmd += " ; RCSBROOT=" + self.__rcsbAppsPath + " ; export RCSBROOT "            
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log  -link -ssbond " 
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif (op == "annot-distant-solvent"):
            cmdPath =os.path.join(self.__annotAppsPath,"bin","CalculateDistantWater")
            thisCmd  = " ; " + cmdPath                        
            cmd += " ; RCSBROOT=" + self.__rcsbAppsPath + " ; export RCSBROOT "            
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log " 
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif (op == "annot-base-pair-info"):
            cmdPath =os.path.join(self.__annotAppsPath,"bin","GetBasePairInfo")
            thisCmd  = " ; " + cmdPath                        
            cmd += " ; RCSBROOT=" + self.__rcsbAppsPath + " ; export RCSBROOT "            
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log " 
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            cmd += " ; cat annot-step.log " + " >> " + lPath
        elif (op == "annot-merge-struct-site"):
            cmdPath =os.path.join(self.__annotAppsPath,"bin","MergeSiteData")
            thisCmd  = " ; " + cmdPath                        
            cmd += " ; RCSBROOT=" + self.__rcsbAppsPath + " ; export RCSBROOT "            
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log "
            if  self.__inputParamDict.has_key('site_info_file_path'):
                topFilePath=self.__inputParamDict['site_info_file_path']                                
                cmd += " -site " + topFilePath            
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif (op == "annot-reposition-solvent"):
            cmdPath =os.path.join(self.__annotAppsPath,"bin","MovingWater")
            thisCmd  = " ; " + cmdPath                        
            cmd += " ; RCSBROOT=" + self.__rcsbAppsPath + " ; export RCSBROOT "            
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log " 
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            cmd += " ; cat annot-step.log " + " >> " + lPath
            
        elif (op == "annot-validation"):
            cmdPath =os.path.join(self.__annotAppsPath,"bin","valdation_with_cif_output")
            thisCmd  = " ; " + cmdPath                        
            cmd += " ; RCSBROOT=" + self.__rcsbAppsPath + " ; export RCSBROOT "            
            cmd += thisCmd + " -cif " + iPath + " -output " + oPath + " -log annot-step.log " 
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            cmd += " ; cat annot-step.log " + " >> " + lPath


        elif (op == "annot-site"):
            cmd += " ; TOOLS_PATH="  + self.__toolsPath    + " ; export TOOLS_PATH "
            cmd += " ; CCP4="        + os.path.join(self.__toolsPath,"ccp4")  + " ; export CCP4 "            
            cmd += " ; SYMINFO="     + os.path.join(self.__toolsPath,"getsite-cif","data","syminfo.lib") + " ; export SYMINFO "
            cmd += " ; MMCIFDIC="    + os.path.join(self.__toolsPath,"getsite-cif","data","cif_mmdic.lib")  + " ; export MMCIFDIC "         
            cmd += " ; STANDATA="    + os.path.join(self.__toolsPath,"getsite-cif","data","standard_geometry.cif")  + " ; export STANDATA "
            cmd += " ; STANDATA="    + os.path.join(self.__toolsPath,"getsite-cif","data","standard_geometry.cif")  + " ; export STANDATA "
            cmd += " ; CCIF_NOITEMIP=off ; export CCIF_NOITEMIP "
            # setenv DYLD_LIBRARY_PATH  "$CCP4/lib/ccif:$CCP4/lib"

            cmd += " ; DYLD_LIBRARY_PATH=" + os.path.join(self.__toolsPath,"ccp4","lib","ccif") + ":" + \
                   os.path.join(self.__toolsPath,"ccp4","lib") + " ; export DYLD_LIBRARY_PATH "

            cmd += " ; LD_LIBRARY_PATH=" + os.path.join(self.__toolsPath,"ccp4","lib","ccif") + ":" + \
                   os.path.join(self.__toolsPath,"ccp4","lib") + " ; export LD_LIBRARY_PATH "                        

            # setenv CIFIN 1abc.cif
            cmd += " ; CIFIN=" + iPath+ " ; export CIFIN "
            #cmd += " ; env "

            if  self.__inputParamDict.has_key('block_id'):
                blockId=self.__inputParamDict['block_id']                                
            else:
                blockId="UNK"

                
            # ../getsite_cif 1abc


            cmdPath =os.path.join(self.__toolsPath,"getsite-cif","bin","getsite_cif")
            thisCmd  = " ; " + cmdPath                        

            cmd += thisCmd + " " + blockId + " "
            
            if  self.__inputParamDict.has_key('site_arguments'):
                cmdArgs=self.__inputParamDict['site_arguments']                                
                cmd += cmdArgs            
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; mv -f " + blockId + "_site.cif " + oPath                         

        elif (op == "annot-merge-sequence-data"):
            cmdPath =os.path.join(self.__annotAppsPath,"bin","MergeSeqModuleData")
            thisCmd  = " ; " + cmdPath                        
            cmd += " ; RCSBROOT=" + self.__rcsbAppsPath + " ; export RCSBROOT "            
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log "
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            cmd += " ; cat annot-step.log " + " >> " + lPath

        else:
            
            return -1
        #
        
        if (self.__debug):
            self.__lfh.write("++INFO - Application string:\n%s\n" % cmd.replace(";","\n"))        
        #
        if (self.__verbose):            
            cmd += " ; ls -la  > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                                    
            
        cmd += " ) > %s 2>&1 " % ePathFull

        cmd += " ; echo '-BEGIN-PROGRAM-ERROR-LOG--------------------------\n'  >> " + lPathFull                
        cmd += " ; cat " + ePathFull + " >> " + lPathFull
        cmd += " ; echo '-END-PROGRAM-ERROR-LOG-------------------------\n'  >> " + lPathFull                        


        ofh = open(lPathFull,'w')
        lt = time.strftime("%Y %m %d %H:%M:%S", time.localtime())
        ofh.write("\n\n-------------------------------------------------\n")
        ofh.write("LogFile:      %s\n" % lPath)
        ofh.write("Working path: %s\n" % self.__wrkPath)
        ofh.write("Date:         %s\n" % lt)
        if (self.__verbose):
            ofh.write("\nStep command:\n%s\n-------------------------------------------------\n" % cmd.replace(";","\n"))
        ofh.close()
           
        iret = os.system(cmd)
        
        self.__resultPathList = [os.path.join(self.__wrkPath,oPath)]
        
        return iret
    
        
    def __maxitStep(self, op, progName="maxit"):
        """ Internal method that performs a single maxit operation.
         
        """
        # Set application specific path details --
        #
        # If this has not been initialized take if from the configuration class.        
        if self.__rcsbAppsPath is None:        
            self.__rcsbAppsPath  =  self.__getConfigPath('SITE_RCSB_APPS_PATH')
        self.__ccCvsPath     =  self.__getConfigPath('SITE_CC_CVS_PATH')        
        # 
        iPath=     self.__getSourceWrkFile(self.__stepNo)
        iPathList= self.__getSourceWrkFileList(self.__stepNo)
        oPath=     self.__getResultWrkFile(self.__stepNo)
        lPath=     self.__getLogWrkFile(self.__stepNo)
        ePath=     self.__getErrWrkFile(self.__stepNo)        
        #
        if (self.__wrkPath != None):
            lPathFull=os.path.join(self.__wrkPath, lPath)            
            ePathFull=os.path.join(self.__wrkPath, ePath)
            cmd = "(cd " + self.__wrkPath
        else:
            ePathFull = ePath
            lPathFull = lPath
            cmd = "("
        #
        if (self.__stepNo > 1):
            pPath = self.__updateInputPath()
            if (os.access(pPath,os.F_OK)):            
                cmd += "; cp " + pPath + " "  + iPath
        #
        maxitPath   = os.path.join(self.__rcsbAppsPath,"bin",progName)        
        maxitCmd = " ; RCSBROOT=" + self.__rcsbAppsPath
        if ((self.__ccCvsPath is not None) and (len(self.__ccCvsPath) > 0)):
            maxitCmd += " ; COMP_PATH=" + self.__ccCvsPath
        maxitCmd += " ; "   +  maxitPath + " -path " + self.__rcsbAppsPath


        if (op == "cif2cif"):
            cmd +=  maxitCmd + " -o 8  -i " + iPath
            cmd += " ; mv -f " + iPath + ".cif " + oPath

        elif (op == "cif2cif-remove"):
            cmd +=  maxitCmd + " -o 8  -remove -i " + iPath
            cmd += " ; mv -f " + iPath + ".cif " + oPath

        elif (op == "cif-rcsb2cif-pdbx"):
            cmd +=  maxitCmd + " -o 56  -i " + iPath            
            cmd += " ; mv -f " + iPath + ".cif " + oPath                         

        elif (op == "cif-seqed2cif-pdbx"):
            cmd +=  maxitCmd + " -o 10  -i " + iPath                        
            cmd += " ; mv -f " + iPath + ".cif " + oPath                         

        elif (op == "cif2cif-pdbx"):
            cmd +=  maxitCmd + " -o 8 -standard -pdbids -no_deriv -no_pdbx_strand_id -no_site -i " + iPath
            cmd += " ; mv -f " + iPath + ".cif " + oPath          
            
        elif (op == "cif2cif-pdbx-skip-process"):
            cmd +=  maxitCmd + " -o 8 -skip_process -i " + iPath
            cmd += " ; mv -f " + iPath + ".cif " + oPath             

        elif (op == "cif2cif-ebi"):
            cmd +=  maxitCmd + " -o 8  "
            cmd += " -get_biol_unit -pdbids -i " + iPath
            cmd += " ; mv -f " + iPath + ".cif " + oPath
            
        elif (op == "pdb2cif"):
            cmd +=  maxitCmd + " -o 1  -i " + iPath
            cmd += " ; mv -f " + iPath + ".cif " + oPath             

        elif (op == "pdb2cif-ebi"):
            cmd +=  maxitCmd + " -o 1  -i " + iPath
            cmd += " ; mv -f " + iPath + ".cif " + oPath             

        elif (op == "cif2pdb"):
            cmd +=  maxitCmd + " -o 2  -i " + iPath
            cmd += " ; mv -f " + iPath + ".pdb " + oPath

        elif (op == "switch-dna"):
            cmd +=  maxitCmd + " -o 68  -i " + iPath
            cmd += " ; mv -f " + iPath + ".cif " + oPath
            
        elif (op == "cif2pdb-assembly"):
            cmd +=  maxitCmd + " -o 55 -pdbids  -i " + iPath

        elif (op == "pdbx2pdb-assembly"):
            cmd +=  maxitCmd + " -o 55 -exchange_in -pdbids  -i " + iPath

        elif (op == "pdbx2deriv"):
            cmd +=  maxitCmd + " -o 60 -exchange_in -exchange_out -pdbids  -i " + iPath
            cmd += " ;  cp -f  *-deriv.cif " + oPath
        else:
            return -1
        #
        if (self.__verbose):            
            cmd += " ; ls -la >> " + lPath        
        #
        cmd += " ; echo '-BEGIN-PROGRAM-ERROR-LOG--------------------------\n'  >> " + lPath        
        cmd += " ; cat maxit.err >> " + lPath
        cmd += " ; echo '-END-PROGRAM-ERROR-LOG--------------------------\n'  >> " + lPath        

            
        cmd += " ; rm -f maxit.err >> " + lPath
        cmd += " ) > %s 2>&1 " % ePathFull
        
        if (self.__debug):
            self.__lfh.write("++INFO - Command string:\n%s\n" % cmd.replace(";","\n"))

        ofh = open(lPathFull,'w')
        lt = time.strftime("%Y %m %d %H:%M:%S", time.localtime())
        ofh.write("\n\n-------------------------------------------------\n")
        ofh.write("LogFile:      %s\n" % lPath)
        ofh.write("Working path: %s\n" % self.__wrkPath)
        ofh.write("Date:         %s\n" % lt)
        if (self.__verbose): ofh.write("\nStep command:\n%s\n-------------------------------------------------\n" % cmd.replace(";","\n"))
        ofh.write("\n")
        ofh.close()

        iret = os.system(cmd)
        #
        if ((op == "cif2pdb-assembly") or (op == "pdbx2pdb-assembly")):
            pat = self.__wrkPath + '/*.pdb[1-9]*'
            self.__resultPathList= glob.glob(pat)
        
        else:
            self.__resultPathList = [os.path.join(self.__wrkPath,oPath)]
        
        return iret


    def __rcsbStep(self, op):
        """ Internal method that performs a single rcsb application operation.
        """
        #
        # Set application specific path details here -
        #
        if self.__rcsbAppsPath is None:                
            self.__rcsbAppsPath  =  self.__getConfigPath('SITE_RCSB_APPS_PATH')
        if self.__localAppsPath is None:                            
            self.__localAppsPath =  self.__getConfigPath('SITE_LOCAL_APPS_PATH')

        #
        self.__ccAppsPath    =  self.__getConfigPath('SITE_CC_APPS_PATH')
        self.__pdbxDictPath  =  self.__getConfigPath('SITE_PDBX_DICT_PATH')
        self.__ccDictPath    =  self.__getConfigPath('SITE_CC_DICT_PATH')
        self.__ccCvsPath     =  self.__getConfigPath('SITE_CC_CVS_PATH')

        
        self.__ccDictPathSdb = os.path.join(self.__ccDictPath,"Components-all-v3.sdb")
        self.__ccDictPathIdx = os.path.join(self.__ccDictPath,"Components-all-v3-r4.idx")        
        #
        self.__pathDdlSdb      = os.path.join(self.__pdbxDictPath,"mmcif_ddl.sdb")
        self.__pathPdbxDictSdb = os.path.join(self.__pdbxDictPath,"mmcif_pdbx.sdb")
        self.__pathPdbxDictOdb = os.path.join(self.__pdbxDictPath,"mmcif_pdbx.odb")
        #
        self.__oeDirPath        = self.__getConfigPath('SITE_CC_OE_DIR')
        self.__oeLicensePath    = self.__getConfigPath('SITE_CC_OE_LICENSE')
        self.__babelDirPath     = self.__getConfigPath('SITE_CC_BABEL_DIR')
        self.__babelDataDirPath = self.__getConfigPath('SITE_CC_BABEL_DATADIR')
        self.__cactvsDirPath    = self.__getConfigPath('SITE_CC_CACTVS_DIR')

        # -------------
        #
        iPath=     self.__getSourceWrkFile(self.__stepNo)
        iPathList= self.__getSourceWrkFileList(self.__stepNo)
        oPath=     self.__getResultWrkFile(self.__stepNo)
        lPath=     self.__getLogWrkFile(self.__stepNo)
        ePath=     self.__getErrWrkFile(self.__stepNo)
        tPath=     self.__getTmpWrkFile(self.__stepNo)        
        #
        if (self.__wrkPath != None):
            ePathFull=os.path.join(self.__wrkPath, ePath)
            lPathFull=os.path.join(self.__wrkPath, lPath)
            tPathFull=os.path.join(self.__wrkPath, tPath)                                    
            cmd = "(cd " + self.__wrkPath
        else:
            ePathFull = ePath
            lPathFull = lPath
            tPathFull = tPath            
            cmd = "("
        #
        if (self.__stepNo > 1):
            pPath = self.__updateInputPath()
            if (os.access(pPath,os.F_OK)):            
                cmd += "; cp " + pPath + " "  + iPath
        #
        
        if (op == "rename-atoms"):
            cmdPath   = os.path.join(self.__ccAppsPath,"bin","switch-atom-element")
            thisCmd    = " ; "   + cmdPath + " -dicodb " + self.__ccDictPathSdb            
            cmd += thisCmd + " -file " + iPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; mv -f " + iPath + ".cif " + oPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
        elif (op == "initial-version"):
            cmdPath   = os.path.join(self.__rcsbAppsPath,"bin","cif-version")
            thisCmd    = " ; "   + cmdPath 
            cmd += thisCmd + " -newfile " + iPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; mv -f " + iPath + ".cif " + oPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
        elif (op == "cif2pdbx"):
            #   need to have an input file list.
            cmdPath = os.path.join(self.__localAppsPath,"bin","cifexch-v3.2")
            thisCmd  = " ; " + cmdPath + " -ddlodb " + self.__pathDdlSdb +" -dicodb " + self.__pathPdbxDictSdb 
            thisCmd += " -reorder  -strip -op in  -pdbids "

            cmd += thisCmd + " -inlist " + iPathList
            cmd += " ; mv -f " + iPath + ".tr " + oPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath            

        elif (op == "pdbx2xml"):
            cmdPath =  os.path.join(self.__localAppsPath,"bin","mmcif2XML")
            thisCmd  =  " ; " + cmdPath + " -prefix  pdbx -ns PDBx -funct mmcif2xmlall "
            thisCmd +=  " -dict mmcif_pdbxR.dic " " -df " + self.__pathPdbxDictOdb
            cmd += thisCmd + " -f " + iPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        

        elif (op == "pdb2dssp"):
            cmdPath = os.path.join(self.__localAppsPath,"bin","dssp")
            thisCmd = " ;  " + cmdPath             
            cmd += thisCmd + "  " + iPath + " " + oPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            #  /lcl/bin/dssp ${id}.ent ${id}.dssp >&  ${id}.dssp.log
        elif (op == "pdb2stride"):
            cmdPath = os.path.join(self.__localAppsPath,"bin","stride")
            thisCmd = " ;  " + cmdPath             
            cmd += thisCmd + " -f" + oPath + " " + iPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            # /lcl/bin/stride -f${id}.stride  ${id}.ent >&  ${id}.stride.log
        elif (op == "poly-link-dist"):
            cmdPath =os.path.join(self.__rcsbAppsPath,"bin","cal_polymer_linkage_distance")
            thisCmd  = " ; " + cmdPath            
            cmd += " ; RCSBROOT=" + self.__rcsbAppsPath + " ; export RCSBROOT "            
            cmd += thisCmd + " -i " + iPath + " -o " + oPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
        elif (op == "chem-comp-link"):
            cmdPath =os.path.join(self.__rcsbAppsPath,"bin","bond_dist")
            thisCmd  = " ; " + cmdPath                        
            cmd += " ; RCSBROOT=" + self.__rcsbAppsPath + " ; export RCSBROOT "            
            cmd += thisCmd + " -i " + iPath + " -o " + oPath + " -format cif "
            if  self.__inputParamDict.has_key('cc_link_radii'):
                link_radii=self.__inputParamDict['cc_link_radii']                                
                cmd += " -link_radii " + link_radii
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            cmd += " ; cat bond_dist.err" + " >> " + lPath                        
        elif (op == "chem-comp-assign"):
            # set up
            #
            cmd += " ; RCSBROOT="      + self.__rcsbAppsPath     + " ; export RCSBROOT "
            cmd += " ; OE_DIR="        + self.__oeDirPath        + " ; export OE_DIR "
            cmd += " ; OE_LICENSE="    + self.__oeLicensePath    + " ; export OE_LICENSE "
            cmd += " ; BABEL_DIR="     + self.__babelDirPath     + " ; export BABEL_DIR "
            cmd += " ; BABEL_DATADIR=" + self.__babelDataDirPath + " ; export BABEL_DATADIR "
            cmd += " ; CACTVS_DIR="    + self.__cactvsDirPath    + " ; export CACTVS_DIR "
            cmd += " ; env "
            cmdPath =os.path.join(self.__ccAppsPath,"bin","ChemCompAssign_main")
            thisCmd  = " ; " + cmdPath                        
            entryId   = self.__inputParamDict['id']
            #
            #cc_link_file_path=''
            #if  self.__inputParamDict.has_key('link_file_path'):
            #    link_file=self.__inputParamDict['link_file_path']                
            #    cmd += " ;  cp " + link_file + " " + self.__wrkPath
            #
            cmd += thisCmd + " -i " + iPath + " -of " + oPath + " -o " + self.__wrkPath  +  " -ifmt pdbx " + " -id " + entryId
            cmd += " -libsdb " + self.__ccDictPathSdb + " -idxFile " +  self.__ccDictPathIdx
            #
            if  self.__inputParamDict.has_key('cc_link_file_path'):
                cmd += " -bond_info " + self.__inputParamDict['cc_link_file_path']
            #
            if  self.__inputParamDict.has_key('cc_instance_id'):
                cmd += " -radii_inst_id " + self.__inputParamDict['cc_instance_id']
            #
            if  self.__inputParamDict.has_key('cc_bond_radii'):
                cmd += " -bond_radii " + self.__inputParamDict['cc_bond_radii']                
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
        elif (op == "chem-comp-assign-validation"):
            # set up
            #
            cmd += " ; RCSBROOT="      + self.__rcsbAppsPath     + " ; export RCSBROOT "
            cmd += " ; OE_DIR="        + self.__oeDirPath        + " ; export OE_DIR "
            cmd += " ; OE_LICENSE="    + self.__oeLicensePath    + " ; export OE_LICENSE "
            cmd += " ; BABEL_DIR="     + self.__babelDirPath     + " ; export BABEL_DIR "
            cmd += " ; BABEL_DATADIR=" + self.__babelDataDirPath + " ; export BABEL_DATADIR "
            cmd += " ; CACTVS_DIR="    + self.__cactvsDirPath    + " ; export CACTVS_DIR "
            cmd += " ; env "
            cmdPath =os.path.join(self.__ccAppsPath,"bin","ChemCompAssign_main")
            thisCmd  = " ; " + cmdPath                        
            entryId   = self.__inputParamDict['id']
            #
            #cc_link_file_path=''
            #if  self.__inputParamDict.has_key('link_file_path'):
            #    link_file=self.__inputParamDict['link_file_path']                
            #    cmd += " ;  cp " + link_file + " " + self.__wrkPath
            # 
            cmd += thisCmd + " -i " + iPath + " -of " + oPath + " -o " + self.__wrkPath  +  " -ifmt pdbx " + " -id " + entryId
            cmd += " -libsdb " + self.__ccDictPathSdb + " -idxFile " +  self.__ccDictPathIdx
            cmd += " -force "
            #
            if  self.__inputParamDict.has_key('cc_validation_ref_file_path'):
                cmd += " -ref " + self.__inputParamDict['cc_validation_ref_file_path']
            #
            if  self.__inputParamDict.has_key('cc_validation_instid_list'):
                cmd += " -search_inst_id " + self.__inputParamDict['cc_validation_instid_list']
            #
            '''
            if  self.__inputParamDict.has_key('cc_bond_radii'):
                cmd += " -bond_radii " + self.__inputParamDict['cc_bond_radii']
            #
            if  self.__inputParamDict.has_key('cc_link_file_path'):
                cmd += " -bond_info " + self.__inputParamDict['cc_link_file_path']
            '''
            #
            cmd += " -log "+self.__inputParamDict['cc_validation_log_file']
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
        elif (op == "chem-comp-instance-update"):
            cmdPath =os.path.join(self.__ccAppsPath,"bin","updateInstance")
            thisCmd  = " ; " + cmdPath                        
            assignPath = self.__inputParamDict['cc_assign_file_path']
            #selectPath = self.__inputParamDict['cc_select_file_path']            
            cmd += thisCmd + " -i " + iPath + " -o " + oPath + " -assign " + assignPath + " -ifmt pdbx " 
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
        else:
            return -1
        #
        
        if (self.__debug):
            self.__lfh.write("++INFO - Application string:\n%s\n" % cmd.replace(";","\n"))        
        #
        if (self.__verbose):            
            cmd += " ; ls -la  > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                                    
            
        cmd += " ) > %s 2>&1 " % ePathFull

        cmd += " ; echo '-BEGIN-PROGRAM-ERROR-LOG--------------------------\n'  >> " + lPathFull                
        cmd += " ; cat " + ePathFull + " >> " + lPathFull
        cmd += " ; echo '-END-PROGRAM-ERROR-LOG-------------------------\n'  >> " + lPathFull                        


        ofh = open(lPathFull,'w')
        lt = time.strftime("%Y %m %d %H:%M:%S", time.localtime())
        ofh.write("\n\n-------------------------------------------------\n")
        ofh.write("LogFile:      %s\n" % lPath)
        ofh.write("Working path: %s\n" % self.__wrkPath)
        ofh.write("Date:         %s\n" % lt)
        if (self.__verbose):
            ofh.write("\nStep command:\n%s\n-------------------------------------------------\n" % cmd.replace(";","\n"))
        ofh.close()
           
        iret = os.system(cmd)
        #
        if ((op == "pdbx2xml")):
            pat = self.__wrkPath + '/*.xml*'
            self.__resultPathList= glob.glob(pat)
        else:
            self.__resultPathList = [os.path.join(self.__wrkPath,oPath)]
        
        return iret

    def __pisaStep(self, op):
        """ Internal method that performs a single tool application operation.

        """
        #
        pisaTopPath       =  self.__getConfigPath('SITE_PISA_TOP_PATH')
        annotToolsPath    =  self.__getConfigPath('SITE_ANNOT_TOOLS_PATH')
        
        
        #
        iPath=     self.__getSourceWrkFile(self.__stepNo)
        iPathList= self.__getSourceWrkFileList(self.__stepNo)
        oPath=     self.__getResultWrkFile(self.__stepNo)
        lPath=     self.__getLogWrkFile(self.__stepNo)
        ePath=     self.__getErrWrkFile(self.__stepNo)
        tPath=     self.__getTmpWrkFile(self.__stepNo)        
        #
        if (self.__wrkPath != None):
            iPathFull=os.path.abspath(os.path.join(self.__wrkPath, iPath))
            ePathFull=os.path.join(self.__wrkPath, ePath)
            lPathFull=os.path.join(self.__wrkPath, lPath)
            tPathFull=os.path.join(self.__wrkPath, tPath)                                    
            cmd = "(cd " + self.__wrkPath
        else:
            iPathull  = iPath
            ePathFull = ePath
            lPathFull = lPath
            tPathFull = tPath            
            cmd = "("
        #
        if (self.__stepNo > 1):
            pPath = self.__updateInputPath()
            if (os.access(pPath,os.F_OK)):
                cmd += "; cp " + pPath + " "  + iPath
        #
        if self.__inputParamDict.has_key('pisa_session_name'):
            pisaSession  = self.__inputParamDict['pisa_session_name']
        else:
            pisaSession = None
        cmd += " ; PISA_TOP="         + os.path.abspath(pisaTopPath)     + " ; export PISA_TOP "
        cmd += " ; PISA_SESSIONS="    + os.path.abspath(self.__wrkPath)         + " ; export PISA_SESSIONS "
        cmd += " ; PISA_CONF_FILE="   + os.path.abspath(os.path.join(pisaTopPath,"configure","pisa-standalone.cfg")) + " ; export PISA_CONF_FILE "
        if (op == "pisa-analysis"):
            cmdPath   = os.path.join(pisaTopPath,"bin","pisa")
            cmd += " ; "   + cmdPath + " " + pisaSession + " -analyse " + iPathFull
            if self.__inputParamDict.has_key('pisa_assembly_arguments'):
                assemblyArgs  = self.__inputParamDict['pisa_assembly_arguments']            
                cmd += " " + assemblyArgs 
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
        elif (op == "pisa-assembly-report-xml"):
            cmdPath   = os.path.join(pisaTopPath,"bin","pisa")
            cmd += " ; "   + cmdPath + " " + pisaSession + " -xml assemblies > " + oPath
            cmd += " 2> " + tPath + " ; cat " + tPath + " >> " + lPath
        elif (op == "pisa-assembly-report-text"):
            cmdPath   = os.path.join(pisaTopPath,"bin","pisa")
            cmd += " ; "   + cmdPath + " " + pisaSession + " -list assemblies > " + oPath
            cmd += " 2> " + tPath + " ; cat " + tPath + " >> " + lPath
        elif  (op == "pisa-interface-report-xml"):
            cmdPath   = os.path.join(pisaTopPath,"bin","pisa")
            cmd += " ; "   + cmdPath + " " + pisaSession + " -xml interfaces > " + oPath
            cmd += " 2> " + tPath + " ; cat " + tPath + " >> " + lPath
        elif  (op == "pisa-assembly-coordinates-pdb"):
            pisaAssemblyId  = self.__inputParamDict['pisa_assembly_id']
            cmdPath   = os.path.join(pisaTopPath,"bin","pisa")
            cmd += " ; "   + cmdPath + " " + pisaSession + " -download assembly " + pisaAssemblyId + "  > " + oPath
            cmd += " 2> " + tPath + " ; cat " + tPath + " >> " + lPath
        elif  (op == "pisa-assembly-coordinates-cif"):
            pisaAssemblyId  = self.__inputParamDict['pisa_assembly_id']
            cmdPath   = os.path.join(pisaTopPath,"bin","pisa")
            cmd += " ; "   + cmdPath + " " + pisaSession + " -cif assembly " + pisaAssemblyId + "  > " + oPath
            cmd += " 2> " + tPath + " ; cat " + tPath + " >> " + lPath
        elif (op == "pisa-assembly-merge-cif"):
            # MergePisaData -input input_ciffile -output output_ciffile -xml xmlfile_from_PISA_output
            #                -log logfile -spacegroup spacegroup_file -list idlist 
            spgFilePath  =  self.__getConfigPath('SITE_SPACE_GROUP_FILE_PATH')                    
            assemblyTupleList = self.__inputParamDict['pisa_assembly_tuple_list']
            assemblyFile      = self.__inputParamDict['pisa_assembly_file_path']
            cmdPath =  os.path.join(annotToolsPath,"bin","MergePisaData")
            #
            cmd   +=  " ; " + cmdPath + " -input " + iPathFull + " -xml " + assemblyFile
            cmd   +=  " -spacegroup " + spgFilePath + " -log " + ePath 
            cmd   +=  " -list " + assemblyTupleList
            cmd   +=  " -output " + oPath
            #cmd   +=  " ; cp -f " + iPath + " " + oPath 
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            
        else:
            return -1
        #
        if (self.__debug):
            self.__lfh.write("++INFO - Application string:\n%s\n" % cmd.replace(";","\n"))        
        #
        if (self.__verbose):            
            cmd += " ; ls -la  > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                                    
            
        cmd += " ) > %s 2>&1 " % ePathFull

        cmd += " ; echo '-BEGIN-PROGRAM-ERROR-LOG--------------------------\n'  >> " + lPathFull                
        cmd += " ; cat " + ePathFull + " >> " + lPathFull
        cmd += " ; echo '-END-PROGRAM-ERROR-LOG-------------------------\n'  >> " + lPathFull                        


        ofh = open(lPathFull,'w')
        lt = time.strftime("%Y %m %d %H:%M:%S", time.localtime())
        ofh.write("\n\n-------------------------------------------------\n")
        ofh.write("LogFile:      %s\n" % lPath)
        ofh.write("Working path: %s\n" % self.__wrkPath)
        ofh.write("Date:         %s\n" % lt)
        if (self.__verbose):
            ofh.write("\nStep command:\n%s\n-------------------------------------------------\n" % cmd.replace(";","\n"))
        ofh.close()
           
        iret = os.system(cmd)
        #
        return iret




    def exp(self,dstPath=None):
        """Export a copy of the last result file to destination file path.
        """
        if (dstPath != None):
            self.setDestination(dstPath)
        rf=self.__getResultWrkFile(self.__stepNo)
        if (self.__wrkPath != None):
            resultPath = os.path.join(self.__wrkPath,rf)
        else:
            resultPath = rf

        f1 = DataFile(resultPath)
        if f1.srcFileExists():
            f1.copy(self.__dstPath)
            if f1.dstFileExists():
                return True
            else:
                return False
        else:
            return False

    def getResultPathList(self):
        return(self.__resultPathList)

    def expList(self,dstPathList=[]):
        """Export  copies of the list of last results to the corresponding paths
           in the destination file path list.
        """
        if (dstPathList == [] or self.__resultPathList == []): return
        #
        ok=True
        for f,fc in map(None,self.__resultPathList,dstPathList):
            f1 = DataFile(f)
            if f1.srcFileExists():
                f1.copy(fc)
            else:
                ok=False
        return ok

    def imp(self,srcPath=None):
        """ Import a local copy of the target source file - Use the working
            directory area if this is defined.  The internal step count is reset by this operation - 
        """
        if (srcPath != None):
            self.setSource(srcPath)
            
        if (self.__srcPath != None):
            if (self.__wrkPath == None):
                self.__makeTempWorkingDir()
            self.__stepNo = 0
            iPath=self.__getSourceWrkFile(self.__stepNo+1)
            f1 = DataFile(self.__srcPath)
            wrkPath = os.path.join(self.__wrkPath,iPath)
            f1.copy(wrkPath)

    def addInput(self,name=None,value=None,type='param'):
        """ Add a named input and value to the dictionary of input parameters.
        """
        try:
            if type == 'param':
                self.__inputParamDict[name]=value
            elif type == 'file':
                self.__inputParamDict[name]=os.path.abspath(value)
            else:
                return False
            return True
        except:
            return False

    def expLog(self,dstPath=None):
        """Append a copy of the current log file to destination path.
        """
        if (dstPath != None):
            self.setLogDestination(dstPath)
        lf=self.__getLogWrkFile(self.__stepNo)
        if (self.__wrkPath != None):
            logPath = os.path.join(self.__wrkPath,lf)
        else:
            logPath = lf
        f1 = DataFile(logPath)
        f1.append(self.__dstLogPath)

    def expErrLog(self,dstPath=None):
        """Append a copy of the current error log file to destination error path.
        """
        if (dstPath != None):
            self.setLogDestination(dstPath)
        lf=self.__getLogWrkFile(self.__stepNo)
        if (self.__wrkPath != None):
            logPath = os.path.join(self.__wrkPath,lf)
        else:
            logPath = lf
        f1 = DataFile(logPath)
        f1.append(self.__dstLogPath)

    def expLogAll(self,dstPath=None):
        """Append all session logs to destination logfile path.
        """
        if (dstPath != None):
            self.setLogDestination(dstPath)
        for sn in range(1,self.__stepNo+1):
            lf=self.__getLogWrkFile(sn)
            if (self.__wrkPath != None):
                logPath = os.path.join(self.__wrkPath,lf)
            else:
                logPath = lf
            f1 = DataFile(logPath)
            f1.append(self.__dstLogPath)


    def cleanup(self):
        """Cleanup temporary files and directories
        """
        return shutil.rmtree(self.__wrkPath)

    
if __name__ == '__main__':
    rdpu=RcsbDpUtility()
    
        
