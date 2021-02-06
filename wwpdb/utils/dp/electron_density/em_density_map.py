#!/usr/bin/env python3

import argparse
import logging
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import json

logger = logging.getLogger()


class EmVolumes:

    def __init__(self, em_map, output_folder, node_path, volume_server_path):

        self.output_folder = output_folder
        self.em_map = em_map
        self.em_map_name = os.path.basename(em_map)
        self.ndb_map = 'em_map.ndb'
        self.bcif_map = 'em_map.bcif'
        self.node_path = node_path
        self.volume_server_path = volume_server_path
        self.ndb_map_path = os.path.join(self.workdir, self.ndb_map)
        self.bcif_map_path = os.path.join(self.output_folder, self.bcif_map)
        self.workdir = None
        self.temp_map = None
        self.working_map = None

    def run_command(self, command, process_name):
        command_list = shlex.split(command)
        process = subprocess.Popen(command_list, cwd=self.workdir)
        out, err = process.communicate()
        if out:
            logging.info(out)
        if err:
            logging.error(err)
        rc = process.returncode
        if rc != 0:
            logging.error('process failed: {}}'.format(process_name))
            return False
        logging.info('process worked: {}'.format(process_name))
        return True

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
            ret = self.run_command(command=gzip_command, process_name='gunzip map')
            logging.debug('temp map path: %s' % self.temp_map)

        return self.temp_map

    def make_volume_server_map(self):
        if os.path.exists(self.working_map):
            if not os.path.exists(self.output_folder):
                os.makedirs(self.output_folder)
            command = '%s %s em %s %s' % (
                self.node_path, self.volume_server_path, self.working_map, self.ndb_map_path)
            logging.debug(command)
            ret = self.run_command(command=command, process_name='make Volume server map')

            if not os.path.exists(self.ndb_map_path):
                logging.error('Volume server map generation failed')
            else:
                logging.info('Volume server map generation worked')
                logging.info('output map: %s' % self.ndb_map_path)
                return True
        else:
            logging.error('map file missing: %s' % self.working_map)
        return False

    def convert_map_to_binary_cif(self, map_id='em_volume'):
        json_filename = 'conversion.json'
        json_content = [{
          "source": {
            "filename": self.ndb_map_path,
            "name": map_id,
            "id": "em"
          },
          "query": {
            "kind": "cell"
          },
          "params": {
            "detail": 4,
            "asBinary": True
          },
          "outputFolder": self.workdir,
          "outputFilename": self.bcif_map_path
        }]
        working_json = os.path.join(self.workdir, json_filename)
        with open(working_json, 'w') as out_file:
            json.dump(json_content, out_file)
        command = "volume-server-query --jobs {}".format(working_json)
        ret = self.run_command(command=command, process_name='ndb_to_binary_cif')
        if ret and os.path.exists(self.bcif_map_path):
            logging.debug('ndb to bcif map conversion worked')
            return True
        logging.error('ndb to bcif map conversion failed')
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', help='output folder', type=str, required=True)
    parser.add_argument('--em_map', help='EM map', type=str, required=True)
    parser.add_argument('--em_id', help='EMDB ID ', type=str, required=True)
    parser.add_argument('--node_path', help='path to node', type=str, required=True)
    parser.add_argument('--volume_server_path', help='path to volume server', type=str, required=True)
    parser.add_argument('--debug', help='debugging', action='store_const', dest='loglevel', const=logging.DEBUG,
                        default=logging.INFO)

    args = parser.parse_args()
    logger.setLevel(args.loglevel)

    if not sys.argv[1:]:
        parser.print_help()
        exit()

    em = EmVolumes(em_id=args.em_id,
                   output_folder=args.output,
                   em_map=args.em_map,
                   node_path=args.node_path,
                   volume_server_path=args.volume_server_path
                   )
    worked = em.run_conversion()
    logging.info('conversion worked: %s' % worked)
    if not worked:
        sys.exit(1)


if __name__ == "__main__":
    main()
