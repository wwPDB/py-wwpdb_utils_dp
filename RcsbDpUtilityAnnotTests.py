##
#
# File:    RcsbDpUtilityAnnotTests.py
# Author:  J. Westbrook
# Date:    June 20,2012
# Version: 0.001
#
# Update:
#   July 16, 2012 jdw added test for new PDBx file format conversions.
#    Aug  2, 2012 jdw add cis peptide example
#    Aug 29, 2012 jdw -  check dependencies installed for site_id WWPDB_DEPLOY_TEST
#
##
"""
Test cases from 

"""

import sys, unittest, os, os.path, traceback

from wwpdb.api.facade.ConfigInfo          import ConfigInfo,getSiteId
from wwpdb.utils.rcsb.DataFile            import DataFile
from wwpdb.utils.rcsb.RcsbDpUtility       import RcsbDpUtility


class RcsbDpUtilityAnnotTests(unittest.TestCase):
    def setUp(self):
        self.__lfh=sys.stderr        
        # Pick up site information from the environment or failover to the development site id.
        self.__siteId=getSiteId(defaultSiteId='WWPDB_DEV_TEST')
        self.__lfh.write("\nTesting with site environment for:  %s\n" % self.__siteId)
        #
        self.__tmpPath         = './rcsb-tmp-dir'        
        cI=ConfigInfo(self.__siteId)
        
        self.__testFilePath       = './data'
        self.__testFileAnnotSS    = 'rcsb070236.cif'
        self.__testFileAnnotSSTop = 'topology.dat'
        #
        self.__testFileAnnotLink       = '3rij.cif'
        self.__testFileAnnotCisPeptide = '5hoh.cif'        
        self.__testFileAnnotSolvent    = '3rij.cif'
        self.__testFileAnnotValidate   = '3rij.cif'        
        self.__testFileAnnotNA         = '1o3q.cif'                
        self.__testFileAnnotSite       = '3rij.cif'
        self.__testIdAnnotSite         = '3rij'
        #
        self.__testFileAnnotRcsb      = 'rcsb033781.cif'
        self.__testFileAnnotRcsbEps   = 'rcsb013067.cifeps'
        #
        self.__testFilePdbPisa    =cI.get('DP_TEST_FILE_PDB_PISA')
        self.__testFileCifPisa    =cI.get('DP_TEST_FILE_CIF_PISA')                
        
            
    def tearDown(self):
        pass


    def testAnnotSite(self): 
        """  Calculate site environment 
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of="annot-site-"+self.__testFileAnnotSite +".gz"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath=os.path.join(self.__testFilePath,self.__testFileAnnotSite)
            dp.imp(inpPath)
            dp.addInput(name="block_id",value=self.__testIdAnnotSite)            
            dp.op("annot-site")
            dp.expLog("annot-site.log")
            dp.exp(of)            
            #dp.cleanup()
            
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testAnnotSiteAndMerge(self): 
        """  Calculate site environment 
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of="annot-site-"+self.__testFileAnnotSite #+".gz"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath=os.path.join(self.__testFilePath,self.__testFileAnnotSite)
            dp.imp(inpPath)
            dp.addInput(name="block_id",value=self.__testIdAnnotSite)            
            dp.op("annot-site")
            dp.expLog("annot-site.log")
            dp.exp(of)            
            
            inpPath=os.path.join(self.__testFilePath,self.__testFileAnnotSite)            
            dp.imp(inpPath)
            dp.addInput(name="site_info_file_path",value=of,type="file")
            dp.op("annot-merge-struct-site")
            dp.exp("annot-site-updated.cif.gz")
            dp.expLog("annot-site-updated-cif.log.gz")

            #dp.cleanup()
            
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testAnnotSecondaryStructureWithTopology(self): 
        """  Calculate secondary structure with a supporting topology file.
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of="annot-ss-with-top-"+self.__testFileAnnotSS +".gz"            
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath=os.path.join(self.__testFilePath,self.__testFileAnnotSS)
            dp.imp(inpPath)
            topPath=os.path.abspath(os.path.join(self.__testFilePath,self.__testFileAnnotSSTop))
            dp.addInput(name="ss_topology_file_path",value=topPath)
            dp.op("annot-secondary-structure")
            dp.expLog("annot-secondary-structure-w-top.log")
            dp.exp(of)            
            dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testAnnotSecondaryStructure(self): 
        """  Calculate secondary structure for a complicated case where pro-motif will fail.
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of="annot-ss-"+self.__testFileAnnotSS +".gz"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath=os.path.join(self.__testFilePath,self.__testFileAnnotSS)
            dp.imp(inpPath)
            dp.op("annot-secondary-structure")
            dp.expLog("annot-secondary-structure.log")
            dp.exp(of)            
            dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testAnnotLinkSSBond(self): 
        """  Calculate link and ss-bond features -
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of="annot-link-"+self.__testFileAnnotLink +".gz"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath=os.path.join(self.__testFilePath,self.__testFileAnnotLink)
            dp.imp(inpPath)
            dp.op("annot-link-ssbond")
            dp.expLog("annot-link-ssbond.log")
            dp.exp(of)            
            dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testAnnotCisPeptide(self): 
        """  Calculate cis-peptide linkages -
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of="annot-link-"+self.__testFileAnnotCisPeptide +".gz"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath=os.path.join(self.__testFilePath,self.__testFileAnnotCisPeptide)
            dp.imp(inpPath)
            dp.op("annot-cis-peptide")
            dp.expLog("annot-cis-peptide.log")
            dp.exp(of)            
            dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()


    def testAnnotDistantSolvent(self): 
        """  Calculate distant solvent
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of="annot-distant-"+self.__testFileAnnotSolvent +".gz"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath=os.path.join(self.__testFilePath,self.__testFileAnnotSolvent)
            dp.imp(inpPath)
            dp.op("annot-distant-solvent")
            dp.expLog("annot-distant-solvent.log")
            dp.exp(of)            
            dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testAnnotRepositionSolvent(self): 
        """  Calculate distant solvent
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of="annot-reposition-"+self.__testFileAnnotSolvent +".gz"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath=os.path.join(self.__testFilePath,self.__testFileAnnotSolvent)
            dp.imp(inpPath)
            dp.op("annot-reposition-solvent")
            dp.expLog("annot-reposition-solvent.log")
            dp.exp(of)            
            dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testAnnotBasePair(self): 
        """  Calculate base pairing
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of="annot-base-pair-"+self.__testFileAnnotNA +".gz"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath=os.path.join(self.__testFilePath,self.__testFileAnnotNA)
            dp.imp(inpPath)
            dp.op("annot-base-pair-info")
            dp.expLog("annot-base-pair.log")
            dp.exp(of)            
            dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testAnnotValidation(self): 
        """  Calculate geometrical validation -
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of="annot-validation-"+self.__testFileAnnotValidate +".gz"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath=os.path.join(self.__testFilePath,self.__testFileAnnotValidate)
            dp.imp(inpPath)
            dp.op("annot-validation")
            dp.expLog("annot-validation.log")
            dp.exp(of)            
            dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testAnnotRcsb2Pdbx(self): 
        """  RCSB CIF -> PDBx conversion  (Using the smaller application in the annotation package)
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of="annot-rcsb2pdbx-"+self.__testFileAnnotRcsb  +".gz"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath=os.path.join(self.__testFilePath,self.__testFileAnnotRcsb)
            dp.imp(inpPath)
            dp.op("annot-rcsb2pdbx")
            dp.expLog("annot-rcsb2pdbx.log")
            dp.exp(of)            
            dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()


    def testAnnotRcsbEps2Pdbx(self): 
        """  RCSB CIFEPS -> PDBx conversion (This still requires using the full maxit application)
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of="annot-rcsbeps2pdbx-"+self.__testFileAnnotRcsbEps  +".gz"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath=os.path.join(self.__testFilePath,self.__testFileAnnotRcsbEps)
            dp.imp(inpPath)
            dp.op("cif2cif")
            dp.expLog("annot-rcsbeps2pdbx.log")
            dp.exp(of)            
            #dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()


def suiteAnnotTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotSecondaryStructure"))
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotSecondaryStructureWithTopology"))
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotLinkSSBond"))
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotCisPeptide"))    
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotDistantSolvent"))
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotRepositionSolvent"))
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotBasePair"))
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotValidation"))            
    return suiteSelect    

def suiteAnnotSiteTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotSite"))
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotSiteAndMerge"))    
    return suiteSelect        


def suiteAnnotFormatConvertTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotRcsb2Pdbx"))
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotRcsbEps2Pdbx"))    
    return suiteSelect        

    
if __name__ == '__main__':
    # Run all tests -- 
    # unittest.main()
    #
    mySuite=suiteAnnotTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)    
    #
    mySuite=suiteAnnotSiteTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)
    #
    mySuite=suiteAnnotFormatConvertTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)
    #
