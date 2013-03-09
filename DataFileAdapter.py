##
# File:    DataFileAdapter.py
# Date:    16-July-2012
#
# Updates:
#
#  4-Jan-2013 -jdw  add filters to remove derived categories after format conversion
# 12-Feb-2013  jdw  add option flags for stipping derived categories -- 
# 25-Feb-2013  jdw  add cif2pdb translation.
##
"""
Encapsulate data model format type conversions.

"""
__docformat__ = "restructuredtext en"
__author__    = "John Westbrook"
__email__     = "jwest@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.07"


import sys, os.path, shutil, traceback
from wwpdb.utils.rcsb.RcsbDpUtility       import RcsbDpUtility



class DataFileAdapter(object):
    """  Manage data model format type conversions.
        
    """
    def __init__(self,reqObj, verbose=False,log=sys.stderr):
        self.__reqObj=reqObj
        self.__verbose=verbose
        self.__lfh=log
        self.__debug=False
        self.__siteId=self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj  =self.__reqObj.getSessionObj()
        self.__sessionId=self.__sObj.getId()
        self.__sessionPath=self.__sObj.getPath()

    def rcsb2Pdbx(self,inpPath,outPath,stripFlag=False): 
        """  RCSB CIF -> PDBx conversion  (Using the smaller application in the annotation package)
        """
        try:
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose,log=self.__lfh)
            dp.imp(inpPath)
            if stripFlag:
                dp.op("annot-rcsb2pdbx-strip")
            else:
                dp.op("annot-rcsb2pdbx")

            logPath=os.path.join(self.__sessionPath,"annot-rcsb2pdbx.log")
            dp.expLog(logPath)
            dp.exp(outPath)
            if (not self.__debug):
                dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            return False
        #
        return True        

    def rcsbEps2Pdbx(self,inpPath,outPath,stripFlag=False): 
        """  RCSB CIFEPS -> PDBx conversion (This still requires using the full maxit application)
        """
        try:
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose,log=self.__lfh)
            dp.imp(inpPath)
            if stripFlag:
                dp.op("annot-rcsbeps2pdbx-strip")
            else:
                dp.op("annot-cif2cif")                

            logPath=os.path.join(self.__sessionPath,"annot-rcsbeps2pdbx.log")
            dp.expLog(logPath)
            dp.exp(outPath)
            if (not self.__debug):            
                dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            return False
        #
        return True                        

    def cif2Pdb(self,inpPath,outPath): 
        """   CIF -> PDB conversion  (Using the smaller application in the annotation package)
        """
        try:
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose,log=self.__lfh)
            dp.imp(inpPath)
            dp.op("annot-cif2pdb")
            logPath=os.path.join(self.__sessionPath,"annot-cif2pdb.log")
            dp.expLog(logPath)
            dp.exp(outPath)
            if (not self.__debug):
                dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            return False
        #
        return True        
    
    def modelConvertToPdbx(self,filePath=None,fileType='pdbx',pdbxFilePath=None):
        """ Convert input model file format to PDBx.   Converted file is stored in the session 
        directory using standard file naming.
        
        Return True for success or False otherwise.
        """
        if self.__verbose:
            self.__lfh.write("+DataFileAdapter.modelConvertToPdbx() filePath %s fileType %s pdbxFilePath %s\n" % 
                             (filePath,fileType,pdbxFilePath))
        try:
            ok =False
            if filePath is None or pdbxFilePath is None:
                return ok
            #
            if (fileType in ['pdbx-mmcif','pdbx']):
                shutil.copyfile(filePath,pdbxFilePath)
                ok=True
            elif (fileType == "rcsb-mmcif"):
                ok=self.rcsb2Pdbx(filePath,pdbxFilePath,stripFlag=False)
            elif (fileType == "rcsb-mmcif-strip"):
                ok=self.rcsb2Pdbx(filePath,pdbxFilePath,stripFlag=True)                
            elif (fileType == "rcsb-cifeps"):
                ok=self.rcsbEps2Pdbx(filePath,pdbxFilePath,stripFlag=False)
            elif (fileType == "rcsb-cifeps-strip"):
                ok=self.rcsbEps2Pdbx(filePath,pdbxFilePath,stripFlag=True)                
                #
            else:
                ok=False
            return ok
        except:
            traceback.print_exc(file=self.__lfh)
            return False
