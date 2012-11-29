##
#
# File:    CvsAdminTests.py
# Author:  j. westbrook
# Date:    11-April-2011
# Version: 0.001
#
# Update:
# 12-April-2011 jdw - revision checkout test cases.
##
"""
Test cases for the CvsAdmin module. 

"""
__docformat__ = "restructuredtext en"
__author__    = "John Westbrook"
__email__     = "jwest@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.001"

import sys, unittest, os, os.path, traceback, logging, shutil

from wwpdb.utils.rcsb.CvsAdmin          import CvsAdmin,CvsSandBoxAdmin

class CvsAdminTests(unittest.TestCase):
    def setUp(self):
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
        self.__realProjectName="prd-v3"                
        self.__testProjectName="test-project-v1"
        self.__testFilePath=os.path.abspath("./data/TEST-FILE.DAT")
            
    def tearDown(self):
        pass

    def testCvsHistory(self): 
        """
        """
        self.__lfh.write("Starting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            text=""            
            vc = CvsAdmin(tmpPath="./")
            vc.setRepositoryPath(host=self.__cvsRepositoryHost,path=self.__cvsRepositoryPath)
            vc.setAuthInfo(user=self.__cvsUser,password=self.__cvsPassword)
            text=vc.getHistory(cvsPath=self.__testFilePath)
            self.__lfh.write("CVS history for %s is:\n%s\n" % (self.__testFilePath,text))
            #
            revList=vc.getRevisionList(cvsPath=self.__testFilePath)
            self.__lfh.write("CVS revision list for %s is:\n%r\n" % (self.__testFilePath,revList))            
            vc.cleanup()
        except:
            self.__lfh.write("Exception in %s\n"  % self.__class__.__name__)
            traceback.print_exc(file=self.__lfh)            
            self.fail()

    def testCvsCheckOutFile(self): 
        """
        """
        self.__lfh.write("Starting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            text=""            
            vc = CvsAdmin(tmpPath="./")
            vc.setRepositoryPath(host=self.__cvsRepositoryHost,path=self.__cvsRepositoryPath)
            vc.setAuthInfo(user=self.__cvsUser,password=self.__cvsPassword)
            text=vc.checkOutFile(cvsPath=self.__testFilePath,outPath='ATP-latest.cif')
            self.__lfh.write("CVS checkout output %s is:\n%s\n" % (self.__testFilePath,text))
            #
            vc.cleanup()
        except:
            self.__lfh.write("Exception in %s\n"  % self.__class__.__name__)
            traceback.print_exc(file=self.__lfh)            
            self.fail()


    def testCvsCheckOutRevisions(self): 
        """
        """
        self.__lfh.write("Starting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            text=""            
            vc = CvsAdmin(tmpPath="./")
            vc.setRepositoryPath(host=self.__cvsRepositoryHost,path=self.__cvsRepositoryPath)
            vc.setAuthInfo(user=self.__cvsUser,password=self.__cvsPassword)

            revList=vc.getRevisionList(cvsPath=self.__testFilePath)
            self.__lfh.write("CVS revision list for %s is:\n%r\n" % (self.__testFilePath,revList))            

            (pth,fn)=os.path.split(self.__testFilePath)
            (base,ext)=os.path.splitext(fn)
            
            for revId in revList:
                rId=revId[0]
                outPath=base+"-"+rId+"."+ext
                text=vc.checkOutFile(cvsPath=self.__testFilePath,outPath=outPath,revId=rId)
                self.__lfh.write("CVS checkout output %s is:\n%s\n" % (self.__testFilePath,text))
            #
            vc.cleanup()
        except:
            self.__lfh.write("Exception in %s\n"  % self.__class__.__name__)
            traceback.print_exc(file=self.__lfh)            
            self.fail()


    def testCvsCheckOutProject(self): 
        """
        """
        self.__lfh.write("Starting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            text=""            
            vc = CvsSandBoxAdmin(tmpPath="./")
            vc.setRepositoryPath(host=self.__cvsRepositoryHost,path=self.__cvsRepositoryPath)
            vc.setAuthInfo(user=self.__cvsUser,password=self.__cvsPassword)
            #
            vc.setSandBoxTopPath("./CVSWORK")
            text=vc.checkOut(projectPath=self.__testProjectName)
            self.__lfh.write("CVS checkout output is:\n%s\n" % text)
            #
            vc.cleanup()
        except:
            self.__lfh.write("Exception in %s\n"  % self.__class__.__name__)
            traceback.print_exc(file=self.__lfh)
            self.fail()


    def testCvsUpdateProject(self): 
        """
        """
        self.__lfh.write("Starting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            text=""            
            vc = CvsSandBoxAdmin(tmpPath="./")
            vc.setRepositoryPath(host=self.__cvsRepositoryHost,path=self.__cvsRepositoryPath)
            vc.setAuthInfo(user=self.__cvsUser,password=self.__cvsPassword)
            #
            vc.setSandBoxTopPath("./CVSWORK")
            text=vc.update(projectPath=self.__testProjectName)
            self.__lfh.write("CVS update output is:\n%s\n" % text)
            #
            vc.cleanup()
        except:
            self.__lfh.write("Exception in %s\n"  % self.__class__.__name__)
            traceback.print_exc(file=self.__lfh)
            self.fail()


    def testCvsAddCommit(self): 
        """
        """
        self.__lfh.write("Starting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            text=""            
            vc = CvsSandBoxAdmin(tmpPath="./")
            vc.setRepositoryPath(host=self.__cvsRepositoryHost,path=self.__cvsRepositoryPath)
            vc.setAuthInfo(user=self.__cvsUser,password=self.__cvsPassword)
            #
            vc.setSandBoxTopPath("./CVSWORK")
            text=vc.checkOut(projectPath=self.__testProjectName)
            self.__lfh.write("CVS update output is:\n%s\n" % text)
            #
            projPath=os.path.join(vc.getSandBoxTopPath(),self.__testProjectName)
            dstDir="D1"
            dstPath=os.path.join(projPath,dstDir)
            if not os.access(dstPath,os.F_OK):
                os.mkdir(dstPath)
            fPath1=os.path.join(dstPath,"F1.DAT")
            shutil.copy2(self.__testFilePath,fPath1)
            fPath2=os.path.join(dstPath,"F2.DAT")
            shutil.copy2(self.__testFilePath,fPath2)
            #
            vc.add(self.__testProjectName,dstDir)
            
            rPath1=os.path.join(dstDir,"F1.DAT")
            rPath2=os.path.join(dstDir,"F2.DAT")            
            vc.add(self.__testProjectName,rPath1)
            vc.add(self.__testProjectName,rPath2)            
            #
            vc.remove(self.__testProjectName,rPath2)
            vc.remove(self.__testProjectName,rPath1)
            vc.remove(self.__testProjectName,dstDir)
            
            vc.update(projectPath=self.__testProjectName,prune=True)            
            #
            vc.cleanup()
        except:
            self.__lfh.write("Exception in  %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))            
            traceback.print_exc(file=self.__lfh)
            self.fail()



def suiteCvsTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(CvsAdminTests("testCvsHistory"))
    suiteSelect.addTest(CvsAdminTests("testCvsCheckOutRevisions"))
    suiteSelect.addTest(CvsAdminTests("testCvsCheckOutFile"))        
    return suiteSelect

def suiteCvsSandBoxTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(CvsAdminTests("testCvsCheckOutProject"))
    suiteSelect.addTest(CvsAdminTests("testCvsUpdateProject"))
    suiteSelect.addTest(CvsAdminTests("testCvsAddCommit"))                
    return suiteSelect


if __name__ == '__main__':
    #mySuite=suiteCvsTests()
    #unittest.TextTestRunner(verbosity=2).run(mySuite)
    #
    mySuite=suiteCvsSandBoxTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)
