#!/usr/bin/env python3

import argparse
import logging
import os
import shutil
import sys
import tempfile

from wwpdb.utils.dp.electron_density.common_functions import convert_mdb_to_binary_cif, \
    run_command_and_check_output_file

logger = logging.getLogger()


class EmVolumes:

    def __init__(self, em_map, output_folder, node_path, volume_server_pack_path, volume_server_query_path,
                 binary_map_out, keep_working=False):

        self.output_folder = output_folder
        self.em_map = em_map
        self.em_map_name = os.path.basename(em_map)
        self.mdb_map = 'em_map.mdb'
        self.node_path = node_path
        self.volume_server_pack_path = volume_server_pack_path
        self.volume_server_query_path = volume_server_query_path
        self.mdb_map_path = None
        self.bcif_map_path = binary_map_out
        self.workdir = None
        self.keep_working = keep_working

    def run_conversion(self):
        self.workdir = tempfile.mkdtemp()
        logging.debug('temp working folder: %s' % self.workdir)
        self.mdb_map_path = os.path.join(self.workdir, self.mdb_map)

        worked = self.make_volume_server_map()

        if worked:
            worked = self.convert_map_to_binary_cif()

            if worked and not self.keep_working:
                logging.debug('removing temp working dir: %s' % self.workdir)
                shutil.rmtree(self.workdir)
        return worked

    def make_volume_server_map(self):
        if os.path.exists(self.em_map):
            if not os.path.exists(self.output_folder):
                os.makedirs(self.output_folder)
            command = '%s %s em %s %s' % (
                self.node_path, self.volume_server_pack_path, self.em_map, self.mdb_map_path)
            logging.debug(command)
            return run_command_and_check_output_file(command=command, process_name='make Volume server map',
                                                     workdir=self.workdir, output_file=self.mdb_map_path)
        else:
            logging.error('input map file missing: %s' % self.em_map)
        return False

    def convert_map_to_binary_cif(self):
        return convert_mdb_to_binary_cif(node_path=self.node_path,
                                         volume_server_query_path=self.volume_server_query_path,
                                         map_id='em_volume', source_id='em',
                                         output_file=self.bcif_map_path,
                                         working_dir=self.workdir,
                                         mdb_map_path=self.mdb_map_path,
                                         output_folder=self.output_folder)


def main():  # pragma: no cover
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_path', help='output folder', type=str, required=True)
    parser.add_argument('--em_map', help='EM map', type=str, required=True)
    parser.add_argument('--binary_map_out', help='Output filename of binary map', type=str, required=True)
    parser.add_argument('--node_path', help='path to node', type=str, required=True)
    parser.add_argument('--volume_server_pack_path', help='path to volume-server-pack', type=str, required=True)
    parser.add_argument('--volume_server_query_path', help='path to volume-server-query', type=str, required=True)
    parser.add_argument('--keep_working_directory', help='keep working directory', action="store_true")
    parser.add_argument('--debug', help='debugging', action='store_const', dest='loglevel', const=logging.DEBUG,
                        default=logging.INFO)

    args = parser.parse_args()
    logger.setLevel(args.loglevel)

    if not sys.argv[1:]:
        parser.print_help()
        exit()

    em = EmVolumes(output_folder=args.output_path,
                   em_map=args.em_map,
                   node_path=args.node_path,
                   volume_server_pack_path=args.volume_server_pack_path,
                   volume_server_query_path=args.volume_server_query_path,
                   binary_map_out=args.binary_map_out,
                   keep_working=args.keep_working_directory
                   )
    worked = em.run_conversion()
    logging.info('EM map conversion worked: {}'.format(worked))
    if not worked:
        sys.exit(1)


if __name__ == "__main__":
    main()
