##
#
# File:    RcsbDpUtilityMetalTests.py
# Author:  C. Shao
# Date:    Nov 10,2025
# Version: 0.001
#
# Update:
##
"""
Test cases for running FindGeo and MetalCoord programs on metallic ligands and entries with such ligands.
These cases can serve as examples of how to use the RcsbDpUtility class to run these metal-related analyses.
Comments with self.dp.addInput are deliberately left in the code for users to see how to set optional parameters.
"""

# pylint: disable=unused-import
import logging
import json
import os
import shutil  # noqa: F401
import sys
import unittest

from wwpdb.utils.config.ConfigInfo import getSiteId
from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility

DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DATA_DIR = os.path.join(DIR, "test_files")
TEST_OUTPUT_DIR = os.path.join(DIR, "test_output")  # for debugging, activate cleanup when deployed
if not os.path.exists(TEST_OUTPUT_DIR):
    os.makedirs(TEST_OUTPUT_DIR)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class TestFindGeo(unittest.TestCase):
    """
    -----------
    Unit test for running the ``metal-findgeo`` operation of :class:`RcsbDpUtility`

    ~~~~~
    - Initialize test environment variables and logging:
        - :attr:`__siteId` -- obtained via :func:`getSiteId`
        - :attr:`__sessionPath` -- ``TEST_OUTPUT_DIR``
        - :attr:`__verbose` -- ``False``
        - :attr:`__lfh` -- ``sys.stderr``
    - Instantiate :class:`RcsbDpUtility` as ``self.dp`` with the above settings.
    - Define file paths:
        - ``self.fp_in`` -- path to input CIF (``TEST_DATA_DIR/"4DHV-internal.cif"``)
        - ``self.fp_out`` -- expected output JSON path (``TEST_OUTPUT_DIR/"4DHV-metal-findgeo.json"``)

    Test flow
    ~~~~~~~~~
    1. Enable debug mode on the data-processing utility::
    2. Import the CIF input::
    3. Run the ``metal-findgeo`` operation::
         - The test asserts that ``rt == 0`` indicating success.
    4. Export the operation result to ``self.fp_out``::
         - Assert that the exported file exists.
         - Open and JSON-load the file and assert the resulting object is non-empty.
    5. Any exceptions raised during export are logged and re-raised to surface failures.

    Configurable behaviors
    ~~~~~~~~~~~~~~~~~~~~~~
    Optional inputs illustrated by commented examples in the test:
    - ``excluded-donors`` -- element symbols to exclude as donors (e.g., ``"H"``).
    - ``excluded-metals`` -- comma-separated metal elements to exclude (e.g., ``"Mg,Ca"``).
    - ``metal`` -- restrict search to a specific metal element (e.g., ``"Fe"``).
    - ``threshold`` -- distance threshold override (e.g., ``"2.9"``).
    - ``workdir`` -- alternate temporary working directory for findgeo intermediate files.

    ~~~~~
    - This is a functional/integration-style unit test that depends on external test
        data and the :class:`RcsbDpUtility` implementation.
    - The test verifies end-to-end behavior (import → operation → export) and checks
        only basic non-emptiness of the resulting JSON; it does not assert detailed
        correctness of the findgeo output content.
    """

    def setUp(self):
        self.__siteId = getSiteId()
        self.__sessionPath = TEST_OUTPUT_DIR
        self.__verbose = False
        self.__lfh = sys.stderr

        self.dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)

        self.fp_in = os.path.join(TEST_DATA_DIR, "4DHV-internal.cif")
        self.fp_out = os.path.join(TEST_OUTPUT_DIR, "4DHV-metal-findgeo.json")

    def tearDown(self):
        # shutil.rmtree(TEST_OUTPUT_DIR, ignore_errors=True)  # enable cleanup after debugging
        pass

    def test(self):
        self.dp.setDebugMode(flag=True)
        assert os.path.exists(self.fp_in), "Input file missing!"
        self.dp.imp(self.fp_in)
        logger.info("test input filepath: %s", self.fp_in)

        # self.dp.addInput(name="excluded-donors", value="H")  # for checking carbon-metal interaction
        # self.dp.addInput(name="excluded-metals", value="Mg,Ca")  # exlcuding a list of metal elements
        # self.dp.addInput(name="metal", value="Fe")  # run on a specific metal element only
        # self.dp.addInput(name="threshold", value="2.9")  # extend the default 2.8 range search
        # self.dp.addInput(name="workdir", value="/tmp")  # output findgeo temporary calculation data to a folder other than the default "./findgeo"

        rt = self.dp.op("metal-findgeo")
        logger.info("run FindGeo on %s with return code %s", self.fp_in, rt)
        self.assertEqual(rt, 0)

        try:
            self.dp.exp(self.fp_out)
            logger.info("test output filepath: %s", self.fp_out)
            self.assertTrue(os.path.exists(self.fp_out))  # check if test file exists

            with open(self.fp_out) as f:
                data = json.load(f)
                self.assertTrue(data)  # check if test file is empty

        except Exception as e:
            logger.exception("Failed to export: %s", e)
            raise


