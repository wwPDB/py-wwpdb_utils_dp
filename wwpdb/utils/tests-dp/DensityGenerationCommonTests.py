import os
import shutil
import tempfile
import unittest

from wwpdb.utils.dp.electron_density.common_functions import run_command_and_check_output_file


class MyTestCase(unittest.TestCase):

    def setUp(self):
        self.test_files = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_files')
        self.test_2fofc_map_coeff_file = os.path.join(self.test_files, '2gc2_validation_2fo-fc_map_coef.cif')
        self.working_dir = tempfile.mkdtemp()
        self.temp_out_map = os.path.join(self.working_dir, 'out.map')

    def test_run_command_none_command(self):
        ok = run_command_and_check_output_file(command=None, output_file=self.temp_out_map, process_name='test')
        self.assertFalse(ok)

    def test_run_command_none_out(self):
        ok = run_command_and_check_output_file(command='test', output_file=None, process_name='test')
        self.assertFalse(ok)

    def test_run_command_python_command_missing_out(self):
        command = 'python --help'
        ok = run_command_and_check_output_file(command=command, output_file=self.temp_out_map, process_name='test')
        self.assertFalse(ok)

    def test_run_command_python_unknown_command(self):
        command = 'missing'
        ok = run_command_and_check_output_file(command=command, output_file=self.temp_out_map, process_name='test')
        self.assertFalse(ok)

    def test_run_command_python_command_correct_out(self):
        command = 'python --help'
        shutil.copy(self.test_2fofc_map_coeff_file, self.temp_out_map)
        ok = run_command_and_check_output_file(command=command, output_file=self.temp_out_map, process_name='test')
        self.assertTrue(ok)

    def tearDown(self):
        shutil.rmtree(self.working_dir, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
