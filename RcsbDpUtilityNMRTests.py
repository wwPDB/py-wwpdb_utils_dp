##
#
# File:    RcsbDpUtilityNMRTests.py
# Author:  J. Westbrook
# Date:    Sept 12,2014
# Version: 0.001
#
# Updates:
##
"""
Test cases for reading, concatenating and obtaining diagnostics about chemical shift files -- 

"""

import sys, unittest, os, os.path, traceback

from wwpdb.api.facade.ConfigInfo          import ConfigInfo,getSiteId
from wwpdb.utils.rcsb.RcsbDpUtility       import RcsbDpUtility

from wwpdb.utils.rcsb.PdbxChemShiftReport import PdbxChemShiftReport



class RcsbDpUtilityNMRTests(unittest.TestCase):
    def setUp(self):
        self.__lfh=sys.stderr        
        self.__verbose=True   
        # Pick up site information from the environment or failover to the development site id.
        self.__siteId=getSiteId(defaultSiteId='WWPDB_DEPLOY_TEST')
        self.__lfh.write("\nTesting with site environment for:  %s\n" % self.__siteId)
        #
        self.__tmpPath         = './rcsb-tmp-dir'        
        cI=ConfigInfo(self.__siteId)
        
        self.__testFilePath       = './data'
        #
        self.__testFileStarCs    = '2MMZ_cs.str'
        self.__testFileNmrModel  = '2MMZ.cif'
        self.__testFileNmrModelAlt = '1MM0.cif'
        self.__testFileNmrMr     = '2MMZ.mr'
        self.__testConcatCS      = '2mmz-cs-file-full-2.cif'
        
        #

    def tearDown(self):
        pass


    def testAnnotCSCheck(self): 
        """  Test CS file check
                             'nmr-cs-check-report'         :  (['html'], 'nmr-cs-check-report'),
                             'nmr-cs-xyz-check-report'     :  (['html'], 'nmr-cs-xyz-check-report'),
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of="cs-file-check.html"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath=os.path.join(self.__testFilePath,self.__testFileStarCs)
            dp.imp(inpPath)
            dp.op("annot-chem-shift-check")
            dp.expLog("annot-cs-file-check.log")
            dp.exp(of)            
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()


    def testAnnotCSCoordCheck(self): 
        """  Test CS + Coordindate file check
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of="cs-coord-file-check.html"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath=os.path.join(self.__testFilePath,self.__testFileStarCs)
            #
            xyzPath=os.path.abspath(os.path.join(self.__testFilePath,self.__testFileNmrModel))
            dp.imp(inpPath)
            dp.addInput(name="coordinate_file_path",value=xyzPath)            
            dp.op("annot-chem-shift-coord-check")
            dp.expLog("annot-cs-coord-file-check.log")
            dp.exp(of)            
            #dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testUploadShiftOneCheck(self): 
        """  Test upload check of one CS file  ---   upload single file 
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            dp.setDebugMode(flag=True)
            inpPath=os.path.join(self.__testFilePath,self.__testFileStarCs)
            outPath="output-cs-file-full.cif"            
            chkPath="cs-diag-upload-check-1.cif"           
            dp.addInput(name="chemical_shifts_file_path_list",value=[inpPath])            
            dp.addInput(name="chemical_shifts_auth_file_name_list",value=['cs_file_1'])            
            dp.addInput(name="chemical_shifts_upload_check_file_path",value=chkPath)

            dp.op("annot-chem-shifts-upload-check")
            dp.expLog("annot-chem-shifts-upload-check.log")
            dp.exp(outPath)            
            #dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()


    def testUploadShiftListCheck(self): 
        """  Test upload check of one CS file  ---  Upload multiple files
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            dp.setDebugMode(flag=True)
            inpPath=os.path.join(self.__testFilePath,self.__testFileStarCs)
            outPath="output-cs-file-full-2.cif" 
            chkPath="cs-diag-upload-check-2.cif"           
            dp.addInput(name="chemical_shifts_file_path_list",value=[inpPath,inpPath])            
            dp.addInput(name="chemical_shifts_auth_file_name_list",value=['cs_file_1','cs_file_2'])            
            dp.addInput(name="chemical_shifts_upload_check_file_path",value=chkPath)

            dp.op("annot-chem-shifts-upload-check")
            dp.expLog("annot-chem-shifts-upload-check-2.log")
            dp.exp(outPath)            
            #dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testChemicalShiftCoordinateCheck(self): 
        """  Test upload check of one CS file  ---   Using a PDB Archive STAR file -- (Does not work)
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            dp.setDebugMode(flag=True)
            inpPath=os.path.join(self.__testFilePath,self.__testFileStarCs)
            xyzPath=os.path.abspath(os.path.join(self.__testFilePath,self.__testFileNmrModel))
            outPath="output-cs-file.cif"
            chkPath="cs-diag-atom-name-check.cif"
            dp.imp(inpPath)
            dp.addInput(name="coordinate_file_path",value=xyzPath)
            dp.addInput(name="chemical_shifts_coord_check_file_path",value=chkPath)

            dp.op("annot-chem-shifts-atom-name-check")
            dp.expLog("annot-chem-shifts-atom-name-check.log")
            dp.exp(outPath)            
            #dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testChemicalShiftCoordinateCheck2(self): 
        """  Test upload check of one CS file  ---  Using a processed chemical shift file 
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            dp.setDebugMode(flag=True)
            inpPath=os.path.join(self.__testFilePath,self.__testConcatCS)
            xyzPath=os.path.abspath(os.path.join(self.__testFilePath,self.__testFileNmrModel))
            outPath="output-cs-file-concat.cif"
            chkPath="cs-diag-atom-name-check-concat.cif"
            dp.imp(inpPath)
            dp.addInput(name="coordinate_file_path",value=xyzPath)
            dp.addInput(name="chemical_shifts_coord_check_file_path",value=chkPath)

            dp.op("annot-chem-shifts-atom-name-check")
            dp.expLog("annot-chem-shifts-atom-name-check-concat.log")
            dp.exp(outPath)            
            #dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testChemicalShiftCoordinateCheck2Alt(self): 
        """  Test upload check of one CS file  --- Using the wrong model to generate errors 
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            dp.setDebugMode(flag=True)
            inpPath=os.path.join(self.__testFilePath,self.__testConcatCS)
            xyzPath=os.path.abspath(os.path.join(self.__testFilePath,self.__testFileNmrModelAlt))
            outPath="output-cs-file-concat-alt.cif"
            chkPath="cs-diag-atom-name-check-concat-alt.cif"
            dp.imp(inpPath)
            dp.addInput(name="coordinate_file_path",value=xyzPath)
            dp.addInput(name="chemical_shifts_coord_check_file_path",value=chkPath)

            dp.op("annot-chem-shifts-atom-name-check")
            dp.expLog("annot-chem-shifts-atom-name-check-concat-alt.log")
            dp.exp(outPath)     
            #
            csr=PdbxChemShiftReport(inputPath=chkPath,verbose=self.__verbose,log=self.__lfh)
            status=csr.getStatus()
            self.__lfh.write("Status code: %s\n" % status)
            warnings=csr.getWarnings()
            self.__lfh.write("\n\nWarning count : %d\n %s\n" % (len(warnings), ('\n').join(warnings) ))
            #
            errors=csr.getErrors()
            self.__lfh.write("\n\nError count : %d\n %s\n" % (len(errors), ('\n').join(errors)))
            #
            #dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()


def suiteAnnotBmrbNmrTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityNMRTests("testAnnotCSCheck"))
    suiteSelect.addTest(RcsbDpUtilityNMRTests("testAnnotCSCoordCheck"))
    return suiteSelect        


def suiteAnnotNmrTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityNMRTests("testUploadShiftOneCheck"))
    suiteSelect.addTest(RcsbDpUtilityNMRTests("testUploadShiftListCheck"))
    suiteSelect.addTest(RcsbDpUtilityNMRTests("testChemicalShiftCoordinateCheck"))
    suiteSelect.addTest(RcsbDpUtilityNMRTests("testChemicalShiftCoordinateCheck2"))
    suiteSelect.addTest(RcsbDpUtilityNMRTests("testChemicalShiftCoordinateCheck2Alt"))

    return suiteSelect        



if __name__ == '__main__':
    #
    doAll=False
    if (doAll):
        mySuite=suiteAnnotBmrbNmrTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)    


    else:
        pass
    mySuite=suiteAnnotNmrTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)    

