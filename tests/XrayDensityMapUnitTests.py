##
# File:    XrayDensityMapUnitTests.py
#
# Update:
##
"""
Hermetic unit tests for wwpdb.utils.dp.electron_density.x_ray_density_map.  The node based
volume server tools are replaced by small python scripts so the full pipeline can be run.

"""

import logging
import os
import shutil
import sys
import tempfile
import unittest
from typing import Any, Dict, List, Optional
from unittest import mock

import gemmi

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.abspath(__file__)))

from wwpdb.utils.dp.electron_density.x_ray_density_map import XrayVolumeServerMap, run_process_with_gemmi

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Fake volume-server-pack: "pack xray <2fofc> <fofc> <out>" - checks inputs and writes output
FAKE_PACK = """import os, sys
assert sys.argv[1] == "xray"
assert os.path.exists(sys.argv[2]) and os.path.exists(sys.argv[3])
with open(sys.argv[-1], "w") as ofh:
    ofh.write("mdb")
"""

# Fake volume-server-query: "query --jobs <json>" - writes output described in json
FAKE_QUERY = """import json, os, sys
with open(sys.argv[-1]) as ifh:
    jobs = json.load(ifh)
for job in jobs:
    with open(os.path.join(job["outputFolder"], job["outputFilename"]), "w") as ofh:
        ofh.write("bcif:" + job["source"]["id"] + ":" + str(job["params"]["detail"]))
"""

FAKE_FAIL = "import sys\nsys.exit(1)\n"

MODULE = "wwpdb.utils.dp.electron_density.x_ray_density_map"


class XrayDensityMapUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        testFiles = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_files")
        self.__twoFofc = os.path.join(testFiles, "2gc2_validation_2fo-fc_map_coef.cif")
        self.__fofc = os.path.join(testFiles, "2gc2_validation_fo-fc_map_coef.cif")
        self.__coord = os.path.join(testFiles, "2gc2.cif")
        self.__workDir = tempfile.mkdtemp()
        self.__scriptDir = tempfile.mkdtemp()
        self.__outDir = tempfile.mkdtemp()
        self.__pack = self.__writeScript("pack.py", FAKE_PACK)
        self.__query = self.__writeScript("query.py", FAKE_QUERY)
        self.__fail = self.__writeScript("fail.py", FAKE_FAIL)
        self.__out = os.path.join(self.__outDir, "out", "xray.bcif")

    def tearDown(self) -> None:
        for dirPath in [self.__workDir, self.__scriptDir, self.__outDir]:
            shutil.rmtree(dirPath, ignore_errors=True)

    def __writeScript(self, name: str, content: str) -> str:
        pth = os.path.join(self.__scriptDir, name)
        with open(pth, "w") as ofh:
            ofh.write(content)
        return pth

    def __xrm(self, nodePath: Optional[str] = sys.executable, packPath: Optional[str] = None, queryPath: Optional[str] = None) -> XrayVolumeServerMap:
        return XrayVolumeServerMap(
            coord_path=self.__coord,
            binary_map_out=self.__out,
            node_path=nodePath,
            volume_server_pack_path=packPath if packPath is not None else self.__pack,
            volume_server_query_path=queryPath if queryPath is not None else self.__query,
            working_dir=self.__workDir,
            two_fofc_mmcif_map_coeff_in=self.__twoFofc,
            fofc_mmcif_map_coeff_in=self.__fofc,
        )

    def testIntermediatePaths(self) -> None:
        xrm = self.__xrm()
        self.assertEqual(xrm.mdb_map_path, os.path.join(self.__workDir, "mdb_map.mdb"))
        self.assertEqual(xrm.two_fo_fc_map, os.path.join(self.__workDir, "2fofc.map"))
        self.assertEqual(xrm.fo_fc_map, os.path.join(self.__workDir, "fofc.map"))

    def testGemmiSf2MapDifferenceMap(self) -> None:
        xrm = self.__xrm()
        mapOut = os.path.join(self.__workDir, "diff.map")
        self.assertTrue(xrm.gemmi_sf2map(self.__fofc, mapOut, "pdbx_DELFWT", "pdbx_DELPHWT"))
        ccp4 = gemmi.read_ccp4_map(mapOut)  # pylint: disable=no-member
        self.assertGreater(ccp4.grid.nu, 0)
        self.assertGreater(ccp4.grid.nv, 0)
        self.assertGreater(ccp4.grid.nw, 0)

    def testGemmiSf2MapWriteMissing(self) -> None:
        """If the map is not written, failure is reported"""
        xrm = self.__xrm()
        mapOut = os.path.join(self.__workDir, "nomap.map")
        with mock.patch("%s.gemmi.Ccp4Map" % MODULE) as mockCcp4:
            self.assertFalse(xrm.gemmi_sf2map(self.__twoFofc, mapOut, "pdbx_FWT", "pdbx_PHWT"))
        mockCcp4.return_value.write_ccp4_map.assert_called_once_with(mapOut)

    def testRunProcess(self) -> None:
        xrm = self.__xrm()
        self.assertTrue(xrm.run_process())
        self.assertTrue(os.path.exists(xrm.two_fo_fc_map))
        self.assertTrue(os.path.exists(xrm.fo_fc_map))
        self.assertTrue(os.path.exists(xrm.mdb_map_path))
        with open(self.__out) as ifh:
            self.assertEqual(ifh.read(), "bcif:x-ray:4")
        self.assertTrue(os.path.exists(os.path.join(self.__workDir, "x_ray_volume_x-ray-cell_d4.bcif")))

    def testRunProcessMapFailure(self) -> None:
        xrm = XrayVolumeServerMap(
            coord_path=self.__coord,
            binary_map_out=self.__out,
            node_path=sys.executable,
            volume_server_pack_path=self.__pack,
            volume_server_query_path=self.__query,
            working_dir=self.__workDir,
            two_fofc_mmcif_map_coeff_in=self.__twoFofc,
            fofc_mmcif_map_coeff_in=self.__twoFofc,  # Lacks difference map columns
        )
        with mock.patch("%s.run_command_and_check_output_file" % MODULE) as mockRun:
            self.assertFalse(xrm.run_process())
        mockRun.assert_not_called()
        self.assertFalse(os.path.exists(self.__out))

    def testRunProcessPackFailure(self) -> None:
        xrm = self.__xrm(packPath=self.__fail)
        with mock.patch("%s.convert_mdb_to_binary_cif" % MODULE) as mockConv:
            self.assertFalse(xrm.run_process())
        mockConv.assert_not_called()
        self.assertFalse(os.path.exists(self.__out))

    def testRunProcessQueryFailure(self) -> None:
        xrm = self.__xrm(queryPath=self.__fail)
        self.assertFalse(xrm.run_process())
        self.assertTrue(os.path.exists(xrm.mdb_map_path))
        self.assertFalse(os.path.exists(self.__out))

    def testMakeMapsToServeChecks(self) -> None:
        mapA = os.path.join(self.__workDir, "a.map")
        mapB = os.path.join(self.__workDir, "b.map")
        for pth in [mapA, mapB]:
            with open(pth, "w") as ofh:
                ofh.write("map")
        self.assertFalse(self.__xrm(nodePath=None).make_maps_to_serve_with_volume_server(mapA, mapB))
        self.assertFalse(self.__xrm(packPath="").make_maps_to_serve_with_volume_server(mapA, mapB))
        self.assertTrue(self.__xrm().make_maps_to_serve_with_volume_server(mapA, mapB))

    def testMakeVolumeServerMapChecks(self) -> None:
        mapA = os.path.join(self.__workDir, "a.map")
        mapB = os.path.join(self.__workDir, "b.map")
        with open(mapA, "w") as ofh:
            ofh.write("map")
        with mock.patch("%s.run_command_and_check_output_file" % MODULE, return_value=True) as mockRun:
            self.assertFalse(self.__xrm(nodePath="").make_volume_server_map(mapA, mapA))
            self.assertFalse(self.__xrm(packPath="").make_volume_server_map(mapA, mapA))
            self.assertFalse(self.__xrm(packPath=os.path.join(self.__scriptDir, "nopack")).make_volume_server_map(mapA, mapA))
            # Second map missing
            self.assertFalse(self.__xrm().make_volume_server_map(mapA, mapB))
            mockRun.assert_not_called()
            xrm = self.__xrm(nodePath="mynode")
            self.assertTrue(xrm.make_volume_server_map(mapA, mapA))
        mockRun.assert_called_once_with(
            command="mynode %s xray %s %s %s" % (self.__pack, mapA, mapA, xrm.mdb_map_path),
            workdir=None,
            process_name="make mdb_map",
            output_file=xrm.mdb_map_path,
        )

    def testConvertMdbMapToBinaryCifArgs(self) -> None:
        xrm = self.__xrm(nodePath="mynode", queryPath="myquery")
        with mock.patch("%s.convert_mdb_to_binary_cif" % MODULE, return_value=True) as mockConv:
            self.assertTrue(xrm.convert_mdb_map_to_binary_cif())
        mockConv.assert_called_once_with(
            map_id="x_ray_volume",
            source_id="x-ray",
            output_file=self.__out,
            working_dir=self.__workDir,
            mdb_map_path=xrm.mdb_map_path,
            volume_server_query_path="myquery",
            node_path="mynode",
            detail=4,
        )

    def testConvertMdbMapToBinaryCifMissingPaths(self) -> None:
        with mock.patch("%s.convert_mdb_to_binary_cif" % MODULE, return_value=True) as mockConv:
            self.assertFalse(self.__xrm(nodePath=None).convert_mdb_map_to_binary_cif())
            self.assertFalse(self.__xrm(queryPath="").convert_mdb_map_to_binary_cif())
        mockConv.assert_not_called()

    def testRunProcessWithGemmi(self) -> None:
        with mock.patch("%s.tempfile.mkdtemp" % MODULE, return_value=self.__workDir):
            ok = run_process_with_gemmi(
                node_path=sys.executable,
                coord_file=self.__coord,
                two_fofc_mmcif_map_coeff_in=self.__twoFofc,
                fofc_mmcif_map_coeff_in=self.__fofc,
                binary_map_out=self.__out,
                volume_server_pack_path=self.__pack,
                volume_server_query_path=self.__query,
            )
        self.assertTrue(ok)
        with open(self.__out) as ifh:
            self.assertEqual(ifh.read(), "bcif:x-ray:4")
        # Working directory cleaned up
        self.assertFalse(os.path.exists(self.__workDir))

    def testRunProcessWithGemmiArgumentChecks(self) -> None:
        base: Dict[str, Optional[str]] = {
            "node_path": sys.executable,
            "coord_file": self.__coord,
            "two_fofc_mmcif_map_coeff_in": self.__twoFofc,
            "fofc_mmcif_map_coeff_in": self.__fofc,
            "binary_map_out": self.__out,
            "volume_server_pack_path": self.__pack,
            "volume_server_query_path": self.__query,
        }
        overrides: List[Dict[str, Optional[str]]] = [
            {"volume_server_pack_path": None},
            {"volume_server_query_path": None},
            {"coord_file": None},
            {"node_path": ""},
            {"node_path": os.path.join(self.__scriptDir, "no-node")},
            {"fofc_mmcif_map_coeff_in": os.path.join(self.__scriptDir, "missing.cif")},
        ]
        with mock.patch("%s.XrayVolumeServerMap" % MODULE) as mockXrm:
            for override in overrides:
                kwargs: Dict[str, Any] = dict(base)
                kwargs.update(override)
                self.assertFalse(run_process_with_gemmi(**kwargs), "override %r" % override)
        mockXrm.assert_not_called()
        self.assertFalse(os.path.exists(self.__out))


if __name__ == "__main__":
    unittest.main()
