##
# File:    EmDensityMapTests.py
#
# Update:
##
"""
Hermetic unit tests for wwpdb.utils.dp.electron_density.em_density_map.  The node based volume
server tools are replaced by small python scripts so no external binaries are required.

"""

import logging
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.abspath(__file__)))

from wwpdb.utils.dp.electron_density.em_density_map import EmVolumes

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Fake volume-server-pack: "pack em <in> <out>" - writes output
FAKE_PACK = """import sys
with open(sys.argv[-1], "w") as ofh:
    ofh.write("mdb:" + sys.argv[1] + ":" + sys.argv[2])
"""

# Fake volume-server-query: "query --jobs <json>" - writes output described in json
FAKE_QUERY = """import json, os, sys
with open(sys.argv[-1]) as ifh:
    jobs = json.load(ifh)
for job in jobs:
    with open(os.path.join(job["outputFolder"], job["outputFilename"]), "w") as ofh:
        ofh.write("bcif:" + job["source"]["id"] + ":" + str(job["params"]["detail"]))
"""

# Fake tool that fails
FAKE_FAIL = """import sys
sys.exit(3)
"""


class EmDensityMapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__workDir = tempfile.mkdtemp()
        self.__scriptDir = tempfile.mkdtemp()
        self.__outDir = tempfile.mkdtemp()
        self.__pack = self.__writeScript("pack.py", FAKE_PACK)
        self.__query = self.__writeScript("query.py", FAKE_QUERY)
        self.__fail = self.__writeScript("fail.py", FAKE_FAIL)
        self.__emMap = os.path.join(self.__outDir, "emd_1234.map")
        with open(self.__emMap, "w") as ofh:
            ofh.write("map")

    def tearDown(self) -> None:
        for dirPath in [self.__workDir, self.__scriptDir, self.__outDir]:
            shutil.rmtree(dirPath, ignore_errors=True)

    def __writeScript(self, name: str, content: str) -> str:
        pth = os.path.join(self.__scriptDir, name)
        with open(pth, "w") as ofh:
            ofh.write(content)
        return pth

    def testConstructor(self) -> None:
        em = EmVolumes(
            em_map="/a/b/emd_1.map",
            node_path="node",
            volume_server_pack_path="pack",
            volume_server_query_path="query",
            binary_map_out="out.bcif",
            working_dir=self.__workDir,
        )
        self.assertEqual(em.em_map_name, "emd_1.map")
        self.assertEqual(em.workdir, self.__workDir)
        self.assertIsNone(em.mdb_map_path)
        self.assertEqual(em.bcif_map_path, "out.bcif")

    def testConstructorDefaultWorkdir(self) -> None:
        em = EmVolumes(em_map="x.map", node_path="n", volume_server_pack_path="p", volume_server_query_path="q", binary_map_out="o", working_dir=None)
        self.assertEqual(em.workdir, os.getcwd())

    def testRunConversion(self) -> None:
        outPath = os.path.join(self.__outDir, "sub", "dir", "out.bcif")
        em = EmVolumes(
            em_map=self.__emMap,
            node_path=sys.executable,
            volume_server_pack_path=self.__pack,
            volume_server_query_path=self.__query,
            binary_map_out=outPath,
            working_dir=self.__workDir,
        )
        self.assertTrue(em.run_conversion())
        self.assertEqual(em.mdb_map_path, os.path.join(self.__workDir, "em_map.mdb"))
        with open(os.path.join(self.__workDir, "em_map.mdb")) as ifh:
            self.assertEqual(ifh.read(), "mdb:em:" + self.__emMap)
        with open(outPath) as ifh:
            self.assertEqual(ifh.read(), "bcif:em:1")
        self.assertTrue(os.path.exists(os.path.join(self.__workDir, "em_volume_em-cell_d1.bcif")))

    def testRunConversionMissingMap(self) -> None:
        outPath = os.path.join(self.__outDir, "out.bcif")
        em = EmVolumes(
            em_map=os.path.join(self.__outDir, "missing.map"),
            node_path=sys.executable,
            volume_server_pack_path=self.__pack,
            volume_server_query_path=self.__query,
            binary_map_out=outPath,
            working_dir=self.__workDir,
        )
        with mock.patch("wwpdb.utils.dp.electron_density.em_density_map.convert_mdb_to_binary_cif") as mockConv:
            self.assertFalse(em.run_conversion())
        mockConv.assert_not_called()
        self.assertFalse(os.path.exists(outPath))

    def testRunConversionPackFails(self) -> None:
        outPath = os.path.join(self.__outDir, "out.bcif")
        em = EmVolumes(
            em_map=self.__emMap,
            node_path=sys.executable,
            volume_server_pack_path=self.__fail,
            volume_server_query_path=self.__query,
            binary_map_out=outPath,
            working_dir=self.__workDir,
        )
        self.assertFalse(em.run_conversion())
        self.assertFalse(os.path.exists(outPath))

    def testRunConversionQueryFails(self) -> None:
        outPath = "out-not-made.bcif"
        em = EmVolumes(
            em_map=self.__emMap,
            node_path=sys.executable,
            volume_server_pack_path=self.__pack,
            volume_server_query_path=self.__fail,
            binary_map_out=outPath,
            working_dir=self.__workDir,
        )
        self.assertFalse(em.run_conversion())
        self.assertFalse(os.path.exists(outPath))

    def testMakeVolumeServerMapCommand(self) -> None:
        em = EmVolumes(
            em_map=self.__emMap,
            node_path="mynode",
            volume_server_pack_path="mypack",
            volume_server_query_path="myquery",
            binary_map_out=os.path.join(self.__outDir, "o.bcif"),
            working_dir=self.__workDir,
        )
        with mock.patch("wwpdb.utils.dp.electron_density.em_density_map.run_command_and_check_output_file", return_value=True) as mockRun, mock.patch(
            "wwpdb.utils.dp.electron_density.em_density_map.convert_mdb_to_binary_cif", return_value=True
        ) as mockConv:
            self.assertTrue(em.run_conversion())
        mdb = os.path.join(self.__workDir, "em_map.mdb")
        mockRun.assert_called_once_with(
            command="mynode mypack em %s %s" % (self.__emMap, mdb),
            process_name="make Volume server map",
            workdir=self.__workDir,
            output_file=mdb,
        )
        mockConv.assert_called_once_with(
            node_path="mynode",
            volume_server_query_path="myquery",
            map_id="em_volume",
            source_id="em",
            output_file=os.path.join(self.__outDir, "o.bcif"),
            working_dir=self.__workDir,
            mdb_map_path=mdb,
            detail=1,
        )


if __name__ == "__main__":
    unittest.main()
