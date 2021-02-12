#!/usr/bin/env python3

import argparse
import logging
import os
import shutil
import sys
import tempfile

from wwpdb.utils.dp.electron_density.common_functions import run_command, convert_mdb_to_binary_cif

logger = logging.getLogger()


class EmVolumes:

    def __init__(self, em_map, output_folder, node_path, volume_server_path, binary_map_out):

        self.output_folder = output_folder
        self.em_map = em_map
        self.em_map_name = os.path.basename(em_map)
        self.ndb_map = 'em_map.ndb'
        self.bcif_map = 'em_map.bcif'
        self.node_path = node_path
        self.volume_server_path = volume_server_path
        self.mdb_map_path = os.path.join(self.workdir, self.ndb_map)
        self.bcif_map_path = binary_map_out
        self.workdir = None
        self.temp_map = None
        self.working_map = None

    def run_conversion(self):
        self.workdir = tempfile.mkdtemp()
        logging.debug('temp working folder: %s' % self.workdir)
        self.working_map = os.path.join(self.workdir, self.em_map_name)

        worked = self.make_volume_server_map()

        if worked:
            worked = self.convert_map_to_binary_cif()

        logging.debug('removing temp working dir: %s' % self.workdir)
        shutil.rmtree(self.workdir)
        return worked

    def get_em_map(self):
        filename, extension = os.path.splitext(self.em_map)
        if extension == 'gz':
            self.working_map = self.copy_map_to_temp()
        else:
            self.working_map = self.em_map
        return self.working_map

    def copy_map_to_temp(self):
        shutil.copy(self.em_map, self.workdir)
        compressed_map_file_name = self.temp_map + '.gz'
        if os.path.exists(compressed_map_file_name):
            gzip_command = 'gzip -d %s' % compressed_map_file_name
            ret = run_command(command=gzip_command, process_name='gunzip map', workdir=self.workdir)
            logging.debug('temp map path: %s' % self.temp_map)

        return self.temp_map

    def make_volume_server_map(self):
        if os.path.exists(self.working_map):
            if not os.path.exists(self.output_folder):
                os.makedirs(self.output_folder)
            command = '%s %s em %s %s' % (
                self.node_path, self.volume_server_path, self.working_map, self.mdb_map_path)
            logging.debug(command)
            ret = run_command(command=command, process_name='make Volume server map', workdir=self.workdir)

            if not os.path.exists(self.mdb_map_path):
                logging.error('Volume server map generation failed')
            else:
                logging.info('Volume server map generation worked')
                logging.info('output map: %s' % self.mdb_map_path)
                return True
        else:
            logging.error('map file missing: %s' % self.working_map)
        return False

    def convert_map_to_binary_cif(self):
        return convert_mdb_to_binary_cif(map_id='em_volume', source_id='em',
                                         output_file=self.bcif_map_path,
                                         working_dir=self.workdir,
                                         mdb_map_path=self.mdb_map_path,
                                         output_folder=self.output_folder)


def main(): # pragma: no cover
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', help='output folder', type=str, required=True)
    parser.add_argument('--em_map', help='EM map', type=str, required=True)
    parser.add_argument('--binary_map_out', 'Output filename of binary map', type=str, required=True)
    parser.add_argument('--node_path', help='path to node', type=str, required=True)
    parser.add_argument('--volume_server_path', help='path to volume server', type=str, required=True)
    parser.add_argument('--debug', help='debugging', action='store_const', dest='loglevel', const=logging.DEBUG,
                        default=logging.INFO)

    args = parser.parse_args()
    logger.setLevel(args.loglevel)

    if not sys.argv[1:]:
        parser.print_help()
        exit()

    em = EmVolumes(output_folder=args.output,
                   em_map=args.em_map,
                   node_path=args.node_path,
                   volume_server_path=args.volume_server_path,
                   binary_map_out=args.binary_map_out
                   )
    worked = em.run_conversion()
    logging.info('conversion worked: %s' % worked)
    if not worked:
        sys.exit(1)


if __name__ == "__main__":
    main()
