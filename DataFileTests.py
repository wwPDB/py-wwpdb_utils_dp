"""

File:    DataFileTests.py
Author:  jdw
Date:    21-Aug-2009
Version: 0.001

"""
import sys, unittest, os, os.path, traceback

from wwpdb.api.facade.ConfigInfo          import ConfigInfo
from wwpdb.utils.rcsb.DataFile            import DataFile



class DataFileTests(unittest.TestCase):
    def setUp(self):
        cI=ConfigInfo('DEV')
        self.__testFilePath=cI.get('TEST_FILE_PATH')
        self.__testFile=cI.get('TEST_FILE')
        self.__testFileGzip=cI.get('TEST_FILE_GZIP')
        self.__testFileZlib=cI.get('TEST_FILE_ZLIB')
        self.__testFileBzip=cI.get('TEST_FILE_BZIP')
        self.__outPath=cI.get('TMP_PATH')
        self.__outFileList = ["OUTPUT.dat.gz","OUTPUT.dat","OUTPUT.dat.bz2","OUTPUT.dat.Z"]        
        self.lfh=sys.stdout
            
    def tearDown(self):
        pass

    def testPrintInfo(self): 
        """
        """
        self.lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            fPath=os.path.join(self.__testFilePath,self.__testFile)
            f1 = DataFile(fPath)
            f1.pr(self.lfh)            
        except:
            traceback.print_exc(file=sys.stdout)
            self.fail()

    def testCopyTimeModePreserve(self):
        self.lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            fPath=os.path.join(self.__testFilePath,self.__testFile)
            f1 = DataFile(fPath)
            f1.pr(self.lfh)
            #
            f1.timeMode("preserve")
            for fn in self.__outFileList:
                fp=os.path.join(self.__outPath,fn)
                f1.copy(fp)
                f1.pr(self.lfh)
                self.lfh.write("Files are the same  = %s\n" %  str(f1.compare()))
                self.lfh.write("Source newer than %s\n" % f1.newerThan(fp))
                f2=DataFile(fp)
                if (f2.srcFileExists()): f2.remove()
        except:
            traceback.print_exc(file=sys.stdout)
            self.fail()                

    def testCopyTimeModeToday(self):
        self.lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:        
            fPath=os.path.join(self.__testFilePath,self.__testFile)
            f1 = DataFile(fPath)
            f1.pr(self.lfh)
            #
            f1.timeMode("today")
            for fn in self.__outFileList:
                fp=os.path.join(self.__outPath,fn)
                f1.copy(fp)
                f1.pr(self.lfh)            
                self.lfh.write("Files are the same  = %s\n" % str(f1.compare()))
                self.lfh.write("Source newer than %s\n" % f1.newerThan(fp))
                f2=DataFile(fp)
                if (f2.srcFileExists()): f2.remove()
        except:
            traceback.print_exc(file=sys.stdout)
            self.fail()                                

    def testCopyTimeModeNone(self):
        self.lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:                
            fPath=os.path.join(self.__testFilePath,self.__testFile)
            f1 = DataFile(fPath)
            f1.pr(self.lfh)
            #
            f1.timeMode(None)
            for fn in self.__outFileList:
                fp=os.path.join(self.__outPath,fn)
                f1.copy(fp)
                f1.pr(self.lfh)                        
                self.lfh.write("Files are the same  = %s\n" %  str(f1.compare()))
                self.lfh.write("Source newer than %s\n" % str(f1.newerThan(fp)))
                f2=DataFile(fp)
                if (f2.srcFileExists()): f2.remove()
        except:
            traceback.print_exc(file=sys.stdout)
            self.fail()                                                
                           
                         
    def testSymbolicLinks(self):
        self.lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:                        
            fList=[self.__testFile,self.__testFileGzip, self.__testFileZlib, self.__testFileBzip]
            for fn in fList:
                fPath=os.path.join(self.__testFilePath,fn)            
                f1 = DataFile(fPath)
                fp=os.path.join(self.__outPath,fn)        
                f1.symLinkRelative(fp)
                f1.pr()
                self.lfh.write("Files are the same  = %s\n" %  str(f1.compare()))
                self.lfh.write("Source newer than %s\n" % str(f1.newerThan(fp)))            
                f2=DataFile(fp)
                if (f2.srcFileExists()): f2.remove()
        except:
            traceback.print_exc(file=sys.stdout)
            self.fail()                                                
                

    def testFileEMail(self):
        self.lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))        
        try:                        
            fPath=os.path.join(self.__testFilePath,self.__testFile)
            f1 = DataFile(fPath)
            f1.eMail("jwest@rcsb.rutgers.edu","jwest@rcsb.rutgers.edu","IGNORE THIS TEST MESSAGE")
        except:
            traceback.print_exc(file=sys.stdout)
            self.fail()                                                

    def suite():
        return unittest.makeSuite(DataFileTests,'test')

if __name__ == '__main__':
    unittest.main()
