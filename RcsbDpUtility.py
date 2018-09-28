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
# 10-Feb-2014 jdw add __emStep and mapfix operation --
# 24-Feb-2014 jdw add em2em
# 25-Feb-2014 jdw make MovingWater an atomic process  called by "annot-reposition-solvent"  or "annot-reposition-solvent-add-derived"
# 15-Mar-2014 jdw add missing arguments parameters for dcc apps.
# 19-Mar-2014 jdw add adjust calling protocol for getsite -
#  3-Apr-2014 jdw suppress additional debugging diags in autogenerated scripts.
# 1-Jun-2014  jdw add maptest operation -- make javapath site dependent -  note - MapFixDep  not providing mandatory parameters at this point -
# 25-Jun-2014 jdw add  "annot-make-omit-maps"
# 27-Jun-2014 jdw add option to remove maximum alignment length
#  8-Jul-2014 jdw make the mode of the temporary directory group -rx-
# 11-Sep-2014 jdw add "annot-chem-shifts-atom-name-check","annot-chem-shifts-upload-check"  ...
# 12-Sep-2014 jdw add  -nmr opt for checkCoorFormat
# 14-Sep-2014 jdw add inputParamDict.has_key('deposit') to annot-merge-xyz
# 16-Sep-2014 jdw add "annot-reorder-models"
# 21-Sep-2014 jdw update annot-wwpdb-validate-test
# 26-Sep-2014 jdw update annot-pdbx2nmrstar (prior version retired to annot-pdbx2nmrstar-bmrb)
#  1-Oct-2014 jdw add "annot-chem-shifts-update"
# 16-Jan-2015 jdw update validation-report-test for NMR
# 23-Jan-2015 jdw add autocorrect option to method 'annot-update-map-header-in-place'
# 16-Sep-2015 jdw replace annot-wwpdb-validate-test with annot-wwpdb-validate-all
# 07-Oct-2015 jdw add 'deposit-update-map-header-in-place'
# 17-Mar-2016 jdw add "chem-comp-dict-makeindex" and "chem-comp-dict-serialize"
# 20-Mar-2016 jdw add clear log before chem-comp-dict- operations -
# 21-Mar-2016 jdw add append/copy mode option on logfile export -
# 04-Apr-2016 ep  update annot-dcc-report to use -auto option as validation always does
# 10-May-2016 jdw update environment: SITE_TOOLS_PATH replaced by SITE_PACKAGES_PATH
# 14-Jul-2016 jdw add support for validation mode setting - 'request_validation_mode'
# 24-Oct-2015 esg for img-convert add +repage argument
# 16-Nov-2016 ep  Add xml-header-check for EMDB header file
# 28-Nov-2016 ep  Add check-cif-ext and cif2pdbx-ext
# 18-Dec-2016 ep  Update annot-wwpdb-validate-all to remove Vpackv2. Remove old annot-wwpdb-validate-alt, annot-wwpdb-validate-2
# 13-Jan-2017 ep  Add annot-dcc-fix-special-position and annot-update-dep-assembly-info
# 21-Dec-2018 ep  Add support for VALID_SCR_PATH from site-config to specify
#                 location that validation reports should run from
# 20-Jul-2018 zf  Add "annot-poly-link-dist-json"
# 20-Aug-2018 ep  For "annot-site" do not include CCP4/lib directory - as including shared libraries from there interferes with system gfortran
##
"""
Wrapper class for data processing and chemical component utilities.

Initial RCSB version - adapted from file utils method collections.


"""
import sys
import os
import os.path
import glob
import time
import datetime
import shutil
import tempfile
import traceback
import socket
import shlex
import stat
import logging
import random

from wwpdb.utils.rcsb.DataFile import DataFile
from wwpdb.api.facade.ConfigInfo import ConfigInfo
from subprocess import call, Popen

from wwpdb.utils.rcsb.PdbxStripCategory import PdbxStripCategory
from wwpdb.utils.rcsb.RunRemote import RunRemote


