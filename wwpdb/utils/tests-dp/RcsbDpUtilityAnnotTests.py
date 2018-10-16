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
#    Apr 3,  2013 jdw -  add map calculation examples
#    Apr 9,  2013 jdw -  add ligand map calculation examples
#    Jun 26, 2013 jdw -  add tests for annot-format-check-pdbx
#    Jun 27, 2013 jdw -  add tests for annot-sf-mtz2pdbx and annot-dcc-report
#    Aug 15, 2013 jdw -  change annot-sf-mtz2pdbx to annot-sf-convert change file format of diag file to cif
#    Feb 10, 2014 jdw -  add em test cases
#    Mar 20  2014 jdw -  set execution of test cases for dcc & sf-convert
#    Dec 19  2016 ep  -  remove old validation test cases - use annot-wwpdb-validate-all only
#    Jan 13  2017 ep  -  Add tests for special positions and correction of such as well as updating with with depositor assembly
#    Oct 16  2018 jdw   adapt for Py2/3 and Python packaging
##
"""
Test cases from

"""

import logging
import os
import platform
import sys
import unittest

HERE = os.path.abspath(os.path.dirname(__file__))
TOPDIR = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
try:
    TESTOUTPUT = os.path.join(HERE, 'test-output', platform.python_version())
    if not os.path.exists(TESTOUTPUT):
        os.makedirs(TESTOUTPUT)
    mockTopPath = os.path.join(TOPDIR, 'wwpdb', 'mock-data')
    from wwpdb.utils.testing.SiteConfigSetup import SiteConfigSetup
    SiteConfigSetup().setupEnvironment(TESTOUTPUT, mockTopPath)
except Exception:
    pass

