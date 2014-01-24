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
# 16-Jul-2012 jdw add new PDBx CIF dialect converion.
#  2-Aug-2012 jdw add new cis peptide annotation
# 15-Aug-2012 jdw add cif check application
#  2-Sep-2012 jdw add consolidated annotation operation 
#  2-Sep-2012 jdw add entry point  "annot-wwpdb-validate-1" for validation calculations
#  5-Sep-2012 jdw working validation report operation
# 12-Dec-2012 jdw next validation module version
#                 add babel library and remove hardwired version in loader path
# 17-Dec-2012 jdw add annot-reposition-solvent-add-derived
# 03-Jan-2013 jdw add format conversions with strip options
# 06-Feb-2013 jdw migrate remaining applications from maxit-v10 to annotation-pack
# 16-Feb-2013 rps "chem-comp-assign-exact" added to support "exact match only" searching (i.e. for LigModule Lite)
# 23-Feb-2013 jdw add "annot-poly-link-dist"
# 26-Feb-2013 jdw update path setting for rcsbroot for annotation tasks.
# 05-Mar-2013 zf  added operation "chem-comp-assign-comp" to support for assignment using chemical component file
#                 updated RCSBROOT & COMP_PATH environmental variable setting for annotation module package
# 08-Mar-2013 jdw put back methods that were overwritten.
# 15-Mar-2013 zf  added operation "prd-search" to support entity transformer
# 25-Mar-2013 jdw add new methods  "annot-merge-sequence-data" and "annot-make-maps"
# 09-Apr-2013 jdw add new methods  "annot-make-ligand-maps"
# 16-Apr-2013 jdw add methods for seqeunce search
# 22-Apr-2013 jdw add additional controls for sequence search
#  1-May-2013 jdw provide for configuration settings of PDBx dictionary names.
#  1-May-2013 jdw repoint RCSBROOT from the old maxit path to the new annotation module 
# 23-May-2013 jdw add annot-pdb2cif-dep annot-cif2cif-dep
# 31-May-2013 rps add use of "-rel" option when "chem-comp-assign-exact" operation is performed
# 26-Jun-2013 jdw add "annot-format-check-pdb" & "annot-format-check-pdbx"
# 27-Jun-2013 jdw add sf format conversion and sf diagnostic report - 
# 15-Jul-2013 jdw correct assignment of PDBx dictionary name from configuration class.
# 15-Jul-2013 jdw add check-cif-v4 method
# 23-Jul-2013 jdw add "annot-rcsb2pdbx-withpdbid"
# 15-Aug-2013 jdw add various new annotation package functions --                                
#                "annot-move-xyz-by-matrix","annot-move-xyz-by-symop","annot-extra-checks","annot-sf-convert"
# 18-Oct-2013 jdw add miscellaneous tools in DCC package -  "annot-dcc-refine-report",
#                "annot-dcc-special-position", and "annot-dcc-reassign-alt-ids"
# 12-Dec-2013 jdw add wrapper for  "annot-update-terminal-atoms" and "annot-merge-xyz"
# 23-Dec-2013 jdw add "annot-gen-assem-pdbx"  and tentative "annot-cif2pdbx-withpdbid"
# 26-Dec-2013 jdw standardize execution via Python subprocess module.   Implement an execution 
#                 function with a timeout.
# 29-Dec-2013 jdw add validate-geometry -- add ignore_errors to cleanup function 
# 31-Dec-2013 jdw add expSize() method
#                 append parsing diagostics to extra and geometry check operations.
#  1-Jan-2014 jdw change debugging output 
#  9-Jan-2014 jdw add new --diags output to  log file from  dcc report -
# 15-Jan-2014 jdw add new --diags output to  log file from  sf conversion/"annot-sf-convert"
# 15-Jan-2014 jdw add additional switch for REQUEST_ANNOTATION_CONTEXT "annot-wwpdb-validate-2" 
# 16-Jan-2014 jdw add "cif2pdbx-public"
##
"""
Wrapper class for data processing and chemical component utilities.

Initial RCSB version - adapted from file utils method collections.


"""
import sys, os, os.path, glob, time, datetime, shutil, tempfile, traceback
import socket,shlex

from wwpdb.utils.rcsb.DataFile          import DataFile
from wwpdb.api.facade.ConfigInfo        import ConfigInfo
from subprocess import call,Popen

from wwpdb.utils.rcsb.PdbxStripCategory import PdbxStripCategory