class RcsbDpUtility(object):

    """ Wrapper class for data processing and chemical component utilities.
    """

    def __init__(self, tmpPath="/scratch", siteId='DEV', verbose=False, log=sys.stderr):
        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        #
        # tmpPath is used (if it exists) to place working directories if these are not explicitly set.
        # This path is not used otherwise.
        #
        self.__tmpPath = tmpPath
        self.__siteId = siteId
        #
        # Working directory and file path details
        #
        # The working directory is where temporary files are stored by utility operations.
        # This can be set explicity via the self.setWorkingDir() method or will be created
        # as a temporary path dynamically as a subdirectory of self.__tmpDir.
        #
        self.__wrkPath = None
        self.__sourceFileList = []
        self.__resultPathList = []
        self.__inputParamDict = {}
        #
        # List of known operations ---
        self.__maxitOps = ["cif2cif", "cif2cif-remove", "cif2cif-ebi", "cif2cif-pdbx", "cif2cif-pdbx-skip-process", "cif-rcsb2cif-pdbx",
                           "cif-seqed2cif-pdbx", "cif2pdb", "pdb2cif", "pdb2cif-ebi", "switch-dna",
                           "cif2pdb-assembly", "pdbx2pdb-assembly", "pdbx2deriv"]
        self.__rcsbOps = ["rename-atoms", "cif2pdbx", "pdbx2xml", "pdb2dssp", "pdb2stride", "initial-version", "poly-link-dist",
                          "chem-comp-link", "chem-comp-assign", "chem-comp-assign-comp", "chem-comp-assign-skip",
                          "chem-comp-assign-exact", "chem-comp-assign-validation", "check-cif", "check-cif-v4", "check-cif-ext",
                          "cif2pdbx-public", "cif2pdbx-ext",
                          "chem-comp-dict-makeindex", "chem-comp-dict-serialize", "chem-comp-annotate-comp"]
        self.__pisaOps = ["pisa-analysis", "pisa-assembly-report-xml", "pisa-assembly-report-text",
                          "pisa-interface-report-xml", "pisa-assembly-coordinates-pdb", "pisa-assembly-coordinates-cif",
                          "pisa-assembly-coordinates-cif", "pisa-assembly-merge-cif"]
        self.__annotationOps = ["annot-secondary-structure", "annot-link-ssbond", "annot-cis-peptide", "annot-distant-solvent",
                                "annot-merge-struct-site", "annot-reposition-solvent", "annot-base-pair-info",
                                "annot-validation", "annot-site", "annot-rcsb2pdbx", "annot-consolidated-tasks",
                                "annot-wwpdb-validate-all", "prd-search",
                                "annot-chem-shift-check", "annot-chem-shift-coord-check",
                                "annot-nmrstar2pdbx", "annot-pdbx2nmrstar", "annot-pdbx2nmrstar-bmrb",
                                "annot-reposition-solvent-add-derived", "annot-rcsb2pdbx-strip", "annot-rcsbeps2pdbx-strip",
                                "annot-rcsb2pdbx-strip-plus-entity", "annot-rcsbeps2pdbx-strip-plus-entity",
                                "chem-comp-instance-update", "annot-cif2cif", "annot-cif2pdb", "annot-pdb2cif", "annot-poly-link-dist",
                                "annot-merge-sequence-data", "annot-make-maps", "annot-make-ligand-maps", "annot-poly-link-dist-json",
                                "annot-make-omit-maps",
                                "annot-cif2cif-dep", "annot-pdb2cif-dep", "annot-format-check-pdbx", "annot-format-check-pdb",
                                "annot-dcc-report", "annot-sf-convert", "annot-tls-range-correction", "annot-dcc-refine-report", "annot-dcc-biso-full",
                                "annot-dcc-special-position", "annot-dcc-fix-special-position", "annot-dcc-reassign-alt-ids",
                                "annot-rcsb2pdbx-withpdbid", "annot-merge-tls-range-data",
                                "annot-rcsb2pdbx-withpdbid-singlequote", "annot-rcsb2pdbx-alt",
                                "annot-move-xyz-by-matrix", "annot-move-xyz-by-symop", "annot-extra-checks",
                                "annot-update-terminal-atoms", "annot-merge-xyz", "annot-gen-assem-pdbx", "annot-cif2pdbx-withpdbid",
                                "annot-validate-geometry", "annot-update-dep-assembly-info",
                                "annot-chem-shifts-atom-name-check", "annot-chem-shifts-upload-check", "annot-reorder-models", "annot-chem-shifts-update", "annot-get-corres-info"]
        self.__sequenceOps = ['seq-blastp', 'seq-blastn']
        self.__validateOps = ['validate-geometry']
        self.__emOps = ['mapfix-big', 'em2em-spider', 'fsc_check',
                        'img-convert', 'annot-read-map-header',
                        'annot-read-map-header-in-place',
                        'annot-update-map-header-in-place',
                        'deposit-update-map-header-in-place',
                        'xml-header-check']

        #
        # Source, destination and logfile path details
        #
        self.__srcPath = None
        self.__dstPath = None
        self.__dstLogPath = None
        self.__dstErrorPath = None
        #
        self.__stepOpList = []
        self.__stepNo = 0
        self.__stepNoSaved = None
        self.__timeout = 0

        self.__run_remote = False

        self.__cI = ConfigInfo(self.__siteId)
        self.__initPath()
        self.__getRunRemote()

    def __getConfigPath(self, ky):
        try:
            pth = os.path.abspath(self.__cI.get(ky))
            if (self.__debug):
                self.__lfh.write("+RcsbDpUtility.__getConfigPath()  - site %s configuration for %s is %s\n" % (self.__siteId, ky, pth))
        except:
            if (self.__verbose):
                self.__lfh.write("++WARN - site %s configuration data missing for %s\n" % (self.__siteId, ky))
            pth = ''
        return pth

    def __initPath(self):
        """ Provide placeholder values for application specific path details
        """
        #
        self.__rcsbAppsPath = None
        self.__localAppsPath = None
        self.__annotAppsPath = None
        self.__toolsPath = None
        #

    def setDebugMode(self, flag=True):
        self.__debug = flag

    def setTimeout(self, seconds):
        try:
            if seconds is None or int(seconds) < 1:
                return False
            self.__lfh.write("+INFO RcsbDpUtility.setTimeout() - Set execution time out %d (seconds)\n" % seconds)
            self.__timeout = int(seconds)
            return True
        except:
            return False

    def setRunRemote(self):
        self.__run_remote = True

    def __getRunRemote(self):
        try:
            if self.__cI.get('PDBE_CLUSTER_QUEUE'):
                self.__run_remote = True
        except Exception as e:
            logging.info('unable to get cluster queue')

    def setRcsbAppsPath(self, fPath):
        """ Set or overwrite the configuration setting for __rcsbAppsPath.
        """
        if (fPath is not None and os.path.isdir(fPath)):
            self.__rcsbAppsPath = os.path.abspath(fPath)

    def setAppsPath(self, fPath):
        """ Set or overwrite the configuration setting for __localAppsPath.
        """
        if (fPath is not None and os.path.isdir(fPath)):
            self.__localAppsPath = os.path.abspath(fPath)

    def saveResult(self):
        return(self.__stepNo)

    def useResult(self, stepNo):
        if (stepNo > 0 and stepNo <= self.__stepNo):
            self.__stepNoSaved = stepNo
            if (self.__verbose):
                self.__lfh.write("+RcsbDpUtility.useResult()  - Using result from step %s\n" % self.__stepNoSaved)

    def __makeTempWorkingDir(self):
        try:
            hostName = str(socket.gethostname()).split('.')[0]
            if ((hostName is not None) and (len(hostName) > 0)):
                suffix = '-' + hostName
            else:
                suffix = '-dir'

            prefix = 'rcsb-'
            if (self.__tmpPath is not None and os.path.isdir(self.__tmpPath)):
                self.__wrkPath = tempfile.mkdtemp(suffix, prefix, self.__tmpPath)
            else:
                self.__wrkPath = tempfile.mkdtemp(suffix, prefix)
            #
            os.chmod(self.__wrkPath, 0o750)
            return True
        except:
            if (self.__verbose):
                self.__lfh.write("+RcsbDpUtility.__makeTempWorkingDir()  - failed \n")
                traceback.print_exc(file=self.__lfh)
            return False

    def setWorkingDir(self, dPath):
        if (not os.path.isdir(dPath)):
            os.makedirs(dPath, 0o755)
        if (os.access(dPath, os.F_OK)):
            self.__wrkPath = os.path.abspath(dPath)

    def getWorkingDir(self):
        return self.__wrkPath

    def setSource(self, fPath):
        if (os.access(fPath, os.F_OK)):
            self.__srcPath = os.path.abspath(fPath)
        else:
            self.__srcPath = None
        self.__stepNo = 0

    def setDestination(self, fPath):
        self.__dstPath = os.path.abspath(fPath)

    def setErrorDestination(self, fPath):
        self.__dstErrorPath = os.path.abspath(fPath)

    def setLogDestination(self, fPath):
        self.__dstLogPath = os.path.abspath(fPath)

    def op(self, op):
        if (self.__srcPath is None and len(self.__inputParamDict) < 1):
            self.__lfh.write("+RcsbDbUtility.op() ++ Error  - no input provided for operation %s\n" % op)
            return -1

        if (self.__verbose):
            self.__lfh.write("\n\n+RcsbDpUtility.op() starting op %s with working path %s\n" % (op, self.__wrkPath))

        if (self.__wrkPath is None):
            self.__makeTempWorkingDir()

        self.__stepOpList.append(op)

        if op in self.__maxitOps:
            self.__stepNo += 1
            return self.__maxitStep(op)
        elif op in self.__rcsbOps:
            self.__stepNo += 1
            return self.__rcsbStep(op)

        elif op in self.__pisaOps:
            self.__stepNo += 1
            return self.__pisaStep(op)

        elif op in self.__annotationOps:
            self.__stepNo += 1
            return self.__annotationStep(op)

        elif op in self.__sequenceOps:
            self.__stepNo += 1
            return self.__sequenceStep(op)

        elif op in self.__validateOps:
            self.__stepNo += 1
            return self.__validateStep(op)

        elif op in self.__emOps:
            self.__stepNo += 1
            return self.__emStep(op)

        else:
            self.__lfh.write("+RcsbDpUtility.op() ++ Error  - Unknown operation %s\n" % op)
            return -1

    def __getSourceWrkFileList(self, stepNo):
        """Build a file containing the current list of source files.
        """
        fn = "input_file_list_" + str(stepNo)
        if (self.__wrkPath is not None):
            iPathList = os.path.join(self.__wrkPath, fn)
        else:
            iPathList = fn
        #
        ofh = open(iPathList, 'w')
        if (self.__sourceFileList == []):
            ofh.write("%s\n" % self.__getSourceWrkFile(self.__stepNo))
        else:
            for f in self.__sourceFileList == []:
                ofh.write("%s\n", f)
        ofh.close()
        #
        return(iPathList)

    def __getSourceWrkFile(self, stepNo):
        return("input_file_" + str(stepNo))

    def __getResultWrkFile(self, stepNo):
        return("result_file_" + str(stepNo))

    def __getLogWrkFile(self, stepNo):
        return("log_file_" + str(stepNo))

    def __getErrWrkFile(self, stepNo):
        return("error_file_" + str(stepNo))

    def __getTmpWrkFile(self, stepNo):
        return("temp_file_" + str(stepNo))

    def __updateInputPath(self):
        """Shuffle the output from the previous step or a selected previous
           step as the input for the current operation.
        """
        #
        if (self.__stepNo > 1):
            if (self.__stepNoSaved is not None):
                return(self.__getResultWrkFile(self.__stepNoSaved))
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
        self.__annotAppsPath = self.__getConfigPath('SITE_ANNOT_TOOLS_PATH')
        self.__localAppsPath = self.__getConfigPath('SITE_LOCAL_APPS_PATH')
        self.__packagePath = self.__getConfigPath('SITE_PACKAGES_PATH')
        self.__deployPath = self.__getConfigPath('SITE_DEPLOY_PATH')
        self.__topPythonDir = self.__getConfigPath('TOP_WWPDB_PYTHON_DIR')
        self.__siteLoc = self.__cI.get('WWPDB_SITE_LOC')
        self.__ccDictPath = self.__getConfigPath('SITE_CC_DICT_PATH')
        self.__ccCvsPath = self.__getConfigPath('SITE_CC_CVS_PATH')
        self.__prdccCvsPath = self.__getConfigPath('SITE_PRDCC_CVS_PATH')
        self.__prdDictPath = os.path.join(self.__getConfigPath('SITE_DEPLOY_PATH'), 'reference', 'components', 'prd-dict')
        self.__siteWebAppsSessionsPath = self.__cI.get('SITE_WEB_APPS_SESSIONS_PATH')
        self.__validScrPath = self.__cI.get('VALID_SCR_PATH')
        self.__siteConfigDir = self.__getConfigPath('TOP_WWPDB_SITE_CONFIG_DIR')
        self.__ccDictPathIdx = os.path.join(self.__ccDictPath, "Components-all-v3-r4.idx")

        # if self.__rcsbAppsPath is None:
        #            self.__rcsbAppsPath  =  self.__getConfigPath('SITE_RCSB_APPS_PATH')
        # JDW 2013-02-26
        self.__rcsbAppsPath = self.__getConfigPath('SITE_ANNOT_TOOLS_PATH')
        #
        # These may not be needed --
        self.__pdbxDictPath = self.__getConfigPath('SITE_PDBX_DICT_PATH')
        self.__pdbxDictName = self.__cI.get('SITE_PDBX_DICT_NAME')
        self.__pathDdlSdb = os.path.join(self.__pdbxDictPath, "mmcif_ddl.sdb")
        self.__pathPdbxDictSdb = os.path.join(self.__pdbxDictPath, self.__pdbxDictName + '.sdb')
        self.__pathPdbxDictOdb = os.path.join(self.__pdbxDictPath, self.__pdbxDictName + '.odb')

        #
        #
        iPath = self.__getSourceWrkFile(self.__stepNo)
        iPathList = self.__getSourceWrkFileList(self.__stepNo)
        oPath = self.__getResultWrkFile(self.__stepNo)
        lPath = self.__getLogWrkFile(self.__stepNo)
        ePath = self.__getErrWrkFile(self.__stepNo)
        tPath = self.__getTmpWrkFile(self.__stepNo)
        #
        if (self.__wrkPath is not None):
            iPathFull = os.path.abspath(os.path.join(self.__wrkPath, iPath))
            ePathFull = os.path.join(self.__wrkPath, ePath)
            lPathFull = os.path.join(self.__wrkPath, lPath)
            tPathFull = os.path.join(self.__wrkPath, tPath)
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
            if (os.access(pPath, os.F_OK)):
                cmd += "; cp " + pPath + " " + iPath

        #
        # Standard setup for maxit ---
        #
        cmd += " ; RCSBROOT=" + self.__rcsbAppsPath + " ; export RCSBROOT  "
        cmd += " ; COMP_PATH=" + self.__ccCvsPath + " ; export COMP_PATH  "
        maxitCmd = os.path.join(self.__rcsbAppsPath, "bin", "maxit")

        #
        if (op == "annot-secondary-structure"):
            cmdPath = os.path.join(self.__annotAppsPath, "bin", "GetSecondStruct")
            thisCmd = " ; " + cmdPath
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log "
            #
            if 'ss_topology_file_path' in self.__inputParamDict:
                topFilePath = self.__inputParamDict['ss_topology_file_path']
                cmd += " -support " + topFilePath
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif (op == "annot-consolidated-tasks"):

            cmdPath = os.path.join(self.__annotAppsPath, "bin", "GetAddAnnotation")
            thisCmd = " ; " + cmdPath
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log "
            #
            if 'ss_topology_file_path' in self.__inputParamDict:
                topFilePath = self.__inputParamDict['ss_topology_file_path']
                cmd += " -support " + topFilePath
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif (op == "annot-validate-geometry"):
            # UpdateValidateCategories -input input_ciffile -output output_ciffile -log logfile
            #
            cmdPath = os.path.join(self.__annotAppsPath, "bin", "UpdateValidateCategories")
            thisCmd = " ; " + cmdPath
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log "
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif (op == "annot-link-ssbond"):
            cmdPath = os.path.join(self.__annotAppsPath, "bin", "GetLinkAndSSBond")
            thisCmd = " ; " + cmdPath
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log  -link -ssbond "
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif (op == "annot-cis-peptide"):
            cmdPath = os.path.join(self.__annotAppsPath, "bin", "GetCisPeptide")
            thisCmd = " ; " + cmdPath
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log "
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif (op == "annot-distant-solvent"):
            cmdPath = os.path.join(self.__annotAppsPath, "bin", "CalculateDistantWater")
            thisCmd = " ; " + cmdPath
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log "
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif (op == "annot-base-pair-info"):
            cmdPath = os.path.join(self.__annotAppsPath, "bin", "GetBasePairInfo")
            thisCmd = " ; " + cmdPath
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log "
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; cat annot-step.log " + " >> " + lPath
        elif (op == "annot-merge-struct-site"):
            cmdPath = os.path.join(self.__annotAppsPath, "bin", "MergeSiteData")
            thisCmd = " ; " + cmdPath
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log "
            if 'site_info_file_path' in self.__inputParamDict:
                topFilePath = self.__inputParamDict['site_info_file_path']
                cmd += " -site " + topFilePath
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif (op == "annot-get-corres-info"):
            cmdPath = os.path.join(self.__annotAppsPath, "bin", "GetCorresInfo")
            thisCmd = " ; " + cmdPath
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log "
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif ((op == "annot-reposition-solvent") or (op == "annot-reposition-solvent-add-derived")):
            cmdPath = os.path.join(self.__annotAppsPath, "bin", "MovingWater")
            thisCmd = " ; " + cmdPath
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log "
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif (op == "annot-reposition-solvent-add-derived-void"):
            #
            # oPath will point to the final result for this step
            #
            oPath2 = oPath + "_B"
            cmdPath = os.path.join(self.__annotAppsPath, "bin", "MovingWater")
            thisCmd = " ; " + cmdPath
            cmd += thisCmd + " -input " + iPath + " -output " + oPath2 + " -log annot-step.log "
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; cat annot-step.log " + " >> " + lPath

            oPath2Full = os.path.join(self.__wrkPath, oPath2)
            oPathFull = os.path.join(self.__wrkPath, oPath)
            #
            # see at the end for the post processing operations --
            #

        elif (op == "annot-reposition-solvent-add-derived-prev"):
            #
            # oPath will point to the final result for this step
            #
            oPath1 = oPath + "_A"
            oPath2 = oPath + "_B"
            cmdPath = os.path.join(self.__annotAppsPath, "bin", "MovingWater")
            thisCmd = " ; " + cmdPath
            cmd += thisCmd + " -input " + iPath + " -output " + oPath1 + " -log annot-step.log "
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; cat annot-step.log " + " >> " + lPath
            #
            # Adding a following step to synchronize required derived data for subsequent steps -
            #
            cmd += " ; " + maxitCmd + " -o 8  -i " + oPath1 + " -log maxit.log "
            cmd += " ; mv -f " + oPath1 + ".cif " + oPath2
            #cmd += " ; cat maxit.err >> " + lPath
            #
            # Paths for post processing --
            #
            oPath2Full = os.path.join(self.__wrkPath, oPath2)
            oPathFull = os.path.join(self.__wrkPath, oPath)
            #
            # see at the end for the post processing operations --
            #
        elif (op == "annot-format-check-pdbx"):
            # CheckCoorFormat -input inputfile -format (pdb|pdbx) -output outputfile
            cmdPath = os.path.join(self.__annotAppsPath, "bin", "CheckCoorFormat")
            thisCmd = " ; " + cmdPath
            nmrOpt = ' '
            if 'nmr' in self.__inputParamDict:
                nmrOpt = ' -nmr '
            cmd += thisCmd + " -input " + iPath + " -format pdbx  -output " + oPath + nmrOpt
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath

        elif (op == "annot-format-check-pdb"):
            # CheckCoorFormat -input inputfile -format (pdb|pdbx) -output outputfile
            cmdPath = os.path.join(self.__annotAppsPath, "bin", "CheckCoorFormat")
            thisCmd = " ; " + cmdPath
            nmrOpt = ' '
            if 'nmr' in self.__inputParamDict:
                nmrOpt = ' -nmr '
            cmd += thisCmd + " -input " + iPath + " -format pdb  -output " + oPath + nmrOpt
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath

        elif (op == "annot-pdbx2nmrstar-bmrb"):
            # self.__packagePath
            if 'data_set_id' in self.__inputParamDict:
                dId = self.__inputParamDict['data_set_id']
            else:
                dId = "UNASSIGNED"
            #
            cmdPath = os.path.join(self.__packagePath, "aditnmr-util", "nmrstar_to_pdbx.sh")
            thisCmd = " ; " + cmdPath
            cmd += " ; PACKAGE_DIR=" + self.__packagePath + " ; export PACKAGE_DIR "
            cmd += thisCmd + "  " + iPath + " " + dId + " " + oPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath

        elif (op == "annot-validation"):
            cmdPath = os.path.join(self.__annotAppsPath, "bin", "valdation_with_cif_output")
            thisCmd = " ; " + cmdPath
            cmd += thisCmd + " -cif " + iPath + " -output " + oPath + " -log annot-step.log "
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif (op == "annot-site"):
            cmd += " ; TOOLS_PATH=" + self.__packagePath + " ; export TOOLS_PATH "
            cmd += " ; CCP4=" + os.path.join(self.__packagePath, "ccp4") + " ; export CCP4 "
            cmd += " ; SYMINFO=" + os.path.join(self.__packagePath, "getsite-cif", "data", "syminfo.lib") + " ; export SYMINFO "
            cmd += " ; MMCIFDIC=" + os.path.join(self.__packagePath, "getsite-cif", "data", "cif_mmdic.lib") + " ; export MMCIFDIC "
            cmd += " ; STANDATA=" + os.path.join(self.__packagePath, "getsite-cif", "data", "standard_geometry.cif") + " ; export STANDATA "
            cmd += " ; CCIF_NOITEMIP=off ; export CCIF_NOITEMIP "
            # setenv DYLD_LIBRARY_PATH  "$CCP4/lib/ccif:$CCP4/lib"
            # cmd += " ; DYLD_LIBRARY_PATH=" + os.path.join(self.__packagePath,"ccp4","lib","ccif") + ":" + \
            #       os.path.join(self.__packagePath,"ccp4","lib") + " ; export DYLD_LIBRARY_PATH "

            cmd += " ; LD_LIBRARY_PATH=" + os.path.join(self.__packagePath, "ccp4-ccif", "lib") + ":" + \
                   os.path.join(self.__packagePath, "ccp4", "lib", "ccif") + " ; export LD_LIBRARY_PATH "

            cmd += " ; DYLD_LIBRARY_PATH=" + os.path.join(self.__packagePath, "ccp4-ccif", "lib") + ":" + \
                os.path.join(self.__packagePath, "ccp4") + " ; export DYLD_LIBRARY_PATH "

            # setenv CIFIN 1abc.cif
            cmd += " ; CIFIN=" + iPath + " ; export CIFIN "
            #cmd += " ; env "

            if 'block_id' in self.__inputParamDict:
                blockId = self.__inputParamDict['block_id']
            else:
                blockId = "UNK"

            # ../getsite_cif 1abc

            cmdPath = os.path.join(self.__packagePath, "getsite-cif", "bin", "getsite_cif")
            thisCmd = " ; " + cmdPath

            cmd += thisCmd + " " + blockId + " "

            if 'site_arguments' in self.__inputParamDict:
                cmdArgs = self.__inputParamDict['site_arguments']
                cmd += cmdArgs
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; mv -f " + blockId + "_site.cif " + oPath

        elif (op == "annot-merge-sequence-data"):
            # example -
            # MergeSeqModuleData -input RCSB056751_model_P1.cif.V1 -assign RCSB056751_seq-assign_P1.cif.V2 -output new_model.cif
            #
            cmdPath = os.path.join(self.__annotAppsPath, "bin", "MergeSeqModuleData")
            thisCmd = " ; " + cmdPath
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log "
            if 'seqmod_assign_file_path' in self.__inputParamDict:
                assignFilePath = self.__inputParamDict['seqmod_assign_file_path']
                cmd += " -assign " + assignFilePath
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif (op == "chem-comp-instance-update"):
            # New version that moved from the chem-comp-pack --
            cmdPath = os.path.join(self.__annotAppsPath, "bin", "updateInstance")
            thisCmd = " ; " + cmdPath
            assignPath = self.__inputParamDict['cc_assign_file_path']
            #selectPath = self.__inputParamDict['cc_select_file_path']
            cmd += thisCmd + " -i " + iPath + " -o " + oPath + " -assign " + assignPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath

        elif (op == "annot-rcsb2pdbx-alt"):
            cmd += " ; " + maxitCmd + " -single_quotation -o 9  -i " + iPath + " -log maxit.log "
            cmd += " ; mv -f " + iPath + ".cif " + oPath

        elif (op == "annot-pdbx2nmrstar"):
            #  For PDBx to NMR STar
            cmdPath = os.path.join(self.__annotAppsPath, "bin", "GenNMRStarCSFile")
            thisCmd = " ; " + cmdPath
            if 'pdb_id' in self.__inputParamDict:
                dId = self.__inputParamDict['pdb_id']
            else:
                dId = "UNASSIGNED"

            idOpt = " -pdbid  %s " % str(dId)
            cmd += thisCmd + " -i " + iPath + " -o " + oPath + idOpt
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath

        elif (op == "annot-rcsb2pdbx"):
            # New minimal RCSB internal cif to PDBx cif converter -
            cmdPath = os.path.join(self.__annotAppsPath, "bin", "PdbxConverter")
            thisCmd = " ; " + cmdPath
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log "
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif ((op == "annot-rcsb2pdbx-withpdbid") or (op == "annot-cif2pdbx-withpdbid")):
            # New minimal RCSB internal cif to PDBx cif converter with internal conversion of entry id to  pdbId -
            cmdPath = os.path.join(self.__annotAppsPath, "bin", "PdbxConverter")
            thisCmd = " ; " + cmdPath
            cmd += thisCmd + " -pdbid -input " + iPath + " -output " + oPath + " -log annot-step.log "
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif (op == "annot-rcsb2pdbx-withpdbid-singlequote"):

            # New minimal RCSB internal cif to PDBx cif converter with internal conversion of entry id to  pdbId -
            cmdPath = os.path.join(self.__annotAppsPath, "bin", "PdbxConverter")
            thisCmd = " ; " + cmdPath
            cmd += thisCmd + " -pdbid -single_quotation -input " + iPath + " -output " + oPath + " -log annot-step.log "
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif (op == "annot-rcsb2pdbx-strip"):

            # New minimal RCSB internal cif to PDBx cif converter followed by removal of derived categories

            oPath2 = oPath + "_A"

            cmdPath = os.path.join(self.__annotAppsPath, "bin", "PdbxConverter")
            thisCmd = " ; " + cmdPath
            cmd += thisCmd + " -input " + iPath + " -output " + oPath2 + " -log annot-step.log "
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; cat annot-step.log " + " >> " + lPath

            oPath2Full = os.path.join(self.__wrkPath, oPath2)
            oPathFull = os.path.join(self.__wrkPath, oPath)

        elif (op == "annot-rcsbeps2pdbx-strip"):
            #
            oPath2 = oPath + "_B"
            #
            # Adding a following step to synchronize required derived data for subsequent steps -
            #
            #
            cmd += " ; " + maxitCmd + " -o 8  -i " + iPath + " -log maxit.log "
            cmd += " ; mv -f " + iPath + ".cif " + oPath2
            #cmd += " ; cat maxit.err >> " + lPath
            #
            # Paths for post processing --
            #
            oPath2Full = os.path.join(self.__wrkPath, oPath2)
            oPathFull = os.path.join(self.__wrkPath, oPath)
            #
            # see at the end for the post processing operations --

        elif (op == "annot-rcsb2pdbx-strip-plus-entity"):

            # New minimal RCSB internal cif to PDBx cif converter followed by removal of derived categories

            oPath2 = oPath + "_A"

            cmdPath = os.path.join(self.__annotAppsPath, "bin", "PdbxConverter")
            thisCmd = " ; " + cmdPath
            cmd += thisCmd + " -input " + iPath + " -output " + oPath2 + " -log annot-step.log "
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; cat annot-step.log " + " >> " + lPath

            oPath2Full = os.path.join(self.__wrkPath, oPath2)
            oPathFull = os.path.join(self.__wrkPath, oPath)

        elif (op == "annot-rcsbeps2pdbx-strip-plus-entity"):
            #
            oPath2 = oPath + "_B"
            #
            # Adding a following step to synchronize required derived data for subsequent steps -
            #
            #
            cmd += " ; " + maxitCmd + " -o 8  -i " + iPath + " -log maxit.log "
            cmd += " ; mv -f " + iPath + ".cif " + oPath2
            #cmd += " ; cat maxit.err >> " + lPath
            #
            # Paths for post processing --
            #
            oPath2Full = os.path.join(self.__wrkPath, oPath2)
            oPathFull = os.path.join(self.__wrkPath, oPath)
            #
            # see at the end for the post processing operations --

        elif (op == "annot-chem-shift-check"):

            nomenclature_map_file = os.path.join(self.__packagePath,
                                                              "aditnmr_req_shifts",
                                                              "adit",
                                                              "config",
                                                              "bmrb-adit",
                                                              "pseudomap.csv")
            ligand_dir = self.__ccDictPath

            cmd += " ; TOOLS_PATH=" + self.__packagePath + " ; export TOOLS_PATH "
            cmd += " ; ADIT_NMR=" + os.path.join(self.__packagePath, "aditnmr_req_shifts") + " ; export ADIT_NMR "
            cmd += " ; LIGAND_DIR=" + ligand_dir + " ; export LIGAND_DIR "
            cmd += " ; NOMENCLATURE_MAP_FILE=" + nomenclature_map_file + " ; export NOMENCLATURE_MAP_FILE "
            #
            # set output option -  html or star
            if 'output_format' in self.__inputParamDict:
                outFmt = self.__inputParamDict['output_format']
            else:
                outFmt = "html"

            htmlPath = oPath
            strPath = self.__getResultWrkFile(2)
            logging.error(htmlPath)
            logging.error(strPath)

            cmdPath = os.path.join(self.__packagePath, "aditnmr_req_shifts", "cgi-bin", "bmrb-adit", "upload_shifts_check")
            thisCmd = " ; " + cmdPath

            cmd += thisCmd + " " + "--html --nomenclature-mapper {} --chem-comp-root-path {} ".format(nomenclature_map_file, ligand_dir)
            cmd += " --preserve-output tmp_chkd.str " + iPath

            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; mv -f " + 'tmp_chkd.str' + " " + strPath
            cmd += " ; mv -f " + tPath + " " + htmlPath

            self.__resultPathList.append(os.path.join(self.__wrkPath, htmlPath))
            self.__resultPathList.append(os.path.join(self.__wrkPath, strPath))

            logging.warning(cmd)

        elif (op == "annot-chem-shift-coord-check"):

            cmd += " ; TOOLS_PATH=" + self.__packagePath + " ; export TOOLS_PATH "
            cmd += " ; ADIT_NMR=" + os.path.join(self.__packagePath, "aditnmr_req_shifts") + " ; export ADIT_NMR "
            cmd += " ; NOMENCLATURE_MAP_FILE=" + os.path.join(self.__packagePath,
                                                              "aditnmr_req_shifts",
                                                              "adit",
                                                              "config",
                                                              "bmrb-adit",
                                                              "pseudomap.csv") + " ; export NOMENCLATURE_MAP_FILE "
            cmd += " ; LIGAND_DIR=" + self.__ccDictPath + " ; export LIGAND_DIR "

            #
            # set input coordinate file path
            if 'coordinate_file_path' in self.__inputParamDict:
                coordFilePath = self.__inputParamDict['coordinate_file_path']
            else:
                coordFilepath = ""

            #
            # set output option -  html or star
            if 'output_format' in self.__inputParamDict:
                outFmt = self.__inputParamDict['output_format']
            else:
                outFmt = "html"

            iPath2 = iPath + '-co'
            cmd += '; cp %s %s' % (coordFilePath, iPath2)

            # Now run  the check versus the coordinates using the output from the previous process
            cmdPath = os.path.join(self.__packagePath, "aditnmr_req_shifts", "cgi-bin", "bmrb-adit", "shift_coord_check")
            cmd += "; " + cmdPath
            cmd += " --html --coordfile " + iPath2 + " --shiftfile " + iPath

            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; mv -f " + tPath + " " + oPath

            logging.warning(cmd)

        elif (op == "annot-wwpdb-validate-all"):
            #
            #   "annot-wwpdb-validate-all" handles inputs for all exp methods  ---
            #
            #   Launches the validation software
            #
            #  'request_validation_mode'    override site and other presentation settings -
            #
            #                      - The following is for legacy support -
            #  'request_annotation_context'  parameter to override site environment setting -- can force annotation
            #
            validation_mode = 'release'
            if 'request_validation_mode' in self.__inputParamDict:
                validation_mode = str(self.__inputParamDict['request_validation_mode']).lower()
                if validation_mode not in ['server', 'deposit', 'release', 'annotate']:
                    validation_mode = 'release'
            elif 'request_annotation_context' in self.__inputParamDict:
                annotContext = self.__inputParamDict['request_annotation_context']
                if annotContext == 'yes':
                    validation_mode = 'annotate'

            # If user requests a run_dir - they cleanup
            # If not - and we create - we cleanup
            # If not specified at all - validation code will delete
            runDir = None
            deleteRunDir = False
            if 'run_dir' in self.__inputParamDict:
                runDir = self.__inputParamDict['run_dir']
            else:
                # Allow site specific override
                if self.__validScrPath and os.access(self.__validScrPath, os.W_OK):
                    runDir = os.path.join(self.__validScrPath, "validation_%s" % random.randrange(9999999))
                    deleteRunDir = True
                elif self.__siteWebAppsSessionsPath and os.access(self.__siteWebAppsSessionsPath, os.W_OK):
                    runDir = os.path.join(self.__siteWebAppsSessionsPath, "validation_%s" % random.randrange(9999999))
                    deleteRunDir = True
            kind = None
            if 'kind' in self.__inputParamDict:
                kind = self.__inputParamDict['kind']

            entryId = None
            if 'entry_id' in self.__inputParamDict:
                entryId = self.__inputParamDict['entry_id']

            if 'sf_file_path' in self.__inputParamDict:
                sfPath = self.__inputParamDict['sf_file_path']
                sfPathFull = os.path.abspath(sfPath)
            else:
                sfPathFull = None

            if 'cs_file_path' in self.__inputParamDict:
                csPath = self.__inputParamDict['cs_file_path']
                csPathFull = os.path.abspath(csPath)
            else:
                csPathFull = None

            if 'vol_file_path' in self.__inputParamDict:
                volPath = self.__inputParamDict['vol_file_path']
                volPathFull = os.path.abspath(volPath)
            else:
                volPathFull = None

            if 'step_list' in self.__inputParamDict:
                stepList = self.__inputParamDict['step_list']
            else:
                stepList = None

            #
            xmlPath = os.path.abspath(os.path.join(self.__wrkPath, "out.xml"))
            pdfPath = os.path.abspath(os.path.join(self.__wrkPath, "out.pdf"))
            pdfFullPath = os.path.abspath(os.path.join(self.__wrkPath, "out_full.pdf"))
            pngPath = os.path.abspath(os.path.join(self.__wrkPath, "out.png"))
            svgPath = os.path.abspath(os.path.join(self.__wrkPath, "out.svg"))
            site_config_command = ". %s/init/env.sh -s %s -l %s" % (self.__siteConfigDir, self.__siteId, self.__siteLoc)

            cmd += " ; %s " % site_config_command
            # Web environment python_path does not include -- needed anymore?
            # cmd += ' ; export PYTHONPATH="$PYTHONPATH:$PACKAGE_DIR/openbabel/lib"'
            # cmd += ' ; export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:$PACKAGE_DIR/openbabel/lib"'
            cmd += " ; %s --validation " % site_config_command
            # cmd += " ; env "

            cmdPath = os.path.join(self.__topPythonDir, 'wwpdb/apps/validation', 'src/python/validator.py')
            thisCmd = " ; python " + cmdPath

            cmd += thisCmd + " --mmciffile %s --xml %s --pdf %s --fullpdf %s --png %s --svg %s" % (iPathFull, xmlPath, pdfPath,
                                                                                                   pdfFullPath, pngPath, svgPath)
            cmd += " --mode " + validation_mode

            # For deposit or validation server - provide a PDB id. Otherwise for annotation incorrect id would be used
            if validation_mode in ['server', 'deposit']:
                if not entryId:
                    entryId = '4abc'
                cmd += " --pdbid " + entryId

            if sfPathFull:
                cmd += " --reflectionsfile " + sfPathFull

            if csPathFull:
                cmd += " --shiftsfiles " + csPathFull

            if volPathFull:
                cmd += " --mapfile " + volPathFull

            if stepList:
                cmd += " --steps " + stepList

            if runDir and runDir != 'none':
                cmd += " --rundir " + runDir

            if kind:
                cmd += " --kind " + kind

            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath

        elif (op == "annot-make-ligand-maps"):
            # The sf-valid package is currently set to self configure in a wrapper
            # shell script.  PACKAGE_DIR and TOOLS_DIR only need to be set here.
            #
            cmd += " ; WWPDB_SITE_ID=" + self.__siteId + " ; export WWPDB_SITE_ID "
            cmd += " ; DEPLOY_DIR=" + self.__deployPath + " ; export DEPLOY_DIR "
            cmd += " ; TOOLS_DIR=" + os.path.join(self.__localAppsPath, 'bin') + " ; export TOOLS_DIR "
            cmd += " ; PACKAGE_DIR=" + self.__packagePath + " ; export PACKAGE_DIR "
            cmd += " ; DCCPY_DIR=" + os.path.join(self.__packagePath, 'sf-valid') + " ; export DCCPY_DIR "

            #
            cmdPath = os.path.join(self.__packagePath, "sf-valid", "bin", "dcc.sh")
            thisCmd = " ; " + cmdPath

            dccArgs = ''
            if 'dcc_arguments' in self.__inputParamDict:
                dccArgs = "  " + self.__inputParamDict['dcc_arguments'] + "  "

            omitArgs = ''
            if 'omit_map' in self.__inputParamDict:
                omitArgs = ' -omitmap '
            #

            if 'sf_file_path' in self.__inputParamDict:
                sfPath = self.__inputParamDict['sf_file_path']
                sfPathFull = os.path.abspath(sfPath)
                (h, sfFileName) = os.path.split(sfPath)
                sfWrkPath = os.path.join(self.__wrkPath, sfFileName)
                shutil.copyfile(sfPathFull, sfWrkPath)
            else:
                sfPath = "none"
                sfPathFull = "none"

            if 'output_data_path' in self.__inputParamDict:
                outDataPath = self.__inputParamDict['output_data_path']
            else:
                outDataPath = '.'

            if 'output_index_path' in self.__inputParamDict:
                outIndexPath = self.__inputParamDict['output_index_path']
            else:
                outIndexPath = './np-map-index.cif'

            outIndexPathFull = os.path.abspath(outIndexPath)
            outDataPathFull = os.path.abspath(outDataPath)
            #

            cmd += thisCmd + dccArgs + " -cif ./" + iPath + " -sf  ./" + sfFileName + " -ligmapcif  -no_xtriage " + omitArgs
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath

        elif (op == "annot-dcc-report"):
            # The sf-valid package is currently set to self configure in a wrapper
            # shell script.  PACKAGE_DIR and TOOLS_DIR only need to be set here.
            #
            cmd += " ; WWPDB_SITE_ID=" + self.__siteId + " ; export WWPDB_SITE_ID "
            cmd += " ; DEPLOY_DIR=" + self.__deployPath + " ; export DEPLOY_DIR "
            cmd += " ; TOOLS_DIR=" + os.path.join(self.__localAppsPath, 'bin') + " ; export TOOLS_DIR "
            cmd += " ; PACKAGE_DIR=" + self.__packagePath + " ; export PACKAGE_DIR "
            cmd += " ; DCCPY_DIR=" + os.path.join(self.__packagePath, 'sf-valid') + " ; export DCCPY_DIR "

            #
            cmdPath = os.path.join(self.__packagePath, "sf-valid", "bin", "dcc.sh")
            thisCmd = " ; " + cmdPath

            dccArgs = ''
            if 'dcc_arguments' in self.__inputParamDict:
                dccArgs = "  " + self.__inputParamDict['dcc_arguments'] + "  "

            if 'sf_file_path' in self.__inputParamDict:
                sfPath = self.__inputParamDict['sf_file_path']
                sfPathFull = os.path.abspath(sfPath)
                (h, sfFileName) = os.path.split(sfPath)
                sfWrkPath = os.path.join(self.__wrkPath, sfFileName)
                shutil.copyfile(sfPathFull, sfWrkPath)
                #
                cmd += thisCmd + dccArgs + " -auto -cif ./" + iPath + " -sf  ./" + sfFileName + " -o " + oPath + " -diags " + lPath

            else:
                sfPath = "none"
                sfPathFull = "none"
                cmd += ' ; echo "No structure factor file"'

            cmd += " > " + tPath + " 2>&1 ; "

        elif (op == "annot-dcc-refine-report"):
            # The sf-valid package is currently set to self configure in a wrapper
            # shell script.  PACKAGE_DIR and TOOLS_DIR only need to be set here.
            #
            cmd += " ; WWPDB_SITE_ID=" + self.__siteId + " ; export WWPDB_SITE_ID "
            cmd += " ; DEPLOY_DIR=" + self.__deployPath + " ; export DEPLOY_DIR "
            cmd += " ; TOOLS_DIR=" + os.path.join(self.__localAppsPath, 'bin') + " ; export TOOLS_DIR "
            cmd += " ; PACKAGE_DIR=" + self.__packagePath + " ; export PACKAGE_DIR "
            cmd += " ; DCCPY_DIR=" + os.path.join(self.__packagePath, 'sf-valid') + " ; export DCCPY_DIR "

            #
            cmdPath = os.path.join(self.__packagePath, "sf-valid", "bin", "dcc.sh")
            thisCmd = " ; " + cmdPath

            dccArgs = ''
            if 'dcc_arguments' in self.__inputParamDict:
                dccArgs = "  " + self.__inputParamDict['dcc_arguments'] + "  "

            if 'sf_file_path' in self.__inputParamDict:
                sfPath = self.__inputParamDict['sf_file_path']
                sfPathFull = os.path.abspath(sfPath)
                (h, sfFileName) = os.path.split(sfPath)
                sfWrkPath = os.path.join(self.__wrkPath, sfFileName)
                shutil.copyfile(sfPathFull, sfWrkPath)
                cmd += thisCmd + dccArgs + " -refine -cif ./" + iPath + " -sf  ./" + sfFileName + " -o " + oPath
            else:
                sfPath = "none"
                sfPathFull = "none"
                cmd += ' ; echo "No structure factor file"'
            #

            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath

        elif (op == "annot-dcc-biso-full"):
            # The sf-valid package is currently set to self configure in a wrapper
            # shell script.  PACKAGE_DIR and TOOLS_DIR only need to be set here.
            #
            cmd += " ; WWPDB_SITE_ID=" + self.__siteId + " ; export WWPDB_SITE_ID "
            cmd += " ; DEPLOY_DIR=" + self.__deployPath + " ; export DEPLOY_DIR "
            cmd += " ; TOOLS_DIR=" + os.path.join(self.__localAppsPath, 'bin') + " ; export TOOLS_DIR "
            cmd += " ; PACKAGE_DIR=" + self.__packagePath + " ; export PACKAGE_DIR "
            cmd += " ; DCCPY_DIR=" + os.path.join(self.__packagePath, 'sf-valid') + " ; export DCCPY_DIR "

            #
            cmdPath = os.path.join(self.__packagePath, "sf-valid", "bin", "dcc.sh")
            thisCmd = " ; " + cmdPath

            #
            cmd += thisCmd + " -bfull ./" + iPath + " -o " + oPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath

        elif (op == "annot-dcc-special-position"):
            # The sf-valid package is currently set to self configure in a wrapper
            # shell script.  PACKAGE_DIR and TOOLS_DIR only need to be set here.
            #
            cmd += " ; WWPDB_SITE_ID=" + self.__siteId + " ; export WWPDB_SITE_ID "
            cmd += " ; DEPLOY_DIR=" + self.__deployPath + " ; export DEPLOY_DIR "
            cmd += " ; TOOLS_DIR=" + os.path.join(self.__localAppsPath, 'bin') + " ; export TOOLS_DIR "
            cmd += " ; PACKAGE_DIR=" + self.__packagePath + " ; export PACKAGE_DIR "
            cmd += " ; DCCPY_DIR=" + os.path.join(self.__packagePath, 'sf-valid') + " ; export DCCPY_DIR "

            #
            cmdPath = os.path.join(self.__packagePath, "sf-valid", "bin", "tool.sh")
            thisCmd = " ; " + cmdPath

            dccArgs = ''
            if 'dcc_arguments' in self.__inputParamDict:
                dccArgs = "  " + self.__inputParamDict['dcc_arguments'] + "  "

            #
            cmd += thisCmd + dccArgs + " -occ ./" + iPath + " -o " + oPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath

        elif (op == "annot-dcc-fix-special-position"):
            # The sf-valid package is currently set to self configure in a wrapper
            # shell script.  PACKAGE_DIR and TOOLS_DIR only need to be set here.
            #
            cmd += " ; WWPDB_SITE_ID=" + self.__siteId + " ; export WWPDB_SITE_ID "
            cmd += " ; DEPLOY_DIR=" + self.__deployPath + " ; export DEPLOY_DIR "
            cmd += " ; TOOLS_DIR=" + os.path.join(self.__localAppsPath, 'bin') + " ; export TOOLS_DIR "
            cmd += " ; PACKAGE_DIR=" + self.__packagePath + " ; export PACKAGE_DIR "
            cmd += " ; DCCPY_DIR=" + os.path.join(self.__packagePath, 'sf-valid') + " ; export DCCPY_DIR "

            #
            cmdPath = os.path.join(self.__packagePath, "sf-valid", "bin", "tool.sh")
            thisCmd = " ; " + cmdPath
            #
            # new model file will not be created if nothing to fix
            newModelFile = os.path.abspath(os.path.join(self.__wrkPath, "special-fixed.cif"))

            cmd += thisCmd + " -occ ./" + iPath + " -oxyz " + newModelFile + " -o " + oPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath

        elif (op == "annot-dcc-reassign-alt-ids"):
            # The sf-valid package is currently set to self configure in a wrapper
            # shell script.  PACKAGE_DIR and TOOLS_DIR only need to be set here.
            #
            cmd += " ; WWPDB_SITE_ID=" + self.__siteId + " ; export WWPDB_SITE_ID "
            cmd += " ; DEPLOY_DIR=" + self.__deployPath + " ; export DEPLOY_DIR "
            cmd += " ; TOOLS_DIR=" + os.path.join(self.__localAppsPath, 'bin') + " ; export TOOLS_DIR "
            cmd += " ; PACKAGE_DIR=" + self.__packagePath + " ; export PACKAGE_DIR "
            cmd += " ; DCCPY_DIR=" + os.path.join(self.__packagePath, 'sf-valid') + " ; export DCCPY_DIR "

            #
            cmdPath = os.path.join(self.__packagePath, "sf-valid", "bin", "tool.sh")
            thisCmd = " ; " + cmdPath

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
            sfCifPath = os.path.join(self.__wrkPath, oPath)
            sfDiagFileName = "sf_information.cif"
            sfDiagPath = os.path.join(self.__wrkPath, sfDiagFileName)
            mtzDmpFileName = "mtzdmp.log"
            mtzDmpPath = os.path.join(self.__wrkPath, mtzDmpFileName)
            #
            mtzFile = iPath + ".mtz"
            mtzPath = os.path.join(self.__wrkPath, mtzFile)
            shutil.copyfile(iPathFull, mtzPath)
            ccp4_path = os.path.join(self.__packagePath, "ccp4")
            #
            cmd += " ; WWPDB_SITE_ID=" + self.__siteId + " ; export WWPDB_SITE_ID "
            cmd += " ; DEPLOY_DIR=" + self.__deployPath + " ; export DEPLOY_DIR "
            cmd += " ; TOOLS_DIR=" + os.path.join(self.__localAppsPath, 'bin') + " ; export TOOLS_DIR "
            cmd += " ; PACKAGE_DIR=" + self.__packagePath + " ; export PACKAGE_DIR "
            cmd += " ; DCCPY_DIR=" + os.path.join(self.__packagePath, 'sf-valid') + " ; export DCCPY_DIR "
            cmd += " ; DCCPY=" + os.path.join(self.__packagePath, 'sf-valid') + " ; export DCCPY "
            cmd += " ; CCP4=" + ccp4_path + " ; export CCP4 "
            cmd += " ; source {}/bin/ccp4.setup.sh ".format(ccp4_path)
            #
            cmdPath = os.path.join(self.__packagePath, "sf-valid", "bin", "sf_convert")
            thisCmd = " ; " + cmdPath
            #
            cmd += thisCmd + " -o mmcif  -sf " + mtzFile + " -out " + oPath + " -diags " + lPath
            #

            if 'xyz_file_path' in self.__inputParamDict:
                xyzPath = self.__inputParamDict['xyz_file_path']
                xyzPathFull = os.path.abspath(xyzPath)
                (h, xyzFileName) = os.path.split(xyzPath)
                xyzWrkPath = os.path.join(self.__wrkPath, xyzFileName)
                shutil.copyfile(xyzPathFull, xyzWrkPath)
                cmd += " -pdb " + xyzFileName

            cmd += " > " + tPath + " 2>&1 ; "
            #

        elif (op == "annot-tls-range-correction"):
            #
            # Run tls_correct.py to correct various TLS problems generated from refmac/phenix/buster refinement program
            #
            depFilePath = ''
            if 'depfile' in self.__inputParamDict:
                depFilePath = self.__inputParamDict['depfile']
            else:
                return -1
            #
            ccp4_path = os.path.join(self.__packagePath, "ccp4")

            cmd += " ; WWPDB_SITE_ID=" + self.__siteId + " ; export WWPDB_SITE_ID "
            cmd += " ; PACKAGE_DIR=" + self.__packagePath + " ; export PACKAGE_DIR "
            cmd += " ; CCP4=" + ccp4_path + " ; export CCP4 "
            cmd += " ; source {}/bin/ccp4.setup.sh ".format(ccp4_path)
            #
            thisCmd = " ; " + os.path.join(self.__packagePath, "sf-valid", "toolpy", "tls_correct.py")
            #
            cmd += thisCmd + " -dep " + depFilePath + " -pdb " + iPath + " -o " + oPath + " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath

        elif (op == "annot-merge-tls-range-data"):
            #
            # Merge tls data output from tls_correct.py program into coordinate model file
            #
            tlsDataFilePath = ''
            if 'tlsfile' in self.__inputParamDict:
                tlsDataFilePath = self.__inputParamDict['tlsfile']
            else:
                return -1
            #
            cmd += " ; " + os.path.join(self.__rcsbAppsPath, "bin", "MergeTLSData") + " -input " + iPath + " -input_tls " + tlsDataFilePath \
                 + " -output " + oPath + " -log " + lPath + " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            #

        elif (op == "annot-make-omit-maps"):
            #
            #  -- Create full maps (2fo-fc and fo-fc) with ligands first removed from the model file --
            #
            # The sf-valid package is currently set to self configure in a wrapper
            # shell script.  PACKAGE_DIR and TOOLS_DIR only need to be set here.
            #
            cmd += " ; WWPDB_SITE_ID=" + self.__siteId + " ; export WWPDB_SITE_ID "
            cmd += " ; DEPLOY_DIR=" + self.__deployPath + " ; export DEPLOY_DIR "
            cmd += " ; TOOLS_DIR=" + os.path.join(self.__localAppsPath, 'bin') + " ; export TOOLS_DIR "
            cmd += " ; PACKAGE_DIR=" + self.__packagePath + " ; export PACKAGE_DIR "
            cmd += " ; DCCPY_DIR=" + os.path.join(self.__packagePath, 'sf-valid') + " ; export DCCPY_DIR "

            #
            cmdPath = os.path.join(self.__packagePath, "sf-valid", "bin", "dcc.sh")
            thisCmd = " ; " + cmdPath

            if 'sf_file_path' in self.__inputParamDict:
                sfPath = self.__inputParamDict['sf_file_path']
                sfPathFull = os.path.abspath(sfPath)
                (h, sfFileName) = os.path.split(sfPath)
                sfWrkPath = os.path.join(self.__wrkPath, sfFileName)
                shutil.copyfile(sfPathFull, sfWrkPath)
            else:
                sfPath = "none"
                sfPathFull = "none"

            #
            map2fofcPath = os.path.abspath(os.path.join(self.__wrkPath, iPath + "_map-omit-2fofc_P1.map"))
            mapfofcPath = os.path.abspath(os.path.join(self.__wrkPath, iPath + "_map-omit-fofc_P1.map"))

            #cmd += thisCmd + " -cif ./" + iPath + " -sf  ./" + sfFileName + " -omitmap -map  -no_xtriage -o " + oPath
            #cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            #
            cmd += thisCmd + " -cif ./" + iPath + " -sf  ./" + sfFileName + " -omitmap  -noeds -no_xtriage -o " + oPath
            cmd += " -2fofc " + map2fofcPath + " -fofc " + mapfofcPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath

        elif (op == "annot-make-maps"):
            #
            #  -- Create full maps (2fo-fc and fo-fc) from the input model and structure factor files
            #
            # The sf-valid package is currently set to self configure in a wrapper
            # shell script.  PACKAGE_DIR and TOOLS_DIR only need to be set here.
            #
            cmd += " ; WWPDB_SITE_ID=" + self.__siteId + " ; export WWPDB_SITE_ID "
            cmd += " ; DEPLOY_DIR=" + self.__deployPath + " ; export DEPLOY_DIR "
            cmd += " ; TOOLS_DIR=" + os.path.join(self.__localAppsPath, 'bin') + " ; export TOOLS_DIR "
            cmd += " ; PACKAGE_DIR=" + self.__packagePath + " ; export PACKAGE_DIR "
            cmd += " ; DCCPY_DIR=" + os.path.join(self.__packagePath, 'sf-valid') + " ; export DCCPY_DIR "

            #
            cmdPath = os.path.join(self.__packagePath, "sf-valid", "bin", "dcc.sh")
            thisCmd = " ; " + cmdPath

            if 'sf_file_path' in self.__inputParamDict:
                sfPath = self.__inputParamDict['sf_file_path']
                sfPathFull = os.path.abspath(sfPath)
                (h, sfFileName) = os.path.split(sfPath)
                sfWrkPath = os.path.join(self.__wrkPath, sfFileName)
                shutil.copyfile(sfPathFull, sfWrkPath)
            else:
                sfPath = "none"
                sfPathFull = "none"

            #
            map2fofcPath = os.path.abspath(os.path.join(self.__wrkPath, iPath + "_map-2fofc_P1.map"))
            mapfofcPath = os.path.abspath(os.path.join(self.__wrkPath, iPath + "_map-fofc_P1.map"))

            #cmd += thisCmd + " -cif ./" + iPath + " -sf  ./" + sfFileName + " -map  -no_xtriage -o " + oPath
            #cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            #
            cmd += thisCmd + " -cif ./" + iPath + " -sf  ./" + sfFileName + " -map  -noeds -no_xtriage -o " + oPath
            cmd += " -2fofc " + map2fofcPath + " -fofc " + mapfofcPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath

        elif (op == "annot-poly-link-dist"):
            cmdPath = os.path.join(self.__annotAppsPath, "bin", "cal_polymer_linkage_distance")
            thisCmd = " ; " + cmdPath
            cmd += thisCmd + " -i " + iPath + " -o " + oPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath

        elif (op == "annot-poly-link-dist-json"):
            cmdPath = os.path.join(self.__annotAppsPath, "bin", "cal_polymer_linkage_distance_json")
            thisCmd = " ; " + cmdPath
            cmd += thisCmd + " -i " + iPath + " -o " + oPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath

        elif ((op == "annot-cif2cif") or (op == "cif2cif")):
            cmd += " ; " + maxitCmd + " -o 8  -i " + iPath + " -log maxit.log "
            cmd += " ; mv -f " + iPath + ".cif " + oPath
            #cmd += " ; cat maxit.err >> " + lPath

        elif ((op == "annot-cif2cif-dep") or (op == "cif2cif-dep")):
            cmd += " ; " + maxitCmd + " -o 8  -i " + iPath + " -dep -log maxit.log "
            cmd += " ; mv -f " + iPath + ".cif " + oPath
            #cmd += " ; cat maxit.err >> " + lPath

        elif ((op == "annot-pdb2cif") or (op == "pdb2cif")):
            cmd += " ; " + maxitCmd + " -o 1  -i " + iPath + " -log maxit.log "
            cmd += " ; mv -f " + iPath + ".cif " + oPath
            #cmd += " ; cat maxit.err >> " + lPath

        elif ((op == "annot-pdb2cif-dep") or (op == "pdb2cif-dep")):
            cmd += " ; " + maxitCmd + " -o 1  -i " + iPath + " -dep -log maxit.log "
            cmd += " ; mv -f " + iPath + ".cif " + oPath
            #cmd += " ; cat maxit.err >> " + lPath

        elif ((op == "annot-cif2pdb") or (op == "cif2pdb")):
            cmd += " ; " + maxitCmd + " -o 2  -i " + iPath + " -log maxit.log "
            cmd += " ; mv -f " + iPath + ".pdb " + oPath
            #cmd += " ; cat maxit.err >> " + lPath

        elif (op == "annot-move-xyz-by-symop"):

            # MovingCoordBySymmetry and MovingCoordByMatrix programs in annotation-pack to move coordinates. The syntax for both programs are:
            #${program} -input input_ciffile -output output_ciffile -assign assignment_file -log logfile

            #
            cmdPath = os.path.join(self.__annotAppsPath, "bin", "MovingCoordBySymmetry")
            thisCmd = " ; " + cmdPath
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log "
            if 'transform_file_path' in self.__inputParamDict:
                assignFilePath = self.__inputParamDict['transform_file_path']
                cmd += " -assign " + assignFilePath
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif (op == "annot-reorder-models"):
            # ReorderModels -input input_ciffile -output output_ciffile -mol_id model_number -log logfile
            #
            cmdPath = os.path.join(self.__annotAppsPath, "bin", "ReorderModels")
            thisCmd = " ; " + cmdPath
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log "
            if 'model_number' in self.__inputParamDict:
                model_number = self.__inputParamDict['model_number']
                cmd += " -mol_id " + model_number
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif (op == "annot-move-xyz-by-matrix"):

            # MovingCoordBySymmetry and MovingCoordByMatrix programs in annotation-pack to move coordinates. The syntax for both programs are:
            #${program} -input input_ciffile -output output_ciffile -assign assignment_file -log logfile

            #
            cmdPath = os.path.join(self.__annotAppsPath, "bin", "MovingCoordByMatrix")
            thisCmd = " ; " + cmdPath
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log "
            if 'transform_file_path' in self.__inputParamDict:
                assignFilePath = self.__inputParamDict['transform_file_path']
                cmd += " -assign " + assignFilePath
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif (op == "annot-extra-checks"):
            #
            # MiscChecking -input ciffile -output outputfile -log logfile
            #
            cmdPath = os.path.join(self.__annotAppsPath, "bin", "MiscChecking")
            thisCmd = " ; " + cmdPath
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log "
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; cat annot-step.log " + " >> " + lPath
            cmd += " ; touch " + iPath + "-parser.log "
            cmd += " ; cat " + iPath + "-parser.log >> " + oPath

            ##
        elif (op == "annot-merge-xyz"):
            #   MergeCoordinates -input input_ciffile -output output_ciffile -newcoord new_coordinate_file -format pdb|cif [-log logfile] [ -dep]
            #
            #        option "-format pdb":   new_coordinates_file is PDB format file
            #        option "-format cif":   new_coordinates_file is cif format file
            #
            ##
            cmdPath = os.path.join(self.__annotAppsPath, "bin", "MergeCoordinates")
            thisCmd = " ; " + cmdPath
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log "
            #
            if 'new_coordinate_file_path' in self.__inputParamDict:
                xyzFilePath = self.__inputParamDict['new_coordinate_file_path']
                cmd += " -newcoord " + xyzFilePath

            if 'new_coordinate_format' in self.__inputParamDict:
                xyzFormat = self.__inputParamDict['new_coordinate_format']
                cmd += " -format " + xyzFormat
            else:
                cmd += " -format cif "
            #
            if 'deposit' in self.__inputParamDict:
                cmd += " -dep "

            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif (op == "annot-update-terminal-atoms"):
            # UpdateTerminalAtom -input input_ciffile -output output_ciffile -option delete|rename [-log logfile]
            #
            #   If option "delete" is selected, "OXT" atom will be deleted. If option "rename" is selected,
            #     the "OXT" will be renamed to "N" in next residue.
            #
            ##
            cmdPath = os.path.join(self.__annotAppsPath, "bin", "UpdateTerminalAtom")
            thisCmd = " ; " + cmdPath
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log "
            #
            if 'option' in self.__inputParamDict:
                option = self.__inputParamDict['option']
                cmd += " -option " + option
            else:
                cmd += " -option delete "
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif (op == "annot-update-dep-assembly-info"):
            cmdPath = os.path.join(self.__annotAppsPath, "bin", "UpdateDepositorAssemblyInfo")
            thisCmd = " ; " + cmdPath
            cmd += thisCmd + " -input " + iPath + " -output " + oPath + " -log annot-step.log "
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif (op == "annot-gen-assem-pdbx"):
            #
            #    GenBioCIFFile -input model_ciffile -depid depositionID -index output_index_file [-log logfile]
            #
            ##
            cmdPath = os.path.join(self.__annotAppsPath, "bin", "GenBioCIFFile")
            thisCmd = " ; " + cmdPath
            cmd += thisCmd + " -input " + iPath + " -log annot-step.log "
            #
            if 'deposition_data_set_id' in self.__inputParamDict:
                depId = self.__inputParamDict['deposition_data_set_id']
                cmd += " -depid " + depId

            idxFilePath = oPath
            if 'index_file_path' in self.__inputParamDict:
                idxFilePath = self.__inputParamDict['index_file_path']
            cmd += " -index " + idxFilePath

            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; cat annot-step.log " + " >> " + lPath

        elif (op == "annot-chem-shifts-upload-check"):

            cmdPath = os.path.join(self.__annotAppsPath, "bin", "upload_shifts_check")
            thisCmd = " ; " + cmdPath
            pList = []
            nList = []
            chkName = "cs-diags.cif"
            lCheckPath = os.path.abspath(os.path.join(self.__wrkPath, chkName))
            chkPath = ""
            if 'chemical_shifts_file_path_list' in self.__inputParamDict:
                pList = self.__inputParamDict['chemical_shifts_file_path_list']

            if 'chemical_shifts_auth_file_name_list' in self.__inputParamDict:
                nList = self.__inputParamDict['chemical_shifts_auth_file_name_list']
            #
            if 'chemical_shifts_upload_check_file_path' in self.__inputParamDict:
                chkPath = self.__inputParamDict['chemical_shifts_upload_check_file_path']
            #
            tt = []
            for i in range(len(pList)):
                if len(nList) > i:
                    fn = nList[i]
                else:
                    dn, fn = os.path.split(pList[i])
                tt.append(" -input %s  -auth_name %s " % (os.path.abspath(str(pList[i])), str(fn)))
            #
            cmd += thisCmd + ' '.join(tt) + " -output " + oPath + " -log " + lCheckPath
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath

        elif (op == "annot-chem-shifts-atom-name-check"):
            #  iPath input is the target chemical shift file oPath is the output cs file
            #
            cmdPath = os.path.join(self.__annotAppsPath, "bin", "shift_coord_check")
            thisCmd = " ; " + cmdPath
            chkName = "cs-coord-diags.cif"
            lCheckPath = os.path.abspath(os.path.join(self.__wrkPath, chkName))
            chkPath = ""
            #
            # auxiliary output file
            if 'chemical_shifts_coord_check_file_path' in self.__inputParamDict:
                chkPath = self.__inputParamDict['chemical_shifts_coord_check_file_path']
            #
            if 'coordinate_file_path' in self.__inputParamDict:
                xyzPath = self.__inputParamDict['coordinate_file_path']
                xyzPathFull = os.path.abspath(xyzPath)
                (h, xyzFileName) = os.path.split(xyzPath)
                xyzWrkPath = os.path.join(self.__wrkPath, xyzFileName)
                xyzCnvWrkPath = os.path.join(self.__wrkPath, 'cnv-' + xyzFileName)
                shutil.copyfile(xyzPathFull, xyzWrkPath)
            else:
                xyzPath = "none"
                xyzPathFull = "none"

            # First add data items to the model
            cmd += " ; " + maxitCmd + " -o 8  -i " + xyzWrkPath + " -dep -log maxit.log "
            cmd += " ; mv -f " + xyzWrkPath + ".cif " + xyzCnvWrkPath
            #
            cmd += thisCmd + ' -input ' + iPath + " -output " + oPath + " -ciffile " + xyzCnvWrkPath + " -log " + lCheckPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath

        elif (op == "annot-chem-shifts-update"):
            #  iPath input is the target chemical shift file oPath is the output cs file
            #
            # update_chemical_shift -input input_chemical_shift_file -output output_chemical_shift_file -ciffile coord_cif_file -log logfile
            #
            cmdPath = os.path.join(self.__annotAppsPath, "bin", "update_chemical_shift")
            thisCmd = " ; " + cmdPath

            if 'coordinate_file_path' in self.__inputParamDict:
                xyzPath = self.__inputParamDict['coordinate_file_path']
                xyzPathFull = os.path.abspath(xyzPath)
                (h, xyzFileName) = os.path.split(xyzPath)
                xyzWrkPath = os.path.join(self.__wrkPath, xyzFileName)
                shutil.copyfile(xyzPathFull, xyzWrkPath)
            else:
                xyzPath = "none"
                xyzPathFull = "none"

            cmd += thisCmd + ' -input ' + iPath + " -output " + oPath + " -ciffile " + xyzWrkPath + " -log " + lPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath

        elif (op == "prd-search"):

            cmd += " ; PRDCC_PATH=" + self.__prdccCvsPath + " ; export PRDCC_PATH "
            cmd += " ; PRD_DICT_PATH=" + self.__prdDictPath + " ; export PRD_DICT_PATH "
            cmdPath = os.path.join(self.__annotAppsPath, "bin", "GetPrdMatch")
            cmd += " ; " + cmdPath + " -input " + iPath + " -output " + oPath \
                + " -path . -index " + self.__prdDictPath + "/prd_summary.sdb -cc_index " + self.__ccDictPathIdx
            if 'logfile' in self.__inputParamDict:
                cmd += " -log " + self.__inputParamDict['logfile']
            if 'firstmodel' in self.__inputParamDict:
                cmd += " -firstmodel " + self.__inputParamDict['firstmodel']
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
        else:

            return -1
        #

        if (self.__debug):
            self.__lfh.write("+RcsbDpUtility._annotationStep()  - Application string:\n%s\n" % cmd.replace(";", "\n"))
        #
        # if (self.__debug):
        #    cmd += " ; ls -la  > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath

        cmd += " ) > %s 2>&1 " % ePathFull

        cmd += " ; cat " + ePathFull + " >> " + lPathFull

        if (self.__debug):
            ofh = open(lPathFull, 'w')
            lt = time.strftime("%Y %m %d %H:%M:%S", time.localtime())
            ofh.write("\n\n-------------------------------------------------\n")
            ofh.write("LogFile:      %s\n" % lPath)
            ofh.write("Working path: %s\n" % self.__wrkPath)
            ofh.write("Date:         %s\n" % lt)
            ofh.write("\nStep command:\n%s\n-------------------------------------------------\n" % cmd.replace(";", "\n"))
            ofh.close()


        iret = self.__run(cmd, lPathFull, op)

        #
        # After execution processing --
        #
        if (op == "annot-reposition-solvent-add-derived-prev"):
            #  Feb 25, 2014 No longer used  ----
            # remove these categories for now --
            stripList = ['pdbx_coord',
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

            strpCt = PdbxStripCategory(verbose=self.__verbose, log=self.__lfh)
            strpCt.strip(oPath2Full, oPathFull, stripList)

        if ((op == "annot-rcsb2pdbx-strip") or (op == "annot-rcsbeps2pdbx-strip")):
            # remove these derived categories for now --
            stripList = ['pdbx_coord',
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
            strpCt = PdbxStripCategory(verbose=self.__verbose, log=self.__lfh)
            strpCt.strip(oPath2Full, oPathFull, stripList)

        if ((op == "annot-rcsb2pdbx-strip-plus-entity") or (op == "annot-rcsbeps2pdbx-strip-plus-entity")):
            # remove derived categories plus selected entity-level categories --
            stripList = [
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
            strpCt = PdbxStripCategory(verbose=self.__verbose, log=self.__lfh)
            strpCt.strip(oPath2Full, oPathFull, stripList)

        if (op == "annot-wwpdb-validate-all"):
            self.__resultPathList = []
            #
            # Push the output pdf and xml files onto the resultPathList.
            #
            if os.access(pdfPath, os.F_OK):
                self.__resultPathList.append(pdfPath)
            else:
                self.__resultPathList.append("missing")
            #
            if os.access(xmlPath, os.F_OK):
                self.__resultPathList.append(xmlPath)
            else:
                self.__resultPathList.append("missing")

            if os.access(pdfFullPath, os.F_OK):
                self.__resultPathList.append(pdfFullPath)
            else:
                self.__resultPathList.append("missing")

            if os.access(pngPath, os.F_OK):
                self.__resultPathList.append(pngPath)
            else:
                self.__resultPathList.append("missing")

            if os.access(svgPath, os.F_OK):
                self.__resultPathList.append(svgPath)
            else:
                self.__resultPathList.append("missing")

            # Cleanup workdir
            if deleteRunDir:
                try:
                    self.__lfh.write("+RcsbDpUtility.__annotationStep() removing working path %s\n" % runDir)
                    shutil.rmtree(runDir, ignore_errors=True)
                    return True
                except:
                    self.__lfh.write("+RcsbDpUtility.__annotationStep() removal failed for working path %s\n" % runDir)



        elif (op == "annot-sf-convert"):
            self.__resultPathList = []
            #
            # Push the output converted and diagnostic files onto the resultPathList.
            #
            if os.access(sfCifPath, os.F_OK):
                self.__resultPathList.append(sfCifPath)
            else:
                self.__resultPathList.append("missing")

            if os.access(sfDiagPath, os.F_OK):
                self.__resultPathList.append(sfDiagPath)
            else:
                self.__resultPathList.append("missing")

            if os.access(mtzDmpPath, os.F_OK):
                self.__resultPathList.append(mtzDmpPath)
            else:
                self.__resultPathList.append("missing")

        elif (op == "annot-make-maps"):
            #
            self.__resultPathList = []
            #
            # Push the output maps  onto the resultPathList [2fofc, fofc] .
            #
            if os.access(map2fofcPath, os.F_OK):
                self.__resultPathList.append(map2fofcPath)
            else:
                self.__resultPathList.append("missing")

            if os.access(mapfofcPath, os.F_OK):
                self.__resultPathList.append(mapfofcPath)
            else:
                self.__resultPathList.append("missing")

        elif (op == "annot-dcc-fix-special-position"):
            #
            self.__resultPathList = []
            #
            # Push the output model file if present or "missing"
            #
            if os.access(newModelFile, os.F_OK):
                self.__resultPathList.append(newModelFile)
            else:
                self.__resultPathList.append("missing")

        elif (op == "annot-gen-assem-pdbx"):
            #
            self.__resultPathList = []
            if os.access(idxFilePath, os.R_OK):
                ifh = open(idxFilePath, 'r')
                for line in ifh:
                    fp = os.path.join(self.__wrkPath, line[:-1])
                    if os.access(fp, os.R_OK):
                        self.__resultPathList.append(fp)

        elif (op == "annot-make-ligand-maps"):
            # Here we manage copying the maps non-polymer CIF snippets and a defining index file to the user
            # specified output path --
            if (self.__verbose):
                self.__lfh.write("+RcsbDpUtility._annotationStep()  - for operation %s return path %s\n" % (op, outDataPathFull))
            pat = os.path.join(self.__wrkPath, '*.map')
            self.__resultMapPathList = glob.glob(pat)
            if (self.__debug):
                self.__lfh.write("+RcsbDpUtility._annotationStep()  - pat %s resultMapPathList %s\n" % (pat, self.__resultMapPathList))
            #
            pat = os.path.join(self.__wrkPath, '[0-9]*.cif')
            self.__resultCifPathList = glob.glob(pat)
            if (self.__debug):
                self.__lfh.write("+RcsbDpUtility._annotationStep()  - pat %s resultCifPathList %s\n" % (pat, self.__resultCifPathList))
            #
            try:
                if (not os.path.isdir(outDataPathFull)):
                    os.makedirs(outDataPathFull, 0o755)
                # index file --
                ipT = os.path.join(self.__wrkPath, 'LIG_PEPTIDE.cif')
                if (os.access(ipT, os.R_OK)):
                    shutil.copyfile(ipT, outIndexPathFull)
                else:
                    if (self.__verbose):
                        self.__lfh.write("+RcsbDpUtility._annotationStep()  - missing map index file %s\n" % ipT)

                # map files
                for fp in self.__resultMapPathList:
                    if fp.endswith('_2fofc.map'):
                        continue
                    (dn, fn) = os.path.split(fp)
                    ofp = os.path.join(outDataPathFull, fn)
                    shutil.copyfile(fp, ofp)
                    if (self.__debug):
                        self.__lfh.write("+RcsbDpUtility._annotationStep()  - returning map file %s\n" % ofp)
                # cif snippet files
                for fp in self.__resultCifPathList:
                    if fp.endswith('-sf.cif'):
                        continue
                    (dn, fn) = os.path.split(fp)
                    ofp = os.path.join(outDataPathFull, fn)
                    shutil.copyfile(fp, ofp)
                    if (self.__debug):
                        self.__lfh.write("+RcsbDpUtility._annotationStep()  - returning cif snippet file %s\n" % ofp)

            except:
                if (self.__verbose):
                    self.__lfh.write("+RcsbDpUtility._annotationStep() - failing return of files for operation %s\n" % op)
                    traceback.print_exc(file=self.__lfh)

        elif (op == "annot-chem-shift-check"):
            pass
        elif (op in ["annot-chem-shifts-atom-name-check", "annot-chem-shifts-upload-check"]):
            if os.access(lCheckPath, os.R_OK):
                shutil.copyfile(lCheckPath, chkPath)
        else:
            self.__resultPathList = [os.path.join(self.__wrkPath, oPath)]

        return iret

    def __validateStep(self, op):
        """ Internal method that performs a single validation operation.

            Now using only validation pack functions.
        """
        #
        # Set application specific path details here -
        #
        self.__localAppsPath = self.__getConfigPath('SITE_LOCAL_APPS_PATH')
        self.__packagePath = self.__getConfigPath('SITE_PACKAGES_PATH')
        self.__deployPath = self.__getConfigPath('SITE_DEPLOY_PATH')
        self.__ccDictPath = self.__getConfigPath('SITE_CC_DICT_PATH')
        self.__ccCvsPath = self.__getConfigPath('SITE_CC_CVS_PATH')
        self.__prdccCvsPath = self.__getConfigPath('SITE_PRDCC_CVS_PATH')
        self.__prdDictPath = os.path.join(self.__getConfigPath('SITE_DEPLOY_PATH'), 'reference', 'components', 'prd-dict')

        self.__rcsbAppsPath = os.path.join(self.__packagePath, 'annotation')
        #
        # These may not be needed --
        self.__pdbxDictPath = self.__getConfigPath('SITE_PDBX_DICT_PATH')
        self.__pdbxDictName = self.__cI.get('SITE_PDBX_DICT_NAME')
        self.__pathDdlSdb = os.path.join(self.__pdbxDictPath, "mmcif_ddl.sdb")
        self.__pathPdbxDictSdb = os.path.join(self.__pdbxDictPath, self.__pdbxDictName + '.sdb')
        self.__pathPdbxDictOdb = os.path.join(self.__pdbxDictPath, self.__pdbxDictName + '.odb')

        #
        #
        iPath = self.__getSourceWrkFile(self.__stepNo)
        iPathList = self.__getSourceWrkFileList(self.__stepNo)
        oPath = self.__getResultWrkFile(self.__stepNo)
        lPath = self.__getLogWrkFile(self.__stepNo)
        ePath = self.__getErrWrkFile(self.__stepNo)
        tPath = self.__getTmpWrkFile(self.__stepNo)
        #
        if (self.__wrkPath is not None):
            iPathFull = os.path.abspath(os.path.join(self.__wrkPath, iPath))
            ePathFull = os.path.join(self.__wrkPath, ePath)
            lPathFull = os.path.join(self.__wrkPath, lPath)
            tPathFull = os.path.join(self.__wrkPath, tPath)
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
            if (os.access(pPath, os.F_OK)):
                cmd += "; cp " + pPath + " " + iPath

        #
        # Standard setup for maxit ---
        #
        cmd += " ; RCSBROOT=" + self.__rcsbAppsPath + " ; export RCSBROOT  "
        cmd += " ; COMP_PATH=" + self.__ccCvsPath + " ; export COMP_PATH  "
        valCmd = os.path.join(self.__rcsbAppsPath, "bin", "validation_with_cif_output")

        #
        if (op == "validate-geometry"):
            thisCmd = " ; " + valCmd
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
            self.__lfh.write("+RcsbDpUtility._validationStep()  - Application string:\n%s\n" % cmd.replace(";", "\n"))
        #
        # if (self.__debug):
        #    cmd += " ; ls -la  > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath

        cmd += " ) > %s 2>&1 " % ePathFull

        cmd += " ; cat " + ePathFull + " >> " + lPathFull

        if (self.__debug):
            ofh = open(lPathFull, 'w')
            lt = time.strftime("%Y %m %d %H:%M:%S", time.localtime())
            ofh.write("\n\n-------------------------------------------------\n")
            ofh.write("LogFile:      %s\n" % lPath)
            ofh.write("Working path: %s\n" % self.__wrkPath)
            ofh.write("Date:         %s\n" % lt)
            ofh.write("\nStep command:\n%s\n-------------------------------------------------\n" % cmd.replace(";", "\n"))
            ofh.close()


        iret = self.__run(cmd, lPathFull, op)

        return iret

    def __emStep(self, op):
        """ Internal method that performs a single em operation.

        """
        #
        # Set application specific path details here -
        #
        self.__packagePath = self.__getConfigPath('SITE_PACKAGES_PATH')
        self.__deployPath = self.__getConfigPath('SITE_DEPLOY_PATH')
        self.__emDictPath = self.__getConfigPath('SITE_EM_DICT_PATH')
        self.__localAppsPath = self.__getConfigPath('SITE_LOCAL_APPS_PATH')

        if self.__siteId in ['WWPDB_DEPLOY_MACOSX']:
            self.__javaPath = '/usr/bin/java'
        else:
            self.__javaPath = os.path.join(self.__packagePath, "java",
                                           "jre", "bin", "java")

        #
        #
        iPath = self.__getSourceWrkFile(self.__stepNo)
        iPathList = self.__getSourceWrkFileList(self.__stepNo)
        oPath = self.__getResultWrkFile(self.__stepNo)
        lPath = self.__getLogWrkFile(self.__stepNo)
        ePath = self.__getErrWrkFile(self.__stepNo)
        tPath = self.__getTmpWrkFile(self.__stepNo)
        #
        if (self.__wrkPath is not None):
            iPathFull = os.path.abspath(os.path.join(self.__wrkPath, iPath))
            ePathFull = os.path.join(self.__wrkPath, ePath)
            lPathFull = os.path.join(self.__wrkPath, lPath)
            tPathFull = os.path.join(self.__wrkPath, tPath)
            cmd = "cd " + self.__wrkPath + " && { "
        else:
            iPathFull = iPath
            ePathFull = ePath
            lPathFull = lPath
            tPathFull = tPath
            cmd = "{ "

        def mapfix_command(input):
            jarPath = os.path.join(self.__packagePath, "mapFix", "mapFixDep.jar")
            out = self.__javaPath + " -Xms256m -Xmx256m -jar " + jarPath
            out += " -in " + input + " -out " + oPath
            if 'options' in self.__inputParamDict:
                options = self.__inputParamDict['options']
                if options != 'None':  # Unbelievable!
                    out += " " + options
            return out

        if (op == "em2em-spider"):

            # First step em2em spider -> ccp4
            imagicPath = os.path.join(self.__packagePath, "em2em_c5")
            binPath = os.path.join(self.__packagePath, "em2em_c5", "em2em.e")

            cFile = os.path.join(self.__wrkPath, "COMMANDS.sh")
            ofh = open(cFile, 'w')
            ofh.write("#!/bin/sh\n")
            ofh.write("unset DISPLAY\n")
            ofh.write("unset TERM\n")
            ofh.write("export IMAGIC_ROOT=%s\n" % imagicPath)
            ofh.write("%s << eof\n" % binPath)
            ofh.write("SPIDER\n")
            ofh.write("SINGLE_FILE\n")
            ofh.write("CCP4\n")
            ofh.write("3D\n")
            ofh.write("%s\n" % iPath)
            ofh.write("tmp.map\n")
            ofh.write("1.0, 1.0, 1.0\n")
            ofh.write("NO\n")
            ofh.write("eof\n")
            ofh.close()
            st = os.stat(cFile)
            os.chmod(cFile, st.st_mode | stat.S_IEXEC)

            cmd += cFile
            cmd += " >& " + ePath + " && "

            cmd += mapfix_command("tmp.map")
            cmd += " ; } 2>> " + ePath + " 1> " + lPath

        if (op == "mapfix-big"):
            cmd += mapfix_command(iPath)
            cmd += " ; } 2> " + ePath + " 1> " + lPath

        elif (op == "fsc_check"):
            system_path = os.path.join(self.__packagePath, "..")
            xmllint = os.path.join(system_path, "bin", "xmllint")
            lib_path = os.path.join(system_path, "lib")
            schema = os.path.join(self.__emDictPath, "emdb_fsc.xsd")
            cmd += "export LD_LIBRARY_PATH=" + lib_path + "; "
            cmd += xmllint + " --format --schema " + schema + " " + iPath
            #
            if 'options' in self.__inputParamDict:
                options = self.__inputParamDict['options']
                if options != 'None':  # Unbelievable!
                    cmd += " " + options
            #
            cmd += " ; } 2> " + lPath + " 1>" + oPath

        elif (op == "img-convert"):
            # ES (17 Dec 2015): commented lines that doesn't have effect. I
            # believe at some point convert was installed in the tools folder,
            # not any more. We rely on the one installed in the different
            # systems and servers (it is quiet ubiquitous).
            #system_path = os.path.join(self.__packagePath, "..")
            #convert = os.path.join(system_path, "bin", "convert")
            #lib_path = os.path.join(system_path, "lib")
            #cmd += "export LD_LIBRARY_PATH=" + lib_path+ "; "
            convert = "convert +repage -quiet -resize x400 "
            cmd += convert
            #
            if 'options' in self.__inputParamDict:
                options = self.__inputParamDict['options']
                if options != 'None':  # Unbelievable!
                    cmd += " " + options
            #
            cmd += iPath + " png:" + oPath
            cmd += " ; } 2> " + lPath
        #
        # Annotation tasks ----
        #
        elif (op == "annot-read-map-header"):
            # update the header of the map file avoiding a local copy -
            # Both options -in and -out must be specified.
            #  -in  <filename>           : input map
            #  -out <filename>           : output map
            #  -cell <x> <y> <z>         : set x/y/z-length x/y/z
            #  -label <DepCode>          : write new label
            #  -gridsampling <x> <y> <z> : set x/y/z- grid sampling
            #  -gridstart <x> <y> <z>    : set x/y/z- grid start point
            #  -voxel <x> <y> <z>        : set x y z pixel spacing
            #  Recommend : java -Xms256m -Xmx256m -jar mapFixAnot.jar -in <filein> -out <fileout>

            # Export map header as JSON packet -
            jarPath = os.path.join(self.__packagePath, "mapFix", "mapFixAnot.jar")
            cmd += self.__javaPath + " -Xms256m -Xmx256m -jar " + jarPath
            # -out is a temporary file place holder --
            cmd += " -in " + iPath + " -out  dummy-out.map "
            # these dummy arguments required to run this code --
            cmd += " -voxel 1.0 1.0 1.0 -label test "
            # oPath here will be the JSON  output containing may header details --
            cmd += " ; } 2> " + ePath + " 1> " + oPath
            cmd += " ; cat " + ePath + " > " + lPath

        elif (op == "annot-read-map-header-in-place"):
            # update the header of the map file avoiding a local copy -
            # Both options -in and -out must be specified.
            #  -in  <filename>           : input map
            #  -out <filename>           : output map
            #  -cell <x> <y> <z>         : set x/y/z-length x/y/z
            #  -label <DepCode>          : write new label
            #  -gridsampling <x> <y> <z> : set x/y/z- grid sampling
            #  -gridstart <x> <y> <z>    : set x/y/z- grid start point
            #  -voxel <x> <y> <z>        : set x y z pixel spacing
            #  Recommend : java -Xms256m -Xmx256m -jar mapFixAnot.jar -in <filein> -out <fileout>

            if 'map_file_path' in self.__inputParamDict:
                inpMapFilePath = self.__inputParamDict['map_file_path']
            # Export map header as JSON packet -
            jarPath = os.path.join(self.__packagePath, "mapFix", "mapFixAnot.jar")
            cmd += self.__javaPath + " -Xms256m -Xmx256m -jar " + jarPath
            # -out is a temporary file place holder --
            cmd += " -in " + inpMapFilePath + " -out  dummy-out.map "
            # these dummy arguments required to run this code --
            cmd += " -voxel 1.0 1.0 1.0 -label test "
            # oPath here will be the JSON  output containing may header details --
            cmd += " ; } 2> " + ePath + " 1> " + oPath
            cmd += " ; cat " + ePath + " > " + lPath

        elif (op == "annot-update-map-header-in-place"):
            # update the header of the map file avoiding a local copy -
            # Both options -in and -out must be specified.
            #  -in  <filename>           : input map
            #  -out <filename>           : output map
            #  -cell <x> <y> <z>         : set x/y/z-length x/y/z
            #  -label <DepCode>          : write new label
            #  -gridsampling <x> <y> <z> : set x/y/z- grid sampling
            #  -gridstart <x> <y> <z>    : set x/y/z- grid start point
            #  -voxel <x> <y> <z>        : set x y z pixel spacing
            #  Recommend : java -Xms256m -Xmx256m -jar mapFixAnot.jar -in <filein> -out <fileout>

            # use references for input and output file paths -
            if 'input_map_file_path' in self.__inputParamDict:
                inpMapFilePath = self.__inputParamDict['input_map_file_path']

            if 'output_map_file_path' in self.__inputParamDict:
                outMapFilePath = self.__inputParamDict['output_map_file_path']
            #
            jarPath = os.path.join(self.__packagePath, "mapFix", "mapFixAnot.jar")
            cmd += self.__javaPath + " -Xms256m -Xmx256m -jar " + jarPath
            # -out is a temporary file place holder --
            cmd += " -in " + inpMapFilePath + " -out  " + outMapFilePath
            #
            if 'voxel' in self.__inputParamDict:
                argVal = self.__inputParamDict['voxel']
                cmd += " -voxel " + argVal

            if 'cell' in self.__inputParamDict:
                argVal = self.__inputParamDict['cell']
                cmd += " -cell " + argVal

            if 'label' in self.__inputParamDict:
                argVal = self.__inputParamDict['label']
                cmd += " -label " + argVal

            if 'gridsampling' in self.__inputParamDict:
                argVal = self.__inputParamDict['gridsampling']
                cmd += " -gridsampling " + argVal

            if 'gridstart' in self.__inputParamDict:
                argVal = self.__inputParamDict['gridstart']
                cmd += " -gridstart " + argVal

            # any options ---
            if 'options' in self.__inputParamDict:
                argVal = str(self.__inputParamDict['options']).strip()
                cmd += " " + argVal

            cmd += " ; } 2> " + ePath + " 1> " + oPath
            cmd += " ; cat " + ePath + " > " + lPath
        elif (op == "deposit-update-map-header-in-place"):
            # Both options -in and -out must be specified.
            #  -in  <filename>           : input map
            #  -out <filename>           : output map
            #  -label <DepCode>          : write new label
            #  -voxel <x> <y> <z>        : set x y z pixel spacing
            #  Recommend : java -Xms256m -Xmx256m -jar mapFixDep.jar -in <filein> -out <fileout> -voxel X Y Z -label 'D_120001'

            # use references for input and output file paths -
            if 'input_map_file_path' in self.__inputParamDict:
                inpMapFilePath = self.__inputParamDict['input_map_file_path']

            if 'output_map_file_path' in self.__inputParamDict:
                outMapFilePath = self.__inputParamDict['output_map_file_path']
            #
            jarPath = os.path.join(self.__packagePath, "mapFix", "mapFixDep.jar")
            cmd += self.__javaPath + " -Xms256m -Xmx256m -jar " + jarPath
            # -out is a temporary file place holder --
            cmd += " -in " + inpMapFilePath + " -out  " + outMapFilePath
            #
            if 'voxel' in self.__inputParamDict:
                argVal = self.__inputParamDict['voxel']
                cmd += " -voxel " + argVal
                argVal = self.__inputParamDict['label']
                cmd += " -label " + argVal

            # any options ---
            if 'options' in self.__inputParamDict:
                argVal = str(self.__inputParamDict['options']).strip()
                cmd += " " + argVal

            cmd += " ; } 2> " + ePath + " 1> " + oPath
            cmd += " ; cat " + ePath + " > " + lPath
        elif (op == "xml-header-check"):
            xmllint = os.path.join(self.__localAppsPath, "bin", "xmllint")
            schema = os.path.join(self.__emDictPath, "emdb_da.xsd")
            cmd += xmllint + " --noout --schema " + schema + " " + iPath
            #
            if 'options' in self.__inputParamDict:
                cmd += " " + self.__inputParamDict['options']
            #
            cmd += " ; } > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
        else:
            pass

        if (op not in ("em2em-spider", "mapfix-big", "fsc_check",
                       "img-convert", "annot-read-map-header",
                       "annot-read-map-header-in-place",
                       "annot-update-map-header-in-place",
                       "deposit-update-map-header-in-place",
                       "xml-header-check")):
            return -1
        #

        if (self.__debug):
            self.__lfh.write("+RcsbDpUtility._emStep()  - Application string:\n%s\n" % cmd)

        #
        if (self.__debug):
            ofh = open(lPathFull, 'w')
            lt = time.strftime("%Y %m %d %H:%M:%S", time.localtime())
            ofh.write("\n\n-------------------------------------------------\n")
            ofh.write("LogFile:      %s\n" % lPath)
            ofh.write("Working path: %s\n" % self.__wrkPath)
            ofh.write("Date:         %s\n" % lt)
            ofh.write("\nStep command:\n%s\n-------------------------------------------------\n" % cmd.replace(";", "\n"))
            ofh.close()


        iret = self.__run(cmd, lPathFull, op)

        return iret

    def __maxitStep(self, op, progName="maxit"):
        """ Internal method that performs a single maxit operation.

        """
        # Set application specific path details --
        #
        # If this has not been initialized take if from the configuration class.
        if self.__rcsbAppsPath is None:
            #self.__rcsbAppsPath  =  self.__getConfigPath('SITE_RCSB_APPS_PATH')
            self.__rcsbAppsPath = self.__getConfigPath('SITE_ANNOT_TOOLS_PATH')
        self.__ccCvsPath = self.__getConfigPath('SITE_CC_CVS_PATH')
        #
        iPath = self.__getSourceWrkFile(self.__stepNo)
        iPathList = self.__getSourceWrkFileList(self.__stepNo)
        oPath = self.__getResultWrkFile(self.__stepNo)
        lPath = self.__getLogWrkFile(self.__stepNo)
        ePath = self.__getErrWrkFile(self.__stepNo)
        #
        if (self.__wrkPath is not None):
            lPathFull = os.path.join(self.__wrkPath, lPath)
            ePathFull = os.path.join(self.__wrkPath, ePath)
            cmd = "(cd " + self.__wrkPath
        else:
            ePathFull = ePath
            lPathFull = lPath
            cmd = "("
        #
        if (self.__stepNo > 1):
            pPath = self.__updateInputPath()
            if (os.access(pPath, os.F_OK)):
                cmd += "; cp " + pPath + " " + iPath
        #
        cmd += " ; RCSBROOT=" + self.__rcsbAppsPath + " ; export RCSBROOT "
        cmd += " ; COMP_PATH=" + self.__ccCvsPath + " ; export COMP_PATH ; "
        maxitCmd = os.path.join(self.__rcsbAppsPath, "bin", progName)

        if (op == "cif2cif"):
            cmd += maxitCmd + " -o 8  -i " + iPath
            cmd += " ; mv -f " + iPath + ".cif " + oPath

        elif (op == "cif2cif-remove"):
            cmd += maxitCmd + " -o 8  -remove -i " + iPath
            cmd += " ; mv -f " + iPath + ".cif " + oPath

        elif (op == "cif-rcsb2cif-pdbx"):
            cmd += maxitCmd + " -o 56  -i " + iPath
            cmd += " ; mv -f " + iPath + ".cif " + oPath

        elif (op == "cif-seqed2cif-pdbx"):
            cmd += maxitCmd + " -o 10  -i " + iPath
            cmd += " ; mv -f " + iPath + ".cif " + oPath

        elif (op == "cif2cif-pdbx"):
            cmd += maxitCmd + " -o 8 -standard -pdbids -no_deriv -no_pdbx_strand_id -no_site -i " + iPath
            cmd += " ; mv -f " + iPath + ".cif " + oPath

        elif (op == "cif2cif-pdbx-skip-process"):
            cmd += maxitCmd + " -o 9 -i " + iPath
            cmd += " ; mv -f " + iPath + ".cif " + oPath

        elif (op == "cif2cif-ebi"):
            cmd += maxitCmd + " -o 8  "
            cmd += " -get_biol_unit -pdbids -i " + iPath
            cmd += " ; mv -f " + iPath + ".cif " + oPath

        elif (op == "pdb2cif"):
            cmd += maxitCmd + " -o 1  -i " + iPath
            cmd += " ; mv -f " + iPath + ".cif " + oPath

        elif (op == "pdb2cif-ebi"):
            cmd += maxitCmd + " -o 1  -i " + iPath
            cmd += " ; mv -f " + iPath + ".cif " + oPath

        elif (op == "cif2pdb"):
            cmd += maxitCmd + " -o 2  -i " + iPath
            cmd += " ; mv -f " + iPath + ".pdb " + oPath

        elif (op == "switch-dna"):
            cmd += maxitCmd + " -o 68  -i " + iPath
            cmd += " ; mv -f " + iPath + ".cif " + oPath

        elif (op == "cif2pdb-assembly"):
            cmd += maxitCmd + " -o 55 -pdbids  -i " + iPath

        elif (op == "pdbx2pdb-assembly"):
            cmd += maxitCmd + " -o 55 -exchange_in -pdbids  -i " + iPath

        elif (op == "pdbx2deriv"):
            cmd += maxitCmd + " -o 60 -exchange_in -exchange_out -pdbids  -i " + iPath
            cmd += " ;  cp -f  *-deriv.cif " + oPath
        else:
            return -1
        #
        # if (self.__debug):
        #    cmd += " ; ls -la >> " + lPath
        #
        cmd += " ) > %s 2>&1 " % ePathFull

        if (self.__debug):
            self.__lfh.write("+RcsbDpUtility.maxitStep()  - Command string:\n%s\n" % cmd.replace(";", "\n"))

        if (self.__debug):
            ofh = open(lPathFull, 'w')
            lt = time.strftime("%Y %m %d %H:%M:%S", time.localtime())
            ofh.write("\n\n-------------------------------------------------\n")
            ofh.write("LogFile:      %s\n" % lPath)
            ofh.write("Working path: %s\n" % self.__wrkPath)
            ofh.write("Date:         %s\n" % lt)
            ofh.write("\nStep command:\n%s\n-------------------------------------------------\n" % cmd.replace(";", "\n"))
            ofh.write("\n")
            ofh.close()


        iret = self.__run(cmd, lPathFull, op)

        #iret = os.system(cmd)
        #
        if ((op == "cif2pdb-assembly") or (op == "pdbx2pdb-assembly")):
            pat = self.__wrkPath + '/*.pdb[1-9]*'
            self.__resultPathList = glob.glob(pat)

        else:
            self.__resultPathList = [os.path.join(self.__wrkPath, oPath)]

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
            self.__rcsbAppsPath = self.__getConfigPath('SITE_ANNOT_TOOLS_PATH')

        if self.__localAppsPath is None:
            self.__localAppsPath = self.__getConfigPath('SITE_LOCAL_APPS_PATH')

        self.__packagePath = self.__getConfigPath('SITE_PACKAGES_PATH')

        #
        self.__ccAppsPath = self.__getConfigPath('SITE_CC_APPS_PATH')
        self.__pdbxDictPath = self.__getConfigPath('SITE_PDBX_DICT_PATH')
        self.__pdbxDictName = self.__cI.get('SITE_PDBX_DICT_NAME')
        self.__pdbxV4DictName = self.__cI.get('SITE_PDBX_V4_DICT_NAME')

        self.__ccDictPath = self.__getConfigPath('SITE_CC_DICT_PATH')
        self.__ccCvsPath = self.__getConfigPath('SITE_CC_CVS_PATH')

        self.__resourcePath = self.__getConfigPath('SITE_RESOURCE_DIRECTORY_PATH')
        self.__patternPath = os.path.join(self.__resourcePath, "fp_patterns.txt")
        self.__ccDictPathCif = os.path.join(self.__ccDictPath, "Components-all-v3.cif")
        self.__ccDictPathSdb = os.path.join(self.__ccDictPath, "Components-all-v3.sdb")
        self.__ccDictPathIdx = os.path.join(self.__ccDictPath, "Components-all-v3-r4.idx")
        #
        self.__pathDdlSdb = os.path.join(self.__pdbxDictPath, "mmcif_ddl.sdb")
        self.__pathDdl = os.path.join(self.__pdbxDictPath, "mmcif_ddl.dic")
        self.__pathPdbxDictSdb = os.path.join(self.__pdbxDictPath, self.__pdbxDictName + '.sdb')
        self.__pathPdbxV4DictSdb = os.path.join(self.__pdbxDictPath, self.__pdbxV4DictName + '.sdb')
        self.__pathPdbxDictOdb = os.path.join(self.__pdbxDictPath, self.__pdbxDictName + '.odb')
        #
        self.__oeDirPath = self.__getConfigPath('SITE_CC_OE_DIR')
        self.__oeLicensePath = self.__getConfigPath('SITE_CC_OE_LICENSE')
        self.__babelLibPath = self.__getConfigPath('SITE_CC_BABEL_LIB')
        self.__babelDirPath = self.__getConfigPath('SITE_CC_BABEL_DIR')
        self.__babelDataDirPath = self.__getConfigPath('SITE_CC_BABEL_DATADIR')
        self.__cactvsDirPath = self.__getConfigPath('SITE_CC_CACTVS_DIR')
        #
        self.__acdDirPath = self.__getConfigPath('SITE_CC_ACD_DIR')
        self.__corinaDirPath = os.path.join(self.__getConfigPath('SITE_CC_CORINA_DIR'), 'bin')
        self.__inchiDirPath = self.__getConfigPath('SITE_CC_INCHI_DIR')

        # -------------
        #
        iPath = self.__getSourceWrkFile(self.__stepNo)
        iPathList = self.__getSourceWrkFileList(self.__stepNo)
        oPath = self.__getResultWrkFile(self.__stepNo)
        lPath = self.__getLogWrkFile(self.__stepNo)
        ePath = self.__getErrWrkFile(self.__stepNo)
        tPath = self.__getTmpWrkFile(self.__stepNo)
        #
        if (self.__wrkPath is not None):
            ePathFull = os.path.join(self.__wrkPath, ePath)
            lPathFull = os.path.join(self.__wrkPath, lPath)
            tPathFull = os.path.join(self.__wrkPath, tPath)
            cmd = "(cd " + self.__wrkPath
        else:
            ePathFull = ePath
            lPathFull = lPath
            tPathFull = tPath
            cmd = "("
        #
        if (self.__stepNo > 1):
            pPath = self.__updateInputPath()
            if (os.access(pPath, os.F_OK)):
                cmd += "; cp " + pPath + " " + iPath
        #

        if (op == "rename-atoms"):
            cmdPath = os.path.join(self.__ccAppsPath, "bin", "switch-atom-element")
            thisCmd = " ; " + cmdPath + " -dicodb " + self.__ccDictPathSdb
            cmd += thisCmd + " -file " + iPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; mv -f " + iPath + ".cif " + oPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath

        elif (op == "chem-comp-annotate-comp"):
            opAnnot = "'stereo-cactvs|aro-cactvs|descriptor-oe|descriptor-cactvs|descriptor-inchi|name-oe|name-acd|xyz-ideal-corina|xyz-model-h-oe|rename|fix'"
            cmd += " ; CC_TOOLS=" + os.path.join(self.__ccAppsPath, 'bin') + " ; export CC_TOOLS "
            cmd += " ; ACD_DIR=" + self.__acdDirPath + " ; export ACD_DIR "
            cmd += " ; CACTVS_DIR=" + self.__cactvsDirPath + " ; export CACTVS_DIR "
            cmd += " ; CORINA_DIR=" + self.__corinaDirPath + " ; export CORINA_DIR "
            cmd += " ; INCHI_DIR=" + self.__inchiDirPath + " ; export INCHI_DIR "
            cmd += " ; OE_DIR=" + self.__oeDirPath + " ; export OE_DIR "
            cmd += " ; OE_LICENSE=" + self.__oeLicensePath + " ; export OE_LICENSE "
            cmd += " ; BABEL_DIR=" + self.__babelDirPath + " ; export BABEL_DIR "
            cmd += " ; BABEL_DATADIR=" + self.__babelDataDirPath + " ; export BABEL_DATADIR "
            cmd += " ; CACTVS_DIR=" + self.__cactvsDirPath + " ; export CACTVS_DIR "
            cmd += " ; LD_LIBRARY_PATH=" + self.__babelLibPath + ":" + os.path.join(self.__localAppsPath, "lib") + ":" + self.__acdDirPath + " ; export LD_LIBRARY_PATH "
            cmdPath = os.path.join(self.__ccAppsPath, "bin", "annotateComp")
            thisCmd = " ; " + cmdPath + " -i " + iPath + " -op " + opAnnot + " -o " + oPath + " -export_format pdbx "
            cmd += thisCmd
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " > " + lPath

        elif (op == "chem-comp-dict-makeindex"):
            # -index oPath(.idx) -lib iPath (.sdb) -type makeindex -fplib $fpPatFile
            #  ipath = dict.sdb   opath = dict.idx
            #  #   serialized files are checked for file extension -- so adding one here --
            lsdbPath = iPath + ".sdb"
            cmd += " ; OE_DIR=" + self.__oeDirPath + " ; export OE_DIR "
            cmd += " ; OE_LICENSE=" + self.__oeLicensePath + " ; export OE_LICENSE "
            cmd += " ;  ln -s " + iPath + " " + lsdbPath
            cmdPath = os.path.join(self.__ccAppsPath, "bin", "matchComp")
            thisCmd = " ; " + cmdPath + "  -v -lib " + lsdbPath + " -type makeindex -fplib " + self.__patternPath
            cmd += thisCmd + " -index " + oPath
            cmd += " > " + tPath + " 2>&1 ;  cat " + tPath + " > " + lPath
            cmd += " ; cat matchComp.log  >> " + lPath
        elif (op == "chem-comp-dict-serialize"):
            # $binPath/checkCifUtil -i $oFileTmp  -osdb $oFileSdbTmp -op serialize
            #
            cmdPath = os.path.join(self.__ccAppsPath, "bin", "checkCifUtil")
            thisCmd = " ; " + cmdPath + " -i " + iPath + " -op serialize "
            cmd += thisCmd + " -osdb " + oPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " > " + lPath
            cmd += " ; cat checkCifUtilIO.log  >> " + lPath
        elif (op == "initial-version"):
            cmdPath = os.path.join(self.__rcsbAppsPath, "bin", "cif-version")
            thisCmd = " ; " + cmdPath
            cmd += thisCmd + " -newfile " + iPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; mv -f " + iPath + ".cif " + oPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
        elif (op == "check-cif"):
            cmdPath = os.path.join(self.__packagePath, "dict", "bin", "CifCheck")
            thisCmd = " ; " + cmdPath
            cmd += thisCmd + " -f " + iPath
            cmd += " -dictSdb " + self.__pathPdbxDictSdb
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; touch " + iPath + "-diag.log "
            cmd += " ; touch " + iPath + "-parser.log "
            cmd += " ; cat " + iPath + "-parser.log > " + oPath
            cmd += " ; cat " + iPath + "-diag.log  >> " + oPath
            #cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
        elif (op == "check-cif-v4"):
            cmdPath = os.path.join(self.__packagePath, "dict", "bin", "CifCheck")
            thisCmd = " ; " + cmdPath
            cmd += thisCmd + " -f " + iPath
            cmd += " -dictSdb " + self.__pathPdbxV4DictSdb
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; touch " + iPath + "-diag.log "
            cmd += " ; touch " + iPath + "-parser.log "
            cmd += " ; cat " + iPath + "-parser.log > " + oPath
            cmd += " ; cat " + iPath + "-diag.log  >> " + oPath
            #cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
        elif (op == "check-cif-ext"):
            # Dictionary check with selectable dictionary
            # Default 'internal' - v5next
            dictName = self.__inputParamDict.get('dictionary', 'deposit')
            dictSdbPath = self.__nameToDictPath(dictName)
            #
            cmdPath = os.path.join(self.__packagePath, "dict", "bin", "CifCheck")
            thisCmd = " ; " + cmdPath
            cmd += thisCmd + " -f " + iPath
            cmd += " -dictSdb " + dictSdbPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; touch " + iPath + "-diag.log "
            cmd += " ; touch " + iPath + "-parser.log "
            cmd += " ; cat " + iPath + "-parser.log > " + oPath
            cmd += " ; cat " + iPath + "-diag.log  >> " + oPath

        elif (op == "cif2pdbx-public"):
            # dict/bin/cifexch2 -dicSdb mmcif_pdbx_v5_next.sdb -reorder -strip -op in -pdbids -input D_1000200033_model_P1.cif -output 4ovr.cif
            # -pdbxDicSdb /whaterver/the/path/is/used/mmcif_pdbx.sdb
            cmdPath = os.path.join(self.__packagePath, "dict", "bin", "cifexch2")
            #thisCmd  = " ; " + cmdPath + " -dicSdb " + self.__pathPdbxDictSdb +  " -reorder  -strip -op in  -pdbids "
            thisCmd = " ; " + cmdPath + " -dicSdb " + self.__pathPdbxDictSdb + " -pdbxDicSdb " + self.__pathPdbxV4DictSdb + " -reorder  -strip -op in  -pdbids "
            cmd += thisCmd + " -input " + iPath + " -output " + oPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath

        elif (op == "cif2pdbx-ext"):
            """Extended version of cif2pdbx that supports both archive and internal"""
            # Default archive
            dictName = self.__inputParamDict.get('destination', 'archive_current')

            if dictName == 'archive_current':
                sDictSdb = self.__nameToDictPath('deposit')
                dDictSdb = self.__nameToDictPath('archive_current')
            elif dictName == 'archive_next':
                sDictSdb = self.__nameToDictPath('archive_next')
                dDictSdb = self.__nameToDictPath('archive_next')

            cmdPath = os.path.join(self.__packagePath, "dict", "bin", "cifexch2")
            thisCmd = " ; " + cmdPath + " -dicSdb " + sDictSdb + " -pdbxDicSdb " + dDictSdb + " -reorder  -strip -op in  -pdbids "
            cmd += thisCmd + " -input " + iPath + " -output " + oPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath

        elif (op == "cif2pdbx"):
            #   need to have an input file list.
            cmdPath = os.path.join(self.__localAppsPath, "bin", "cifexch-v3.2")
            thisCmd = " ; " + cmdPath + " -ddlodb " + self.__pathDdlSdb + " -dicodb " + self.__pathPdbxDictSdb
            thisCmd += " -reorder  -strip -op in  -pdbids "

            cmd += thisCmd + " -inlist " + iPathList
            cmd += " ; mv -f " + iPath + ".tr " + oPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath

        elif (op == "pdbx2xml"):
            cmdPath = os.path.join(self.__localAppsPath, "bin", "mmcif2XML")
            thisCmd = " ; " + cmdPath + " -prefix  pdbx -ns PDBx -funct mmcif2xmlall "
            thisCmd += " -dict mmcif_pdbxR.dic " " -df " + self.__pathPdbxDictOdb
            cmd += thisCmd + " -f " + iPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath

        elif (op == "pdb2dssp"):
            cmdPath = os.path.join(self.__localAppsPath, "bin", "dssp")
            thisCmd = " ;  " + cmdPath
            cmd += thisCmd + "  " + iPath + " " + oPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            #  /lcl/bin/dssp ${id}.ent ${id}.dssp >&  ${id}.dssp.log
        elif (op == "pdb2stride"):
            cmdPath = os.path.join(self.__localAppsPath, "bin", "stride")
            thisCmd = " ;  " + cmdPath
            cmd += thisCmd + " -f" + oPath + " " + iPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            # /lcl/bin/stride -f${id}.stride  ${id}.ent >&  ${id}.stride.log
        elif (op == "poly-link-dist"):
            cmdPath = os.path.join(self.__rcsbAppsPath, "bin", "cal_polymer_linkage_distance")
            thisCmd = " ; " + cmdPath
            cmd += " ; RCSBROOT=" + self.__rcsbAppsPath + " ; export RCSBROOT "
            cmd += thisCmd + " -i " + iPath + " -o " + oPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
        elif (op == "chem-comp-link"):
            cmdPath = os.path.join(self.__rcsbAppsPath, "bin", "bond_dist")
            thisCmd = " ; " + cmdPath
            cmd += " ; RCSBROOT=" + self.__rcsbAppsPath + " ; export RCSBROOT "
            cmd += thisCmd + " -i " + iPath + " -o " + oPath + " -format cif "
            if 'cc_link_radii' in self.__inputParamDict:
                link_radii = self.__inputParamDict['cc_link_radii']
                cmd += " -link_radii " + link_radii
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; cat bond_dist.err" + " >> " + lPath
        elif ((op == "chem-comp-assign") or (op == "chem-comp-assign-skip") or (op == "chem-comp-assign-exact")):
            # set up
            #
            skipOp = ""
            exactOp = ""
            relOnlyOp = ""

            if (op == "chem-comp-assign-skip"):
                skipOp = " -skip_search "
            if (op == "chem-comp-assign-exact"):
                exactOp = " -exact "
                relOnlyOp = " -rel "  # i.e. released entries only

            cmd += " ; RCSBROOT=" + self.__rcsbAppsPath + " ; export RCSBROOT "
            cmd += " ; OE_DIR=" + self.__oeDirPath + " ; export OE_DIR "
            cmd += " ; OE_LICENSE=" + self.__oeLicensePath + " ; export OE_LICENSE "
            cmd += " ; BABEL_DIR=" + self.__babelDirPath + " ; export BABEL_DIR "
            cmd += " ; BABEL_DATADIR=" + self.__babelDataDirPath + " ; export BABEL_DATADIR "
            cmd += " ; CACTVS_DIR=" + self.__cactvsDirPath + " ; export CACTVS_DIR "
            cmd += " ; LD_LIBRARY_PATH=" + self.__babelLibPath + ":" \
                   + os.path.join(self.__packagePath, "ccp4", "lib") + ":" \
                   + os.path.join(self.__localAppsPath, "lib") + " ; export LD_LIBRARY_PATH "

            cmd += " ; env "
            cmdPath = os.path.join(self.__ccAppsPath, "bin", "ChemCompAssign_main")
            thisCmd = " ; rm -f " + oPath + " ; " + cmdPath
            entryId = self.__inputParamDict['id']
            #
            # cc_link_file_path=''
            # if  self.__inputParamDict.has_key('link_file_path'):
            #    link_file=self.__inputParamDict['link_file_path']
            #    cmd += " ;  cp " + link_file + " " + self.__wrkPath
            #
            cmd += thisCmd + skipOp + exactOp + relOnlyOp + " -i " + iPath + " -of " + oPath + " -o " + self.__wrkPath + " -ifmt pdbx " + " -id " + entryId
            cmd += " -libsdb " + self.__ccDictPathSdb + " -idxFile " + self.__ccDictPathIdx
            #
            if 'cc_link_file_path' in self.__inputParamDict:
                cmd += " -bond_info " + self.__inputParamDict['cc_link_file_path']
            #
            if 'cc_instance_id' in self.__inputParamDict:
                cmd += " -radii_inst_id " + self.__inputParamDict['cc_instance_id']
            #
            if 'cc_bond_radii' in self.__inputParamDict:
                cmd += " -bond_radii " + self.__inputParamDict['cc_bond_radii']
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
        elif (op == "chem-comp-assign-comp"):
            # set up
            #
            cmd += " ; RCSBROOT=" + self.__rcsbAppsPath + " ; export RCSBROOT "
            cmd += " ; OE_DIR=" + self.__oeDirPath + " ; export OE_DIR "
            cmd += " ; OE_LICENSE=" + self.__oeLicensePath + " ; export OE_LICENSE "
            cmd += " ; BABEL_DIR=" + self.__babelDirPath + " ; export BABEL_DIR "
            cmd += " ; BABEL_DATADIR=" + self.__babelDataDirPath + " ; export BABEL_DATADIR "
            cmd += " ; CACTVS_DIR=" + self.__cactvsDirPath + " ; export CACTVS_DIR "
            cmd += " ; LD_LIBRARY_PATH=" + self.__babelLibPath + ":" \
                   + os.path.join(self.__packagePath, "ccp4", "lib") + ":" \
                   + os.path.join(self.__localAppsPath, "lib") + " ; export LD_LIBRARY_PATH "

            cmd += " ; env ; rm -f " + oPath + " ; " + os.path.join(self.__ccAppsPath, "bin", "ChemCompAssign_main")
            entryId = self.__inputParamDict['id']
            instId = self.__inputParamDict['cc_instance_id']
            cmd += " -i " + iPath + " -of " + oPath + " -o " + self.__wrkPath + " -ifmt comp -id " + entryId
            cmd += " -search_inst_id " + instId + " -libsdb " + self.__ccDictPathSdb + " -idxFile " \
                + self.__ccDictPathIdx
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
        elif (op == "chem-comp-assign-validation"):
            # set up
            #
            cmd += " ; RCSBROOT=" + self.__rcsbAppsPath + " ; export RCSBROOT "
            cmd += " ; OE_DIR=" + self.__oeDirPath + " ; export OE_DIR "
            cmd += " ; OE_LICENSE=" + self.__oeLicensePath + " ; export OE_LICENSE "
            cmd += " ; BABEL_DIR=" + self.__babelDirPath + " ; export BABEL_DIR "
            cmd += " ; BABEL_DATADIR=" + self.__babelDataDirPath + " ; export BABEL_DATADIR "
            cmd += " ; CACTVS_DIR=" + self.__cactvsDirPath + " ; export CACTVS_DIR "
            cmd += " ; LD_LIBRARY_PATH=" + self.__babelLibPath + ":" \
                   + os.path.join(self.__packagePath, "ccp4", "lib") + ":" \
                   + os.path.join(self.__localAppsPath, "lib") + " ; export LD_LIBRARY_PATH "
            cmd += " ; env "
            cmdPath = os.path.join(self.__ccAppsPath, "bin", "ChemCompAssign_main")
            thisCmd = " ; " + cmdPath
            entryId = self.__inputParamDict['id']
            #
            # cc_link_file_path=''
            # if  self.__inputParamDict.has_key('link_file_path'):
            #    link_file=self.__inputParamDict['link_file_path']
            #    cmd += " ;  cp " + link_file + " " + self.__wrkPath
            #
            cmd += thisCmd + " -i " + iPath + " -of " + oPath + " -o " + self.__wrkPath + " -ifmt comp " + " -id " + entryId
            cmd += " -libsdb " + self.__ccDictPathSdb + " -idxFile " + self.__ccDictPathIdx
            cmd += " -force "
            #
            if 'cc_validation_ref_file_path' in self.__inputParamDict:
                cmd += " -ref " + self.__inputParamDict['cc_validation_ref_file_path']
            #
            if 'cc_validation_instid_list' in self.__inputParamDict:
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
            cmd += " -log " + self.__inputParamDict['cc_validation_log_file']
            #
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
        else:
            return -1
        #

        if (self.__debug):
            self.__lfh.write("+RcsbDpUtility._rcsbStep()  - Application string:\n%s\n" % cmd.replace(";", "\n"))
        #
        # if (self.__debug):
        #    cmd += " ; ls -la  > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath

        cmd += " ) > %s 2>&1 " % ePathFull

        cmd += " ; cat " + ePathFull + " >> " + lPathFull

        if (self.__debug):
            ofh = open(lPathFull, 'w')
            lt = time.strftime("%Y %m %d %H:%M:%S", time.localtime())
            ofh.write("\n\n-------------------------------------------------\n")
            ofh.write("LogFile:      %s\n" % lPath)
            ofh.write("Working path: %s\n" % self.__wrkPath)
            ofh.write("Date:         %s\n" % lt)
            ofh.write("\nStep command:\n%s\n-------------------------------------------------\n" % cmd.replace(";", "\n"))
            ofh.close()


        iret = self.__run(cmd, lPathFull, op)

        #iret = os.system(cmd)
        #
        if ((op == "pdbx2xml")):
            pat = self.__wrkPath + '/*.xml*'
            self.__resultPathList = glob.glob(pat)
        else:
            self.__resultPathList = [os.path.join(self.__wrkPath, oPath)]

        return iret

    def __pisaStep(self, op):
        """ Internal method that performs assembly calculation and management tasks.

        """
        #
        pisaTopPath = self.__getConfigPath('SITE_PISA_TOP_PATH')
        pisaConfPath = self.__getConfigPath('SITE_PISA_CONF_PATH')
        annotToolsPath = self.__getConfigPath('SITE_ANNOT_TOOLS_PATH')

        #
        iPath = self.__getSourceWrkFile(self.__stepNo)
        iPathList = self.__getSourceWrkFileList(self.__stepNo)
        oPath = self.__getResultWrkFile(self.__stepNo)
        lPath = self.__getLogWrkFile(self.__stepNo)
        ePath = self.__getErrWrkFile(self.__stepNo)
        tPath = self.__getTmpWrkFile(self.__stepNo)
        #
        if (self.__wrkPath is not None):
            iPathFull = os.path.abspath(os.path.join(self.__wrkPath, iPath))
            ePathFull = os.path.join(self.__wrkPath, ePath)
            lPathFull = os.path.join(self.__wrkPath, lPath)
            tPathFull = os.path.join(self.__wrkPath, tPath)
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
            if (os.access(pPath, os.F_OK)):
                cmd += "; cp " + pPath + " " + iPath
        #
        if 'pisa_session_name' in self.__inputParamDict:
            pisaSession = str(self.__inputParamDict['pisa_session_name'])
        else:
            pisaSession = None
        cmd += " ; PISA_TOP=" + os.path.abspath(pisaTopPath) + " ; export PISA_TOP "
        cmd += " ; PISA_SESSIONS=" + os.path.abspath(self.__wrkPath) + " ; export PISA_SESSIONS "
        cmd += " ; PISA_CONF_FILE=" + os.path.abspath(os.path.join(pisaConfPath, "pisa-standalone.cfg")) + " ; export PISA_CONF_FILE "
        #
        #cmd += " ; PISA_CONF_FILE="   + os.path.abspath(os.path.join(pisaTopPath,"share","pisa","pisa.cfg")) + " ; export PISA_CONF_FILE "
        if (op == "pisa-analysis"):
            cmdPath = os.path.join(pisaTopPath, "bin", "pisa")
            cmd += " ; " + cmdPath + " " + pisaSession + " -analyse " + iPathFull
            if 'pisa_assembly_arguments' in self.__inputParamDict:
                assemblyArgs = self.__inputParamDict['pisa_assembly_arguments']
                cmd += " " + assemblyArgs
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
        elif (op == "pisa-assembly-report-xml"):
            cmdPath = os.path.join(pisaTopPath, "bin", "pisa")
            cmd += " ; " + cmdPath + " " + pisaSession + " -xml assemblies > " + oPath
            cmd += " 2> " + tPath + " ; cat " + tPath + " >> " + lPath
        elif (op == "pisa-assembly-report-text"):
            cmdPath = os.path.join(pisaTopPath, "bin", "pisa")
            cmd += " ; " + cmdPath + " " + pisaSession + " -list assemblies > " + oPath
            cmd += " 2> " + tPath + " ; cat " + tPath + " >> " + lPath
        elif (op == "pisa-interface-report-xml"):
            cmdPath = os.path.join(pisaTopPath, "bin", "pisa")
            cmd += " ; " + cmdPath + " " + pisaSession + " -xml interfaces > " + oPath
            cmd += " 2> " + tPath + " ; cat " + tPath + " >> " + lPath
        elif (op == "pisa-assembly-coordinates-pdb"):
            pisaAssemblyId = self.__inputParamDict['pisa_assembly_id']
            cmdPath = os.path.join(pisaTopPath, "bin", "pisa")
            cmd += " ; " + cmdPath + " " + pisaSession + " -download assembly " + pisaAssemblyId + "  > " + oPath
            cmd += " 2> " + tPath + " ; cat " + tPath + " >> " + lPath
        elif (op == "pisa-assembly-coordinates-cif"):
            pisaAssemblyId = self.__inputParamDict['pisa_assembly_id']
            cmdPath = os.path.join(pisaTopPath, "bin", "pisa")
            cmd += " ; " + cmdPath + " " + pisaSession + " -cif assembly " + str(pisaAssemblyId) + "  > " + oPath
            cmd += " 2> " + tPath + " ; cat " + tPath + " >> " + lPath
        elif (op == "pisa-assembly-merge-cif"):
            # MergePisaData -input input_ciffile -output output_ciffile -xml xmlfile_from_PISA_output
            #                -log logfile -spacegroup spacegroup_file -list idlist
            #
            spgFilePath = self.__getConfigPath('SITE_SPACE_GROUP_FILE_PATH')
            #assemblyTupleList = self.__inputParamDict['pisa_assembly_tuple_list']
            assemblyFile = self.__inputParamDict['pisa_assembly_file_path']
            assignmentFile = self.__inputParamDict['pisa_assembly_assignment_file_path']
            cmdPath = os.path.join(annotToolsPath, "bin", "MergePisaData")
            #
            cmd += " ; " + cmdPath + " -input " + iPathFull + " -xml " + assemblyFile
            cmd += " -spacegroup " + spgFilePath + " -log " + ePath
            cmd += " -assign " + assignmentFile
            cmd += " -output " + oPath
            #cmd   +=  " ; cp -f " + iPath + " " + oPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath

        else:
            return -1
        #
        if (self.__debug):
            self.__lfh.write("+RcsbDpUtility._pisaStep()  - Application string:\n%s\n" % cmd.replace(";", "\n"))
        #
        # if (self.__debug):
        #    cmd += " ; ls -la  > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath

        cmd += " ) > %s 2>&1 " % ePathFull

        cmd += " ; cat " + ePathFull + " >> " + lPathFull

        if (self.__debug):
            ofh = open(lPathFull, 'w')
            lt = time.strftime("%Y %m %d %H:%M:%S", time.localtime())
            ofh.write("\n\n-------------------------------------------------\n")
            ofh.write("LogFile:      %s\n" % lPath)
            ofh.write("Working path: %s\n" % self.__wrkPath)
            ofh.write("Date:         %s\n" % lt)
            ofh.write("\nStep command:\n%s\n-------------------------------------------------\n" % cmd.replace(";", "\n"))
            ofh.close()


        iret = self.__run(cmd, lPathFull, op)

        #iret = os.system(cmd)
        #
        return iret

    def __sequenceStep(self, op):
        """ Internal method that performs sequence search and entry selection operations.

        """
        #
        packagePath = self.__getConfigPath('SITE_PACKAGES_PATH')
        seqDbPath = self.__getConfigPath('SITE_REFDATA_SEQUENCE_DB_PATH')
        ncbiToolsPath = os.path.join(packagePath, 'ncbi-blast+')

        #
        iPath = self.__getSourceWrkFile(self.__stepNo)
        iPathList = self.__getSourceWrkFileList(self.__stepNo)
        oPath = self.__getResultWrkFile(self.__stepNo)
        lPath = self.__getLogWrkFile(self.__stepNo)
        ePath = self.__getErrWrkFile(self.__stepNo)
        tPath = self.__getTmpWrkFile(self.__stepNo)
        #
        if (self.__wrkPath is not None):
            iPathFull = os.path.abspath(os.path.join(self.__wrkPath, iPath))
            ePathFull = os.path.join(self.__wrkPath, ePath)
            lPathFull = os.path.join(self.__wrkPath, lPath)
            tPathFull = os.path.join(self.__wrkPath, tPath)
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
            if (os.access(pPath, os.F_OK)):
                cmd += "; cp " + pPath + " " + iPath

        if 'db_name' in self.__inputParamDict:
            dbName = str(self.__inputParamDict['db_name'])
        else:
            dbName = "my_uniprot_all"

        if 'evalue' in self.__inputParamDict:
            eValue = str(self.__inputParamDict['evalue'])
        else:
            eValue = '0.001'

        if 'num_threads' in self.__inputParamDict:
            numThreads = str(self.__inputParamDict['num_threads'])
        else:
            numThreads = '1'

        if 'max_hits' in self.__inputParamDict:
            maxHits = str(self.__inputParamDict['max_hits'])
        else:
            maxHits = '100'

        if maxHits > 0:
            hOpt = " -num_alignments " + maxHits
        else:
            # use a large cutoff
            hOpt = " -num_alignments 10000 "

        if 'one_letter_code_sequence' in self.__inputParamDict:
            sequence = str(self.__inputParamDict['one_letter_code_sequence'])
            self.__writeFasta(iPathFull, sequence, comment="myQuery")

        cmd += " ; BLASTDB=" + os.path.abspath(seqDbPath) + " ; export BLASTDB "

        if (op == "seq-blastp"):
            #
            # $NCBI_BIN/blastp -evalue 0.001 -db $SEQUENCE_DB/$1  -num_threads 4 -query $2 -outfmt 5 -out $3
            #
            if 'db_name' in self.__inputParamDict:
                dbName = str(self.__inputParamDict['db_name'])
            else:
                dbName = "my_uniprot_all"

            cmdPath = os.path.join(ncbiToolsPath, "bin", "blastp")
            cmd += " ; " + cmdPath + " -outfmt 5  -num_threads " + numThreads + hOpt + " -evalue " + \
                eValue + " -db " + os.path.join(seqDbPath, dbName) + " -query " + iPathFull + " -out " + oPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
        elif (op == "seq-blastn"):
            # -max_target_seqs
            if 'db_name' in self.__inputParamDict:
                dbName = str(self.__inputParamDict['db_name'])
            else:
                dbName = "my_ncbi_nt"
            cmdPath = os.path.join(ncbiToolsPath, "bin", "blastn")
            cmd += " ; " + cmdPath + " -outfmt 5  -num_threads " + numThreads + hOpt + " -evalue " + \
                eValue + " -db " + os.path.join(seqDbPath, dbName) + " -query " + iPathFull + " -out " + oPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
        else:
            return -1
        #
        if (self.__debug):
            self.__lfh.write("+RcsbDpUtility._sequenceStep()  - Application string:\n%s\n" % cmd.replace(";", "\n"))
        #
        # if (self.__debug):
        #    cmd += " ; ls -la  > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath

        cmd += " ) > %s 2>&1 " % ePathFull

        cmd += " ; cat " + ePathFull + " >> " + lPathFull

        if (self.__debug):
            ofh = open(lPathFull, 'w')
            lt = time.strftime("%Y %m %d %H:%M:%S", time.localtime())
            ofh.write("\n\n-------------------------------------------------\n")
            ofh.write("LogFile:      %s\n" % lPath)
            ofh.write("Working path: %s\n" % self.__wrkPath)
            ofh.write("Date:         %s\n" % lt)
            ofh.write("\nStep command:\n%s\n-------------------------------------------------\n" % cmd.replace(";", "\n"))
            ofh.close()


        iret = self.__run(cmd, lPathFull, op)

        #iret = os.system(cmd)
        #
        return iret

    def expSize(self):
        """Return the size of the last result file...
        """
        rf = self.__getResultWrkFile(self.__stepNo)
        if (self.__wrkPath is not None):
            resultPath = os.path.join(self.__wrkPath, rf)
        else:
            resultPath = rf

        f1 = DataFile(resultPath)
        if f1.srcFileExists():
            return f1.srcFileSize()
        else:
            return 0

    def exp(self, dstPath=None):
        """Export a copy of the last result file to destination file path.
        """
        if (dstPath is not None):
            self.setDestination(dstPath)
        rf = self.__getResultWrkFile(self.__stepNo)
        if (self.__wrkPath is not None):
            resultPath = os.path.join(self.__wrkPath, rf)
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

    def expList(self, dstPathList=[]):
        """Export  copies of the list of last results to the corresponding paths
           in the destination file path list.
        """
        if (dstPathList == [] or self.__resultPathList == []):
            return
        #
        if (self.__verbose):
            self.__lfh.write("+RcsbUtility.expList dstPathList    %r\n" % dstPathList)
            self.__lfh.write("+RcsbUtility.expList resultPathList %r\n" % self.__resultPathList)
        #

        ok = True
        for f, fc in map(None, self.__resultPathList, dstPathList):
            if (self.__verbose):
                self.__lfh.write("+RcsbUtility.expList exporting %s to %s\n" % (f, fc))
            f1 = DataFile(f)
            if f1.srcFileExists():
                f1.copy(fc)
            else:
                ok = False
        return ok

    def imp(self, srcPath=None):
        """ Import a local copy of the target source file - Use the working
            directory area if this is defined.  The internal step count is reset by this operation -
        """
        if (srcPath is not None):
            self.setSource(srcPath)

        if (self.__srcPath is not None):
            if (self.__wrkPath is None):
                self.__makeTempWorkingDir()
            self.__stepNo = 0
            iPath = self.__getSourceWrkFile(self.__stepNo + 1)
            f1 = DataFile(self.__srcPath)
            wrkPath = os.path.join(self.__wrkPath, iPath)
            f1.copy(wrkPath)

    def addInput(self, name=None, value=None, type='param'):
        """ Add a named input and value to the dictionary of input parameters.
        """
        try:
            if type == 'param':
                self.__inputParamDict[name] = value
            elif type == 'file':
                self.__inputParamDict[name] = os.path.abspath(value)
            else:
                return False
            return True
        except:
            return False

    def expLog(self, dstPath=None, appendMode=True):
        """Append or copy  the current log file to destination path.
        """
        if (dstPath is not None):
            self.setLogDestination(dstPath)
        lf = self.__getLogWrkFile(self.__stepNo)
        if (self.__wrkPath is not None):
            logPath = os.path.join(self.__wrkPath, lf)
        else:
            logPath = lf
        f1 = DataFile(logPath)
        if appendMode:
            f1.append(self.__dstLogPath)
        else:
            f1.copy(self.__dstLogPath)

    def expErrLog(self, dstPath=None, appendMode=True):
        """Append a copy of the current error log file to destination error path.
        """
        if (dstPath is not None):
            self.setLogDestination(dstPath)
        lf = self.__getLogWrkFile(self.__stepNo)
        if (self.__wrkPath is not None):
            logPath = os.path.join(self.__wrkPath, lf)
        else:
            logPath = lf
        f1 = DataFile(logPath)
        if appendMode:
            f1.append(self.__dstLogPath)
        else:
            f1.copy(self.__dstLogPath)

    def expLogAll(self, dstPath=None):
        """Append all session logs to destination logfile path.
        """
        if (dstPath is not None):
            self.setLogDestination(dstPath)
        for sn in range(1, self.__stepNo + 1):
            lf = self.__getLogWrkFile(sn)
            if (self.__wrkPath is not None):
                logPath = os.path.join(self.__wrkPath, lf)
            else:
                logPath = lf
            f1 = DataFile(logPath)
            f1.append(self.__dstLogPath)

    def cleanup(self):
        """Cleanup temporary files and directories
        """
        try:
            self.__lfh.write("+RcsbDpUtility.cleanup() removing working path %s\n" % self.__wrkPath)
            shutil.rmtree(self.__wrkPath, ignore_errors=True)
            return True
        except:
            self.__lfh.write("+RcsbDpUtility.cleanup() removal failed for working path %s\n" % self.__wrkPath)

        return False

    def __writeFasta(self, filePath, sequence, comment="myquery"):
        num_per_line = 60
        l = len(sequence) / num_per_line
        x = len(sequence) % num_per_line
        m = l
        if x:
            m = l + 1

        seq = '>' + str(comment).strip() + '\n'
        for i in range(m):
            n = num_per_line
            if i == l:
                n = x
            seq += sequence[i * num_per_line:i * num_per_line + n]
            if i != (m - 1):
                seq += '\n'
        try:
            ofh = open(filePath, 'w')
            ofh.write(seq)
            ofh.close()
            return True
        except:
            if (self.__verbose):
                self.__lfh.write("+RcsbDpUtility.__writeFasta() failed for path %s\n" % filePath)
                traceback.print_exc(file=self.__lfh)

        return False

    def __nameToDictPath(self, name, suffix='.sdb'):
        """Returns the environment variable name for a particular dictionary"""
        mapping = {'archive_current': 'ARCHIVE_CURRENT',
                   'deposit': 'DEPOSIT',
                   'archive_next': 'ARCHIVE_NEXT'}
        envName = mapping[name]

        pdbxDictPath = self.__getConfigPath('SITE_PDBX_DICT_PATH')
        dictBase = self.__cI.get('SITE_PDBX_DICTIONARY_NAME_DICT')[envName]
        fName = os.path.join(pdbxDictPath, dictBase + suffix)
        return fName

    def __runTimeout(self, command, timeout, logPath=None):
        """ Execute the input command string (sh semantics) as a subprocess with a timeout.


        """
        import subprocess
        import datetime
        import os
        import time
        import signal
        import stat
        self.__lfh.write("+RcsbDpUtility.__runTimeout() - Execution time out %d (seconds)\n" % timeout)
        start = datetime.datetime.now()
        cmdfile = os.path.join(self.__wrkPath, 'timeoutscript.sh')
        ofh = open(cmdfile, 'w')
        ofh.write("#!/bin/sh\n")
        ofh.write(command)
        ofh.write("\n#\n")
        ofh.close()
        st = os.stat(cmdfile)
        os.chmod(cmdfile, st.st_mode | stat.S_IEXEC)
        self.__lfh.write("+RcsbDpUtility.__runTimeout() running command %r\n" % cmdfile)
        process = subprocess.Popen(cmdfile, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, close_fds=True, preexec_fn=os.setsid)
        while process.poll() is None:
            time.sleep(0.1)
            now = datetime.datetime.now()
            if (now - start).seconds > timeout:
                #os.kill(-process.pid, signal.SIGKILL)
                os.killpg(process.pid, signal.SIGKILL)
                os.waitpid(-1, os.WNOHANG)
                self.__lfh.write("+ERROR RcsbDpUtility.__runTimeout() Execution terminated by timeout %d (seconds)\n" % timeout)
                if logPath is not None:
                    ofh = open(logPath, 'a')
                    ofh.write("+ERROR - Execution terminated by timeout %d (seconds)\n" % timeout)
                    ofh.close()
                return None
        self.__lfh.write("+RcsbDpUtility.__runTimeout() completed with return code %r\n" % process.stdout.read())
        return 0

    def __run(self, command, lPathFull, op):

        if self.__run_remote:
            random_suffix = random.randrange(9999999)
            job_name = '{}_{}'.format(op, random_suffix)
            return RunRemote(command=command, job_name=job_name, log_dir=os.path.dirname(lPathFull),
                             timeout=self.__timeout).run()

        if self.__timeout > 0:
            return self.__runTimeout(command, self.__timeout, lPathFull).run()
        else:
            retcode = -1000
            try:
                retcode = call(command, shell=True)
                if retcode != 0:
                    self.__lfh.write("+RcsbDpUtility.__run() operation %s completed with return code %r\n" % (self.__stepOpList, retcode))
            except OSError as e:
                self.__lfh.write("+RcsbDpUtility.__run() operation %s failed  with exception %r\n" % (self.__stepOpList, str(e)))
            except:
                self.__lfh.write("+RcsbDpUtility.__run() operation %s failed  with exception\n" % self.__stepOpList)
            return retcode

    def __runP(self, cmd):
        retcode = -1000
        try:
            p1 = Popen(cmd, shell=True)
            retcode = p1.wait()
            if retcode != 0:
                self.__lfh.write("+RcsbDpUtility.__run() completed with return code %r\n" % retcode)
        except OSError as e:
            self.__lfh.write("+RcsbDpUtility.__run() failed  with exception %r\n" % str(e))
        except:
            self.__lfh.write("+RcsbDpUtility.__run() failed  with exception\n")
        return retcode


if __name__ == '__main__':
    rdpu = RcsbDpUtility()
