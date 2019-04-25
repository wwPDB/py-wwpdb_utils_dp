"""

File:    ImportTests.py

     Some test cases ..

"""
import unittest

if __package__ is None or __package__ == '':
    import sys
    from os import path
    sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
    from commonsetup import TESTOUTPUT
else:
    from .commonsetup import TESTOUTPUT

from wwpdb.utils.dp.DataFileAdapter import DataFileAdapter


class ImportTests(unittest.TestCase):
    def setUp(self):
        pass

    def testInstantiate(self):
        pass

