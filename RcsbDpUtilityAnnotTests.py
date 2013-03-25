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
#    Sep  2, 2012 jdw -  add example for chemical shift nomenclature checks
#    Sep  5, 2012 jdw -  add example for wwPDB validation package
#    Sep  6, 2012 jdw -  add example for consolidated annotation steps
#    Dec 12, 2012 jdw -  add and verify test cases for version 2 of validation module. 
#    Mar 25, 2013 jdw -  add testSequenceAssignMerge()
##
"""
Test cases from 

"""

import sys, unittest, os, os.path, traceback

from wwpdb.api.facade.ConfigInfo          import ConfigInfo,getSiteId
from wwpdb.utils.rcsb.DataFile            import DataFile
from wwpdb.utils.rcsb.RcsbDpUtility       import RcsbDpUtility

from wwpdb.api.facade.WfDataObject  import WfDataObject



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
        self.__testFileAnnotSSTop = 'topology.txt'
        #
        self.__testFileAnnotLink       = '3rij.cif'
        self.__testFileAnnotCisPeptide = '5hoh.cif'        
        self.__testFileAnnotSolvent    = 'D_900002_model_P1.cif'
        self.__testFileAnnotValidate   = '3rij.cif'        
        self.__testFileAnnotNA         = '1o3q.cif'                
        self.__testFileAnnotSite       = '1xbb.cif'
        self.__testIdAnnotSite         = '1xbb'
        #
        self.__testFileAnnotRcsb      = 'rcsb033781.cif'
        self.__testFileAnnotRcsbEps   = 'rcsb013067.cifeps'
        #
        self.__testFilePdbPisa    =cI.get('DP_TEST_FILE_PDB_PISA')
        self.__testFileCifPisa    =cI.get('DP_TEST_FILE_CIF_PISA')
        #
        self.__testFileStarCs       = "star_16703_test_2.str"
        self.__testFileCsRelatedCif = "cor_16703_test.cif"
        #
        self.__testFileValidateXyz = "1cbs.cif"
        self.__testFileValidateSf  = "1cbs-sf.cif"
        self.__testValidateIdList  = ["1cbs","3of4","3oqp"]
        self.__testArchiveIdList  = [("D_900002","4EC0"),("D_600000","4F3R")]
        #
        self.__testFileCifSeq       = "RCSB095269_model_P1.cif.V1"
        self.__testFileSeqAssign    = "RCSB095269_seq-assign_P1.cif.V1"

            
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


    def testAnnotSiteArchive(self): 
        """  Calculate site environment 
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            for (depId,pdbId) in self.__testArchiveIdList:
                ofpdf=depId+"-valrpt.pdf"
                ofxml=depId+"-valdata.xml"

                wfo1=WfDataObject()
                wfo1.setDepositionDataSetId(depId)
                wfo1.setStorageType('archive')
                wfo1.setContentTypeAndFormat('model','pdbx')
                wfo1.setVersionId('latest')
                if (wfo1.isReferenceValid()):
                    dP=wfo1.getDirPathReference()
                    fP=wfo1.getFilePathReference()
                    self.__lfh.write("Directory path: %s\n" % dP)
                    self.__lfh.write("File      path: %s\n" % fP)
                else:
                    self.__lfh.write("Bad archival reference\n")
                    
                inpPath=fP
            
                of="annot-site-"+depId+".gz"
                dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
                dp.imp(inpPath)
                dp.addInput(name="block_id",value=pdbId)            
                dp.op("annot-site")
                dp.expLog("annot-site-"+depId+".log")
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
            #of="annot-reposition-"+self.__testFileAnnotSolvent +".gz"
            of="annot-reposition-"+self.__testFileAnnotSolvent            
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
            of="annot-rcsb2pdbx-"+self.__testFileAnnotRcsb
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath=os.path.join(self.__testFilePath,self.__testFileAnnotRcsb)
            dp.imp(inpPath)
            dp.op("annot-rcsb2pdbx-strip")
            dp.expLog("annot-rcsb2pdbx-strip.log")
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
            of="annot-rcsbeps2pdbx-"+self.__testFileAnnotRcsbEps
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath=os.path.join(self.__testFilePath,self.__testFileAnnotRcsbEps)
            dp.imp(inpPath)
            dp.op("annot-rcsbeps2pdbx-strip")
            dp.expLog("annot-rcsbeps2pdbx-strip.log")
            dp.exp(of)            
            #dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testAnnotCSCheck(self): 
        """  Test CS file check
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
            #dp.cleanup()
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
            xyzPath=os.path.abspath(os.path.join(self.__testFilePath,self.__testFileCsRelatedCif))
            dp.imp(inpPath)
            dp.addInput(name="coordinate_file_path",value=xyzPath)            
            dp.op("annot-chem-shift-coord-check")
            dp.expLog("annot-cs-coord-file-check.log")
            dp.exp(of)            
            #dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()


    def testAnnotValidate1(self): 
        """  Test create validation report
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            ofpdf="1cbs-valrpt.pdf"
            ofxml="1cbs-valdata.xml"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            xyzPath=os.path.join(self.__testFilePath,self.__testFileValidateXyz)
            sfPath=os.path.join(self.__testFilePath,self.__testFileValidateSf)            
            dp.imp(xyzPath)
            dp.addInput(name="sf_file_path",value=sfPath)            
            dp.op("annot-wwpdb-validate-1")
            dp.expLog("annot-validate-1.log")
            #dp.exp(ofpdf)
            dp.expList(dstPathList=[ofpdf,ofxml])
            dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()


    def testAnnotValidateList(self): 
        """  Test create validation report for the test list of example PDB ids
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            for pdbId in self.__testValidateIdList:
                ofpdf=pdbId+"-valrpt.pdf"
                ofxml=pdbId+"-valdata.xml"
                testFileValidateXyz=pdbId+".cif"
                testFileValidateSf=pdbId+"-sf.cif"
                dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
                xyzPath=os.path.join(self.__testFilePath,testFileValidateXyz)
                sfPath=os.path.join(self.__testFilePath,testFileValidateSf)            
                dp.imp(xyzPath)
                dp.addInput(name="sf_file_path",value=sfPath)            
                dp.op("annot-wwpdb-validate-1")
                dp.expLog(pdbId+"-annot-validate.log")
                dp.expList(dstPathList=[ofpdf,ofxml])
                dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testAnnotValidateListV2(self): 
        """  Test create validation report for the test list of example PDB ids
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            for pdbId in self.__testValidateIdList:
                ofpdf=pdbId+"-valrpt.pdf"
                ofxml=pdbId+"-valdata.xml"
                testFileValidateXyz=pdbId+".cif"
                testFileValidateSf=pdbId+"-sf.cif"
                dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
                xyzPath=os.path.join(self.__testFilePath,testFileValidateXyz)
                sfPath=os.path.join(self.__testFilePath,testFileValidateSf)            
                dp.imp(xyzPath)
                dp.addInput(name="sf_file_path",value=sfPath)            
                dp.op("annot-wwpdb-validate-2")
                dp.expLog(pdbId+"-annot-validate-v2.log")
                dp.expList(dstPathList=[ofpdf,ofxml])
                dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()


    def testArchiveValidateListV2(self): 
        """  Test create validation report for the test list of example dep dataset ids
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            for (depId,pdbId) in self.__testArchiveIdList:
                ofpdf=depId+"-valrpt.pdf"
                ofxml=depId+"-valdata.xml"

                wfo1=WfDataObject()
                wfo1.setDepositionDataSetId(depId)
                wfo1.setStorageType('archive')
                wfo1.setContentTypeAndFormat('model','pdbx')
                wfo1.setVersionId('latest')
                if (wfo1.isReferenceValid()):
                    dP=wfo1.getDirPathReference()
                    fP=wfo1.getFilePathReference()
                    self.__lfh.write("Directory path: %s\n" % dP)
                    self.__lfh.write("File      path: %s\n" % fP)
                else:
                    self.__lfh.write("Bad archival reference\n")
                    
                testFileValidateXyz=fP
                
                wfo2=WfDataObject()
                wfo2.setDepositionDataSetId(depId)
                wfo2.setStorageType('archive')
                wfo2.setContentTypeAndFormat('structure-factors','pdbx')
                wfo2.setVersionId('latest')
                if (wfo2.isReferenceValid()):
                    dP=wfo2.getDirPathReference()
                    fP=wfo2.getFilePathReference()
                    self.__lfh.write("Directory path: %s\n" % dP)
                    self.__lfh.write("File      path: %s\n" % fP)
                else:
                    self.__lfh.write("Bad archival reference\n")
                    
                testFileValidateSf=fP
                #
                dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
                xyzPath=os.path.join(self.__testFilePath,testFileValidateXyz)
                sfPath=os.path.join(self.__testFilePath,testFileValidateSf)            
                dp.imp(xyzPath)
                dp.addInput(name="sf_file_path",value=sfPath)            
                dp.op("annot-wwpdb-validate-2")
                dp.expLog(depId+"-annot-validate-v2.log")
                dp.expList(dstPathList=[ofpdf,ofxml])
                dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()


    def testAnnotConsolidatedTasksWithTopology(self): 
        """  Calculate annotation tasks in a single step including supporting topology data.
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of="annot-consolidated-top-"+self.__testFileAnnotSS +".gz"            
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath=os.path.join(self.__testFilePath,self.__testFileAnnotSS)
            dp.imp(inpPath)
            topPath=os.path.abspath(os.path.join(self.__testFilePath,self.__testFileAnnotSSTop))
            dp.addInput(name="ss_topology_file_path",value=topPath)
            dp.op("annot-consolidated-tasks")
            dp.expLog("annot-consolidated-w-top.log")
            dp.exp(of)            
            dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testAnnotRepositionSolventPlusDerived(self): 
        """  Calculate distant solvent followed by computing key derived categories -- 
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of="annot-reposition-add-derived-"+self.__testFileAnnotSolvent
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath=os.path.join(self.__testFilePath,self.__testFileAnnotSolvent)
            dp.imp(inpPath)
            dp.op("annot-reposition-solvent-add-derived")
            dp.expLog("annot-reposition-solvent-plus-derived.log")
            dp.exp(of)            
            dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testSequenceAssignMerge(self): 
        """  test sequence assignment merge
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath=os.path.join(self.__testFilePath,self.__testFileCifSeq)
            dp.imp(inpPath)
            assignPath=os.path.join(self.__testFilePath,self.__testFileSeqAssign)
            dp.addInput(name="seqmod_assign_file_path",value=assignPath,type="file")
            dp.op("annot-merge-sequence-data")
            dp.exp("model-with-merged-seq-assignments.cif")
            dp.expLog("annot-seqmod-merge.log")

            #dp.cleanup()
            
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testAnnotMapCalc(self): 
        """  Test create density maps --
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            for pdbId in ['1cbs']:
                ofpdf=pdbId+"-valrpt.pdf"
                ofxml=pdbId+"-valdata.xml"

                testFileXyz=pdbId+".cif"
                testFileSf=pdbId+"-sf.cif"
                
                dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
                xyzPath=os.path.join(self.__testFilePath,testFileXyz)
                sfPath=os.path.join(self.__testFilePath,testFileSf)            
                dp.imp(xyzPath)
                dp.addInput(name="sf_file_path",value=sfPath)            
                dp.op("annot-make-maps")
                dp.expLog(pdbId+"-annot-make-maps.log")
                #dp.expList(dstPathList=[ofpdf,ofxml])
                #dp.cleanup()
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()



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


def suiteAnnotNMRTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotCSCheck"))
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotCSCoordCheck"))
    return suiteSelect        

def suiteAnnotValidationTests():
    suiteSelect = unittest.TestSuite()
    #suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotValidate1"))
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotValidateList"))    
    return suiteSelect        

def suiteAnnotValidationV2Tests():
    suiteSelect = unittest.TestSuite()
    #suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotValidate1"))
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotValidateListV2"))    
    return suiteSelect        

def suiteArchiveValidationV2Tests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testArchiveValidateListV2"))    
    return suiteSelect        


def suiteArchiveSiteTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotSiteArchive"))    
    return suiteSelect        


def suiteAnnotConsolidatedTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotConsolidatedTasksWithTopology"))
    return suiteSelect        

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

def suiteSolventPlusDerivedTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotRepositionSolvent"))    
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotRepositionSolventPlusDerived"))
    return suiteSelect    

def suiteMergeSeqAssignTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testSequenceAssignMerge"))
    return suiteSelect    


def suiteMapCalcTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotMapCalc"))
    return suiteSelect    



if __name__ == '__main__':
    # Run all tests -- 
    # unittest.main()
    #
    doAll=False
    if (doAll):
        mySuite=suiteAnnotTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)    
        #
        mySuite=suiteAnnotSiteTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)
        #
        mySuite=suiteAnnotFormatConvertTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)
        #
        mySuite=suiteAnnotNMRTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)    

        mySuite=suiteAnnotValidationTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)

        mySuite=suiteAnnotValidationV2Tests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)
        
        mySuite=suiteAnnotConsolidatedTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)

        mySuite=suiteSolventPlusDerivedTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)            

        mySuite=suiteAnnotFormatConvertTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)

        mySuite=suiteMergeSeqAssignTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)
        
        #mySuite=suiteArchiveValidationV2Tests()  
        #unittest.TextTestRunner(verbosity=2).run(mySuite)
    else:
        pass

    #
    mySuite=suiteMapCalcTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)
    #
