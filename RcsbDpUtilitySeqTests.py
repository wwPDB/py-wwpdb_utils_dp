##
#
# File:    RcsbDpUtilitySeqTests.py
# Author:  J. Westbrook
# Date:    April 16, 2013
# Version: 0.001
#
# Update:
##
"""
Test cases for sequence search  and entry fetch/extract operations -- 
"""

import sys, unittest, os, os.path, traceback

from wwpdb.api.facade.ConfigInfo          import ConfigInfo,getSiteId
from wwpdb.utils.rcsb.DataFile            import DataFile
from wwpdb.utils.rcsb.RcsbDpUtility       import RcsbDpUtility


class RcsbDpUtilityTests(unittest.TestCase):
    def setUp(self):
        self.__lfh=sys.stderr        
        # Pick up site information from the environment or failover to the development site id.
        self.__siteId=getSiteId(defaultSiteId='WWPDB_DEPLOY_TEST')
        self.__lfh.write("\nTesting with site environment for:  %s\n" % self.__siteId)
        #
        cI=ConfigInfo(self.__siteId)
        self.__tmpPath         = './rcsb-tmp-dir'
        #
        self.__testFileFastaP     = os.path.join('./data','1KIP.fasta')
        self.__testFileFastaN     = os.path.join('./data','2WDK.fasta')
        #
        self.__lfh.write("\nTest fasta protein file path %s\n" % (self.__testFileFastaP))
        self.__lfh.write("\nTest fasta RNA     file path %s\n" % (self.__testFileFastaN))
            
    def tearDown(self):
        pass

    def testProteinSequenceSearch(self): 
        """
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            dp.imp(self.__testFileFastaP)
            dp.addInput(name="db_name",value="my_uniprot_all")
            dp.addInput(name="num_threads",value="4")
            dp.op("seq-blastp")
            dp.expLog("seq-blastp.log")
            dp.exp("seq-blastp.xml")
            dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testRnaSequenceSearch(self): 
        """
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            dp.imp(self.__testFileFastaN)
            dp.addInput(name="db_name",value="my_ncbi_nt")
            dp.addInput(name="num_threads",value="4")
            dp.op("seq-blastn")
            dp.expLog("seq-blastn.log")
            dp.exp("seq-blastn.xml")
            dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

def suiteSequenceSearchTests():
    suiteSelect = unittest.TestSuite()
    #suiteSelect.addTest(RcsbDpUtilityTests("testProteinSequenceSearch"))
    suiteSelect.addTest(RcsbDpUtilityTests("testRnaSequenceSearch"))
    return suiteSelect    

if __name__ == '__main__':
    #
    mySuite=suiteSequenceSearchTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)    
