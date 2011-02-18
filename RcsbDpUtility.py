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
##
"""
Wrapper class for data processing and chemical component utilities.

Initial RCSB version - adapted from file utils method collections.


"""
import sys, os, os.path, glob, time, datetime, shutil, tempfile

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
        # tmpPath is used to place working directories if these are not explicitly set.
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
                           "initial-version","poly-link-dist","chem-comp-link", "chem-comp-assign", "chem-comp-assign-validation", "chem-comp-instance-update"]
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
        
        self.__initPath()

    def __initPath(self):
        """Set paths that depend on top-level resource paths
        """
        cI=ConfigInfo(self.__siteId)
        self.__rcsbAppsPath  =  os.path.abspath(cI.get('SITE_RCSB_APPS_PATH'))
        self.__ccAppsPath    =  os.path.abspath(cI.get('SITE_CC_APPS_PATH'))
        self.__pdbxDictPath  =  os.path.abspath(cI.get('SITE_PDBX_DICT_PATH'))
        self.__ccDictPath    =  os.path.abspath(cI.get('SITE_CC_DICT_PATH'))
        self.__localAppsPath =  os.path.abspath(cI.get('SITE_LOCAL_APPS_PATH'))
        
        self.__schemaPath    = os.path.join(self.__localAppsPath,"schema")
        self.__ccDictPathSdb = os.path.join(self.__ccDictPath,"Components-all-v3.sdb")
        self.__ccDictPathIdx = os.path.join(self.__ccDictPath,"Components-all-v3-r4.idx")        
        #
        self.__pathDdlSdb      = os.path.join(self.__pdbxDictPath,"mmcif_ddl.sdb")
        self.__pathPdbxDictSdb = os.path.join(self.__pdbxDictPath,"mmcif_pdbx.sdb")
        self.__pathPdbxDictOdb = os.path.join(self.__pdbxDictPath,"mmcif_pdbx.odb")
        #
        self.__oeDirPath        = os.path.abspath(cI.get('SITE_CC_OE_DIR'))
        self.__oeLicensePath    = os.path.abspath(cI.get('SITE_CC_OE_LICENSE'))
        self.__babelDirPath     = os.path.abspath(cI.get('SITE_CC_BABEL_DIR'))
        self.__babelDataDirPath = os.path.abspath(cI.get('SITE_CC_BABEL_DATADIR'))
        self.__cactvsDirPath    = os.path.abspath(cI.get('SITE_CC_CACTVS_DIR'))
        #
        
    def setRcsbAppsPath(self,fPath):
        if (fPath != None and os.path.isdir(fPath)):
            self.__rcsbAppsPath = os.path.abspath(fPath)

    def setAppsPath(self,fPath):
        if (fPath != None and os.path.isdir(fPath)):
            self.__localAppsPath = os.path.abspath(fPath)
            self.__initPath()

    def saveResult(self):
        return(self.__stepNo)
    
    def useResult(self,stepNo):
        if (stepNo > 0 and stepNo <= self.__stepNo):
            self.__stepNoSaved = stepNo
            if (self.__verbose): 
                self.__lfh.write("++INFO - Using result from step %s\n" % self.__stepNoSaved)        
        
    def __makeTempWorkingDir(self):
        if (self.__tmpPath != None and os.path.isdir(self.__tmpPath)):
            self.__wrkPath = tempfile.mkdtemp('dir','rcsbDp',self.__tmpPath)
        else:
            self.__wrkPath = tempfile.mkdtemp('dir','rcsbDp')            

        
    def setWorkingDir(self,dPath):
        if (not os.path.isdir(dPath)):
            os.makedirs(dPath,0755)
        if (os.access(dPath,os.F_OK)):
            self.__wrkPath = os.path.abspath(dPath)

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
        """Shuffle the output from the previous or a selected previous
           step as the input for the current operation.
        """
        #
        if (self.__stepNo > 1):
            if (self.__stepNoSaved != None ):
                return(self.__getResultWrkFile(self.__stepNoSaved) )
                self.__stepNoSaved = None
            else:
                return(self.__getResultWrkFile(self.__stepNo - 1))
            
        
    def __maxitStep(self, op):
        """ Internal method that performs a single maxit operation.
        """
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
            cmd += "; cp " + pPath + " "  + iPath
        #
        maxitPath   = os.path.join(self.__rcsbAppsPath,"bin","maxit")        
        maxitCmd = " ; RCSBROOT=" + self.__rcsbAppsPath 
        maxitCmd += " ; "   +  maxitPath + " -path " + self.__rcsbAppsPath


        if (op == "cif2cif"):
            cmd +=  maxitCmd + " -o 8  -i " + iPath
            cmd += " ; mv -f " + iPath + ".cif " + oPath

        elif (op == "cif2cif-remove"):
            cmd +=  maxitCmd + " -o 8  -remove -i " + iPath
            cmd += " ; mv -f " + iPath + ".cif " + oPath

        elif (op == "cif-rcsb2cif-pdbx"):
            #cmd +=  maxitCmd + " -o 56  -i " + iPath
            cmd +=  maxitCmd + " -o 10  -i " + iPath            
            cmd += " ; mv -f " + iPath + ".cif " + oPath                         

        elif (op == "cif-seqed2cif-pdbx"):
            #cmd +=  maxitCmd + " -o 56  -i " + iPath
            #cmd +=  maxitCmd + " -o 10  -i " + iPath
            cmd +=  maxitCmd + " -o 8  -i " + iPath                        
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
            cmd += thisCmd + " -i " + iPath + " -o " + oPath + " -assign " + assignPath +  " -ifmt pdbx " 
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
        f1.copy(self.__dstPath)

    def getResultPathList(self):
        return(self.__resultPathList)

    def expList(self,dstPathList=[]):
        """Export a copies of the list of last results to the corresponding paths
           in teh destination file path list.
        """
        if (dstPathList == [] or self.__resultPathList == []): return
        #
        for f,fc in map(None,self.__resultPathList,dstPathList):
            f1 = DataFile(f)
            f1.copy(fc)

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
    
        
