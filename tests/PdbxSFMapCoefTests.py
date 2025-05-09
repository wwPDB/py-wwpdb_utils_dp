##
# Update:

##
"""
Test cases for SF Map coefficients

"""

import logging
import os
import unittest

if __package__ is None or __package__ == "":
    import sys
    from os import path

    sys.path.append(path.dirname(path.abspath(__file__)))
    from commonsetup import TESTOUTPUT, mockTopPath, toolsmissing  # pylint: disable=import-error
else:
    from .commonsetup import TESTOUTPUT, mockTopPath, toolsmissing

from wwpdb.utils.dp.PdbxSFMapCoefficients import PdbxSFMapCoefficients

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class PdbxSFTests(unittest.TestCase):
    def setUp(self):
        pass

    def testImport(self):
        _p = PdbxSFMapCoefficients()  # noqa: F841

    @unittest.skipIf(toolsmissing, "Cannot test sf conversion without tools")
    def testMtzConversion(self):
        """Tests conversion of MTZ file to sf file"""
        inpfile = os.path.join(mockTopPath, "dp-utils", "mtz-good.mtz")
        foout = os.path.join(TESTOUTPUT, "fo.cif")
        twofoout = os.path.join(TESTOUTPUT, "2fo.cif")
        if os.path.exists(foout):
            os.unlink(foout)
        if os.path.exists(twofoout):
            os.unlink(twofoout)

        psf = PdbxSFMapCoefficients()
        ret = psf.read_mtz_sf(inpfile)
        self.assertTrue(ret, "Error parsing mtz file")
        ret = psf.write_mmcif_coef(foout, twofoout, "zyxw")
        self.assertTrue(ret, "Writing SF file")
        self.assertTrue(os.path.exists(foout))
        self.assertTrue(os.path.exists(twofoout))


if __name__ == "__main__":
    # Run all tests --
    unittest.main()
