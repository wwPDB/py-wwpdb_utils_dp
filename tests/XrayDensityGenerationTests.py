import logging
import os
import shutil
import tempfile
import unittest

from wwpdb.utils.dp.electron_density.x_ray_density_map import XrayVolumeServerMap, run_process_with_gemmi

logger = logging.getLogger()


class TestXrayMolStarMaps(unittest.TestCase):
    def setUp(self):
        self.test_files = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_files")
        self.test_2fofc_map_coeff_file = os.path.join(self.test_files, "2gc2_validation_2fo-fc_map_coef.cif")
        self.test_fofc_map_coeff_file = os.path.join(self.test_files, "2gc2_validation_fo-fc_map_coef.cif")
        self.test_coord_file = os.path.join(self.test_files, "2gc2.cif")
        self.working_dir = tempfile.mkdtemp()
        self.binary_cif_out = os.path.join(self.working_dir, "binary_cif.map")
        self.xrm = XrayVolumeServerMap(
            coord_path=self.test_coord_file,
            node_path=None,
            volume_server_pack_path="missing",
            volume_server_query_path=None,
            binary_map_out=self.binary_cif_out,
            fofc_mmcif_map_coeff_in=self.test_fofc_map_coeff_file,
            two_fofc_mmcif_map_coeff_in=self.test_2fofc_map_coeff_file,
            working_dir=self.working_dir,
        )

        self.temp_out_map = os.path.join(self.working_dir, "out.map")

    def test_none_map(self):
        ok = self.xrm.gemmi_sf2map(
            sf_mmcif_in=None,
            map_out=self.temp_out_map,
            f_column="F",
            phi_column="Phi",
        )
        self.assertFalse(ok)

    def test_missing_map(self):
        ok = self.xrm.gemmi_sf2map(
            sf_mmcif_in="test.map",
            map_out=self.temp_out_map,
            f_column="F",
            phi_column="Phi",
        )
        self.assertFalse(ok)

    def test_incorrect_columns(self):
        ok = self.xrm.gemmi_sf2map(
            sf_mmcif_in=self.test_2fofc_map_coeff_file,
            map_out=self.temp_out_map,
            f_column="F",
            phi_column="Phi",
        )
        self.assertFalse(ok)

    def test_correct_columns(self):
        ok = self.xrm.gemmi_sf2map(
            sf_mmcif_in=self.test_2fofc_map_coeff_file,
            map_out=self.temp_out_map,
            f_column="pdbx_FWT",
            phi_column="pdbx_PHWT",
        )
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(self.temp_out_map))

    def test_volume_server_incorrect_exe(self):
        ok = self.xrm.make_volume_server_map(
            two_fofc_map_in=None,
            fofc_map_in=None,
        )
        self.assertFalse(ok)

    def test_volume_server_missing(self):
        ok = self.xrm.make_volume_server_map(
            two_fofc_map_in=None,
            fofc_map_in=None,
        )
        self.assertFalse(ok)

    def test_make_maps_to_serve_with_volume_server_no_exe(self):
        ok = self.xrm.make_maps_to_serve_with_volume_server(
            fofc_map_in=self.test_fofc_map_coeff_file,
            two_fofc_map_in=self.test_2fofc_map_coeff_file,
        )
        self.assertFalse(ok)

    def test_run_process_with_gemmi_no_exe(self):
        ok = run_process_with_gemmi(
            node_path=None,
            two_fofc_mmcif_map_coeff_in=self.test_2fofc_map_coeff_file,
            fofc_mmcif_map_coeff_in=self.test_fofc_map_coeff_file,
            volume_server_pack_path=None,
            volume_server_query_path=None,
            coord_file=self.test_coord_file,
            binary_map_out=self.binary_cif_out,
        )

        self.assertFalse(ok)

    def test_run_process_with_gemmi_volume_missing(self):
        ok = run_process_with_gemmi(
            node_path="node",
            two_fofc_mmcif_map_coeff_in=self.test_2fofc_map_coeff_file,
            fofc_mmcif_map_coeff_in=self.test_fofc_map_coeff_file,
            volume_server_pack_path="missing",
            volume_server_query_path="missing",
            coord_file=self.test_coord_file,
            binary_map_out=self.binary_cif_out,
        )

        self.assertFalse(ok)

    def test_run_process_with_gemmi_node_missing(self):
        ok = run_process_with_gemmi(
            node_path=None,
            two_fofc_mmcif_map_coeff_in=self.test_2fofc_map_coeff_file,
            fofc_mmcif_map_coeff_in=self.test_fofc_map_coeff_file,
            volume_server_pack_path="missing",
            volume_server_query_path="missing",
            coord_file=self.test_coord_file,
            binary_map_out=self.binary_cif_out,
        )

        self.assertFalse(ok)

    def test_run_process_with_gemmi_missing_mmcif(self):
        ok = run_process_with_gemmi(
            node_path="node",
            two_fofc_mmcif_map_coeff_in="missing",
            fofc_mmcif_map_coeff_in="missing",
            volume_server_pack_path="volume",
            volume_server_query_path="query",
            coord_file=self.test_coord_file,
            binary_map_out=self.binary_cif_out,
        )

        self.assertFalse(ok)

    def test_run_process_with_gemmi_missing_out_map(self):
        ok = run_process_with_gemmi(
            node_path="node",
            two_fofc_mmcif_map_coeff_in=self.test_2fofc_map_coeff_file,
            fofc_mmcif_map_coeff_in=self.test_fofc_map_coeff_file,
            volume_server_pack_path="volume",
            volume_server_query_path="query",
            coord_file=self.test_coord_file,
            binary_map_out=self.binary_cif_out,
        )

        self.assertFalse(ok)

    def tearDown(self):
        shutil.rmtree(self.working_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