class TestMetalCoordStats(unittest.TestCase):
    """
    -----------
    Unit test for running the ``metal-metalcoord-stats`` operation of :class:`RcsbDpUtility`

    ~~~~~
    - Initialize test environment variables and logging:
        - :attr:`__siteId` -- obtained via :func:`getSiteId`
        - :attr:`__sessionPath` -- ``TEST_OUTPUT_DIR``
        - :attr:`__verbose` -- ``False``
        - :attr:`__lfh` -- ``sys.stderr``
    - Instantiate :class:`RcsbDpUtility` as ``self.dp`` with the above settings.
    - Define file paths:
        - ``self.fp_in`` -- path to input CIF (``TEST_DATA_DIR/"4DHV-internal.cif"``)
        - ``self.fp_out`` -- expected output JSON path (``TEST_OUTPUT_DIR/"4DHV-metal-metalcoord-stats.json"``)

    Test flow
    ~~~~~~~~~
    1. Enable debug mode on the data-processing utility::
    2. Import the CIF input::
    3. Run the ``metal-metalcoord-stats`` operation::
            - The test asserts that ``rt == 0`` indicating success.
    4. Export the operation result to ``self.fp_out``::
            - Assert that the exported file exists.
            - Open and JSON-load the file and assert the resulting object is non-empty.
    5. Any exceptions raised during export are logged and re-raised to surface failures.

    Configurable behaviors
    ~~~~~~~~~~~~~~~~~~~~~~
    Optional inputs illustrated by commented examples in the test:
    - ``ligand`` -- CCD ID of the metal ligand to check (e.g., ``"0KA"``).
    - ``max_size`` -- maximum sample size for reference statistics (e.g., ``"2000"``).
    - ``threshold`` -- Procrustes distance threshold for COD reference (e.g., ``"0.2"``).
    - ``workdir`` -- alternate temporary working directory for metalcoord intermediate files.
    - ``pdb`` -- PDB code or file path as input (e.g., ``"4DHV"``).
    - ``metalcoord_exe`` -- path to MetalCoord executable for testing new versions.

    ~~~~~
    - This is a functional/integration-style unit test that depends on external test
        data and the :class:`RcsbDpUtility` implementation.
    - The test verifies end-to-end behavior (import → operation → export) and checks
        only basic non-emptiness of the resulting JSON; it does not assert detailed
        correctness of the metalcoord output content.
    """

    def setUp(self):
        self.__siteId = getSiteId()
        self.__sessionPath = TEST_OUTPUT_DIR
        self.__verbose = False
        self.__lfh = sys.stderr

        self.dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)

        self.fp_in = os.path.join(TEST_DATA_DIR, "4DHV-internal.cif")
        self.fp_out = os.path.join(TEST_OUTPUT_DIR, "4DHV-metal-metalcoord-stats.json")

    def tearDown(self):
        # shutil.rmtree(TEST_OUTPUT_DIR, ignore_errors=True)
        pass

    def test(self):
        self.dp.setDebugMode(flag=True)
        self.dp.imp(self.fp_in)
        logger.info("test input filepath: %s", self.fp_in)

        self.dp.addInput(name="ligand", value="0KA")  # CCD ID of the metal ligand to check on
        # self.dp.addInput(name="max_size", value="2000")  # Maximum sample size for reference statistics.
        # self.dp.addInput(name="threshold", value="0.2")  # Procrustes distance threshold for finding COD reference.
        # self.dp.addInput(name="workdir", value="/tmp")  # output to a folder other than the default "./metalcoord"
        # self.dp.addInput(name="pdb", value="4DHV")  # PDB code or pdb file as input
        # self.dp.addInput(name="metalcoord_exe", value="")  # MetalCoord executable file, only use for testing new versions

        rt = self.dp.op("metal-metalcoord-stats")
        logger.info("run MetalCoord on ligand 0KA in file %s with return code %s", self.fp_in, rt)
        self.assertEqual(rt, 0)

        try:
            self.dp.exp(self.fp_out)
            logger.info("test output filepath: %s", self.fp_out)
            self.assertTrue(os.path.exists(self.fp_out))  # check if test file exists

            with open(self.fp_out) as f:
                data = json.load(f)
                self.assertTrue(data)  # check if test file is empty

        except Exception as e:
            logger.exception("Failed to export: %s", e)
            raise