class RcsbDpUtility(object):
    """ Wrapper class for data processing and chemical component utilities.
    """
    def __init__(self, tmpPath="/scratch", siteId="DEV",  verbose=False, log=sys.stderr):
        self.__verbose  = verbose
        self.__debug    = False
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
        self.__rcsbOps = [ "rename-atoms", "cif2pdbx", "pdbx2xml", "pdb2dssp", "pdb2stride", "initial-version","poly-link-dist",
                           "chem-comp-link", "chem-comp-assign", "chem-comp-assign-comp", "chem-comp-assign-skip",
                           "chem-comp-assign-exact","chem-comp-assign-validation","check-cif","check-cif-v4","cif2pdbx-public"]
        self.__pisaOps = ["pisa-analysis","pisa-assembly-report-xml","pisa-assembly-report-text",
                          "pisa-interface-report-xml","pisa-assembly-coordinates-pdb","pisa-assembly-coordinates-cif",
                          "pisa-assembly-coordinates-cif","pisa-assembly-merge-cif"]
        self.__annotationOps = ["annot-secondary-structure", "annot-link-ssbond", "annot-cis-peptide","annot-distant-solvent",
                                "annot-merge-struct-site","annot-reposition-solvent","annot-base-pair-info",
                                "annot-validation","annot-site","annot-rcsb2pdbx","annot-consolidated-tasks",
                                "annot-wwpdb-validate-test","annot-wwpdb-validate-2","prd-search","annot-wwpdb-validate-alt",
                                "annot-chem-shift-check","annot-chem-shift-coord-check","annot-nmrstar2pdbx","annot-pdbx2nmrstar",
                                "annot-reposition-solvent-add-derived", "annot-rcsb2pdbx-strip", "annot-rcsbeps2pdbx-strip",
                                "annot-rcsb2pdbx-strip-plus-entity", "annot-rcsbeps2pdbx-strip-plus-entity",
                                "chem-comp-instance-update","annot-cif2cif","annot-cif2pdb","annot-pdb2cif","annot-poly-link-dist",
                                "annot-merge-sequence-data","annot-make-maps","annot-make-ligand-maps",
                                "annot-cif2cif-dep","annot-pdb2cif-dep","annot-format-check-pdbx","annot-format-check-pdb",
                                "annot-dcc-report","annot-sf-convert","annot-dcc-refine-report","annot-dcc-biso-full",
                                "annot-dcc-special-position","annot-dcc-reassign-alt-ids",
                                "annot-rcsb2pdbx-withpdbid",
                                "annot-rcsb2pdbx-withpdbid-singlequote", "annot-rcsb2pdbx-alt",
                                "annot-move-xyz-by-matrix","annot-move-xyz-by-symop","annot-extra-checks",
                                "annot-update-terminal-atoms","annot-merge-xyz","annot-gen-assem-pdbx","annot-cif2pdbx-withpdbid",
                                "annot-validate-geometry"]
        self.__sequenceOps = ['seq-blastp','seq-blastn']
        self.__validateOps = ['validate-geometry']

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
        self.__timeout = 0

        self.__cI=ConfigInfo(self.__siteId)        
        self.__initPath()

    def __getConfigPath(self, ky):
        try:
            pth =  os.path.abspath(self.__cI.get(ky))
            if (self.__debug): 
                self.__lfh.write("+RcsbDpUtility.__getConfigPath()  - site %s configuration for %s is %s\n" % (self.__siteId,ky,pth))            
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

    def setTimeout(self,seconds):
        self.__lfh.write("+INFO RcsbDpUtility.setTimeout() - Set execution time out %d (seconds)\n" % seconds)
        self.__timeout=seconds

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
                self.__lfh.write("+RcsbDpUtility.useResult()  - Using result from step %s\n" % self.__stepNoSaved)        
        
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
        if (self.__srcPath == None and len(self.__inputParamDict) < 1): 
            self.__lfh.write("+RcsbDbUtility.op() ++ Error  - no input provided for operation %s\n" % op)
            return

        if (self.__verbose):
            self.__lfh.write("\n\n+RcsbDpUtility.op() starting op %s with working path %s\n" % (op,self.__wrkPath))

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

        elif op in self.__sequenceOps:
            self.__stepNo += 1            
            self.__sequenceStep(op)

        elif op in self.__validateOps:
            self.__stepNo += 1            
            self.__validateStep(op)
        else:
            self.__lfh.write("+RcsbDpUtility.op() ++ Error  - Unknown operation %s\n" % op)


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

            Now using only 2013 annotation pack functions.
        """
        #
        # Set application specific path details here -
        #
        self.__annotAppsPath  =  self.__getConfigPath('SITE_ANNOT_TOOLS_PATH')
        self.__localAppsPath  =  self.__getConfigPath('SITE_LOCAL_APPS_PATH')
        self.__packagePath    =  self.__getConfigPath('SITE_TOOLS_PATH')
        self.__deployPath     =  self.__getConfigPath('SITE_DEPLOY_PATH')        
        self.__ccDictPath     =  self.__getConfigPath('SITE_CC_DICT_PATH')
        self.__ccCvsPath      =  self.__getConfigPath('SITE_CC_CVS_PATH')                
        self.__prdccCvsPath   =  self.__getConfigPath('SITE_PRDCC_CVS_PATH')
        self.__prdDictPath    =  os.path.join(self.__getConfigPath('SITE_DEPLOY_PATH'), 'reference', 'components', 'prd-dict')

        # if self.__rcsbAppsPath is None:        
        #            self.__rcsbAppsPath  =  self.__getConfigPath('SITE_RCSB_APPS_PATH')
        # JDW 2013-02-26
        self.__rcsbAppsPath  =  self.__getConfigPath('SITE_ANNOT_TOOLS_PATH')
        #
        # These may not be needed -- 
        self.__pdbxDictPath  =  self.__getConfigPath('SITE_PDBX_DICT_PATH')
        self.__pdbxDictName  =  self.__cI.get('SITE_PDBX_DICT_NAME')
        self.__pathDdlSdb      = os.path.join(self.__pdbxDictPath,"mmcif_ddl.sdb")
        self.__pathPdbxDictSdb = os.path.join(self.__pdbxDictPath,self.__pdbxDictName+'.sdb')
        self.__pathPdbxDictOdb = os.path.join(self.__pdbxDictPath,self.__pdbxDictName+'.odb')

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
            iPathFull=os.path.abspath(os.path.join(self.__wrkPath, iPath))            
            ePathFull=os.path.join(self.__wrkPath, ePath)
            lPathFull=os.path.join(self.__wrkPath, lPath)
            tPathFull=os.path.join(self.__wrkPath, tPath)                                    
            cmd = "(cd " + self.__wrkPath
        else:
            iPathFull = iPath
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
        # Standard setup for maxit ---
        #
        cmd += " ; RCSBROOT=" + self.__rcsbAppsPath + " ; export RCSBROOT  "            
        cmd += " ; COMP_PATH=" + self.__ccCvsPath + " ; export COMP_PATH  "
        maxitCmd = os.path.join(self.__rcsbAppsPath,"bin","maxit")        

        #
        if (op == "annot-secondary-structure"):
            cmdPath =os.path.join(self.__annotAppsPath,"bin","GetSecondStruct")
            thisCmd  = " ; " + cmdPath                        
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log " 
            #
            if  self.__inputParamDict.has_key('ss_topology_file_path'):
                topFilePath=self.__inputParamDict['ss_topology_file_path']                                
                cmd += " -support " + topFilePath
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif (op == "annot-consolidated-tasks"):
            
            cmdPath =os.path.join(self.__annotAppsPath,"bin","GetAddAnnotation")
            thisCmd  = " ; " + cmdPath                        
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log " 
            #
            if  self.__inputParamDict.has_key('ss_topology_file_path'):
                topFilePath=self.__inputParamDict['ss_topology_file_path']                                
                cmd += " -support " + topFilePath
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif (op == "annot-validate-geometry"):
            # UpdateValidateCategories -input input_ciffile -output output_ciffile -log logfile 
            #
            cmdPath =os.path.join(self.__annotAppsPath,"bin","UpdateValidateCategories")
            thisCmd  = " ; " + cmdPath                        
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log " 
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            cmd += " ; cat annot-step.log " + " >> " + lPath
            
        elif (op == "annot-link-ssbond"):
            cmdPath =os.path.join(self.__annotAppsPath,"bin","GetLinkAndSSBond")
            thisCmd  = " ; " + cmdPath                        
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log  -link -ssbond " 
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif (op == "annot-cis-peptide"):
            cmdPath =os.path.join(self.__annotAppsPath,"bin","GetCisPeptide")
            thisCmd  = " ; " + cmdPath                        
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log " 
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif (op == "annot-distant-solvent"):
            cmdPath =os.path.join(self.__annotAppsPath,"bin","CalculateDistantWater")
            thisCmd  = " ; " + cmdPath                        
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log " 
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif (op == "annot-base-pair-info"):
            cmdPath =os.path.join(self.__annotAppsPath,"bin","GetBasePairInfo")
            thisCmd  = " ; " + cmdPath                        
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log " 
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            cmd += " ; cat annot-step.log " + " >> " + lPath
        elif (op == "annot-merge-struct-site"):
            cmdPath =os.path.join(self.__annotAppsPath,"bin","MergeSiteData")
            thisCmd  = " ; " + cmdPath                        
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
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log " 
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif (op == "annot-reposition-solvent-add-derived-new"):
            #
            # oPath will point to the final result for this step
            #
            oPath2=oPath+"_B"            
            cmdPath =os.path.join(self.__annotAppsPath,"bin","MovingWater")
            thisCmd  = " ; " + cmdPath                        
            cmd += thisCmd + " -input " + iPath + " -output " + oPath2 + " -log annot-step.log " 
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            cmd += " ; cat annot-step.log " + " >> " + lPath

            oPath2Full=os.path.join(self.__wrkPath, oPath2)                            
            oPathFull=os.path.join(self.__wrkPath, oPath)                            
            #
            # see at the end for the post processing operations --
            #

        elif (op == "annot-reposition-solvent-add-derived"):
            #
            # oPath will point to the final result for this step
            #
            oPath1=oPath+"_A"
            oPath2=oPath+"_B"            
            cmdPath =os.path.join(self.__annotAppsPath,"bin","MovingWater")
            thisCmd  = " ; " + cmdPath                        
            cmd += thisCmd + " -input " + iPath + " -output " + oPath1 + " -log annot-step.log " 
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            cmd += " ; cat annot-step.log " + " >> " + lPath
            #
            # Adding a following step to synchronize required derived data for subsequent steps -
            #
            cmd +=  " ; " + maxitCmd + " -o 8  -i " + oPath1 + " -log maxit.log " 
            cmd += " ; mv -f " + oPath1 + ".cif " + oPath2
            #cmd += " ; cat maxit.err >> " + lPath
            #
            # Paths for post processing --
            #
            oPath2Full=os.path.join(self.__wrkPath, oPath2)
            oPathFull=os.path.join(self.__wrkPath, oPath)                            
            #
            # see at the end for the post processing operations --
            #
        elif (op == "annot-format-check-pdbx"):
            # CheckCoorFormat -input inputfile -format (pdb|pdbx) -output outputfile
            cmdPath =os.path.join(self.__annotAppsPath,"bin","CheckCoorFormat")
            thisCmd  = " ; " + cmdPath                        
            cmd += thisCmd + " -input " + iPath + " -format pdbx  -output " + oPath 
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        

        elif (op == "annot-format-check-pdb"):
            # CheckCoorFormat -input inputfile -format (pdb|pdbx) -output outputfile
            cmdPath =os.path.join(self.__annotAppsPath,"bin","CheckCoorFormat")
            thisCmd  = " ; " + cmdPath                        
            cmd += thisCmd + " -input " + iPath + " -format pdb  -output " + oPath 
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        

        elif (op == "annot-nmrstar2pdbx"):
            # self.__packagePath
            if  self.__inputParamDict.has_key('data_set_id'):
                dId=self.__inputParamDict['data_set_id']                                
            else:
                dId="UNASSIGNED"
            #
            cmdPath =os.path.join(self.__packagePath,"aditnmr-util","pdbx_to_nmrstar.sh")
            thisCmd  = " ; " + cmdPath                        
            cmd += " ; PACKAGE_DIR="  + self.__packagePath    + " ; export PACKAGE_DIR "
            cmd += thisCmd + "  " + iPath + " " + dId + " " + oPath 
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        

        elif (op == "annot-pdbx2nmrstar"):
            # self.__packagePath
            if  self.__inputParamDict.has_key('data_set_id'):
                dId=self.__inputParamDict['data_set_id']                                
            else:
                dId="UNASSIGNED"
            #
            cmdPath =os.path.join(self.__packagePath,"aditnmr-util","nmrstar_to_pdbx.sh")
            thisCmd  = " ; " + cmdPath                        
            cmd += " ; PACKAGE_DIR="  + self.__packagePath    + " ; export PACKAGE_DIR "
            cmd += thisCmd + "  " + iPath + " " + dId + " " + oPath 
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        


        elif (op == "annot-validation"):
            cmdPath =os.path.join(self.__annotAppsPath,"bin","valdation_with_cif_output")
            thisCmd  = " ; " + cmdPath                        
            cmd += thisCmd + " -cif " + iPath + " -output " + oPath + " -log annot-step.log " 
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            cmd += " ; cat annot-step.log " + " >> " + lPath


        elif (op == "annot-site"):
            cmd += " ; TOOLS_PATH="  + self.__packagePath    + " ; export TOOLS_PATH "
            cmd += " ; CCP4="        + os.path.join(self.__packagePath,"ccp4")  + " ; export CCP4 "            
            cmd += " ; SYMINFO="     + os.path.join(self.__packagePath,"getsite-cif","data","syminfo.lib") + " ; export SYMINFO "
            cmd += " ; MMCIFDIC="    + os.path.join(self.__packagePath,"getsite-cif","data","cif_mmdic.lib")  + " ; export MMCIFDIC "         
            cmd += " ; STANDATA="    + os.path.join(self.__packagePath,"getsite-cif","data","standard_geometry.cif")  + " ; export STANDATA "
            cmd += " ; CCIF_NOITEMIP=off ; export CCIF_NOITEMIP "
            # setenv DYLD_LIBRARY_PATH  "$CCP4/lib/ccif:$CCP4/lib"

            cmd += " ; DYLD_LIBRARY_PATH=" + os.path.join(self.__packagePath,"ccp4","lib","ccif") + ":" + \
                   os.path.join(self.__packagePath,"ccp4","lib") + " ; export DYLD_LIBRARY_PATH "

            cmd += " ; LD_LIBRARY_PATH=" + os.path.join(self.__packagePath,"ccp4","lib","ccif") + ":" + \
                   os.path.join(self.__packagePath,"ccp4","lib") + " ; export LD_LIBRARY_PATH "                        

            # setenv CIFIN 1abc.cif
            cmd += " ; CIFIN=" + iPath+ " ; export CIFIN "
            #cmd += " ; env "

            if  self.__inputParamDict.has_key('block_id'):
                blockId=self.__inputParamDict['block_id']                                
            else:
                blockId="UNK"

                
            # ../getsite_cif 1abc


            cmdPath =os.path.join(self.__packagePath,"getsite-cif","bin","getsite_cif")
            thisCmd  = " ; " + cmdPath                        

            cmd += thisCmd + " " + blockId + " "
            
            if  self.__inputParamDict.has_key('site_arguments'):
                cmdArgs=self.__inputParamDict['site_arguments']                                
                cmd += cmdArgs            
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; mv -f " + blockId + "_site.cif " + oPath                         

        elif (op == "annot-merge-sequence-data"):
            # example -
            # MergeSeqModuleData -input RCSB056751_model_P1.cif.V1 -assign RCSB056751_seq-assign_P1.cif.V2 -output new_model.cif 
            #
            cmdPath =os.path.join(self.__annotAppsPath,"bin","MergeSeqModuleData")
            thisCmd  = " ; " + cmdPath                        
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log "
            if  self.__inputParamDict.has_key('seqmod_assign_file_path'):
                assignFilePath=self.__inputParamDict['seqmod_assign_file_path']                                
                cmd += " -assign " + assignFilePath           
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif (op == "chem-comp-instance-update"):
            # New version that moved from the chem-comp-pack --
            cmdPath =os.path.join(self.__annotAppsPath,"bin","updateInstance")            
            thisCmd  = " ; " + cmdPath                        
            assignPath = self.__inputParamDict['cc_assign_file_path']
            #selectPath = self.__inputParamDict['cc_select_file_path']            
            cmd += thisCmd + " -i " + iPath + " -o " + oPath + " -assign " + assignPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath

        elif (op == "annot-rcsb2pdbx-alt"): 
            cmd +=  " ; " + maxitCmd + " -single_quotation -o 9  -i " + iPath + " -log maxit.log "
            cmd += " ; mv -f " + iPath + ".cif " + oPath

        elif (op == "annot-rcsb2pdbx"):
            
            # New minimal RCSB internal cif to PDBx cif converter -
            cmdPath =os.path.join(self.__annotAppsPath,"bin","PdbxConverter")
            thisCmd  = " ; " + cmdPath                        
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log "
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif ((op == "annot-rcsb2pdbx-withpdbid") or (op == "annot-cif2pdbx-withpdbid")):
            # New minimal RCSB internal cif to PDBx cif converter with internal conversion of entry id to  pdbId -
            cmdPath =os.path.join(self.__annotAppsPath,"bin","PdbxConverter")
            thisCmd  = " ; " + cmdPath                        
            cmd += thisCmd + " -pdbid -input " + iPath + " -output " + oPath + " -log annot-step.log "
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif (op == "annot-rcsb2pdbx-withpdbid-singlequote"):
            
            # New minimal RCSB internal cif to PDBx cif converter with internal conversion of entry id to  pdbId -
            cmdPath =os.path.join(self.__annotAppsPath,"bin","PdbxConverter")
            thisCmd  = " ; " + cmdPath                        
            cmd += thisCmd + " -pdbid -single_quotation -input " + iPath + " -output " + oPath + " -log annot-step.log "
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif (op == "annot-rcsb2pdbx-strip"):

            # New minimal RCSB internal cif to PDBx cif converter followed by removal of derived categories
            
            oPath2=oPath+"_A"
            

            cmdPath =os.path.join(self.__annotAppsPath,"bin","PdbxConverter")
            thisCmd  = " ; " + cmdPath                        
            cmd += thisCmd + " -input " + iPath + " -output " + oPath2 + " -log annot-step.log "
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            cmd += " ; cat annot-step.log " + " >> " + lPath

            oPath2Full=os.path.join(self.__wrkPath, oPath2)
            oPathFull=os.path.join(self.__wrkPath, oPath)                            

        elif  (op == "annot-rcsbeps2pdbx-strip"):
            #
            oPath2=oPath+"_B"            
            #
            # Adding a following step to synchronize required derived data for subsequent steps -
            #
            #
            cmd +=  " ; " + maxitCmd + " -o 8  -i " + iPath + " -log maxit.log "
            cmd += " ; mv -f " + iPath + ".cif " + oPath2
            #cmd += " ; cat maxit.err >> " + lPath
            #
            # Paths for post processing --
            #
            oPath2Full=os.path.join(self.__wrkPath, oPath2)
            oPathFull=os.path.join(self.__wrkPath, oPath)                            
            #
            # see at the end for the post processing operations --

        elif (op == "annot-rcsb2pdbx-strip-plus-entity"):

            # New minimal RCSB internal cif to PDBx cif converter followed by removal of derived categories
            
            oPath2=oPath+"_A"
            

            cmdPath =os.path.join(self.__annotAppsPath,"bin","PdbxConverter")
            thisCmd  = " ; " + cmdPath                        
            cmd += thisCmd + " -input " + iPath + " -output " + oPath2 + " -log annot-step.log "
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            cmd += " ; cat annot-step.log " + " >> " + lPath

            oPath2Full=os.path.join(self.__wrkPath, oPath2)
            oPathFull=os.path.join(self.__wrkPath, oPath)                            

        elif  (op == "annot-rcsbeps2pdbx-strip-plus-entity"):
            #
            oPath2=oPath+"_B"            
            #
            # Adding a following step to synchronize required derived data for subsequent steps -
            #
            #
            cmd +=  " ; " + maxitCmd + " -o 8  -i " + iPath + " -log maxit.log "
            cmd += " ; mv -f " + iPath + ".cif " + oPath2
            #cmd += " ; cat maxit.err >> " + lPath
            #
            # Paths for post processing --
            #
            oPath2Full=os.path.join(self.__wrkPath, oPath2)
            oPathFull=os.path.join(self.__wrkPath, oPath)                            
            #
            # see at the end for the post processing operations --
            
        elif (op == "annot-chem-shift-check"):

            cmd += " ; TOOLS_PATH="  + self.__packagePath    + " ; export TOOLS_PATH "
            cmd += " ; ADIT_NMR="    + os.path.join(self.__packagePath,"aditnmr_req_shifts")  + " ; export ADIT_NMR "
            cmd += " ; LIGAND_DIR="  + self.__ccDictPath   + " ; export LIGAND_DIR "
            cmd += " ; NOMENCLATURE_MAP_FILE="    + os.path.join(self.__packagePath,"aditnmr_req_shifts","adit","config","bmrb-adit","pseudomap.csv")  + " ; export NOMENCLATURE_MAP_FILE "            
            #
            # set output option -  html or star
            if  self.__inputParamDict.has_key('output_format'):
                outFmt=self.__inputParamDict['output_format']                                
            else:
                outFmt="html"

            cmdPath =os.path.join(self.__packagePath,"aditnmr_req_shifts","cgi-bin","bmrb-adit","upload_shifts_check")
            thisCmd  = " ; " + cmdPath                        

            cmd += thisCmd + " " + "--html --nomenclature-mapper ${NOMENCLATURE_MAP_FILE} --chem-comp-root-path ${LIGAND_DIR} "
            cmd += " --preserve-output tmp_chkd.str " + iPath 

            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            if (outFmt == "html"):
                cmd += " ; mv -f " + tPath + " " + oPath
            else:
                cmd += " ; mv -f  tmp_chkd.str " + oPath                

        elif (op == "annot-chem-shift-coord-check"):

            cmd += " ; TOOLS_PATH="  + self.__packagePath    + " ; export TOOLS_PATH "
            cmd += " ; ADIT_NMR="    + os.path.join(self.__packagePath,"aditnmr_req_shifts")  + " ; export ADIT_NMR "
            cmd += " ; NOMENCLATURE_MAP_FILE="    + os.path.join(self.__packagePath,"aditnmr_req_shifts","adit","config","bmrb-adit","pseudomap.csv")  + " ; export NOMENCLATURE_MAP_FILE "
            cmd += " ; LIGAND_DIR="  + self.__ccDictPath   + " ; export LIGAND_DIR "

            #
            # set input coordinate file path
            if  self.__inputParamDict.has_key('coordinate_file_path'):
                coordFilePath=self.__inputParamDict['coordinate_file_path']                                
            else:
                coordFilepath=""

            #
            # set output option -  html or star
            if  self.__inputParamDict.has_key('output_format'):
                outFmt=self.__inputParamDict['output_format']                                
            else:
                outFmt="html"

            cmdPath =os.path.join(self.__packagePath,"aditnmr_req_shifts","cgi-bin","bmrb-adit","shift_coord_check")
            thisCmd  = " ; " + cmdPath                        

            cmd += thisCmd + " " + "--html --coordfile " + coordFilePath + " --shiftfile " + iPath 

            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            if (outFmt == "html"):
                cmd += " ; mv -f " + tPath + " " + oPath
            else:
                cmd += " ; cp -f  " + iPath + " " + oPath                

        elif (op == "annot-wwpdb-validate-2"):
            # For the second version of the validation package --
            #
            # The validation package is currently set to self configure in a wrapper
            # shell script.  See the environment in this file for details --
            #

            # This parameter permits overriding the 
            #
            if  self.__inputParamDict.has_key('request_annotation_context'):
                annotContext=self.__inputParamDict['request_annotation_context']
                if annotContext in ["yes","no"]:
                    cmd += " ; REQUEST_ANNOTATION_CONTEXT="  + annotContext + " ; export REQUEST_ANNOTATION_CONTEXT "
                
            cmd += " ; WWPDB_SITE_ID="  + self.__siteId  + " ; export WWPDB_SITE_ID "
            cmd += " ; DEPLOY_DIR="  + self.__deployPath  + " ; export DEPLOY_DIR "
            cmdPath =os.path.join(self.__packagePath,"Vpack-v2","scripts","vpack-run.sh")
            thisCmd  = " ; " + cmdPath                        

            if  self.__inputParamDict.has_key('sf_file_path'):
                sfPath=self.__inputParamDict['sf_file_path']
                sfPathFull = os.path.abspath(sfPath)                
            else:
                sfPath="none"
                sfPathFull="none"                

            #
            xmlPath=os.path.join(self.__wrkPath, "out.xml")
            pdfPath=os.path.join(self.__wrkPath, "out.pdf")
            pdfFullPath=os.path.join(self.__wrkPath, "out_full.pdf")
            pngPath=os.path.join(self.__wrkPath, "out.png")
            svgPath=os.path.join(self.__wrkPath, "out.svg")
            if (not self.__verbose):
                cleanOpt="cleanup"
            else:
                cleanOpt="none"
            #
            cmd += thisCmd + " 1abc " + iPathFull + " " + sfPathFull + " " + pdfPath +  " " + xmlPath + " " + cleanOpt 
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; cp  -f " + pdfPath + " " + oPath

        elif (op == "annot-wwpdb-validate-alt"):
            # For the second version of the validation package --
            #
            # The validation package is currently set to self configure in a wrapper
            # shell script.  See the environment in this file for details --
            #

            # This parameter permits overriding the 
            #
            if  self.__inputParamDict.has_key('request_annotation_context'):
                annotContext=self.__inputParamDict['request_annotation_context']
                if annotContext in ["yes","no"]:
                    cmd += " ; REQUEST_ANNOTATION_CONTEXT="  + annotContext + " ; export REQUEST_ANNOTATION_CONTEXT "
                
            cmd += " ; WWPDB_SITE_ID="  + self.__siteId  + " ; export WWPDB_SITE_ID "
            cmd += " ; DEPLOY_DIR="  + self.__deployPath  + " ; export DEPLOY_DIR "
            cmdPath =os.path.join(self.__packagePath,"Vpack-v2","scripts","vpack-alt-run.sh")
            thisCmd  = " ; " + cmdPath                        

            if  self.__inputParamDict.has_key('sf_file_path'):
                sfPath=self.__inputParamDict['sf_file_path']
                sfPathFull = os.path.abspath(sfPath)                
            else:
                sfPath="none"
                sfPathFull="none"                

            #
            xmlPath=os.path.join(self.__wrkPath, "out.xml")
            pdfPath=os.path.join(self.__wrkPath, "out.pdf")
            #
            pdfFullPath=os.path.join(self.__wrkPath, "out_full.pdf")
            pngPath=os.path.join(self.__wrkPath, "out.png")
            svgPath=os.path.join(self.__wrkPath, "out.svg")
            #
            if (not self.__verbose):
                cleanOpt="cleanup"
            else:
                cleanOpt="none"
            #
            cmd += thisCmd + " 1abc " + iPathFull + " " + sfPathFull + " " + pdfPath +  " " + xmlPath + " " + pdfFullPath + " " + pngPath + " " + svgPath + " " + cleanOpt 
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; cp  -f " + pdfPath + " " + oPath

        elif (op == "annot-wwpdb-validate-test"):
            # For the second version of the validation package --
            #
            # The validation package is currently set to self configure in a wrapper
            # shell script.  No environment settings are required here at this point.
            #
            cmd += " ; WWPDB_SITE_ID="  + self.__siteId  + " ; export WWPDB_SITE_ID "
            cmd += " ; DEPLOY_DIR="  + self.__deployPath  + " ; export DEPLOY_DIR "
            cmdPath =os.path.join(self.__packagePath,"Vpack-test","scripts","vpack-run.sh")
            thisCmd  = " ; " + cmdPath                        
            
            if  self.__inputParamDict.has_key('sf_file_path'):
                sfPath=self.__inputParamDict['sf_file_path']
                sfPathFull = os.path.abspath(sfPath)                
            else:
                sfPath="none"
                sfPathFull="none"                

            #
            xmlPath=os.path.join(self.__wrkPath, "out.xml")
            pdfPath=os.path.join(self.__wrkPath, "out.pdf")
            pdfFullPath=os.path.join(self.__wrkPath, "out_full.pdf")
            pngPath=os.path.join(self.__wrkPath, "out.png")
            svgPath=os.path.join(self.__wrkPath, "out.svg")
            if (not self.__verbose):
                cleanOpt="cleanup"
            else:
                cleanOpt="none"
            #
            cmd += thisCmd + " 1abc " + iPathFull + " " + sfPathFull + " " + pdfPath +  " " + xmlPath + " " + cleanOpt 
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; cp  -f " + pdfPath + " " + oPath


        elif (op == "annot-make-ligand-maps"):
            # The sf-valid package is currently set to self configure in a wrapper
            # shell script.  PACKAGE_DIR and TOOLS_DIR only need to be set here.
            #
            cmd += " ; WWPDB_SITE_ID="  + self.__siteId  + " ; export WWPDB_SITE_ID "
            cmd += " ; DEPLOY_DIR="  + self.__deployPath  + " ; export DEPLOY_DIR "
            cmd += " ; TOOLS_DIR="  + os.path.join(self.__localAppsPath,'bin')  + " ; export TOOLS_DIR "
            cmd += " ; PACKAGE_DIR="  + self.__packagePath + " ; export PACKAGE_DIR "
            cmd += " ; DCCPY_DIR="  + os.path.join(self.__packagePath,'sf-valid')  + " ; export DCCPY_DIR "            
            
            #
            cmdPath =os.path.join(self.__packagePath,"sf-valid","bin","dcc.sh")
            thisCmd  = " ; " + cmdPath                        
            
            if  self.__inputParamDict.has_key('sf_file_path'):
                sfPath=self.__inputParamDict['sf_file_path']
                sfPathFull = os.path.abspath(sfPath)       
                (h,sfFileName)=os.path.split(sfPath)
                sfWrkPath=os.path.join(self.__wrkPath,sfFileName)
                shutil.copyfile(sfPathFull,sfWrkPath)
            else:
                sfPath="none"
                sfPathFull="none"                

            if  self.__inputParamDict.has_key('output_map_file_path'):
                outMapPath=self.__inputParamDict['output_map_file_path']
            else:
                outMapPath='.'
                
            outMapPathFull=os.path.abspath(outMapPath)
            map2fofcPath=os.path.join(self.__wrkPath, iPath+"_2fofc.map")            
            #

            cmd += thisCmd + " -cif ./" + iPath + " -sf  ./" + sfFileName + " -ligmap  -no_xtriage "
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath

        elif (op == "annot-dcc-report"):
            # The sf-valid package is currently set to self configure in a wrapper
            # shell script.  PACKAGE_DIR and TOOLS_DIR only need to be set here.
            #
            cmd += " ; WWPDB_SITE_ID="  + self.__siteId  + " ; export WWPDB_SITE_ID "
            cmd += " ; DEPLOY_DIR="  + self.__deployPath  + " ; export DEPLOY_DIR "
            cmd += " ; TOOLS_DIR="  + os.path.join(self.__localAppsPath,'bin')  + " ; export TOOLS_DIR "
            cmd += " ; PACKAGE_DIR="  + self.__packagePath + " ; export PACKAGE_DIR "
            cmd += " ; DCCPY_DIR="  + os.path.join(self.__packagePath,'sf-valid')  + " ; export DCCPY_DIR "            
            
            #
            cmdPath =os.path.join(self.__packagePath,"sf-valid","bin","dcc.sh")
            thisCmd  = " ; " + cmdPath                        
            
            if  self.__inputParamDict.has_key('sf_file_path'):
                sfPath=self.__inputParamDict['sf_file_path']
                sfPathFull = os.path.abspath(sfPath)       
                (h,sfFileName)=os.path.split(sfPath)
                sfWrkPath=os.path.join(self.__wrkPath,sfFileName)
                shutil.copyfile(sfPathFull,sfWrkPath)
                #
                cmd += thisCmd + " -cif ./" + iPath + " -sf  ./" + sfFileName + " -o " + oPath + " -diags " + lPath

            else:
                sfPath="none"
                sfPathFull="none"                
                cmd += ' ; echo "No structure factor file"'
                
            cmd += " > " + tPath + " 2>&1 ; "


        elif (op == "annot-dcc-refine-report"):
            # The sf-valid package is currently set to self configure in a wrapper
            # shell script.  PACKAGE_DIR and TOOLS_DIR only need to be set here.
            #
            cmd += " ; WWPDB_SITE_ID="  + self.__siteId  + " ; export WWPDB_SITE_ID "
            cmd += " ; DEPLOY_DIR="  + self.__deployPath  + " ; export DEPLOY_DIR "
            cmd += " ; TOOLS_DIR="  + os.path.join(self.__localAppsPath,'bin')  + " ; export TOOLS_DIR "
            cmd += " ; PACKAGE_DIR="  + self.__packagePath + " ; export PACKAGE_DIR "
            cmd += " ; DCCPY_DIR="  + os.path.join(self.__packagePath,'sf-valid')  + " ; export DCCPY_DIR "            
            
            #
            cmdPath =os.path.join(self.__packagePath,"sf-valid","bin","dcc.sh")
            thisCmd  = " ; " + cmdPath                        
            
            if  self.__inputParamDict.has_key('sf_file_path'):
                sfPath=self.__inputParamDict['sf_file_path']
                sfPathFull = os.path.abspath(sfPath)       
                (h,sfFileName)=os.path.split(sfPath)
                sfWrkPath=os.path.join(self.__wrkPath,sfFileName)
                shutil.copyfile(sfPathFull,sfWrkPath)
                cmd += thisCmd + " -refine -cif ./" + iPath + " -sf  ./" + sfFileName + " -o " + oPath
            else:
                sfPath="none"
                sfPathFull="none"                
                cmd += ' ; echo "No structure factor file"'
            #

            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath

        elif (op == "annot-dcc-biso-full"):
            # The sf-valid package is currently set to self configure in a wrapper
            # shell script.  PACKAGE_DIR and TOOLS_DIR only need to be set here.
            #
            cmd += " ; WWPDB_SITE_ID="  + self.__siteId  + " ; export WWPDB_SITE_ID "
            cmd += " ; DEPLOY_DIR="  + self.__deployPath  + " ; export DEPLOY_DIR "
            cmd += " ; TOOLS_DIR="  + os.path.join(self.__localAppsPath,'bin')  + " ; export TOOLS_DIR "
            cmd += " ; PACKAGE_DIR="  + self.__packagePath + " ; export PACKAGE_DIR "
            cmd += " ; DCCPY_DIR="  + os.path.join(self.__packagePath,'sf-valid')  + " ; export DCCPY_DIR "            
            
            #
            cmdPath =os.path.join(self.__packagePath,"sf-valid","bin","dcc.sh")
            thisCmd  = " ; " + cmdPath                        
            
            #
            cmd += thisCmd + " -bfull ./" + iPath + " -o " + oPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath

        elif (op == "annot-dcc-special-position"):
            # The sf-valid package is currently set to self configure in a wrapper
            # shell script.  PACKAGE_DIR and TOOLS_DIR only need to be set here.
            #
            cmd += " ; WWPDB_SITE_ID="  + self.__siteId  + " ; export WWPDB_SITE_ID "
            cmd += " ; DEPLOY_DIR="  + self.__deployPath  + " ; export DEPLOY_DIR "
            cmd += " ; TOOLS_DIR="  + os.path.join(self.__localAppsPath,'bin')  + " ; export TOOLS_DIR "
            cmd += " ; PACKAGE_DIR="  + self.__packagePath + " ; export PACKAGE_DIR "
            cmd += " ; DCCPY_DIR="  + os.path.join(self.__packagePath,'sf-valid')  + " ; export DCCPY_DIR "            
            
            #
            cmdPath =os.path.join(self.__packagePath,"sf-valid","bin","tool.sh")
            thisCmd  = " ; " + cmdPath                        
            
            #
            cmd += thisCmd + " -occ ./" + iPath + " -o " + oPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath

        elif (op == "annot-dcc-reassign-alt-ids"):
            # The sf-valid package is currently set to self configure in a wrapper
            # shell script.  PACKAGE_DIR and TOOLS_DIR only need to be set here.
            #
            cmd += " ; WWPDB_SITE_ID="  + self.__siteId  + " ; export WWPDB_SITE_ID "
            cmd += " ; DEPLOY_DIR="  + self.__deployPath  + " ; export DEPLOY_DIR "
            cmd += " ; TOOLS_DIR="  + os.path.join(self.__localAppsPath,'bin')  + " ; export TOOLS_DIR "
            cmd += " ; PACKAGE_DIR="  + self.__packagePath + " ; export PACKAGE_DIR "
            cmd += " ; DCCPY_DIR="  + os.path.join(self.__packagePath,'sf-valid')  + " ; export DCCPY_DIR "            
            
            #
            cmdPath =os.path.join(self.__packagePath,"sf-valid","bin","tool.sh")
            thisCmd  = " ; " + cmdPath                        
            
            #
            cmd += thisCmd + " -alt  ./" + iPath + " -o " + oPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath



        elif (op == "annot-sf-convert"):
            # The sf-valid package is currently set to self configure in a wrapper
            # shell script.  PACKAGE_DIR and TOOLS_DIR only need to be set here.
            #
            # sf_convert -o mmcif  -sf refine.mtz    -out test-mtz-sf.cif  [-pdb model-xyz.cif]
            #
            # input  is sf file in mtz format
            # output is sf in pdbx  format
            sfCifPath=os.path.join(self.__wrkPath, oPath)            
            sfDiagFileName="sf_information.cif"
            sfDiagPath=os.path.join(self.__wrkPath,sfDiagFileName)
            mtzDmpFileName="mtzdmp.log"
            mtzDmpPath=os.path.join(self.__wrkPath,mtzDmpFileName)
            #
            mtzFile=iPath+".mtz"            
            mtzPath=os.path.join(self.__wrkPath, mtzFile) 
            shutil.copyfile(iPathFull,mtzPath)
            #
            cmd += " ; WWPDB_SITE_ID="  + self.__siteId  + " ; export WWPDB_SITE_ID "
            cmd += " ; DEPLOY_DIR="  + self.__deployPath  + " ; export DEPLOY_DIR "
            cmd += " ; TOOLS_DIR="  + os.path.join(self.__localAppsPath,'bin')  + " ; export TOOLS_DIR "
            cmd += " ; PACKAGE_DIR="  + self.__packagePath + " ; export PACKAGE_DIR "
            cmd += " ; DCCPY_DIR="  + os.path.join(self.__packagePath,'sf-valid')  + " ; export DCCPY_DIR "
            cmd += " ; DCCPY="  + os.path.join(self.__packagePath,'sf-valid')  + " ; export DCCPY "            
            cmd += " ; CCP4="        + os.path.join(self.__packagePath,"ccp4")  + " ; export CCP4 "
            cmd += " ; source $CCP4/bin/ccp4.setup.sh "
            #
            cmdPath =os.path.join(self.__packagePath,"sf-valid","bin","sf_convert")
            thisCmd  = " ; " + cmdPath                        
            #
            cmd += thisCmd + " -o mmcif  -sf " + mtzFile + " -out " + oPath + " -diags " + lPath
            #
            
            if  self.__inputParamDict.has_key('xyz_file_path'):
                xyzPath=self.__inputParamDict['xyz_file_path']
                xyzPathFull = os.path.abspath(xyzPath)       
                (h,xyzFileName)=os.path.split(xyzPath)
                xyzWrkPath=os.path.join(self.__wrkPath,xyzFileName)
                shutil.copyfile(xyzPathFull,xyzWrkPath)
                cmd += " -pdb " + xyzFileName 

            cmd += " > " + tPath + " 2>&1 ; "
            #

        elif (op == "annot-make-maps"):
            # The sf-valid package is currently set to self configure in a wrapper
            # shell script.  PACKAGE_DIR and TOOLS_DIR only need to be set here.
            #
            cmd += " ; WWPDB_SITE_ID="  + self.__siteId  + " ; export WWPDB_SITE_ID "
            cmd += " ; DEPLOY_DIR="  + self.__deployPath  + " ; export DEPLOY_DIR "
            cmd += " ; TOOLS_DIR="  + os.path.join(self.__localAppsPath,'bin')  + " ; export TOOLS_DIR "
            cmd += " ; PACKAGE_DIR="  + self.__packagePath + " ; export PACKAGE_DIR "
            cmd += " ; DCCPY_DIR="  + os.path.join(self.__packagePath,'sf-valid')  + " ; export DCCPY_DIR "            
            
            #
            cmdPath =os.path.join(self.__packagePath,"sf-valid","bin","dcc.sh")
            thisCmd  = " ; " + cmdPath                        
            
            if  self.__inputParamDict.has_key('sf_file_path'):
                sfPath=self.__inputParamDict['sf_file_path']
                sfPathFull = os.path.abspath(sfPath)       
                (h,sfFileName)=os.path.split(sfPath)
                sfWrkPath=os.path.join(self.__wrkPath,sfFileName)
                shutil.copyfile(sfPathFull,sfWrkPath)
            else:
                sfPath="none"
                sfPathFull="none"                

            #
            map2fofcPath=os.path.join(self.__wrkPath, iPath+".cif_2fofc.map")
            mapfofcPath=os.path.join(self.__wrkPath, iPath+".cif_fofc.map")

            cmd += thisCmd + " -cif ./" + iPath + " -sf  ./" + sfFileName + " -map  -no_xtriage -o " + oPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath

        elif (op == "annot-poly-link-dist"):
            cmdPath =os.path.join(self.__annotAppsPath,"bin","cal_polymer_linkage_distance")
            thisCmd  = " ; " + cmdPath            
            cmd += thisCmd + " -i " + iPath + " -o " + oPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        

        elif ((op == "annot-cif2cif") or (op == "cif2cif")):            
            cmd +=  " ; " + maxitCmd + " -o 8  -i " + iPath + " -log maxit.log "
            cmd += " ; mv -f " + iPath + ".cif " + oPath
            #cmd += " ; cat maxit.err >> " + lPath

        elif ((op == "annot-cif2cif-dep") or (op == "cif2cif-dep")):            
            cmd +=  " ; " + maxitCmd + " -o 8  -i " + iPath + " -dep -log maxit.log "
            cmd += " ; mv -f " + iPath + ".cif " + oPath
            #cmd += " ; cat maxit.err >> " + lPath

        elif ((op == "annot-pdb2cif") or (op == "pdb2cif")):
            cmd +=  " ; " + maxitCmd + " -o 1  -i " + iPath + " -log maxit.log "
            cmd += " ; mv -f " + iPath + ".cif " + oPath
            #cmd += " ; cat maxit.err >> " + lPath            

        elif ((op == "annot-pdb2cif-dep") or (op == "pdb2cif-dep")):
            cmd +=  " ; " + maxitCmd + " -o 1  -i " + iPath + " -dep -log maxit.log "
            cmd += " ; mv -f " + iPath + ".cif " + oPath
            #cmd += " ; cat maxit.err >> " + lPath            

        elif ((op == "annot-cif2pdb") or (op == "cif2pdb")):
            cmd +=  " ; " + maxitCmd + " -o 2  -i " + iPath + " -log maxit.log "
            cmd += " ; mv -f " + iPath + ".pdb " + oPath
            #cmd += " ; cat maxit.err >> " + lPath            

        elif (op == "annot-move-xyz-by-symop"):

            # MovingCoordBySymmetry and MovingCoordByMatrix programs in annotation-pack to move coordinates. The syntax for both programs are:
            #${program} -input input_ciffile -output output_ciffile -assign assignment_file -log logfile

            #
            cmdPath =os.path.join(self.__annotAppsPath,"bin","MovingCoordBySymmetry")
            thisCmd  = " ; " + cmdPath                        
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log "
            if  self.__inputParamDict.has_key('transform_file_path'):
                assignFilePath=self.__inputParamDict['transform_file_path']                                
                cmd += " -assign " + assignFilePath           
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif (op == "annot-move-xyz-by-matrix"):

            # MovingCoordBySymmetry and MovingCoordByMatrix programs in annotation-pack to move coordinates. The syntax for both programs are:
            #${program} -input input_ciffile -output output_ciffile -assign assignment_file -log logfile

            #
            cmdPath =os.path.join(self.__annotAppsPath,"bin","MovingCoordByMatrix")
            thisCmd  = " ; " + cmdPath                        
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log "
            if  self.__inputParamDict.has_key('transform_file_path'):
                assignFilePath=self.__inputParamDict['transform_file_path']                                
                cmd += " -assign " + assignFilePath           
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif (op == "annot-extra-checks"):
            #
            # MiscChecking -input ciffile -output outputfile -log logfile
            #
            cmdPath =os.path.join(self.__annotAppsPath,"bin","MiscChecking")
            thisCmd  = " ; " + cmdPath                        
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log "
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            cmd += " ; cat annot-step.log " + " >> " + lPath
            cmd += " ; touch " + iPath + "-parser.log "             
            cmd += " ; cat " + iPath + "-parser.log >> " + oPath

            ##
        elif (op == "annot-merge-xyz"):
            #   MergeCoordinates -input input_ciffile -output output_ciffile -newcoord new_coordinate_file -format pdb|cif [-log logfile]
            #
            #        option "-format pdb":   new_coordinates_file is PDB format file
            #        option "-format cif":   new_coordinates_file is cif format file
            #
            ##
            cmdPath =os.path.join(self.__annotAppsPath,"bin","MergeCoordinates")
            thisCmd  = " ; " + cmdPath                        
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log " 
            #
            if  self.__inputParamDict.has_key('new_coordinate_file_path'):
                xyzFilePath=self.__inputParamDict['new_coordinate_file_path']
                cmd += " -newcoord " + xyzFilePath

            if  self.__inputParamDict.has_key('new_coordinate_format'):
                xyzFormat=self.__inputParamDict['new_coordinate_format']
                cmd += " -format " + xyzFormat
            else:
                cmd += " -format cif "
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif (op == "annot-update-terminal-atoms"):
            # UpdateTerminalAtom -input input_ciffile -output output_ciffile -option delete|rename [-log logfile]
            #
            #   If option "delete" is selected, "OXT" atom will be deleted. If option "rename" is selected, 
            #     the "OXT" will be renamed to "N" in next residue.
            #
            ##
            cmdPath =os.path.join(self.__annotAppsPath,"bin","UpdateTerminalAtom")
            thisCmd  = " ; " + cmdPath                        
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log " 
            #
            if  self.__inputParamDict.has_key('option'):
                option=self.__inputParamDict['option']
                cmd += " -option " + option
            else:
                cmd += " -option delete "
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            cmd += " ; cat annot-step.log " + " >> " + lPath
        elif (op == "annot-gen-assem-pdbx"):
            #   
            #    GenBioCIFFile -input model_ciffile -depid depositionID -index output_index_file [-log logfile]
            #
            ##
            cmdPath =os.path.join(self.__annotAppsPath,"bin","GenBioCIFFile")
            thisCmd  = " ; " + cmdPath                        
            cmd += thisCmd + " -input " + iPath + " -log annot-step.log " 
            #
            if  self.__inputParamDict.has_key('deposition_data_set_id'):
                depId=self.__inputParamDict['deposition_data_set_id']
                cmd += " -depid " + depId

            idxFilePath=oPath
            if  self.__inputParamDict.has_key('index_file_path'):
                idxFilePath=self.__inputParamDict['index_file_path']
            cmd += " -index " + idxFilePath

            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif (op == "prd-search"):
            cmd += " ; PRDCC_PATH="  + self.__prdccCvsPath + " ; export PRDCC_PATH "
            cmd += " ; PRD_DICT_PATH="  + self.__prdDictPath + " ; export PRD_DICT_PATH "
            cmdPath = os.path.join(self.__annotAppsPath,"bin","GetPrdMatch")
            cmd += " ; " + cmdPath + " -input " + iPath + " -output " + oPath \
                 + " -path . -index ${PRD_DICT_PATH}/prd_summary.sdb"
            if self.__inputParamDict.has_key('logfile'):
                cmd += " -log " + self.__inputParamDict['logfile']
            if self.__inputParamDict.has_key('firstmodel'):
                cmd += " -firstmodel " + self.__inputParamDict['firstmodel']
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
        else:
            
            return -1
        #
        
        if (self.__debug):
            self.__lfh.write("+RcsbDpUtility._annotationStep()  - Application string:\n%s\n" % cmd.replace(";","\n"))        
        #
        if (self.__debug):            
            cmd += " ; ls -la  > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                                    
            
        cmd += " ) > %s 2>&1 " % ePathFull
        
        cmd += " ; cat " + ePathFull + " >> " + lPathFull

        if (self.__debug):
            ofh = open(lPathFull,'w')
            lt = time.strftime("%Y %m %d %H:%M:%S", time.localtime())
            ofh.write("\n\n-------------------------------------------------\n")
            ofh.write("LogFile:      %s\n" % lPath)
            ofh.write("Working path: %s\n" % self.__wrkPath)
            ofh.write("Date:         %s\n" % lt)
            if (self.__verbose):
                ofh.write("\nStep command:\n%s\n-------------------------------------------------\n" % cmd.replace(";","\n"))
            ofh.close()
           

        if self.__timeout > 0:
            iret=self.__runTimeout(cmd, self.__timeout,lPathFull)
        else:
            iret = self.__run(cmd)



        #
        # After execution processing --
        #
        if ((op == "annot-reposition-solvent-add-derived") or (op == "annot-reposition-solvent-add-derived-org")):
            # remove these categories for now -- 
            stripList=    ['pdbx_coord',
                           # 'pdbx_entity_nonpoly',
                           # 'pdbx_missing_residue_list',
                           'pdbx_nonstandard_list',
                           'pdbx_protein_info',
                           'pdbx_solvent_info',
                           'pdbx_struct_sheet_hbond',
                           'pdbx_unobs_or_zero_occ_residues',
                           'pdbx_validate_torsion',
                           'struct_biol_gen',
                           'struct_conf',
                           'struct_conf_type',
                           'struct_mon_prot_cis',
                           'struct_sheet',
                           'struct_sheet_order',
                           'struct_sheet_range',
                           'struct_conn',
                           'struct_site',
                           'struct_site_gen']

            strpCt=PdbxStripCategory(verbose=self.__verbose,log=self.__lfh)
            strpCt.strip(oPath2Full,oPathFull,stripList)

        if ((op == "annot-rcsb2pdbx-strip") or (op == "annot-rcsbeps2pdbx-strip")):
            # remove these derived categories for now -- 
            stripList=    ['pdbx_coord',
                           'pdbx_nonstandard_list',
                           'pdbx_protein_info',
                           'pdbx_solvent_info',
                           'pdbx_struct_sheet_hbond',
                           'pdbx_unobs_or_zero_occ_residues',
                           'pdbx_validate_torsion',
                           'struct_biol_gen',
                           'struct_conf',
                           'struct_conf_type',
                           'struct_mon_prot_cis',
                           'struct_sheet',
                           'struct_sheet_order',
                           'struct_sheet_range',
                           'struct_conn',
                           'struct_site',
                           'struct_site_gen',
                           'pdbx_validate_close_contact',
                           'pdbx_validate_symm_contact',
                           'pdbx_validate_peptide_omega',
                           'pdbx_struct_mod_residue',
                           'pdbx_missing_residue_list',
                           'pdbx_poly_seq_scheme',
                           'pdbx_nonpoly_scheme',
                           'struct_biol_gen',
                           'struct_asym']
            strpCt=PdbxStripCategory(verbose=self.__verbose,log=self.__lfh)
            strpCt.strip(oPath2Full,oPathFull,stripList)

        if ((op == "annot-rcsb2pdbx-strip-plus-entity") or (op == "annot-rcsbeps2pdbx-strip-plus-entity")):
            # remove derived categories plus selected entity-level categories -- 
            stripList=    [
                'entity_poly_seq',
                'pdbx_coord',
                'pdbx_nonstandard_list',
                'pdbx_protein_info',
                'pdbx_solvent_info',
                'pdbx_struct_sheet_hbond',
                'pdbx_unobs_or_zero_occ_residues',
                'pdbx_validate_torsion',
                'struct_biol_gen',
                'struct_conf',
                'struct_conf_type',
                'struct_mon_prot_cis',
                'struct_sheet',
                'struct_sheet_order',
                'struct_sheet_range',
                'struct_conn',
                'struct_site',
                'struct_site_gen',
                'pdbx_validate_close_contact',
                'pdbx_validate_symm_contact',
                'pdbx_validate_peptide_omega',
                'pdbx_struct_mod_residue',
                'pdbx_missing_residue_list',
                'pdbx_poly_seq_scheme',
                'pdbx_nonpoly_scheme',
                'struct_asym'
            ]
            strpCt=PdbxStripCategory(verbose=self.__verbose,log=self.__lfh)
            strpCt.strip(oPath2Full,oPathFull,stripList)
        
        if ((op == "annot-wwpdb-validate-1") or (op == "annot-wwpdb-validate-2") or (op == "annot-wwpdb-validate-alt") ):
            self.__resultPathList=[]
            #
            # Push the output pdf and xml files onto the resultPathList.
            #
            if os.access(pdfPath,os.F_OK):
                self.__resultPathList.append(pdfPath)
            else:
                self.__resultPathList.append("missing")                
            #
            if os.access(xmlPath,os.F_OK):
                self.__resultPathList.append(xmlPath)
            else:
                self.__resultPathList.append("missing")

            if os.access(pdfFullPath,os.F_OK):
                self.__resultPathList.append(pdfFullPath)
            else:
                self.__resultPathList.append("missing")

            if os.access(pngPath,os.F_OK):
                self.__resultPathList.append(pngPath)
            else:
                self.__resultPathList.append("missing")

            if os.access(svgPath,os.F_OK):
                self.__resultPathList.append(svgPath)
            else:
                self.__resultPathList.append("missing")

        elif (op == "annot-sf-convert"):
            self.__resultPathList=[]
            #
            # Push the output converted and diagnostic files onto the resultPathList.
            #
            if os.access(sfCifPath,os.F_OK):
                self.__resultPathList.append(sfCifPath)
            else:
                self.__resultPathList.append("missing")                

            if os.access(sfDiagPath,os.F_OK):
                self.__resultPathList.append(sfDiagPath)
            else:
                self.__resultPathList.append("missing")                

            if os.access(mtzDmpPath,os.F_OK):
                self.__resultPathList.append(mtzDmpPath)
            else:
                self.__resultPathList.append("missing")                
            

        elif (op == "annot-make-maps"):
            #
            self.__resultPathList=[]
            #
            # Push the output pdf and xml files onto the resultPathList.
            #
            if os.access(map2fofcPath,os.F_OK):
                self.__resultPathList.append(map2fofcPath)
            else:
                self.__resultPathList.append("missing")                

            if os.access(mapfofcPath,os.F_OK):
                self.__resultPathList.append(mapfofcPath)
            else:
                self.__resultPathList.append("missing")                

        elif (op == "annot-gen-assem-pdbx"):
            #
            self.__resultPathList=[]
            if os.access(idxFilePath,os.R_OK):
                ifh=open(idxFilePath,'r')
                for line in ifh:
                    fp=os.path.join(self.__wrkPath,line[:-1])
                    if os.access(fp,os.R_OK):
                        self.__resultPathList.append(fp)

        elif (op == "annot-make-ligand-maps"):
            pat = self.__wrkPath + '/*.map'
            self.__resultPathList= glob.glob(pat)
            if (self.__debug):
                self.__lfh.write("+RcsbDpUtility._annotationStep()  - pat %s resultPathList %s\n" % (pat,self.__resultPathList))
                self.__lfh.write("+RcsbDpUtility._annotationStep()  - return path %s\n" % outMapPathFull)

            if os.access(outMapPathFull,os.W_OK):
                try:
                    for fp in self.__resultPathList:
                        if fp.endswith('_2fofc.map'):
                            continue
                        (dn,fn)=os.path.split(fp)
                        ofp=os.path.join(outMapPathFull,fn)
                        shutil.copyfile(fp,ofp)
                        if (self.__verbose):
                            self.__lfh.write("+RcsbDpUtility._annotationStep()  - returning map file %s\n" % ofp)
                except:
                    if (self.__debug):
                        traceback.print_exc(file=self.__lfh)                    
        else:
            self.__resultPathList = [os.path.join(self.__wrkPath,oPath)]


        
        return iret
    

    def __validateStep(self, op):
        """ Internal method that performs a single validation operation.

            Now using only validation pack functions.
        """
        #
        # Set application specific path details here -
        #
        self.__localAppsPath  =  self.__getConfigPath('SITE_LOCAL_APPS_PATH')
        self.__packagePath    =  self.__getConfigPath('SITE_TOOLS_PATH')
        self.__deployPath     =  self.__getConfigPath('SITE_DEPLOY_PATH')        
        self.__ccDictPath     =  self.__getConfigPath('SITE_CC_DICT_PATH')
        self.__ccCvsPath      =  self.__getConfigPath('SITE_CC_CVS_PATH')                
        self.__prdccCvsPath   =  self.__getConfigPath('SITE_PRDCC_CVS_PATH')
        self.__prdDictPath    =  os.path.join(self.__getConfigPath('SITE_DEPLOY_PATH'), 'reference', 'components', 'prd-dict')

        self.__rcsbAppsPath  =  os.path.join(self.__packagePath,'validation-pack')
        #
        # These may not be needed -- 
        self.__pdbxDictPath  =  self.__getConfigPath('SITE_PDBX_DICT_PATH')
        self.__pdbxDictName  =  self.__cI.get('SITE_PDBX_DICT_NAME')
        self.__pathDdlSdb      = os.path.join(self.__pdbxDictPath,"mmcif_ddl.sdb")
        self.__pathPdbxDictSdb = os.path.join(self.__pdbxDictPath,self.__pdbxDictName+'.sdb')
        self.__pathPdbxDictOdb = os.path.join(self.__pdbxDictPath,self.__pdbxDictName+'.odb')

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
            iPathFull=os.path.abspath(os.path.join(self.__wrkPath, iPath))            
            ePathFull=os.path.join(self.__wrkPath, ePath)
            lPathFull=os.path.join(self.__wrkPath, lPath)
            tPathFull=os.path.join(self.__wrkPath, tPath)                                    
            cmd = "(cd " + self.__wrkPath
        else:
            iPathFull = iPath
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
        # Standard setup for maxit ---
        #
        cmd += " ; RCSBROOT=" + self.__rcsbAppsPath + " ; export RCSBROOT  "            
        cmd += " ; COMP_PATH=" + self.__ccCvsPath + " ; export COMP_PATH  "
        valCmd = os.path.join(self.__rcsbAppsPath,"bin","validation_with_cif_output")        

        #
        if (op == "validate-geometry"):
            thisCmd  = " ; " + valCmd                        
            cmd += thisCmd + " -cif " + iPath + " -output " + oPath + " -log validation-step.log " 
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            cmd += " ; cat validation-step.log " + " >> " + lPath
            cmd += " ; touch " + iPath + "-parser.log "             
            cmd += " ; cat " + iPath + "-parser.log >> " + lPath
        else:
            return -1
        #
        
        if (self.__debug):
            self.__lfh.write("+RcsbDpUtility._validationStep()  - Application string:\n%s\n" % cmd.replace(";","\n"))        
        #
        if (self.__debug):            
            cmd += " ; ls -la  > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                                    
            
        cmd += " ) > %s 2>&1 " % ePathFull

        cmd += " ; cat " + ePathFull + " >> " + lPathFull

        if (self.__debug):
            ofh = open(lPathFull,'w')
            lt = time.strftime("%Y %m %d %H:%M:%S", time.localtime())
            ofh.write("\n\n-------------------------------------------------\n")
            ofh.write("LogFile:      %s\n" % lPath)
            ofh.write("Working path: %s\n" % self.__wrkPath)
            ofh.write("Date:         %s\n" % lt)
            if (self.__verbose):
                ofh.write("\nStep command:\n%s\n-------------------------------------------------\n" % cmd.replace(";","\n"))
            ofh.close()
           
        if self.__timeout > 0:
            iret=self.__runTimeout(cmd, self.__timeout,lPathFull)
        else:
            iret = self.__run(cmd)

        return iret
    

                
    def __maxitStep(self, op, progName="maxit"):
        """ Internal method that performs a single maxit operation.
                    
        """
        # Set application specific path details --
        #
        # If this has not been initialized take if from the configuration class.        
        if self.__rcsbAppsPath is None:
            #self.__rcsbAppsPath  =  self.__getConfigPath('SITE_RCSB_APPS_PATH')
            self.__rcsbAppsPath  =  self.__getConfigPath('SITE_ANNOT_TOOLS_PATH')
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
        cmd += " ; RCSBROOT=" + self.__rcsbAppsPath + " ; export RCSBROOT "            
        cmd += " ; COMP_PATH=" + self.__ccCvsPath + " ; export COMP_PATH ; "
        maxitCmd = os.path.join(self.__rcsbAppsPath,"bin",progName)        

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
            cmd +=  maxitCmd + " -o 9 -i " + iPath
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
        if (self.__debug):            
            cmd += " ; ls -la >> " + lPath        
        #
        cmd += " ) > %s 2>&1 " % ePathFull
        
        if (self.__debug):
            self.__lfh.write("+RcsbDpUtility.maxitStep()  - Command string:\n%s\n" % cmd.replace(";","\n"))

        if (self.__debug):
            ofh = open(lPathFull,'w')
            lt = time.strftime("%Y %m %d %H:%M:%S", time.localtime())
            ofh.write("\n\n-------------------------------------------------\n")
            ofh.write("LogFile:      %s\n" % lPath)
            ofh.write("Working path: %s\n" % self.__wrkPath)
            ofh.write("Date:         %s\n" % lt)
            if (self.__verbose): 
                ofh.write("\nStep command:\n%s\n-------------------------------------------------\n" % cmd.replace(";","\n"))
                ofh.write("\n")
            ofh.close()

        if self.__timeout > 0:
            iret=self.__runTimeout(cmd, self.__timeout,lPathFull)
        else:
            iret = self.__run(cmd)

        #iret = os.system(cmd)
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
            #self.__rcsbAppsPath  =  self.__getConfigPath('SITE_RCSB_APPS_PATH')
            # 01-05-2013 -  Now point to the new annotation module
            self.__rcsbAppsPath  =  self.__getConfigPath('SITE_ANNOT_TOOLS_PATH')

        if self.__localAppsPath is None:                            
            self.__localAppsPath =  self.__getConfigPath('SITE_LOCAL_APPS_PATH')

        self.__packagePath    =  self.__getConfigPath('SITE_TOOLS_PATH')            

        #
        self.__ccAppsPath    =  self.__getConfigPath('SITE_CC_APPS_PATH')
        self.__pdbxDictPath  =  self.__getConfigPath('SITE_PDBX_DICT_PATH')
        self.__pdbxDictName  =  self.__cI.get('SITE_PDBX_DICT_NAME')
        self.__pdbxV4DictName  =  self.__cI.get('SITE_PDBX_V4_DICT_NAME')

        self.__ccDictPath    =  self.__getConfigPath('SITE_CC_DICT_PATH')
        self.__ccCvsPath     =  self.__getConfigPath('SITE_CC_CVS_PATH')

        
        self.__ccDictPathSdb = os.path.join(self.__ccDictPath,"Components-all-v3.sdb")
        self.__ccDictPathIdx = os.path.join(self.__ccDictPath,"Components-all-v3-r4.idx")        
        #
        self.__pathDdlSdb      = os.path.join(self.__pdbxDictPath,"mmcif_ddl.sdb")
        self.__pathDdl         = os.path.join(self.__pdbxDictPath,"mmcif_ddl.dic")        
        self.__pathPdbxDictSdb = os.path.join(self.__pdbxDictPath,self.__pdbxDictName+'.sdb')
        self.__pathPdbxV4DictSdb = os.path.join(self.__pdbxDictPath,self.__pdbxV4DictName+'.sdb')
        self.__pathPdbxDictOdb = os.path.join(self.__pdbxDictPath,self.__pdbxDictName+'.odb')
        #
        self.__oeDirPath        = self.__getConfigPath('SITE_CC_OE_DIR')
        self.__oeLicensePath    = self.__getConfigPath('SITE_CC_OE_LICENSE')
        self.__babelLibPath     = self.__getConfigPath('SITE_CC_BABEL_LIB')        
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
        elif (op == "check-cif"):
            cmdPath   = os.path.join(self.__packagePath,"dict","bin","CifCheck")
            thisCmd    = " ; "   + cmdPath 
            cmd += thisCmd + " -f " + iPath
            cmd += " -dictSdb " + self.__pathPdbxDictSdb 
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; touch " + iPath + "-diag.log "
            cmd += " ; touch " + iPath + "-parser.log "             
            cmd += " ; cat " + iPath + "-parser.log > " + oPath
            cmd += " ; cat " + iPath + "-diag.log  >> " + oPath            
            #cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
        elif (op == "check-cif-v4"):
            cmdPath   = os.path.join(self.__packagePath,"dict","bin","CifCheck")
            thisCmd    = " ; "   + cmdPath 
            cmd += thisCmd + " -f " + iPath
            cmd += " -dictSdb " + self.__pathPdbxV4DictSdb 
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; touch " + iPath + "-diag.log "
            cmd += " ; touch " + iPath + "-parser.log "             
            cmd += " ; cat " + iPath + "-parser.log > " + oPath
            cmd += " ; cat " + iPath + "-diag.log  >> " + oPath            
            #cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        

        elif (op == "cif2pdbx-public"):
            # dict/bin/cifexch2 -dicSdb mmcif_pdbx_v5_next.sdb -reorder -strip -op in -pdbids -input D_1000200033_model_P1.cif -output 4ovr.cif
            #
            cmdPath = os.path.join(self.__packagePath,"dict","bin","cifexch2")
            thisCmd  = " ; " + cmdPath + " -dicSdb " + self.__pathPdbxDictSdb +  " -reorder  -strip -op in  -pdbids "
            cmd += thisCmd + " -input " + iPath  + " -output " + oPath
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
        elif ( (op == "chem-comp-assign") or (op == "chem-comp-assign-skip") or (op == "chem-comp-assign-exact") ):
            # set up
            #
            skipOp=""
            exactOp=""
            relOnlyOp=""
            
            if ( op == "chem-comp-assign-skip" ):
                skipOp=" -skip_search "
            if ( op == "chem-comp-assign-exact" ):
                exactOp=" -exact "
                relOnlyOp=" -rel " #i.e. released entries only
                
            cmd += " ; RCSBROOT="      + self.__rcsbAppsPath     + " ; export RCSBROOT "
            cmd += " ; OE_DIR="        + self.__oeDirPath        + " ; export OE_DIR "
            cmd += " ; OE_LICENSE="    + self.__oeLicensePath    + " ; export OE_LICENSE "
            cmd += " ; BABEL_DIR="     + self.__babelDirPath     + " ; export BABEL_DIR "
            cmd += " ; BABEL_DATADIR=" + self.__babelDataDirPath + " ; export BABEL_DATADIR "
            cmd += " ; CACTVS_DIR="    + self.__cactvsDirPath    + " ; export CACTVS_DIR "
            cmd += " ; LD_LIBRARY_PATH=" + self.__babelLibPath + ":" \
                   + os.path.join(self.__packagePath,"ccp4","lib") + ":" \
                   + os.path.join(self.__localAppsPath,"lib") +  " ; export LD_LIBRARY_PATH "              
            
            cmd += " ; env "
            cmdPath =os.path.join(self.__ccAppsPath,"bin","ChemCompAssign_main")
            thisCmd  = " ; rm -f " + oPath + " ; " + cmdPath
            entryId   = self.__inputParamDict['id']
            #
            #cc_link_file_path=''
            #if  self.__inputParamDict.has_key('link_file_path'):
            #    link_file=self.__inputParamDict['link_file_path']                
            #    cmd += " ;  cp " + link_file + " " + self.__wrkPath
            #
            cmd += thisCmd + skipOp + exactOp + relOnlyOp + " -i " + iPath + " -of " + oPath + " -o " + self.__wrkPath  +  " -ifmt pdbx " + " -id " + entryId
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
        elif (op == "chem-comp-assign-comp"):
            # set up
            #
            cmd += " ; RCSBROOT="      + self.__rcsbAppsPath     + " ; export RCSBROOT "
            cmd += " ; OE_DIR="        + self.__oeDirPath        + " ; export OE_DIR "
            cmd += " ; OE_LICENSE="    + self.__oeLicensePath    + " ; export OE_LICENSE "
            cmd += " ; BABEL_DIR="     + self.__babelDirPath     + " ; export BABEL_DIR "
            cmd += " ; BABEL_DATADIR=" + self.__babelDataDirPath + " ; export BABEL_DATADIR "
            cmd += " ; CACTVS_DIR="    + self.__cactvsDirPath    + " ; export CACTVS_DIR "
            cmd += " ; LD_LIBRARY_PATH=" + self.__babelLibPath + ":" \
                   + os.path.join(self.__packagePath,"ccp4","lib") + ":" \
                   + os.path.join(self.__localAppsPath,"lib") +  " ; export LD_LIBRARY_PATH "              
            
            cmd += " ; env ; rm -f " + oPath + " ; " + os.path.join(self.__ccAppsPath,"bin","ChemCompAssign_main")
            entryId = self.__inputParamDict['id']
            instId  = self.__inputParamDict['cc_instance_id']
            cmd += " -i " + iPath + " -of " + oPath + " -o " + self.__wrkPath +  " -ifmt comp -id " + entryId
            cmd += " -search_inst_id " + instId + " -libsdb " + self.__ccDictPathSdb + " -idxFile " \
                 + self.__ccDictPathIdx
            #
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
            cmd += " ; LD_LIBRARY_PATH=" + self.__babelLibPath + ":" \
                   + os.path.join(self.__packagePath,"ccp4","lib") + ":" \
                   + os.path.join(self.__localAppsPath,"lib") +  " ; export LD_LIBRARY_PATH "  
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
            cmd += thisCmd + " -i " + iPath + " -of " + oPath + " -o " + self.__wrkPath  +  " -ifmt comp " + " -id " + entryId
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
        else:
            return -1
        #
        
        if (self.__debug):
            self.__lfh.write("+RcsbDpUtility._rcsbStep()  - Application string:\n%s\n" % cmd.replace(";","\n"))        
        #
        if (self.__debug):            
            cmd += " ; ls -la  > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                                    
            
        cmd += " ) > %s 2>&1 " % ePathFull

        cmd += " ; cat " + ePathFull + " >> " + lPathFull

        if (self.__debug):
            ofh = open(lPathFull,'w')
            lt = time.strftime("%Y %m %d %H:%M:%S", time.localtime())
            ofh.write("\n\n-------------------------------------------------\n")
            ofh.write("LogFile:      %s\n" % lPath)
            ofh.write("Working path: %s\n" % self.__wrkPath)
            ofh.write("Date:         %s\n" % lt)
            if (self.__verbose):
                ofh.write("\nStep command:\n%s\n-------------------------------------------------\n" % cmd.replace(";","\n"))
            ofh.close()

        if self.__timeout > 0:
            iret=self.__runTimeout(cmd, self.__timeout,lPathFull)
        else:
            iret = self.__run(cmd)
           
        #iret = os.system(cmd)
        #
        if ((op == "pdbx2xml")):
            pat = self.__wrkPath + '/*.xml*'
            self.__resultPathList= glob.glob(pat)
        else:
            self.__resultPathList = [os.path.join(self.__wrkPath,oPath)]
        
        return iret

    def __pisaStep(self, op):
        """ Internal method that performs assembly calculation and management tasks.

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
            pisaSession  = str(self.__inputParamDict['pisa_session_name'])
        else:
            pisaSession = None
        cmd += " ; PISA_TOP="         + os.path.abspath(pisaTopPath)     + " ; export PISA_TOP "
        cmd += " ; PISA_SESSIONS="    + os.path.abspath(self.__wrkPath)         + " ; export PISA_SESSIONS "
        cmd += " ; PISA_CONF_FILE="   + os.path.abspath(os.path.join(pisaTopPath,"configure","pisa-standalone.cfg")) + " ; export PISA_CONF_FILE "
        #
        #cmd += " ; PISA_CONF_FILE="   + os.path.abspath(os.path.join(pisaTopPath,"share","pisa","pisa.cfg")) + " ; export PISA_CONF_FILE "
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
            cmd += " ; "   + cmdPath + " " + pisaSession + " -cif assembly " + str(pisaAssemblyId) + "  > " + oPath
            cmd += " 2> " + tPath + " ; cat " + tPath + " >> " + lPath
        elif (op == "pisa-assembly-merge-cif"):
            # MergePisaData -input input_ciffile -output output_ciffile -xml xmlfile_from_PISA_output
            #                -log logfile -spacegroup spacegroup_file -list idlist 
            #
            spgFilePath  =  self.__getConfigPath('SITE_SPACE_GROUP_FILE_PATH')                    
            #assemblyTupleList = self.__inputParamDict['pisa_assembly_tuple_list']
            assemblyFile      = self.__inputParamDict['pisa_assembly_file_path']
            assignmentFile      = self.__inputParamDict['pisa_assembly_assignment_file_path']
            cmdPath =  os.path.join(annotToolsPath,"bin","MergePisaData")
            #
            cmd   +=  " ; " + cmdPath + " -input " + iPathFull + " -xml " + assemblyFile
            cmd   +=  " -spacegroup " + spgFilePath + " -log " + ePath 
            cmd   +=  " -assign " + assignmentFile
            cmd   +=  " -output " + oPath
            #cmd   +=  " ; cp -f " + iPath + " " + oPath 
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            
        else:
            return -1
        #
        if (self.__debug):
            self.__lfh.write("+RcsbDpUtility._pisaStep()  - Application string:\n%s\n" % cmd.replace(";","\n"))        
        #
        if (self.__debug):            
            cmd += " ; ls -la  > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                                    
            
        cmd += " ) > %s 2>&1 " % ePathFull

        cmd += " ; cat " + ePathFull + " >> " + lPathFull

        if (self.__debug):
            ofh = open(lPathFull,'w')
            lt = time.strftime("%Y %m %d %H:%M:%S", time.localtime())
            ofh.write("\n\n-------------------------------------------------\n")
            ofh.write("LogFile:      %s\n" % lPath)
            ofh.write("Working path: %s\n" % self.__wrkPath)
            ofh.write("Date:         %s\n" % lt)
            if (self.__verbose):
                ofh.write("\nStep command:\n%s\n-------------------------------------------------\n" % cmd.replace(";","\n"))
            ofh.close()
           
        if self.__timeout > 0:
            iret=self.__runTimeout(cmd, self.__timeout,lPathFull)
        else:
            iret = self.__run(cmd)

        #iret = os.system(cmd)
        #
        return iret

    def __sequenceStep(self, op):
        """ Internal method that performs sequence search and entry selection operations.

        """
        #
        packagePath   =  self.__getConfigPath('SITE_TOOLS_PATH')
        seqDbPath     =  self.__getConfigPath('SITE_REFDATA_SEQUENCE_DB_PATH')
        ncbiToolsPath =  os.path.join(packagePath,'ncbi-blast+')
        
        
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

        if self.__inputParamDict.has_key('db_name'):
            dbName  = str(self.__inputParamDict['db_name'])
        else:
            dbName = "my_uniprot_all"

        if self.__inputParamDict.has_key('evalue'):
            eValue  = str(self.__inputParamDict['evalue'])
        else:
            eValue = '0.001'

        if self.__inputParamDict.has_key('num_threads'):
            numThreads  = str(self.__inputParamDict['num_threads'])
        else:
            numThreads = '1'

        if self.__inputParamDict.has_key('max_hits'):
            maxHits  = str(self.__inputParamDict['max_hits'])
        else:
            maxHits = '100'


        if self.__inputParamDict.has_key('one_letter_code_sequence'):
            sequence = str(self.__inputParamDict['one_letter_code_sequence'])
            self.__writeFasta(iPathFull,sequence,comment="myQuery")

        cmd += " ; BLASTDB="         + os.path.abspath(seqDbPath)     + " ; export BLASTDB "

        if (op == "seq-blastp"):
            #
            # $NCBI_BIN/blastp -evalue 0.001 -db $SEQUENCE_DB/$1  -num_threads 4 -query $2 -outfmt 5 -out $3
            #
            if self.__inputParamDict.has_key('db_name'):
                dbName  = str(self.__inputParamDict['db_name'] )
            else:
                dbName = "my_uniprot_all"

            cmdPath   = os.path.join(ncbiToolsPath,"bin","blastp")
            cmd += " ; "   + cmdPath + " -outfmt 5  -num_threads " + numThreads + " -num_alignments " + maxHits + " -evalue " + eValue + " -db " + os.path.join(seqDbPath,dbName)   + " -query " + iPathFull  + " -out " + oPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
        elif (op == "seq-blastn"):
            # -max_target_seqs 
            if self.__inputParamDict.has_key('db_name'):
                dbName  = str(self.__inputParamDict['db_name'])
            else:
                dbName = "my_ncbi_nt"
            cmdPath   = os.path.join(ncbiToolsPath,"bin","blastn")
            cmd += " ; "   + cmdPath + " -outfmt 5  -num_threads " + numThreads + " -num_alignments " + maxHits + " -evalue " + eValue + " -db " + os.path.join(seqDbPath,dbName)   + " -query " + iPathFull  + " -out " + oPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
        else:
            return -1
        #
        if (self.__debug):
            self.__lfh.write("+RcsbDpUtility._sequenceStep()  - Application string:\n%s\n" % cmd.replace(";","\n"))        
        #
        if (self.__debug):            
            cmd += " ; ls -la  > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                                    
            
        cmd += " ) > %s 2>&1 " % ePathFull

        cmd += " ; cat " + ePathFull + " >> " + lPathFull

        if (self.__debug):
            ofh = open(lPathFull,'w')
            lt = time.strftime("%Y %m %d %H:%M:%S", time.localtime())
            ofh.write("\n\n-------------------------------------------------\n")
            ofh.write("LogFile:      %s\n" % lPath)
            ofh.write("Working path: %s\n" % self.__wrkPath)
            ofh.write("Date:         %s\n" % lt)
            if (self.__verbose):
                ofh.write("\nStep command:\n%s\n-------------------------------------------------\n" % cmd.replace(";","\n"))
            ofh.close()

        if self.__timeout > 0:
            iret=self.__runTimeout(cmd, self.__timeout,lPathFull)
        else:
            iret = self.__run(cmd)
           
        #iret = os.system(cmd)
        #
        return iret

    def expSize(self):
        """Return the size of the last result file...
        """
        rf=self.__getResultWrkFile(self.__stepNo)
        if (self.__wrkPath != None):
            resultPath = os.path.join(self.__wrkPath,rf)
        else:
            resultPath = rf

        f1 = DataFile(resultPath)
        if f1.srcFileExists():
            return f1.srcFileSize()
        else:
            return 0

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
        if (self.__verbose):
            self.__lfh.write("+RcsbUtility.expList dstPathList    %r\n" % dstPathList)
            self.__lfh.write("+RcsbUtility.expList resultPathList %r\n" % self.__resultPathList)            
        #
        
        ok=True
        for f,fc in map(None,self.__resultPathList,dstPathList):
            if (self.__verbose):
                self.__lfh.write("+RcsbUtility.expList exporting %s to %s\n" % (f,fc))
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
        try:
            self.__lfh.write("+RcsbDpUtility.cleanup() removing working path %s\n" % self.__wrkPath)
            shutil.rmtree(self.__wrkPath,ignore_errors=True)
            return True
        except:
            self.__lfh.write("+RcsbDpUtility.cleanup() removal failed for working path %s\n" % self.__wrkPath)
            
        return False

    def __writeFasta(self, filePath,sequence,comment="myquery"):
        num_per_line = 60
        l = len(sequence) / num_per_line
        x = len(sequence) % num_per_line
        m = l
        if x:
            m = l + 1

        seq = '>'+str(comment).strip()+'\n'
        for i in range(m):
            n = num_per_line
            if i == l:
                n = x
            seq += sequence[i*num_per_line:i*num_per_line+n]
            if i != (m - 1):
                seq += '\n'
        try:
            ofh=open(filePath,'w')
            ofh.write(seq)
            ofh.close()
            return True
        except:
            if (self.__verbose):
                self.__lfh.write("+RcsbDpUtility.__writeFasta() failed for path %s\n" % filePath)
                traceback.print_exc(file=self.__lfh)                    

        return False

    def __runTimeout(self,command, timeout, logPath=None):
        """ Execute the input command string (sh semantics) as a subprocess with a timeout.

            
        """
        import subprocess, datetime, os, time, signal, stat
        self.__lfh.write("+RcsbDpUtility.__runTimeout() - Execution time out %d (seconds)\n" % timeout)
        start = datetime.datetime.now()
        cmdfile=os.path.join(self.__wrkPath,'timeoutscript.sh')
        ofh=open(cmdfile,'w')
        ofh.write("#!/bin/sh\n")
        ofh.write(command)
        ofh.write("#\n")
        ofh.close()
        st = os.stat(cmdfile)
        os.chmod(cmdfile, st.st_mode | stat.S_IEXEC)
        self.__lfh.write("+RcsbDpUtility.__runTimeout() running command %r\n" % cmdfile)        
        process = subprocess.Popen(cmdfile, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False,close_fds=True,preexec_fn=os.setsid)
        while process.poll() is None:
            time.sleep(0.1)
            now = datetime.datetime.now()
            if (now - start).seconds> timeout:
                #os.kill(-process.pid, signal.SIGKILL)
                os.killpg(process.pid, signal.SIGKILL)
                os.waitpid(-1, os.WNOHANG)
                self.__lfh.write("+ERROR RcsbDpUtility.__runTimeout() Execution terminated by timeout %d (seconds)\n" % timeout)
                if logPath is not None:
                    ofh=open(logPath,'a')
                    ofh.write("+ERROR - Execution terminated by timeout %d (seconds)\n" % timeout)
                    ofh.close()
                return None
        self.__lfh.write("+RcsbDpUtility.__runTimeout() completed with return code %r\n" % process.stdout.read())
        return 0

    def __run(self,command):
        retcode=-1000
        try:
            retcode = call(command, shell=True)        
            if retcode < 0:
                self.__lfh.write("+RcsbDpUtility.__run() operation %s completed with return code %r\n" % (self.__stepOpList,retcode))
            else:
                self.__lfh.write("+RcsbDpUtility.__run() operation %s completed with return code %r\n" % (self.__stepOpList,retcode))
        except OSError as e:
            self.__lfh.write("+RcsbDpUtility.__run() operation %s failed  with exception %r\n" % (self.__stepOpList,e))
        except:
            self.__lfh.write("+RcsbDpUtility.__run() operation %s failed  with exception\n" % self.__stepOpList)
        return retcode

    def __runP(self,cmd):
        retcode=-1000
        try:
            p1 = Popen(cmd, shell=True)
            retcode=p1.wait()
            if retcode < 0:
                self.__lfh.write("+RcsbDpUtility.__run() completed with return code %r\n" % retcode)
            else:
                self.__lfh.write("+RcsbDpUtility.__run() completed with return code %r\n" % retcode)
        except OSError as e:
            self.__lfh.write("+RcsbDpUtility.__run() failed  with exception %r\n" % e)
        except:
            self.__lfh.write("+RcsbDpUtility.__run() failed  with exception\n")
        return retcode
    
if __name__ == '__main__':
    rdpu=RcsbDpUtility()
    
        
