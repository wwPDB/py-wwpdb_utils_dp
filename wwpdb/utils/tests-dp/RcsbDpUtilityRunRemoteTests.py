import logging
import os
import platform
import random
import sys
import tempfile
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
        # self.__siteWebAppsSessionsPath = self.__cI.get('SITE_WEB_APPS_SESSIONS_PATH')
        self.__tmpPath = os.path.join(HERE, 'test-output')
        self.__siteWebAppsSessionsPath = self.__tmpPath
        self.__testFilePath = os.path.join(TOPDIR, 'wwpdb', 'mock-data', 'dp-utils')
        #
        self.__testFileAnnotLink = '3rij.cif'
        self.__testFileAnnotCisPeptide = '5hoh.cif'
        self.__testFileAnnotValidate = '3rij.cif'
        self.__testFileAnnotNA = '1o3q.cif'
        self.__testFileAnnotSite = '1xbb.cif'
        self.__testIdAnnotSite = '1xbb'
        #
        # OK
        self.__testFileAnnotRcsb = 'rcsb033781.cif'
        #
        self.__testFileStarCs = "star_16703_test_2.str"
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
        self.__testMapLarge = "large.map"

        self.__testValidateXrayIdList = ['1cbs', '4hea']
        self.__testValidateNmrIdList = ['2MM4', '2MMZ']

    def tearDown(self):
        pass
        # if os.path.exists(self.__tmpPath):
        #     shutil.rmtree(self.__tmpPath)

    def test_AnnotValidateGeometryCheck(self):
        """  Test of updating geometrical validation diagnostics -
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        of = os.path.join(self.__tmpPath, "annot-validate-geometry-check.cif")
        dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
        inp_path = os.path.join(self.__testFilePath, self.__testFileAnnotSite)
        dp.imp(inp_path)
        ret = dp.op("annot-validate-geometry")
        dp.expLog(os.path.join(self.__tmpPath, "annot-validate-geometry-check-pdbx.log"))
        dp.exp(of)
        # dp.cleanup()

        self.assertTrue(ret == 0)
        self.assertTrue(os.path.exists(of))

    def test_AnnotValidateGeometryCheckRemote(self):
        """  Test of updating geometrical validation diagnostics -
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))

        of = os.path.join(self.__tmpPath, "annot-validate-geometry-check-remote.cif")
        dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
        inp_path = os.path.join(self.__testFilePath, self.__testFileAnnotSite)
        dp.imp(inp_path)
        # dp.setRunRemote()
        ret = dp.op("annot-validate-geometry")
        dp.expLog(os.path.join(self.__tmpPath, "annot-validate-geometry-check-pdbx-remote.log"))
        dp.exp(of)
        # dp.cleanup()

        self.assertTrue(ret == 0)
        self.assertTrue(os.path.exists(of))

    def testAnnotRcsb2PdbxRemote(self):
        """  RCSB CIF -> PDBx conversion  (Using the smaller application in the annotation package)

             Converting to RCSB to PDB id in _entry.id and related items.
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        of = os.path.join(self.__tmpPath, "annot-rcsb2pdbx-withpdbid-" + self.__testFileAnnotRcsb)
        dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
        inpPath = os.path.join(self.__testFilePath, self.__testFileAnnotRcsb)
        dp.imp(inpPath)
        # dp.setRunRemote()
        ret = dp.op("annot-rcsb2pdbx-withpdbid")
        dp.expLog(os.path.join(self.__tmpPath, "annot-rcsb2pdbx.log"))
        dp.exp(of)
        # dp.cleanup()

        self.assertTrue(ret == 0)
        self.assertTrue(os.path.exists(of))

    def testAnnotValidateListXrayTestRemote(self):
        """  Test create validation report for the test list of example PDB ids (x-ray examples)
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        for pdbId in self.__testValidateXrayIdList:
            self.__tmpPath = tempfile.mkdtemp(dir=self.__siteWebAppsSessionsPath)
            logger.info("\nStarting {} in {}\n".format(pdbId, self.__tmpPath))
            ofpdf = os.path.join(self.__tmpPath, pdbId + "-valrpt.pdf")
            ofxml = os.path.join(self.__tmpPath, pdbId + "-valdata.xml")
            offullpdf = os.path.join(self.__tmpPath, pdbId + "-valrpt_full.pdf")
            ofpng = os.path.join(self.__tmpPath, pdbId + "-val-slider.png")
            ofsvg = os.path.join(self.__tmpPath, pdbId + "-val-slider.svg")
            #
            testFileValidateXyz = pdbId + ".cif"
            testFileValidateSf = pdbId + "-sf.cif"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            # dp.setDebugMode(True)

            xyzPath = os.path.abspath(os.path.join(self.__testFilePath, testFileValidateXyz))
            sfPath = os.path.abspath(os.path.join(self.__testFilePath, testFileValidateSf))
            # dp.addInput(name="request_annotation_context", value="yes")
            dp.addInput(name="request_validation_mode", value="annotate")
            dp.addInput(name='run_dir',
                        value=os.path.join(self.__siteWebAppsSessionsPath, "validation_%s" % random.randrange(9999999)))
            # dp.addInput(name="request_validation_mode", value="server")
            dp.imp(xyzPath)
            dp.addInput(name="sf_file_path", value=sfPath)
            # dp.setRunRemote()
            ret = dp.op("annot-wwpdb-validate-all")
            dp.expLog(os.path.join(self.__tmpPath, pdbId + "-annot-validate-test.log"))
            dp.expList(dstPathList=[ofpdf, ofxml, offullpdf, ofpng, ofsvg])
            # dp.cleanup()

            self.assertTrue(ret == 0)
            self.assertTrue(os.path.exists(ofpdf))
            self.assertTrue(os.path.exists(ofxml))
            self.assertTrue(os.path.exists(offullpdf))
            self.assertTrue(os.path.exists(ofpng))
            self.assertTrue(os.path.exists(ofsvg))

    def testAnnotValidateListNmrTestRemote(self):
        """  Test create validation report for the test list of example PDB ids (NMR examples)
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        for pdbId in self.__testValidateNmrIdList:
            self.__tmpPath = tempfile.mkdtemp(dir=self.__siteWebAppsSessionsPath)
            logger.info("\nStarting {} in {}\n".format(pdbId, self.__tmpPath))
            ofpdf = os.path.join(self.__tmpPath, pdbId + "-valrpt.pdf")
            ofxml = os.path.join(self.__tmpPath, pdbId + "-valdata.xml")
            offullpdf = os.path.join(self.__tmpPath, pdbId + "-valrpt_full.pdf")
            ofpng = os.path.join(self.__tmpPath, pdbId + "-val-slider.png")
            ofsvg = os.path.join(self.__tmpPath, pdbId + "-val-slider.svg")
            #
            testFileValidateXyz = pdbId + ".cif"
            testFileValidateCs = pdbId + "-cs.cif"
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)

            xyzPath = os.path.abspath(os.path.join(self.__testFilePath, testFileValidateXyz))
            csPath = os.path.abspath(os.path.join(self.__testFilePath, testFileValidateCs))
            dp.addInput(name="request_annotation_context", value="yes")
            dp.addInput(name='run_dir',
                        value=os.path.join(self.__siteWebAppsSessionsPath, "validation_%s" % random.randrange(9999999)))
            # adding explicit selection of steps --
            # Alternate
            #dp.addInput(name="step_list", value=" coreclust,chemicalshifts,writexml,writepdf ")
            dp.addInput(name='kind', value='nmr')
            dp.imp(xyzPath)
            dp.addInput(name="cs_file_path", value=csPath)
            # dp.setRunRemote()
            ret = dp.op("annot-wwpdb-validate-all")
            dp.expLog(os.path.join(self.__tmpPath, pdbId + "-annot-validate-test.log"))
            dp.expList(dstPathList=[ofpdf, ofxml, offullpdf, ofpng, ofsvg])
            # dp.cleanup()

            self.assertTrue(ret == 0)
            self.assertTrue(os.path.exists(ofpdf))
            self.assertTrue(os.path.exists(ofxml))
            self.assertTrue(os.path.exists(offullpdf))
            self.assertTrue(os.path.exists(ofpng))
            self.assertTrue(os.path.exists(ofsvg))

    def testMapFixRemote(self):
        """  Test mapfix utility
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))

        dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
        #
        inpPath = os.path.join(self.__testFilePath, self.__testMapNormal)
        of = os.path.join(self.__tmpPath, self.__testMapNormal + "-fix.map")
        dp.imp(inpPath)
        pixelSize = 2.54
        #dp.addInput(name="pixel-spacing-x", value=pixelSize)
        #dp.addInput(name="pixel-spacing-y", value=pixelSize)
        #dp.addInput(name="pixel-spacing-z", value=pixelSize)
        dp.addInput(name="input_map_file_path", value=inpPath)
        dp.addInput(name="output_map_file_path", value=of)
        dp.addInput(name="label", value='test')
        dp.addInput(name="voxel", value='{0} {0} {0}'.format(pixelSize))
        # dp.setRunRemote()
        ret = dp.op("deposit-update-map-header-in-place")
        dp.expLog(os.path.join(self.__tmpPath, "mapfix-big.log"))
        dp.exp(of)
        # dp.cleanup()

        self.assertTrue(ret == 0)
        self.assertTrue(os.path.exists(of))

    # def testMapFixLargeMapRemote(self):
    #     """  Test mapfix utility
    #     """
    #     logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
    #     logger.info("\nRunning in {}\n".format(self.__tmpPath))
    #
    #     dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
    #     #
    #     inpPath = os.path.join(self.__testFilePath, self.__testMapLarge)
    #     of = os.path.join(self.__tmpPath, self.__testMapLarge + "-fix.map")
    #     dp.imp(inpPath)
    #     pixelSize = 1.327
    #     dp.addInput(name="input_map_file_path", value=inpPath)
    #     dp.addInput(name="output_map_file_path", value=of)
    #     dp.addInput(name="label", value='test')
    #     dp.addInput(name="voxel", value='{0} {0} {0}'.format(pixelSize))
    #     # dp.setRunRemote()
    #     ret = dp.op("deposit-update-map-header-in-place")
    #     dp.expLog(os.path.join(self.__tmpPath, "mapfix-big.log"))
    #     dp.exp(of)
    #     # dp.cleanup()
    #
    #     self.assertTrue(ret == 0)
    #     self.assertTrue(os.path.exists(of))

    def testAnnotSiteRemote(self):
        """  Calculate site environment
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        of = os.path.join(self.__tmpPath, "annot-site-" + self.__testFileAnnotSite)
        dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
        inpPath = os.path.join(self.__testFilePath, self.__testFileAnnotSite)
        dp.imp(inpPath)
        dp.addInput(name="block_id", value=self.__testIdAnnotSite)
        # dp.setRunRemote()
        ret = dp.op("annot-site")
        dp.expLog(os.path.join(self.__tmpPath, "annot-site.log"))
        dp.exp(of)
        # dp.cleanup()

        self.assertTrue(ret == 0)
        self.assertTrue(os.path.exists(of))

    def test_AnnotMergeRemote(self):
        """  Test of updating geometrical validation diagnostics -
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        for pdbId in self.__testValidateXrayIdList:
            self.__tmpPath = tempfile.mkdtemp(dir=self.__siteWebAppsSessionsPath)
            testFileValidateXyz = pdbId + ".cif"
            xyzPath = os.path.abspath(os.path.join(self.__testFilePath, testFileValidateXyz))

            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            of = os.path.join(self.__tmpPath, "annot-merge-xyz-remote.cif")
            dp.imp(xyzPath)
            dp.addInput(name="new_coordinate_file_path", value=xyzPath)
            dp.addInput(name="new_coordinate_format", value='cif')
            # dp.setRunRemote()
            ret = dp.op("annot-merge-xyz")
            dp.expLog(os.path.join(self.__tmpPath, "annot-merge-xyz-remote.log"))
            dp.exp(of)
            # dp.cleanup()

            self.assertTrue(ret == 0)
            self.assertTrue(os.path.exists(of))

    def testAnnotMtz2PdbxGood(self):
        """  Test mtz to pdbx conversion  (good mtz)
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        diagfn = os.path.join(self.__tmpPath, "sf-convert-diags.cif")
        ciffn = os.path.join(self.__tmpPath, "sf-convert-datafile.cif")
        dmpfn = os.path.join(self.__tmpPath, "sf-convert-mtzdmp.log")
        #
        dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
        mtzPath = os.path.join(self.__testFilePath, self.__testFileMtzGood)
        dp.imp(mtzPath)
        dp.setTimeout(15)
        ret = dp.op("annot-sf-convert")
        dp.expLog(os.path.join(self.__tmpPath, "sf-convert.log"))
        dp.expList(dstPathList=[ciffn, diagfn, dmpfn])
        # dp.cleanup()

        self.assertTrue(ret == 0)
        self.assertTrue(ciffn)
        self.assertTrue(diagfn)
        self.assertTrue(dmpfn)


if __name__ == '__main__':
    unittest.main()