class TestMetalCoordUpdate(unittest.TestCase):
    """
    -----------
    Unit test for running the ``metal-metalcoord-update`` operation of :class:`RcsbDpUtility`

    ~~~~~
    - Initialize test environment variables and logging:
        - :attr:`__siteId` -- obtained via :func:`getSiteId`
        - :attr:`__sessionPath` -- ``TEST_OUTPUT_DIR``
        - :attr:`__verbose` -- ``False``
        - :attr:`__lfh` -- ``sys.stderr``
    - Instantiate :class:`RcsbDpUtility` as ``self.dp`` with the above settings.
    - Define file paths:
        - ``self.fp_in_ccd`` -- path to input ligand CIF (``TEST_DATA_DIR/"0KA.cif"``)
        - ``self.fp_in_pdb`` -- path to reference PDB/CIF (``TEST_DATA_DIR/"4DHV-internal.cif"``)
        - ``self.fp_out_list`` -- expected output list:
            [ ``TEST_OUTPUT_DIR/"0KA-updated.cif"``, ``TEST_OUTPUT_DIR/"4DHV-metal-metalcoord-update.json"`` ]

    Test flow
    ~~~~~~~~~
    1. Enable debug mode on the data-processing utility.
    2. Import the ligand CCD/CIF input.
    3. Provide the reference PDB/CIF as an additional input (``name="pdb"``).
    4. Run the ``metal-metalcoord-update`` operation:
         - The test asserts that ``rt == 0`` indicating success.
    5. Export the operation result list to ``self.fp_out_list``:
         - Assert that each exported file exists.
         - Open and JSON-load the metadata file and assert the resulting object is non-empty.
    6. Any exceptions raised during export are logged and re-raised to surface failures.

    Configurable behaviors
    ~~~~~~~~~~~~~~~~~~~~~~
    Optional inputs illustrated by commented examples in the test:
    - ``acedrg_exe`` -- path to Acedrg executable for testing alternate versions.
    - ``metalcoord_exe`` -- path to MetalCoord executable for testing alternate versions.
    - ``servalcat_exe`` -- path to Servalcat executable for testing alternate versions.
    - ``workdir`` -- alternate output working directory for metalcoord intermediate files.
    - ``threshold`` -- Procrustes distance threshold for COD reference (e.g., ``"0.2"``).

    ~~~~~
    - This is a functional/integration-style unit test that depends on external test
      data and the :class:`RcsbDpUtility` implementation.
    - The test verifies end-to-end behavior (import → operation → export) and checks
      only basic non-emptiness of the resulting files; it does not assert detailed
      correctness of the metalcoord update contents.
    """

    def setUp(self):
        self.__siteId = getSiteId()
        self.__sessionPath = TEST_OUTPUT_DIR
        self.__verbose = False
        self.__lfh = sys.stderr

        self.dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)

        self.fp_in_ccd = os.path.join(TEST_DATA_DIR, "0KA.cif")
        self.fp_in_pdb = os.path.join(TEST_DATA_DIR, "4DHV-internal.cif")
        self.fp_out_list = [os.path.join(TEST_OUTPUT_DIR, "0KA-updated.cif"), os.path.join(TEST_OUTPUT_DIR, "4DHV-metal-metalcoord-update.json")]

    def tearDown(self):
        # shutil.rmtree(TEST_OUTPUT_DIR, ignore_errors=True)
        pass

    def test(self):
        self.dp.setDebugMode(flag=True)
        self.dp.imp(self.fp_in_ccd)
        logger.info("test input filepath: %s", self.fp_in_ccd)

        self.dp.addInput(name="pdb", value=os.path.join(TEST_DATA_DIR, "4DHV-internal.cif"))  # PDB code or pdb file as reference
        # self.dp.addInput(name="acedrg_exe", value="")  # Acedrg executable file, only use for testing new versions
        # self.dp.addInput(name="metalcoord_exe", value="")  # MetalCoord executable file, only use for testing new versions
        # self.dp.addInput(name="servalcat_exe", value="")   # Servalcat executable file, only use for testing new versions
        # self.dp.addInput(name="workdir", value="/tmp")  # Directory to write outputs. Default is metalcoord subfolder in the current folder
        # self.dp.addInput(name="threshold", value="0.2")  # Procrustes distance threshold for finding COD reference.

        rt = self.dp.op("metal-metalcoord-update")
        logger.info("run MetalCoord on ligand file %s with return code %s", self.fp_in_ccd, rt)
        self.assertEqual(rt, 0)

        try:
            self.dp.expList(self.fp_out_list)
            logger.info("test output filepath list: %s", self.fp_out_list)

            [ligand_cif, metal_json] = self.fp_out_list
            self.assertTrue(os.path.exists(ligand_cif))  # check if ligand cif file exists
            self.assertTrue(os.path.exists(metal_json))  # check if json file exists

            with open(metal_json) as f:
                data = json.load(f)
                self.assertTrue(data)  # check if json file is empty

        except Exception as e:
            logger.exception("Failed to export: %s", e)
            raise


def suite():
    loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    test_suite.addTests(loader.loadTestsFromTestCase(TestFindGeo))
    test_suite.addTests(loader.loadTestsFromTestCase(TestMetalCoordStats))
    test_suite.addTests(loader.loadTestsFromTestCase(TestMetalCoordUpdate))

    return test_suite


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite())
