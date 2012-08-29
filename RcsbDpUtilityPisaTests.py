##
#
# File:    RcsbDpUtilityPisaTests.py
# Author:  J. Westbrook
# Date:    June 20,2012
# Version: 0.001
#
# Update:
#   28-Aug-2012  jdw   test with latest tools deployment using site_id WWPDB_DEPLOY_TEST
##
"""
Test cases for assembly calculation using both PDBx/mmCIF and PDB form input data files - 

"""

import sys, unittest, os, os.path, traceback

from wwpdb.api.facade.ConfigInfo          import ConfigInfo,getSiteId
from wwpdb.utils.rcsb.DataFile            import DataFile
from wwpdb.utils.rcsb.RcsbDpUtility       import RcsbDpUtility


class RcsbDpUtilityTests(unittest.TestCase):
    def setUp(self):
        self.__lfh=sys.stderr        
        # Pick up site information from the environment or failover to the development site id.
        self.__siteId=getSiteId(defaultSiteId='WWPDB_DEV_TEST')
        self.__lfh.write("\nTesting with site environment for:  %s\n" % self.__siteId)
        #
        cI=ConfigInfo(self.__siteId)
        self.__testFilePath    =cI.get('DP_TEST_FILE_PATH')

        #self.__testFileCif     =cI.get('DP_TEST_FILE_CIF')
        #self.__testFileCifEps1 =cI.get('DP_TEST_FILE_CIFEPS')
        #self.__testFileCifEps2 =cI.get('DP_TEST_FILE_CIFEPS_2')
        #self.__tmpPath        =cI.get('TMP_PATH')
        
        self.__tmpPath         = './rcsb-tmp-dir'
        #
        self.__testFilePdbPisa    =cI.get('DP_TEST_FILE_PDB_PISA')
        self.__testFileCifPisa    =cI.get('DP_TEST_FILE_CIF_PISA')
        #
        self.__lfh.write("\nTest file path %s\n" % (self.__testFilePath))
        self.__lfh.write("\nCIF  file path %s\n" % (self.__testFileCifPisa))
            
    def tearDown(self):
        pass

    def testPisaAnalysisPdb(self): 
        """
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            pdbPath=os.path.join(self.__testFilePath,self.__testFilePdbPisa)
            dp.imp(pdbPath)
            dp.addInput(name="pisa_session_name",value="session_3re3_pdb")
            dp.op("pisa-analysis")
            dp.expLog("pisa-anal-pdb.log.gz")
            dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testPisaAnalysisCif(self): 
        """
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            cifPath=os.path.join(self.__testFilePath,self.__testFileCifPisa)
            dp.imp(cifPath)
            dp.addInput(name="pisa_session_name",value="session_3re3_cif")
            dp.op("pisa-analysis")
            dp.expLog("pisa-anal-cif.log.gz")
            dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testPisaAssemblyReportXmlCif(self): 
        """
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            fPath=os.path.join(self.__testFilePath,self.__testFileCifPisa)
            dp.imp(fPath)
            dp.addInput(name="pisa_session_name",value="session_3re3_cif")            
            dp.op("pisa-analysis")
            dp.expLog("pisa-anal-assembly-cif.log.gz")                        
            dp.op("pisa-assembly-report-xml")
            dp.exp("pisa-assembly-report-cif.xml")
            dp.expLog("pisa-report-xml-cif.log.gz")                                    
            dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testPisaAssemblyReportXmlPdb(self): 
        """
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            fPath=os.path.join(self.__testFilePath,self.__testFilePdbPisa)
            dp.imp(fPath)
            dp.addInput(name="pisa_session_name",value="session_3re3_cif")            
            dp.op("pisa-analysis")
            dp.expLog("pisa-anal-assembly-pdb.log.gz")                        
            dp.op("pisa-assembly-report-xml")
            dp.exp("pisa-assembly-report-pdb.xml")
            dp.expLog("pisa-report-xml-pdb.log.gz")                                    
            dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()


    def testPisaAssemblyDownloadModelCif(self): 
        """
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            fPath=os.path.join(self.__testFilePath,self.__testFileCifPisa)
            dp.imp(fPath)
            dp.addInput(name="pisa_session_name",value="session_3re3_cif")            
            dp.op("pisa-analysis")
            dp.expLog("pisa-anal-assembly-cif.log.gz")                        
            dp.op("pisa-assembly-report-xml")
            dp.exp("pisa-assembly-report-cif.xml")
            dp.expLog("pisa-report-xml-cif.log.gz")
            #
            for assemId in ['1','2','3','4','5']:
                dp.addInput(name="pisa_assembly_id",value=assemId)
                oFileName='3rer-assembly-'+assemId+'.cif.gz'
                oLogName='3rer-assembly-'+assemId+'-cif.log.gz'                
                dp.op("pisa-assembly-coordinates-cif")
                dp.exp(oFileName)
                dp.expLog(oLogName)
            dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()


    def testPisaAssemblyDownloadModelPdb(self): 
        """
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            fPath=os.path.join(self.__testFilePath,self.__testFileCifPisa)
            dp.imp(fPath)
            dp.addInput(name="pisa_session_name",value="session_3re3_cif")            
            dp.op("pisa-analysis")
            dp.expLog("pisa-anal-assembly-cif.log.gz")                        
            dp.op("pisa-assembly-report-xml")
            dp.exp("pisa-assembly-report-cif.xml")
            dp.expLog("pisa-report-xml-cif.log.gz")
            #
            for assemId in ['1','2','3','4','5']:
                dp.addInput(name="pisa_assembly_id",value=assemId)
                oFileName='3rer-assembly-'+assemId+'.pdb.gz'
                oLogName='3rer-assembly-'+assemId+'-pdb.log.gz'                
                dp.op("pisa-assembly-coordinates-pdb")
                dp.exp(oFileName)
                dp.expLog(oLogName)
            dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testPisaAssemblyMergeModelCif(self): 
        """
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            fPath=os.path.join(self.__testFilePath,self.__testFileCifPisa)
            dp.imp(fPath)
            dp.addInput(name="pisa_session_name",value="session_3re3-cif")            
            dp.op("pisa-analysis")
            dp.op("pisa-assembly-report-xml")
            dp.exp("pisa-assembly-report-cif.xml")
            #
            cifPath=os.path.join(self.__testFilePath,self.__testFileCifPisa)
            dp.imp(cifPath)
            dp.addInput(name="pisa_assembly_tuple_list",value="1,2,3")
            dp.addInput(name="pisa_assembly_file_path",value="pisa-assembly-report-cif.xml",type="file")
            dp.op("pisa-assembly-merge-cif")
            dp.exp("3rer-updated.cif.gz")
            dp.expLog("3rer-updated-cif.log.gz")
            #dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()


def suitePisaTestsCif():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityTests("testPisaAnalysisCif"))
    suiteSelect.addTest(RcsbDpUtilityTests("testPisaAssemblyReportXmlCif"))
    suiteSelect.addTest(RcsbDpUtilityTests("testPisaAssemblyDownloadModelCif"))
    suiteSelect.addTest(RcsbDpUtilityTests("testPisaAssemblyMergeModelCif"))    
    return suiteSelect    

def suitePisaTestsPdb():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityTests("testPisaAnalysisPdb"))
    suiteSelect.addTest(RcsbDpUtilityTests("testPisaAssemblyReportXmlPdb"))
    suiteSelect.addTest(RcsbDpUtilityTests("testPisaAssemblyDownloadModelPdb"))
    
    return suiteSelect    

    
if __name__ == '__main__':
    # Run all tests -- 
    # unittest.main()
    #
    mySuite=suitePisaTestsPdb()
    unittest.TextTestRunner(verbosity=2).run(mySuite)    
    #
    mySuite=suitePisaTestsCif()
    unittest.TextTestRunner(verbosity=2).run(mySuite)    