from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId
from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class RcsbDpUtilityAnnotTests(unittest.TestCase):

    def setUp(self):
        self.__siteId = getSiteId(defaultSiteId=None)
        logger.info("\nTesting with site environment for:  %s\n" % self.__siteId)
        #
        self.__cI = ConfigInfo(self.__siteId)
        #
        self.__tmpPath = os.path.join(HERE, 'test-output')
        self.__testFilePath = os.path.join(TOPDIR, 'wwpdb', 'mock-data', 'dp-utils')
        self.__testFileCif = '1xbb.cif'

        self.__testFileAnnotSS = '4deq.cif'
        self.__testFileAnnotSSTop = 'topology.txt'
        #
        self.__testFileAnnotLink = '3rij.cif'
        self.__testFileAnnotCisPeptide = '5hoh.cif'

        self.__testFileAnnotSolvent = '4ec0.cif'
        self.__testFileAnnotValidate = '3rij.cif'
        self.__testFileAnnotNA = '1o3q.cif'
        self.__testFileAnnotSite = '1xbb.cif'
        self.__testIdAnnotSite = '1xbb'
        #
        self.__testFileAnnotSiteAlt = '4p00.cif'
        self.__testIdAnnotSiteAlt = '4P00'

        ## OK JDW
        self.__testFileAnnotRcsb = 'rcsb033781.cif'
        #
        self.__testFilePdbPisa = '1xbb.pdb'
        self.__testFileCifPisa = '1xbb.cif'
        #
        self.__testFileStarCs = "2MMZ-cs.str"
        self.__testFileCsRelatedCif = "cor_16703_test.cif"
        #
        self.__testFileValidateXyz = "1cbs.cif"
        self.__testFileValidateSf = "1cbs-sf.cif"
        self.__testValidateIdList = ["1cbs", "3of4", "3oqp"]
        #

        self.__testFileMtzBad = "mtz-bad.mtz"
        self.__testFileMtzGood = "mtz-good.mtz"

        self.__testFileMtzRunaway = "bad-runaway.mtz"
        self.__testFileXyzRunaway = "bad-runaway.cif"

        self.__testMapNormal = "normal.map"
        self.__testMapSpider = "testmap.spi"
        ## OK JDW
        self.__testFilePrdSearch = 'D_1200000237_model_P1.cif.V1'

        self.__testValidateXrayIdList = ['1cbs']
        self.__testValidateNmrIdList = ['2MM4', '2MMZ']

        self.__testDccModelId = '4wpo'

        self.__testSpecialPosition = '5uee.cif'
        self.__testDepAssembly = "1cbs.cif"

    def tearDown(self):
        pass

    def testValidateGeometryCheck(self):
        """  Test format sanity check for pdbx
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of = "validate-geometry-check.cif"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath = os.path.join(self.__testFilePath, self.__testFileAnnotSite)
            dp.imp(inpPath)
            dp.op("validate-geometry")
            dp.expLog("validate-geometry-check-pdbx.log")
            dp.exp(of)
            # dp.cleanup()

        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotValidateGeometryCheck(self):
        """  Test of updating geometrical validation diagnostics -
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of = "annot-validate-geometry-check.cif"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath = os.path.join(self.__testFilePath, self.__testFileAnnotSite)
            dp.imp(inpPath)
            dp.op("annot-validate-geometry")
            dp.expLog("annot-validate-geometry-check-pdbx.log")
            dp.exp(of)
            # dp.cleanup()

        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotGetCorresInfo(self):
        """  Test running GetCorresInfo to get correspondance info -
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of = os.path.join(self.__tmpPath, "annot-get-corres-info-check.cif")
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            dp.setDebugMode(True)
            inpPath = os.path.join(self.__testFilePath, self.__testFileAnnotSite)
            dp.imp(inpPath)
            dp.op("annot-get-corres-info")
            dp.expLog(os.path.join(self.__tmpPath, "annot-get-corres-info-check-pdbx.log"))
            dp.exp(of)
            # dp.cleanup()

        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotFormatCheck(self):
        """  Test format sanity check for pdbx
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of = "annot-format-check.txt"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            #
            inpPath = os.path.join(self.__testFilePath, self.__testFileAnnotSite)
            dp.imp(inpPath)
            dp.op("annot-format-check-pdbx")
            dp.expLog("format-check-pdbx.log")
            dp.exp(of)
            # dp.cleanup()

        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotSite(self):
        """  Calculate site environment
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of = "annot-site-" + self.__testFileAnnotSite + ".gz"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath = os.path.join(self.__testFilePath, self.__testFileAnnotSite)
            dp.imp(inpPath)
            dp.addInput(name="block_id", value=self.__testIdAnnotSite)
            dp.op("annot-site")
            dp.expLog("annot-site.log")
            dp.exp(of)
            # dp.cleanup()

        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotSiteAlt(self):
        """  Calculate site environment
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of = "annot-site-" + self.__testIdAnnotSiteAlt + '.cif'
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath = os.path.join(self.__testFilePath, self.__testFileAnnotSiteAlt)
            dp.imp(inpPath)
            dp.addInput(name="block_id", value=self.__testIdAnnotSiteAlt)
            dp.op("annot-site")
            dp.expLog("annot-site.log")
            dp.exp(of)
            # dp.cleanup()

        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotSiteAndMerge(self):
        """  Calculate site environment
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of = "annot-site-" + self.__testFileAnnotSite  # +".gz"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath = os.path.join(self.__testFilePath, self.__testFileAnnotSite)
            dp.imp(inpPath)
            dp.addInput(name="block_id", value=self.__testIdAnnotSite)
            dp.op("annot-site")
            dp.expLog("annot-site.log")
            dp.exp(of)

            inpPath = os.path.join(self.__testFilePath, self.__testFileAnnotSite)
            dp.imp(inpPath)
            dp.addInput(name="site_info_file_path", value=of, type="file")
            dp.op("annot-merge-struct-site")
            dp.exp("annot-site-updated.cif.gz")
            dp.expLog("annot-site-updated-cif.log.gz")

            # dp.cleanup()

        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotSecondaryStructureWithTopology(self):
        """  Calculate secondary structure with a supporting topology file.
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of = "annot-ss-with-top-" + self.__testFileAnnotSS + ".gz"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath = os.path.join(self.__testFilePath, self.__testFileAnnotSS)
            dp.imp(inpPath)
            topPath = os.path.abspath(os.path.join(self.__testFilePath, self.__testFileAnnotSSTop))
            dp.addInput(name="ss_topology_file_path", value=topPath)
            dp.op("annot-secondary-structure")
            dp.expLog("annot-secondary-structure-w-top.log")
            dp.exp(of)
            dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotSecondaryStructure(self):
        """  Calculate secondary structure for a complicated case where pro-motif will fail.
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of = "annot-ss-" + self.__testFileAnnotSS + ".gz"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath = os.path.join(self.__testFilePath, self.__testFileAnnotSS)
            dp.imp(inpPath)
            dp.op("annot-secondary-structure")
            dp.expLog("annot-secondary-structure.log")
            dp.exp(of)
            dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotLinkSSBond(self):
        """  Calculate link and ss-bond features -
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of = "annot-link-" + self.__testFileAnnotLink + ".gz"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath = os.path.join(self.__testFilePath, self.__testFileAnnotLink)
            dp.imp(inpPath)
            dp.op("annot-link-ssbond")
            dp.expLog("annot-link-ssbond.log")
            dp.exp(of)
            dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotCisPeptide(self):
        """  Calculate cis-peptide linkages -
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of = "annot-link-" + self.__testFileAnnotCisPeptide + ".gz"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath = os.path.join(self.__testFilePath, self.__testFileAnnotCisPeptide)
            dp.imp(inpPath)
            dp.op("annot-cis-peptide")
            dp.expLog("annot-cis-peptide.log")
            dp.exp(of)
            dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotDistantSolvent(self):
        """  Calculate distant solvent
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of = "annot-distant-" + self.__testFileAnnotSolvent + ".gz"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath = os.path.join(self.__testFilePath, self.__testFileAnnotSolvent)
            dp.imp(inpPath)
            dp.op("annot-distant-solvent")
            dp.expLog("annot-distant-solvent.log")
            dp.exp(of)
            dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotRepositionSolvent(self):
        """  Calculate distant solvent
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of = "annot-reposition-" + self.__testFileAnnotSolvent
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath = os.path.join(self.__testFilePath, self.__testFileAnnotSolvent)
            dp.imp(inpPath)
            dp.op("annot-reposition-solvent")
            dp.expLog("annot-reposition-solvent.log")
            dp.exp(of)
            dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotBasePair(self):
        """  Calculate base pairing
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of = "annot-base-pair-" + self.__testFileAnnotNA + ".gz"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath = os.path.join(self.__testFilePath, self.__testFileAnnotNA)
            dp.imp(inpPath)
            dp.op("annot-base-pair-info")
            dp.expLog("annot-base-pair.log")
            dp.exp(of)
            dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotValidation(self):
        """  Calculate geometrical validation -
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of = "annot-validation-" + self.__testFileAnnotValidate + ".gz"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath = os.path.join(self.__testFilePath, self.__testFileAnnotValidate)
            dp.imp(inpPath)
            dp.op("annot-validation")
            dp.expLog("annot-validation.log")
            dp.exp(of)
            dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotRcsb2Pdbx(self):
        """  RCSB CIF -> PDBx conversion  (Using the smaller application in the annotation package)

             Converting to RCSB to PDB id in _entry.id and related items.
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of = "annot-rcsb2pdbx-withpdbid-" + self.__testFileAnnotRcsb
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath = os.path.join(self.__testFilePath, self.__testFileAnnotRcsb)
            dp.imp(inpPath)
            dp.op("annot-rcsb2pdbx-withpdbid")
            dp.expLog("annot-rcsb2pdbx.log")
            dp.exp(of)
            dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotRcsb2PdbxSQ(self):
        """  RCSB CIF -> PDBx conversion  (Using the smaller application in the annotation package)

             Converting to RCSB to PDB id in _entry.id and related items.
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of = "annot-rcsb2pdbx-withpdbid-sq-" + self.__testFileAnnotRcsb
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath = os.path.join(self.__testFilePath, self.__testFileAnnotRcsb)
            dp.imp(inpPath)
            dp.op("annot-rcsb2pdbx-withpdbid-singlequote")
            dp.expLog("annot-rcsb2pdbx-sq.log")
            dp.exp(of)
            dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotRcsb2PdbxSQAlt(self):
        """  RCSB CIF -> PDBx conversion  (Using the smaller application in the annotation package)
             using maxit
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of = "annot-rcsb2pdbx-alt-" + self.__testFileAnnotRcsb
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath = os.path.join(self.__testFilePath, self.__testFileAnnotRcsb)
            dp.imp(inpPath)
            dp.op("annot-rcsb2pdbx-alt")
            dp.expLog("annot-rcsb2pdbx-alt.log")
            dp.exp(of)
            dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotRcsb2PdbxStrip(self):
        """  RCSB CIF -> PDBx conversion  (Using the smaller application in the annotation package)
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of = "annot-rcsb2pdbx-strip-" + self.__testFileAnnotRcsb
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath = os.path.join(self.__testFilePath, self.__testFileAnnotRcsb)
            dp.imp(inpPath)
            dp.op("annot-rcsb2pdbx-strip")
            dp.expLog("annot-rcsb2pdbx-strip.log")
            dp.exp(of)
            dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotCSCheck(self):
        """  Test CS file check
                             'nmr-cs-check-report'         :  (['html'], 'nmr-cs-check-report'),
                             'nmr-cs-xyz-check-report'     :  (['html'], 'nmr-cs-xyz-check-report'),
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of = "cs-file-check.html"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath = os.path.join(self.__testFilePath, self.__testFileStarCs)
            dp.imp(inpPath)
            dp.op("annot-chem-shift-check")
            dp.expLog("annot-cs-file-check.log")
            dp.exp(of)
            # dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotCSCoordCheck(self):
        """  Test CS + Coordindate file check
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of = "cs-coord-file-check.html"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath = os.path.join(self.__testFilePath, self.__testFileStarCs)
            xyzPath = os.path.abspath(os.path.join(self.__testFilePath, self.__testFileCsRelatedCif))
            dp.imp(inpPath)
            dp.addInput(name="coordinate_file_path", value=xyzPath)
            dp.op("annot-chem-shift-coord-check")
            dp.expLog("annot-cs-coord-file-check.log")
            dp.exp(of)
            # dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotValidateListNmrTest(self):
        """  Test create validation report for the test list of example PDB ids (NMR examples)
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            count = 0
            for pdbId in self.__testValidateNmrIdList:
                ofpdf = pdbId + "-valrpt.pdf"
                ofxml = pdbId + "-valdata.xml"
                offullpdf = pdbId + "-valrpt_full.pdf"
                ofpng = pdbId + "-val-slider.png"
                ofsvg = pdbId + "-val-slider.svg"
                #
                testFileValidateXyz = pdbId + ".cif"
                testFileValidateCs = pdbId + "-cs.cif"
                dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)

                xyzPath = os.path.abspath(os.path.join(self.__testFilePath, testFileValidateXyz))
                csPath = os.path.abspath(os.path.join(self.__testFilePath, testFileValidateCs))
                dp.addInput(name="request_annotation_context", value="yes")
                # adding explicit selection of steps --
                # Alternate
                if count % 2 == 0:
                    dp.addInput(name="step_list", value=" coreclust,chemicalshifts,writexml,writepdf ")
                count += 1
                dp.imp(xyzPath)
                dp.addInput(name="cs_file_path", value=csPath)
                dp.op("annot-wwpdb-validate-all")
                dp.expLog(pdbId + "-annot-validate-test.log")
                dp.expList(dstPathList=[ofpdf, ofxml, offullpdf, ofpng, ofsvg])
                dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotValidateListXrayTest(self):
        """  Test create validation report for the test list of example PDB ids (NMR examples)
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            for pdbId in self.__testValidateXrayIdList:
                ofpdf = pdbId + "-valrpt.pdf"
                ofxml = pdbId + "-valdata.xml"
                offullpdf = pdbId + "-valrpt_full.pdf"
                ofpng = pdbId + "-val-slider.png"
                ofsvg = pdbId + "-val-slider.svg"
                #
                testFileValidateXyz = pdbId + ".cif"
                testFileValidateSf = pdbId + "-sf.cif"
                dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
                # dp.setDebugMode(True)

                xyzPath = os.path.abspath(os.path.join(self.__testFilePath, testFileValidateXyz))
                sfPath = os.path.abspath(os.path.join(self.__testFilePath, testFileValidateSf))
                #dp.addInput(name="request_annotation_context", value="yes")
                dp.addInput(name="request_validation_mode", value="annotate")
                #dp.addInput(name="request_validation_mode", value="server")
                dp.imp(xyzPath)
                dp.addInput(name="sf_file_path", value=sfPath)
                dp.op("annot-wwpdb-validate-all")
                dp.expLog(pdbId + "-annot-validate-test.log")
                dp.expList(dstPathList=[ofpdf, ofxml, offullpdf, ofpng, ofsvg])
                # dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotConsolidatedTasksWithTopology(self):
        """  Calculate annotation tasks in a single step including supporting topology data.
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of = "annot-consolidated-top-" + self.__testFileAnnotSS + ".gz"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath = os.path.join(self.__testFilePath, self.__testFileAnnotSS)
            dp.imp(inpPath)
            topPath = os.path.abspath(os.path.join(self.__testFilePath, self.__testFileAnnotSSTop))
            dp.addInput(name="ss_topology_file_path", value=topPath)
            dp.op("annot-consolidated-tasks")
            dp.expLog("annot-consolidated-w-top.log")
            dp.exp(of)
            dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotRepositionSolventPlusDerived(self):
        """  Calculate distant solvent followed by computing key derived categories --
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of = "annot-reposition-add-derived-" + self.__testFileAnnotSolvent
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath = os.path.join(self.__testFilePath, self.__testFileAnnotSolvent)
            dp.imp(inpPath)
            dp.op("annot-reposition-solvent-add-derived")
            dp.expLog("annot-reposition-solvent-plus-derived.log")
            dp.exp(of)
            dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotMapCalc(self):
        """  Test create density maps --
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            for pdbId in ['1cbs', '3of4', '3oqp']:
                of2fofc = pdbId + "_2fofc.map"
                offofc = pdbId + "_fofc.map"

                testFileXyz = pdbId + ".cif"
                testFileSf = pdbId + "-sf.cif"

                dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
                xyzPath = os.path.join(self.__testFilePath, testFileXyz)
                sfPath = os.path.join(self.__testFilePath, testFileSf)
                dp.imp(xyzPath)
                dp.addInput(name="sf_file_path", value=sfPath)
                dp.op("annot-make-maps")
                dp.expLog(pdbId + "-annot-make-maps.log")
                dp.expList(dstPathList=[of2fofc, offofc])
                # dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotLigandMapCalc(self):
        """  Test create density maps --
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            for pdbId in ['2yn2']:
                # of2fofc=pdbId+"_2fofc.map"
                # offofc=pdbId+"_fofc.map"

                testFileXyz = pdbId + ".cif"
                testFileSf = pdbId + "-sf.cif"

                dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
                xyzPath = os.path.join(self.__testFilePath, testFileXyz)
                sfPath = os.path.join(self.__testFilePath, testFileSf)
                outMapPath = '.'
                outMapPathFull = os.path.abspath(outMapPath)
                #
                dp.imp(xyzPath)
                dp.addInput(name="sf_file_path", value=sfPath)
                dp.addInput(name="output_map_file_path", value=outMapPathFull)
                dp.op("annot-make-ligand-maps")
                dp.expLog(pdbId + "-annot-make-ligand-maps.log")
                # dp.expList(dstPathList=[of2fofc,offofc])
                # dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotDccRsrReport(self):
        """  Test create DCC report -
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            ofn = "dcc-rsr-report.cif"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)

            xyzPath = os.path.join(self.__testFilePath, self.__testDccModelId + '.cif')
            sfPath = os.path.join(self.__testFilePath, self.__testDccModelId + '-sf.cif')
            dp.imp(xyzPath)
            dp.addInput(name="sf_file_path", value=sfPath)
            dp.addInput(name="dcc_arguments", value=" -rsr -refmac ")
            dp.op("annot-dcc-report")
            dp.expLog("dcc-rsr-report.log")
            dp.exp(ofn)
            # dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotDccReport(self):
        """  Test create DCC report -
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            ofn = "dcc-report.cif"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            xyzPath = os.path.join(self.__testFilePath, self.__testFileValidateXyz)
            sfPath = os.path.join(self.__testFilePath, self.__testFileValidateSf)
            dp.imp(xyzPath)
            dp.addInput(name="sf_file_path", value=sfPath)
            dp.op("annot-dcc-report")
            dp.expLog("dcc-report.log")
            dp.exp(ofn)
            # dp.expList(dstPathList=[ofpdf,ofxml])
            dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotMtz2PdbxGood(self):
        """  Test mtz to pdbx conversion  (good mtz)
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            diagfn = "sf-convert-diags.cif"
            ciffn = "sf-convert-datafile.cif"
            dmpfn = "sf-convert-mtzdmp.log"
            #
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            mtzPath = os.path.join(self.__testFilePath, self.__testFileMtzGood)
            dp.imp(mtzPath)
            dp.setTimeout(15)
            dp.op("annot-sf-convert")
            dp.expLog("sf-convert.log")
            dp.expList(dstPathList=[ciffn, diagfn, dmpfn])
            # dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotMtz2PdbxBad(self):
        """  Test mtz to pdbx conversion
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            diagfn = "sf-convert-diags-bad.cif"
            ciffn = "sf-convert-datafile-bad.cif"
            dmpfn = "sf-convert-mtzdmp-bad.log"
            #
            #self.__testFileMtzRunaway  = "bad-runaway.mtz"
            #self.__testFileXyzRunaway  = "bad-runaway.cif"
            #
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            mtzPath = os.path.join(self.__testFilePath, self.__testFileMtzBad)
            dp.imp(mtzPath)
            # xyzPath=os.path.join(self.__testFilePath,self.__testFileXyzBad)
            dp.setTimeout(15)
            # dp.addInput(name="xyz_file_path",value=xyzPath)
            dp.op("annot-sf-convert")
            dp.expLog("sf-convert-bad.log")
            dp.expList(dstPathList=[ciffn, diagfn, dmpfn])
            # dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotMtz2PdbxBadTimeout(self):
        """  Test mtz to pdbx conversion
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            diagfn = "sf-convert-diags-bad-runaway.cif"
            ciffn = "sf-convert-datafile-bad-runaway.cif"
            dmpfn = "sf-convert-mtzdmp-bad-runaway.log"
            #
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            mtzPath = os.path.join(self.__testFilePath, self.__testFileMtzRunaway)
            dp.imp(mtzPath)
            dp.setTimeout(15)
            dp.op("annot-sf-convert")
            dp.expLog("sf-convert-runaway.log")
            dp.expList(dstPathList=[ciffn, diagfn, dmpfn])
            # dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testMapFix(self):
        """  Test mapfix utility
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:

            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            #
            inpPath = os.path.join(self.__testFilePath, self.__testMapNormal)
            of = self.__testMapNormal + "-fix.map"
            dp.imp(inpPath)
            dp.op("mapfix-big")
            dp.expLog("mapfix-big.log")
            dp.exp(of)
            # dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testSpecialPosition(self):
        """  Test for atom on special position
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:

            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            #
            # dp.setDebugMode(True)
            #
            inpPath = os.path.join(self.__testFilePath, self.__testFileValidateXyz)
            dp.imp(inpPath)
            dp.op("annot-dcc-special-position")
            dp.expLog("special-position.log")
            dp.exp("special-position-output.log")
            f = open('special-position-output.log', 'r')
            lines = f.read()
            f.close()
            self.assertIn('No atoms sit on special position', lines)
            dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

        # This case has atoms on special position that needs correction
        try:

            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            #
            # dp.setDebugMode(True)
            #
            inpPath = os.path.join(self.__testFilePath, self.__testSpecialPosition)
            dp.imp(inpPath)
            dp.op("annot-dcc-special-position")
            dp.expLog("special-position2.log")
            dp.exp("special-position-output2.log")
            f = open('special-position-output2.log', 'r')
            lines = f.read()
            f.close()
            self.assertIn('Error: Wrong occupancy of 1.00 for atom (O : id=D_HOH_1)', lines)
            dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testFixSpecialPosition(self):
        """  Test for fixing atoms on special position
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:

            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            #
            inpPath = os.path.join(self.__testFilePath, self.__testFileValidateXyz)
            dp.imp(inpPath)
            dp.op("annot-dcc-fix-special-position")
            dp.expLog("special-position-fix.log")
            dp.exp("special-position-output-fix.log")

            # No output - none on special
            self.assertEqual(['missing'], dp.getResultPathList())

            f = open('special-position-output-fix.log', 'r')
            lines = f.read()
            f.close()
            self.assertIn('No atoms sit on special position', lines)
            dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

        # This case has atoms on special position that needs correction
        try:

            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            #
            # dp.setDebugMode(True)
            #
            inpPath = os.path.join(self.__testFilePath, self.__testSpecialPosition)
            dp.imp(inpPath)
            dp.op("annot-dcc-fix-special-position")
            dp.expLog("special-position-fix2.log")
            dp.exp("special-position-output-fix2.log")

            print(dp.getResultPathList())

            # We expect output
            self.assertNotEqual(['missing'], dp.getResultPathList())

            dp.expList(dstPathList=['special-position-out-fix2.cif'])
            # Check output - for differences...

            f = open('special-position-output-fix2.log', 'r')
            lines = f.read()
            f.close()
            self.assertIn('Error: Wrong occupancy of 1.00 for atom (O : id=D_HOH_1)', lines)
            dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testEm2EmSpider(self):
        """  Test mapfix utility
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:

            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            #
            inpPath = os.path.join(self.__testFilePath, self.__testMapSpider)
            of = self.__testMapSpider + "-spider-cnv.map"
            dp.imp(inpPath)
            pixelSize = 2.54
            dp.addInput(name="pixel-spacing-x", value=pixelSize)
            dp.addInput(name="pixel-spacing-y", value=pixelSize)
            dp.addInput(name="pixel-spacing-z", value=pixelSize)
            dp.op("em2em-spider")
            dp.expLog("em2em-spider.log")
            dp.exp(of)
            # dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotPrdSearch(self):
        """  Test case for PRD Search --
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            ofn = "prd-search-result.cif"
            firstModelPath = os.path.abspath('firstmodel.cif')
            logFilePath = os.path.abspath("prd-search-log.log")
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath = os.path.join(self.__testFilePath, self.__testFilePrdSearch)
            dp.imp(inpPath)
            dp.addInput(name='firstmodel', value=firstModelPath)
            dp.addInput(name='logfile', value=logFilePath)
            dp.op("prd-search")
            dp.expLog("prd-search-execution.log")
            dp.exp(ofn)
            # dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testAnnotUpdateDepositorAssembly(self):
        """  Update deposition provided assembly info into model (need better test example)
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            of = "annot-update-assembly-" + self.__testDepAssembly

            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            inpPath = os.path.join(self.__testFilePath, self.__testDepAssembly)
            dp.imp(inpPath)
            dp.op("annot-update-dep-assembly-info")
            dp.expLog("annot-update-dep-assembly.log")
            dp.exp(of)
            dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()


def suiteAnnotPrdSearchTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotPrdSearch"))
    return suiteSelect


def suiteAnnotEmTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testMapFix"))
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testEm2EmSpider"))
    return suiteSelect


def suiteAnnotSiteTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotSite"))
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotSiteAndMerge"))
    return suiteSelect


def suiteAnnotSiteAltTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotSiteAlt"))
    return suiteSelect


def suiteAnnotNMRTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotCSCheck"))
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotCSCoordCheck"))
    return suiteSelect


def suiteArchiveValidationXrayTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotValidateListXrayTest"))
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
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotUpdateDepositorAssembly"))
    return suiteSelect


def suiteSolventPlusDerivedTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotRepositionSolvent"))
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotRepositionSolventPlusDerived"))
    return suiteSelect


def suiteMergeSeqAssignTests():
    suiteSelect = unittest.TestSuite()
    return suiteSelect


def suiteMapCalcTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotMapCalc"))
    # suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotLigandMapCalc"))
    return suiteSelect


def suiteSpecialPositionTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testSpecialPosition"))
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testFixSpecialPosition"))
    return suiteSelect


def suiteRsrCalcTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotDccRsrReport"))
    return suiteSelect


def suiteFormatCheckTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotFormatCheck"))
    return suiteSelect


def suiteValidateGeometryCheckTests():
    suiteSelect = unittest.TestSuite()
    # suiteSelect.addTest(RcsbDpUtilityAnnotTests("testValidateGeometryCheck"))
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotValidateGeometryCheck"))
    return suiteSelect


