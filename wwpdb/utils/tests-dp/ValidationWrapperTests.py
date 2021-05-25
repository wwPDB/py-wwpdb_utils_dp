##
# Update:

##
"""
Test cases for validation wrapper

"""
import logging
import unittest
import sys
import os

if __package__ is None or __package__ == '':
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT, toolsmissing, mockTopPath  # pylint: disable=import-error
else:
    from .commonsetup import TESTOUTPUT, toolsmissing, mockTopPath

from wwpdb.utils.config.ConfigInfo import getSiteId
from wwpdb.utils.dp.ValidationWrapper import ValidationWrapper

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.setLevel(logging.DEBUG)


class ValidationWrapperTests(unittest.TestCase):
    def setUp(self):
        pass

    def testImport(self):
        _vw = ValidationWrapper(tmpPath=TESTOUTPUT, siteId=getSiteId())  # noqa: F841

    @unittest.skipIf(toolsmissing, "Cannot test validation without tools")
    @unittest.skipIf(True, "Tests do not work yet - need site-config for validation")
    def testWrapper(self):
        """Tests wrapper"""
        modelfile = os.path.join(mockTopPath, 'dp-utils', '1cbs.cif')
        sffile = os.path.join(mockTopPath, 'dp-utils', '1cbs-sf.cif')
        foout = os.path.join(TESTOUTPUT, '1cbs-fo.cif')
        twofoout = os.path.join(TESTOUTPUT, '1cbs-2fo.cif')
        pdf = os.path.join(TESTOUTPUT, '1cbs-val.pdf')
        fullpdf = os.path.join(TESTOUTPUT, '1cbs-full-val.pdf')
        xml = os.path.join(TESTOUTPUT, '1cbs-val.xml')
        svg = os.path.join(TESTOUTPUT, '1cbs-val.svg')
        png = os.path.join(TESTOUTPUT, '1cbs-val.png')
        oflog = os.path.join(TESTOUTPUT, '1cbs-val.log')

        # ofpdf, ofxml, offullpdf, ofpng, ofsvg, ofmtz
        if os.path.exists(foout):
            os.unlink(foout)
        if os.path.exists(twofoout):
            os.unlink(twofoout)

        sys.stderr.write("CKP1\n")
        siteid = getSiteId()
        sys.stderr.write("SITEID %s\n" % siteid)

        vw = ValidationWrapper(tmpPath=TESTOUTPUT, siteId=getSiteId())
        vw.imp(modelfile)
        vw.addInput(name="sf_file_path", value=sffile)

        vw.addInput(name='step_list', value='mogul,percentiles,writexml,writepdf,eds')

        vw.addInput(name='run_dir', value=os.path.join(TESTOUTPUT, 'validation_run'))
        vw.addInput(name="request_annotation_context", value="yes")
        vw.addInput(name="always_clear_calcs", value="yes")

        vw.op("annot-wwpdb-validate-all-sf")

        vw.expLog(oflog)
        ret = vw.expList(dstPathList=[pdf, xml, fullpdf, png, svg, foout, twofoout])

        self.assertTrue(ret, "Writing SF file")
        self.assertTrue(os.path.exists(foout))
        self.assertTrue(os.path.exists(twofoout))


if __name__ == '__main__':
    # Run all tests --
    unittest.main()
