##
#
# File:    CvsUtilityTests.py
# Author:  j. westbrook
# Date:    11-April-2011
# Version: 0.001
#
# Update:
# 12-April-2011 jdw - revision checkout test cases.
##
"""
Test cases for the CvsUtiltity module. 

"""
__docformat__ = "restructuredtext en"
__author__    = "John Westbrook"
__email__     = "jwest@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.001"

import sys, unittest, os, os.path, traceback, logging

from wwpdb.utils.rcsb.CvsUtility          import CvsWrapper

class CvsUtilityTests(unittest.TestCase):
    def setUp(self):
        self.__logger=logging.getLogger("wwpdb.utils.rcsb")        
        self.__siteId='DEV'
        self.__lfh=sys.stdout
        #
        self.__testFilePath="ligand-dict-v3/A/ATP/ATP.cif"
        self.__testDirPath="ligand-dict-v3/A/ATP/"        
        #
        self.__cvsRepositoryPath="/cvs-ligands"
        self.__cvsRepositoryHost="rcsb-cvs-1.rutgers.edu"
        self.__cvsUser="liganon3"
        self.__cvsPassword="lig1234"
        
            
    def tearDown(self):
        pass

    def testCvsHistory(self): 
        """
        """
        self.__logger.info("Starting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            text=""            
            vc = CvsWrapper(tmpPath="./")
            vc.setRepositoryPath(host=self.__cvsRepositoryHost,path=self.__cvsRepositoryPath)
            vc.setAuthInfo(user=self.__cvsUser,password=self.__cvsPassword)
            text=vc.getHistory(cvsPath=self.__testFilePath)
            self.__logger.debug("CVS history for %s is:\n%s\n" % (self.__testFilePath,text))
            #
            revList=vc.getRevisionList(cvsPath=self.__testFilePath)
            self.__logger.debug("CVS revision list for %s is:\n%r\n" % (self.__testFilePath,revList))            
            vc.cleanup()
        except:
            self.__logger.exception("Exception in %s\n"  % self.__class__.__name__)
            self.fail()


    def testCvsCheckOutFile(self): 
        """
        """
        self.__logger.info("Starting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            text=""            
            vc = CvsWrapper(tmpPath="./")
            vc.setRepositoryPath(host=self.__cvsRepositoryHost,path=self.__cvsRepositoryPath)
            vc.setAuthInfo(user=self.__cvsUser,password=self.__cvsPassword)
            text=vc.checkOutFile(cvsPath=self.__testFilePath,outPath='ATP-latest.cif')
            self.__logger.debug("CVS checkout output %s is:\n%s\n" % (self.__testFilePath,text))
            #
            vc.cleanup()
        except:
            self.__logger.exception("Exception in %s\n"  % self.__class__.__name__)
            self.fail()


    def testCvsCheckOutRevisions(self): 
        """
        """
        self.__logger.info("Starting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            text=""            
            vc = CvsWrapper(tmpPath="./")
            vc.setRepositoryPath(host=self.__cvsRepositoryHost,path=self.__cvsRepositoryPath)
            vc.setAuthInfo(user=self.__cvsUser,password=self.__cvsPassword)

            revList=vc.getRevisionList(cvsPath=self.__testFilePath)
            self.__logger.debug("CVS revision list for %s is:\n%r\n" % (self.__testFilePath,revList))            

            (pth,fn)=os.path.split(self.__testFilePath)
            (base,ext)=os.path.splitext(fn)
            
            for revId in revList:
                rId=revId[0]
                outPath=base+"-"+rId+"."+ext
                text=vc.checkOutFile(cvsPath=self.__testFilePath,outPath=outPath,revId=rId)
                self.__logger.debug("CVS checkout output %s is:\n%s\n" % (self.__testFilePath,text))
            #
            vc.cleanup()
        except:
            self.__logger.exception("Exception in %s\n"  % self.__class__.__name__)
            self.fail()


    def suite():
        return unittest.makeSuite(CvsUtilityTests,'test')

if __name__ == '__main__':
    logger=logging.getLogger("wwpdb.utils.rcsb")
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler("CvsUtilityTests.log")
    fh.setLevel(logging.DEBUG)
    formatter= logging.Formatter("%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    #
    unittest.main()