def suiteGetCorresInfoTests():
    suiteSelect = unittest.TestSuite()
    # suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotGetCorresInfo"))
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotGetCorresInfo"))
    return suiteSelect


def suiteAnnotDccTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotDccReport"))
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotMtz2PdbxGood"))
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotMtz2PdbxBad"))
    return suiteSelect


def suiteAnnotFormatConvertTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotRcsb2Pdbx"))
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotRcsb2PdbxSQ"))
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotRcsb2PdbxSQAlt"))
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotRcsb2PdbxStrip"))
    return suiteSelect


def suiteArchiveValidationNmrTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(RcsbDpUtilityAnnotTests("testAnnotValidateListNmrTest"))
    return suiteSelect


if __name__ == '__main__':
    # Run all tests --
    # unittest.main()
    #
    doAll = True
#    doAll = True

    if (doAll):
        mySuite = suiteAnnotTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)
        #
        mySuite = suiteAnnotSiteTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)
        #
        mySuite = suiteAnnotSiteAltTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)
        #
        mySuite = suiteAnnotFormatConvertTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)
        #
        mySuite = suiteAnnotNMRTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)

        mySuite = suiteAnnotConsolidatedTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)

        mySuite = suiteSolventPlusDerivedTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)

        mySuite = suiteAnnotFormatConvertTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)

        mySuite = suiteMapCalcTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)

        mySuite = suiteFormatCheckTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)

        mySuite = suiteAnnotDccTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)

        mySuite = suiteValidateGeometryCheckTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)

        mySuite = suiteSpecialPositionTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)

        mySuite = suiteAnnotEmTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)

        mySuite = suiteAnnotPrdSearchTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)

        mySuite = suiteArchiveValidationNmrTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)

        mySuite = suiteArchiveValidationXrayTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)

        mySuite = suiteRsrCalcTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)

    else:
        pass

    mySuite = suiteArchiveValidationXrayTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)
    #
    mySuite = suiteArchiveValidationNmrTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)
    #
    mySuite = suiteGetCorresInfoTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)
