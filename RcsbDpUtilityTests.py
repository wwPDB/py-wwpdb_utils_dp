##
#
# File:    RcsbDpUtilityTests.py
# Author:  j. westbrook
# Date:    9-Sep-2010
# Version: 0.001
#
# Update:
#  Sep 10, 2010 jdw -  Added test cases for chemical component applications.
#                      Cleaned up error reporting .
#  Jun 23, 2011 jdw -  Update examples -- verify configuration --  site_id = WWPDB_DEV tested
#  Apr 15, 2012 jdw -  Add PISA application tasks
##
"""
Test cases from 

"""

import sys, unittest, os, os.path, traceback

from wwpdb.api.facade.ConfigInfo          import ConfigInfo,getSiteId
from wwpdb.utils.rcsb.DataFile            import DataFile
from wwpdb.utils.rcsb.RcsbDpUtility       import RcsbDpUtility


class RcsbDpUtilityTests(unittest.TestCase):
    def setUp(self):
        # Pick up site information from the environment or failover to the development site id.
        self.__siteId=getSiteId(defaultSiteId='WWPDB_DEV_TEST')
        self.__lfh.write("\nTesting with site environment for:  %s\n" % self.__siteId)
        #
        cI=ConfigInfo(self.__siteId)
        self.__testFilePath    =cI.get('DP_TEST_FILE_PATH')
        self.__testFileCif     =cI.get('DP_TEST_FILE_CIF')
        self.__testFileCifEps1 =cI.get('DP_TEST_FILE_CIFEPS')
        self.__testFileCifEps2 =cI.get('DP_TEST_FILE_CIFEPS_2')
        #self.__tmpPath        =cI.get('TMP_PATH')
        self.__tmpPath         = './rcsb-tmp-dir'
        #
        self.__testFilePdbPisa    =cI.get('DP_TEST_FILE_PDB_PISA')
        self.__testFileCifPisa    =cI.get('DP_TEST_FILE_CIF_PISA')                
        
        self.__lfh=sys.stderr
            
    def tearDown(self):
        pass

    def testCifToPdb(self): 
        """
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath,siteId=self.__siteId,verbose=True)
            cifPath=os.path.join(self.__testFilePath,self.__testFileCif)
            dp.imp(cifPath)
            dp.op("cif2pdb")
            dp.exp("myTest1.pdb.gz")
            dp.expLog("myLog1.log.gz")    
            #dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testCifEpsToPdb(self): 
        """
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            cifPath=os.path.join(self.__testFilePath,self.__testFileCifEps1)
            dp.imp(cifPath)
            dp.op("cif2pdb")
            dp.exp("myTest2.pdb.gz")
            dp.expLog("myLog2.log.gz")    
            #dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testChemCompAssign(self): 
        """   Test with no links
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath,siteId=self.__siteId,verbose=True)
            dp.setWorkingDir('tmp-assign')
            cifPath=os.path.join(self.__testFilePath,self.__testFileCifEps2)
            (head,tail) = os.path.split(cifPath)
            (id,ext) = os.path.splitext(tail)
            link_file_path=os.path.join(self.__testFilePath,id+"-cc-link.cif")
            dp.addInput(name="id",value=id)
            dp.addInput(name="cc_link_file_path",value=link_file_path,type='file')
            dp.imp(cifPath)
            dp.op("chem-comp-assign")
            dp.exp("chem-comp-assign.cif.gz")
            dp.expLog("chem-comp-assign.log.gz")
            dp.cleanup()

        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testChemCompInstanceUpdate(self): 
        """   Test with no links
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath,siteId=self.__siteId,verbose=True)
            dp.setWorkingDir('tmp-update')
            cifPath=os.path.join(self.__testFilePath,self.__testFileCifEps2)
            (head,tail) = os.path.split(cifPath)
            (id,ext) = os.path.splitext(tail)
            assign_file_path=os.path.join(self.__testFilePath,id+"-cc-assign.cif")
            dp.addInput(name="cc_assign_file_path",value=assign_file_path,type='file')
            dp.imp(cifPath)
            dp.op("chem-comp-instance-update")
            dp.exp(id+"-cc-instance-update.cif.gz")
            dp.expLog("chem-comp-update.log.gz")
            dp.cleanup()

        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testChemCompLink(self): 
        """
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath,siteId=self.__siteId,verbose=True)
            cifPath=os.path.join(self.__testFilePath,self.__testFileCifEps2)
            dp.imp(cifPath)
            dp.op("chem-comp-link")
            dp.exp("chem-comp-link.cif.gz")
            dp.expLog("chem-comp-link.log.gz")    
            dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()


    def testPisaAnalysis(self): 
        """
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            pdbPath=os.path.join(self.__testFilePath,self.__testFilePdbPisa)
            dp.imp(pdbPath)
            dp.addInput(name="pisa_session_name",value="session_3re3")
            dp.op("pisa-analysis")
            dp.expLog("pisa-anal.log.gz")
            dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testPisaAssemblyReportXml(self): 
        """
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            pdbPath=os.path.join(self.__testFilePath,self.__testFilePdbPisa)
            dp.imp(pdbPath)
            dp.addInput(name="pisa_session_name",value="session_3re3")            
            dp.op("pisa-analysis")
            dp.expLog("pisa-anal-assembly.log.gz")                        
            dp.op("pisa-assembly-report-xml")
            dp.exp("pisa-assembly-report.xml")
            dp.expLog("pisa-report-xml.log.gz")                                    
            dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testPisaAssemblyDownloadModel(self): 
        """
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            pdbPath=os.path.join(self.__testFilePath,self.__testFilePdbPisa)
            dp.imp(pdbPath)
            dp.addInput(name="pisa_session_name",value="session_3re3")            
            dp.op("pisa-analysis")
            dp.expLog("pisa-anal-assembly.log.gz")                        
            dp.op("pisa-assembly-report-xml")
            dp.exp("pisa-assembly-report.xml")
            dp.expLog("pisa-report-xml.log.gz")
            #
            for assemId in ['1','2','3','4','5']:
                dp.addInput(name="pisa_assembly_id",value=assemId)
                oFileName='3rer-assembly-'+assemId+'.pdb.gz'
                oLogName='3rer-assembly-'+assemId+'.log.gz'                
                dp.op("pisa-assembly-coordinates-pdb")
                dp.exp(oFileName)
                dp.expLog(oLogName)
            dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testPisaAssemblyMergeModel(self): 
        """
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            pdbPath=os.path.join(self.__testFilePath,self.__testFilePdbPisa)
            dp.imp(pdbPath)
            dp.addInput(name="pisa_session_name",value="session_3re3")            
            dp.op("pisa-analysis")
            dp.op("pisa-assembly-report-xml")
            dp.exp("pisa-assembly-report.xml")
            #
            cifPath=os.path.join(self.__testFilePath,self.__testFileCifPisa)
            dp.imp(cifPath)
            dp.addInput(name="pisa_assembly_tuple_list",value="0:0,1:0,1:1,2:0")
            dp.addInput(name="pisa_assembly_file_path",value="pisa-assembly-report.xml",type="file")
            dp.op("pisa-assembly-merge-cif")
            dp.exp("3rer-updated.cif.gz")
            dp.expLog("3rer-updated.log.gz")
            #dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()



def suiteMaxitTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityTests("testCifEpsToPdb"))
    suiteSelect.addTest(RcsbDpUtilityTests("testCifToPdb"))
    return suiteSelect

def suiteChemCompTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityTests("testChemCompLink"))
    suiteSelect.addTest(RcsbDpUtilityTests("testChemCompInstanceUpdate"))
    suiteSelect.addTest(RcsbDpUtilityTests("testChemCompAssign"))
    return suiteSelect    

def suitePisaTests():
    suiteSelect = unittest.TestSuite()
    #suiteSelect.addTest(RcsbDpUtilityTests("testPisaAnalysis"))
    #suiteSelect.addTest(RcsbDpUtilityTests("testPisaAssemblyReportXml"))
    #suiteSelect.addTest(RcsbDpUtilityTests("testPisaAssemblyDownloadModel"))
    suiteSelect.addTest(RcsbDpUtilityTests("testPisaAssemblyMergeModel"))    
    
    return suiteSelect    
    
if __name__ == '__main__':
    # Run all tests -- 
    # unittest.main()
    #
    #mySuite=suiteMaxitTests()
    #unittest.TextTestRunner(verbosity=2).run(mySuite)
    #
    #mySuite=suiteChemCompTests()
    #unittest.TextTestRunner(verbosity=2).run(mySuite)
    #
    mySuite=suitePisaTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)    
