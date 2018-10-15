##
# File: RcsbDpUtil.py
# Date: 03-May-2007
#
# Updates:
# 05-Feb-2010 jdw Adapted for SBKB
# 08-May-2010 jdw Add log unit to constructor
# 08-May-2010 jdw Add missing environment to polymer linkage command setup.
# 03-May-2011 jdw update maxit operations 
##
"""
Wrapper class for RCSB data processing utilities.

File:    RcsbDpUtil.py
Author:  jdw
Original:  03-Mar-2007
Version: 001
Initial version - adapted from file utils method collections.


"""
import sys, os, os.path, glob, time, datetime, shutil, tempfile

from wwpdb.utils.rcsb.DataFile import DataFile
    
class RcsbDpUtil:
    """ Wrapper class for RCSB data processing utilities.
    """
    def __init__(self,rcsbPath="/rcsbapps", tmpPath="/scratch", verbose=False, log=sys.stderr):
        self.test        = " "
        self.verbose     = verbose
        self.rcsbPath    =  rcsbPath
        self.tmpPath       = tmpPath
        
        self.vout        = log
        #
        # Working directory and file path details
        self.wrkPath       = None
        self.logFile       = None
        self.resultFileList = []
        self.sourceFileList = []        

        #
        # Default resource path details

        self.appsPath     = "/lcl"
        
        self.maxitOps = ["cif2cif","cif2cif-remove","cif2cif-ebi","cif2cif-pdbx","cif-rcsb2cif-pdbx",
                         "cif-seqed2cif-pdbx", "cif2pdb","pdb2cif","pdb2cif-ebi","switch-dna",
                        "cif2pdb-assembly","pdbx2pdb-assembly","pdbx2deriv"]

        self.rcsbOps = [ "rename-atoms", "cif2pdbx", "pdbx2xml", "pdb2dssp", "pdb2stride",
                         "initial-version","poly-link-dist"]
        #
        # Source, destination and logfile path details
        self.srcPath     = None
        self.dstPath     = None
        self.dstLogPath  = None
        self.dstErrorPath  = None        
        #
        self.stepOpList  = []
        self.stepNo      = 0
        self.stepNoSaved = None
        
        self.__initPath()

    def __initPath(self):
        """Set paths that depend on top-level resource paths
        """
        self.schemaPath       = os.path.join(self.appsPath,"schema")
        
        self.ccDictPath       = os.path.join("/data/components","cc-dict")
        self.ccDictPathOdb    = os.path.join(self.ccDictPath,"Components-all-v3.sdb")
        self.ccDictPathAltOdb = os.path.join(self.ccDictPath,"Components-all-v3.sdb")
        
        self.dictPath         = os.path.join(self.appsPath,"dict-v3.2")
        self.pathDdlSdb       = os.path.join(self.dictPath,"mmcif_ddl.sdb")
        self.pathDictSdb      = os.path.join(self.dictPath,"mmcif_pdbx.sdb")
        self.pathDictOdb      = os.path.join(self.dictPath,"mmcif_pdbx.odb")        
        

    def saveResult(self):
        return(self.stepNo)
    
    def useResult(self,stepNo):
        if (stepNo > 0 and stepNo <= self.stepNo):
            self.stepNoSaved = stepNo
            if (self.verbose): 
                self.vout.write("++INFO - Using result from step %s\n" % self.stepNoSaved)        
        
    def __makeTempWorkingDir(self):
        if (self.tmpPath != None and os.path.isdir(self.tmpPath)):
            self.wrkPath = tempfile.mkdtemp('dir','rcsbDp',self.tmpPath)
        else:
            self.wrkPath = tempfile.mkdtemp('dir','rcsbDp')            

    def setRcsbAppsPath(self,fPath):
        if (fPath != None and os.path.isdir(fPath)):
            self.rcsbPath = fPath

    def setAppsPath(self,fPath):
        if (fPath != None and os.path.isdir(fPath)):
            self.appsPath = fPath
            self.__initPath()

    def setRcsbAppsPathAlt(self):
        self.setRcsbAppsPath("/rcsbapps-alt")
        self.__initPath()        
        
    def setWorkingDir(self,dPath):
        if (not os.path.isdir(path)):
            os.makedirs(path,0755)
        if (os.access(fPath,os.F_OK)):
            self.wrkPath = dPath

    def setSource(self, fPath):
        if (os.access(fPath,os.F_OK)):
            self.srcPath = fPath
        else:
            self.srcPath = None
        self.stepNo      = 0

    def setDestination(self,fPath):
        self.dstPath = fPath        

    def setErrorDestination(self,fPath):
        self.dstErrorPath = fPath

    def setLogDestination(self,fPath):
        self.dstLogPath = fPath        
        
    def op(self,op):
        if (self.srcPath == None): return

        if (self.wrkPath == None):
            self.__makeTempWorkingDir()

        self.stepOpList.append(op)
        
        if op in self.maxitOps:
            self.stepNo += 1            
            self.__maxitStep(op)
        elif op in self.rcsbOps:
            self.stepNo += 1            
            self.__rcsbStep(op)

        else:
            self.vout.write("++ERROR - Unknown operation %s\n" % op)
        

    def __getSourceWrkFileList(self,stepNo):
        """Build a file containing the current list of source files.
        """
        fn = "input_file_list_"  + str(stepNo)
        if (self.wrkPath != None):
            iPathList=os.path.join(self.wrkPath,fn)
        else:
            iPathList= fn
        #
        ofh = open(iPathList,'w')        
        if (self.sourceFileList == []):
            ofh.write("%s\n" % self.__getSourceWrkFile(self.stepNo))
        else:
            for f in self.sourceFileList == []:
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
        if (self.stepNo > 1):
            if (self.stepNoSaved != None ):
                return(self.__getResultWrkFile(self.stepNoSaved) )
                self.stepNoSaved = None
            else:
                return(self.__getResultWrkFile(self.stepNo - 1))
            
        
    def __maxitStep(self, op):
        """ Internal method that performs a single maxit operation.
        """
        #
        iPath=     self.__getSourceWrkFile(self.stepNo)
        iPathList= self.__getSourceWrkFileList(self.stepNo)
        oPath=     self.__getResultWrkFile(self.stepNo)
        lPath=     self.__getLogWrkFile(self.stepNo)
        ePath=     self.__getErrWrkFile(self.stepNo)        
        #
        if (self.wrkPath != None):
            lPathFull=os.path.join(self.wrkPath, lPath)            
            ePathFull=os.path.join(self.wrkPath, ePath)
            cmd = "(cd " + self.wrkPath
        else:
            ePathFull = ePath
            lPathFull = lPath
            cmd = "("
        #
        if (self.stepNo > 1):
            pPath = self.__updateInputPath()
            cmd += "; cp " + pPath + " "  + iPath
        #
        maxitPath   = os.path.join(self.rcsbPath,"bin","maxit")        
        maxitCmd = " ; RCSBROOT=" + self.rcsbPath 
        maxitCmd += " ; "   +  maxitPath + " -path " + self.rcsbPath


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
            cmd +=  maxitCmd + " -o 8  -standard -pdbids -no_deriv -no_pdbx_strand_id -no_site -i " + iPath
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
        if (self.verbose):            
            cmd += " ; ls -la >> " + lPath        
        #
        cmd += " ; echo '-BEGIN-PROGRAM-ERROR-LOG--------------------------\n'  >> " + lPath        
        cmd += " ; cat maxit.err >> " + lPath
        cmd += " ; echo '-END-PROGRAM-ERROR-LOG--------------------------\n'  >> " + lPath        

            
        cmd += " ; rm -f maxit.err >> " + lPath
        cmd += " ) > %s 2>&1 " % ePathFull
        
        if (self.verbose):
            self.vout.write("++INFO - Command string:\n%s\n" % cmd.replace(";","\n"))

        ofh = open(lPathFull,'w')
        lt = time.strftime("%Y %m %d %H:%M:%S", time.localtime())
        ofh.write("\n\n-------------------------------------------------\n")
        ofh.write("LogFile:      %s\n" % lPath)
        ofh.write("Working path: %s\n" % self.wrkPath)
        ofh.write("Date:         %s\n" % lt)
        if (self.verbose): ofh.write("\nStep command:\n%s\n-------------------------------------------------\n" % cmd.replace(";","\n"))
        ofh.write("\n")
        ofh.close()

        iret = os.system(cmd)
        #
        if ((op == "cif2pdb-assembly") or (op == "pdbx2pdb-assembly")):
            pat = self.wrkPath + '/*.pdb[1-9]*'
            self.resultPathList= glob.glob(pat)
        
        else:
            self.resultPathList = [os.path.join(self.wrkPath,oPath)]
        
        return iret

    def __rcsbStep(self, op):
        """ Internal method that performs a single rcsb application operation.
        """
        #
        iPath=     self.__getSourceWrkFile(self.stepNo)
        iPathList= self.__getSourceWrkFileList(self.stepNo)
        oPath=     self.__getResultWrkFile(self.stepNo)
        lPath=     self.__getLogWrkFile(self.stepNo)
        ePath=     self.__getErrWrkFile(self.stepNo)
        tPath=     self.__getTmpWrkFile(self.stepNo)        
        #
        if (self.wrkPath != None):
            ePathFull=os.path.join(self.wrkPath, ePath)
            lPathFull=os.path.join(self.wrkPath, lPath)
            tPathFull=os.path.join(self.wrkPath, tPath)                                    
            cmd = "(cd " + self.wrkPath
        else:
            ePathFull = ePath
            lPathFull = lPath
            tPathFull = tPath            
            cmd = "("
        #
        if (self.stepNo > 1):
            pPath = self.__updateInputPath()
            cmd += "; cp " + pPath + " "  + iPath
        #
        cifversionPath   = os.path.join(self.rcsbPath,"bin","cif-version")
        cifversionCmd    = " ; "   + cifversionPath 
        
        switchAtomPath   = os.path.join(self.rcsbPath,"bin","switch-atom-element")
        switchAtomCmd    = " ; "   + switchAtomPath + " -dicodb " + self.ccDictPathOdb

        cifexchPath = os.path.join(self.appsPath,"bin","cifexch-v3.2")
        cifexchCmd  = " ; " + cifexchPath + " -ddlodb " + self.pathDdlSdb +" -dicodb " + self.pathDictSdb 
        cifexchCmd += " -reorder  -strip -op in  -pdbids "

        cif2xmlPath =  os.path.join(self.appsPath,"bin","mmcif2XML")
        cif2xmlCmd  =  " ; " + cif2xmlPath + " -prefix  pdbx -ns PDBx -funct mmcif2xmlall "
        cif2xmlCmd +=  " -dict mmcif_pdbxR.dic " " -df " + self.pathDictOdb 

        pdb2dsspPath = os.path.join(self.appsPath,"bin","dssp")
        pdb2dsspCmd = " ;  " + pdb2dsspPath 

        pdb2stridePath = os.path.join(self.appsPath,"bin","stride")
        pdb2strideCmd = " ;  " + pdb2stridePath 


        polyLinkPath =os.path.join(self.rcsbPath,"bin","cal_polymer_linkage_distance")
        polyLinkCmd  = " ; " + polyLinkPath

        
        if (op == "rename-atoms"):
            cmd += switchAtomCmd + " -file " + iPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; mv -f " + iPath + ".cif " + oPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
        elif (op == "initial-version"):
            cmd += cifversionCmd + " -newfile " + iPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            cmd += " ; mv -f " + iPath + ".cif " + oPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
        elif (op == "cif2pdbx"):
            #   need to have an input file list.
            cmd += cifexchCmd + " -inlist " + iPathList
            cmd += " ; mv -f " + iPath + ".tr " + oPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath            
        elif (op == "pdbx2xml"):
            cmd += cif2xmlCmd + " -f " + iPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        

        elif (op == "pdb2dssp"):
            cmd += pdb2dsspCmd + "  " + iPath + " " + oPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath
            #  /lcl/bin/dssp ${id}.ent ${id}.dssp >&  ${id}.dssp.log
        elif (op == "pdb2stride"):
            cmd += pdb2strideCmd + " -f" + oPath + " " + iPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
            # /lcl/bin/stride -f${id}.stride  ${id}.ent >&  ${id}.stride.log
        elif (op == "poly-link-dist"):
            cmd += " ; RCSBROOT=" + self.rcsbPath + " ; export RCSBROOT "            
            cmd += polyLinkCmd + " -i " + iPath + " -o " + oPath
            cmd += " > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                        
        else:
            return -1
        #
        #
        if (self.verbose):            
            cmd += " ; ls -la  > " + tPath + " 2>&1 ; cat " + tPath + " >> " + lPath                                    
            
        cmd += " ) > %s 2>&1 " % ePathFull

        cmd += " ; echo '-BEGIN-PROGRAM-ERROR-LOG--------------------------\n'  >> " + lPathFull                
        cmd += " ; cat " + ePathFull + " >> " + lPathFull
        cmd += " ; echo '-END-PROGRAM-ERROR-LOG-------------------------\n'  >> " + lPathFull                        
        
        if (self.verbose):
            self.vout.write("++INFO - Command string:\n%s\n" % cmd.replace(";","\n"))


        ofh = open(lPathFull,'w')
        lt = time.strftime("%Y %m %d %H:%M:%S", time.localtime())
        ofh.write("\n\n-------------------------------------------------\n")
        ofh.write("LogFile:      %s\n" % lPath)
        ofh.write("Working path: %s\n" % self.wrkPath)
        ofh.write("Date:         %s\n" % lt)
        if (self.verbose): ofh.write("\nStep command:\n%s\n-------------------------------------------------\n" % cmd.replace(";","\n"))
        ofh.close()
           
        iret = os.system(cmd)
        #
        if ((op == "pdbx2xml")):
            pat = self.wrkPath + '/*.xml*'
            self.resultPathList= glob.glob(pat)
        
        else:
            self.resultPathList = [os.path.join(self.wrkPath,oPath)]
        
        return iret

    def exp(self,dstPath=None):
        """Export a copy of the last result file to destination file path.
        """
        if (dstPath != None):
            self.setDestination(dstPath)
        rf=self.__getResultWrkFile(self.stepNo)
        if (self.wrkPath != None):
            resultPath = os.path.join(self.wrkPath,rf)
        else:
            resultPath = rf

        f1 = DataFile(resultPath)
        f1.copy(self.dstPath)

    def getResultPathList(self):
        return(self.resultPathList)

    def expList(self,dstPathList=[]):
        """Export a copies of the list of last results to the corresponding paths
           in teh destination file path list.
        """
        if (dstPathList == [] or self.resultPathList == []): return
        #
        for f,fc in map(None,self.resultPathList,dstPathList):
            f1 = DataFile(f)
            f1.copy(fc)

    def imp(self,srcPath=None):
        """ Import a local copy of the target source file - Use the working
            directory area if this is defined.
        """
        if (srcPath != None):
            self.setSource(srcPath)
            
        if (self.srcPath != None):
            if (self.wrkPath == None):
                self.__makeTempWorkingDir()
            self.stepNo = 0
            iPath=self.__getSourceWrkFile(self.stepNo+1)
            f1 = DataFile(self.srcPath)
            wrkPath = os.path.join(self.wrkPath,iPath)
            f1.copy(wrkPath)

    def expLog(self,dstPath=None):
        """Append a copy of the current log file to destination path.
        """
        if (dstPath != None):
            self.setLogDestination(dstPath)
        lf=self.__getLogWrkFile(self.stepNo)
        if (self.wrkPath != None):
            logPath = os.path.join(self.wrkPath,lf)
        else:
            logPath = lf
        f1 = DataFile(logPath)
        f1.append(self.dstLogPath)

    def expErrLog(self,dstPath=None):
        """Append a copy of the current error log file to destination error path.
        """
        if (dstPath != None):
            self.setLogDestination(dstPath)
        lf=self.__getLogWrkFile(self.stepNo)
        if (self.wrkPath != None):
            logPath = os.path.join(self.wrkPath,lf)
        else:
            logPath = lf
        f1 = DataFile(logPath)
        f1.append(self.dstLogPath)

    def expLogAll(self,dstPath=None):
        """Append all session logs to destination logfile path.
        """
        if (dstPath != None):
            self.setLogDestination(dstPath)
        for sn in range(1,self.stepNo+1):
            lf=self.__getLogWrkFile(sn)
            if (self.wrkPath != None):
                logPath = os.path.join(self.wrkPath,lf)
            else:
                logPath = lf
            f1 = DataFile(logPath)
            f1.append(self.dstLogPath)


    def cleanup(self):
        """Cleanup temporary files and directories
        """
        return shutil.rmtree(self.wrkPath)

    
if __name__ == '__main__':
    unitTest4()
    
        
