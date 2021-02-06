import logging
import os
import shutil
import tempfile
import unittest
from wwpdb.utils.dp.electron_density.x_ray_density_map import XrayVolumeServerMap, run_process_with_gemmi

logger = logging.getLogger()


class TestXrayMolStarMaps(unittest.TestCase):

    def setUp(self):
        self.this_file = os.path.realpath(__file__)
        self.test_files = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_files')
        self.test_2fofc_map_coeff_file = os.path.join(self.test_files, '2gc2_validation_2fo-fc_map_coef.cif')
        self.test_fofc_map_coeff_file = os.path.join(self.test_files, '2gc2_validation_fo-fc_map_coef.cif')
        self.test_coord_file = os.path.join(self.test_files, '2gc2.cif')
        self.xrm = XrayVolumeServerMap()
        self.working_dir = tempfile.mkdtemp()
        self.temp_out_map = os.path.join(self.working_dir, 'out.map')

    def test_none_map(self):
        ok = self.xrm.gemmi_sf2map(sf_mmcif_in=None, map_out=self.temp_out_map, f_column='F', phi_column='Phi',
                                   coord_path=self.test_coord_file)
        self.assertFalse(ok)

    def test_missing_map(self):
        ok = self.xrm.gemmi_sf2map(sf_mmcif_in='test.map',
                                   map_out=self.temp_out_map, f_column='F', phi_column='Phi',
                                   coord_path=self.test_coord_file)
        self.assertFalse(ok)

    def test_incorrect_columns(self):
        ok = self.xrm.gemmi_sf2map(sf_mmcif_in=self.test_2fofc_map_coeff_file,
                                   map_out=self.temp_out_map, f_column='F', phi_column='Phi',
                                   coord_path=self.test_coord_file)
        self.assertFalse(ok)

    def test_correct_columns(self):
        ok = self.xrm.gemmi_sf2map(sf_mmcif_in=self.test_2fofc_map_coeff_file,
                                   map_out=self.temp_out_map, f_column='pdbx_FWT', phi_column='pdbx_PHWT',
                                   coord_path=self.test_coord_file)
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(self.temp_out_map))

    def test_volume_server_incorrect_exe(self):
        ok = self.xrm.make_volume_server_map(node_path=None, volume_server_path='missing', two_fofc_map_in=None,
                                             fofc_map_in=None,
                                             map_out=self.temp_out_map)
        self.assertFalse(ok)

    def test_volume_server_missing(self):
        ok = self.xrm.make_volume_server_map(node_path=None, volume_server_path=None, two_fofc_map_in=None,
                                             fofc_map_in=None,
                                             map_out=self.temp_out_map)
        self.assertFalse(ok)

    def test_make_maps_to_serve_with_volume_server_no_exe(self):
        ok = self.xrm.make_maps_to_serve_with_volume_server(volume_server_path=None,
                                                            fofc_map_in=self.test_fofc_map_coeff_file,
                                                            two_fofc_map_in=self.test_2fofc_map_coeff_file,
                                                            node_path=None, map_out=self.temp_out_map)
        self.assertFalse(ok)

    def test_run_command_none_command(self):
        ok = self.xrm.run_command(command=None, output_file=self.temp_out_map)
        self.assertFalse(ok)

    def test_run_command_none_out(self):
        ok = self.xrm.run_command(command='test', output_file=None)
        self.assertFalse(ok)

    def test_run_command_python_command_missing_out(self):
        command = 'python {} --help'.format(self.this_file)
        ok = self.xrm.run_command(command=command, output_file=self.temp_out_map)
        self.assertFalse(ok)

    def test_run_command_python_unknown_command(self):
        command = 'missing'
        ok = self.xrm.run_command(command=command, output_file=self.temp_out_map)
        self.assertFalse(ok)

    def test_run_command_python_command_correct_out(self):
        command = 'python {} --help'.format(self.this_file)
        shutil.copy(self.test_2fofc_map_coeff_file, self.temp_out_map)
        ok = self.xrm.run_command(command=command, output_file=self.temp_out_map)
        self.assertTrue(ok)

    def test_run_process_with_gemmi_no_exe(self):
        ok = run_process_with_gemmi(node_path=None,
                                    two_fofc_mmcif_map_coeff_in=self.test_2fofc_map_coeff_file,
                                    fofc_mmcif_map_coeff_in=self.test_fofc_map_coeff_file,
                                    volume_server_map_out=self.temp_out_map,
                                    volume_server_path=None,
                                    keep_working=False,
                                    coord_file=self.test_coord_file)

        self.assertFalse(ok)

    def test_run_process_with_gemmi_volume_missing(self):
        ok = run_process_with_gemmi(node_path='node',
                                    two_fofc_mmcif_map_coeff_in=self.test_2fofc_map_coeff_file,
                                    fofc_mmcif_map_coeff_in=self.test_fofc_map_coeff_file,
                                    volume_server_map_out=self.temp_out_map,
                                    volume_server_path='missing',
                                    keep_working=False,
                                    coord_file=self.test_coord_file)

        self.assertFalse(ok)

    def test_run_process_with_gemmi_node_missing(self):
        ok = run_process_with_gemmi(node_path=None,
                                    two_fofc_mmcif_map_coeff_in=self.test_2fofc_map_coeff_file,
                                    fofc_mmcif_map_coeff_in=self.test_fofc_map_coeff_file,
                                    volume_server_map_out=self.temp_out_map,
                                    volume_server_path='missing',
                                    keep_working=False,
                                    coord_file=self.test_coord_file)

        self.assertFalse(ok)

    def test_run_process_with_gemmi_missing_mmcif(self):
        ok = run_process_with_gemmi(node_path='node',
                                    two_fofc_mmcif_map_coeff_in='missing',
                                    fofc_mmcif_map_coeff_in='missing',
                                    volume_server_map_out=self.temp_out_map,
                                    volume_server_path='volume',
                                    keep_working=False,
                                    coord_file=self.test_coord_file)

        self.assertFalse(ok)

    def test_run_process_with_gemmi_missing_out_map(self):
        ok = run_process_with_gemmi(node_path='node',
                                    two_fofc_mmcif_map_coeff_in=self.test_2fofc_map_coeff_file,
                                    fofc_mmcif_map_coeff_in=self.test_fofc_map_coeff_file,
                                    volume_server_map_out=None,
                                    volume_server_path='volume',
                                    keep_working=False,
                                    coord_file=self.test_coord_file)

        self.assertFalse(ok)

    def tearDown(self):
        shutil.rmtree(self.working_dir, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
