"""

File:    ImportTests.py

     Some test cases ..

"""
import unittest

if __package__ is None or __package__ == "":
    import sys
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT  # noqa: F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import TESTOUTPUT  # noqa: F401 pylint: disable=unused-import

from wwpdb.utils.dp.DataFileAdapter import DataFileAdapter  # noqa: F401 pylint: disable=unused-import
from wwpdb.utils.dp.DensityWrapper import DensityWrapper  # noqa: F401 pylint: disable=unused-import
from wwpdb.utils.dp.PdbxChemShiftReport import PdbxChemShiftReport  # noqa: F401 pylint: disable=unused-import
from wwpdb.utils.dp.PdbxMergeCategory import PdbxMergeCategory
from wwpdb.utils.dp.PdbxSFMapCoefficients import PdbxSFMapCoefficients
from wwpdb.utils.dp.PdbxStripCategory import PdbxStripCategory
from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility
from wwpdb.utils.dp.RunRemote import RunRemote  # noqa: F401 pylint: disable=unused-import
from wwpdb.utils.dp.ValidationWrapper import ValidationWrapper


class ImportTests(unittest.TestCase):
    def setUp(self):
        pass

    def testInstantiate(self):
        _pmc = PdbxMergeCategory()  # noqa: F841
        _psc = PdbxStripCategory()  # noqa: F841
        _rdp = RcsbDpUtility()  # noqa: F841
        _vw = ValidationWrapper()  # noqa: F841
        _pdmc = PdbxSFMapCoefficients()  # noqa: F841
