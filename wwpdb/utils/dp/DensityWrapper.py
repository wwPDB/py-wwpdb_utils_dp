import os
import sys
import logging
import argparse
import tempfile
import shutil

from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId

# from wwpdb.utils.dp.electron_density.em_density_map import EmVolumes
from wwpdb.utils.dp.electron_density.x_ray_density_map import XrayVolumeServerMap
from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility

class DensityWrapper:

    def __init__(self):
        self.__site_id = getSiteId()
        self.__cI = ConfigInfo(siteId=self.__site_id)
        self.__packagePath = self.__cI.get('SITE_PACKAGES_PATH')
        self.node_path = os.path.join(self.__packagePath, 'node', 'bin', 'node')
        self.volume_server_pack = self.__cI.get('VOLUME_SERVER_PACK')
        self.volume_server_query = self.__cI.get('VOLUME_SERVER_QUERY')

    def convert_xray_density_map(self, coord_file, in_2fofc_map, in_fofc_map, out_binary_cif, working_dir):
        xray_conversion = XrayVolumeServerMap(coord_path=coord_file,
                                              binary_map_out=out_binary_cif,
                                              node_path=self.node_path,
                                              volume_server_query_path=self.volume_server_query,
                                              volume_server_pack_path=self.volume_server_pack,
                                              two_fofc_mmcif_map_coeff_in=in_2fofc_map,
                                              fofc_mmcif_map_coeff_in=in_fofc_map,
                                              working_dir=working_dir)
        return xray_conversion.run_process()

    def convert_em_volume(self, in_em_volume, out_binary_volume, working_dir):

        logging.debug(working_dir)
        rdb = RcsbDpUtility(tmpPath=working_dir, siteId=self.__site_id, verbose=True)
        rdb.imp(in_em_volume)
        rdb.op('em-density-bcif')
        rdb.exp(out_binary_volume)

        if out_binary_volume:
            if os.path.exists(out_binary_volume):
                return True
        return False

        #em_conversion = EmVolumes(em_map=in_em_volume,
        #                          binary_map_out=out_binary_volume,
        #                          node_path=self.node_path,
        #                          volume_server_pack_path=self.volume_server_pack,
        #                          volume_server_query_path=self.volume_server_query,
        #                          working_dir=working_dir)
        #return em_conversion.run_conversion()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--em_map', help='EM map', type=str)
    parser.add_argument('--binary_map_out', help='Output filename of binary map', type=str, required=True)
    parser.add_argument('--debug', help='debugging', action='store_const', dest='loglevel', const=logging.DEBUG,
                        default=logging.INFO)

    args = parser.parse_args()
    logger = logging.getLogger()
    logger.setLevel(args.loglevel)

    if not sys.argv[1:]:
        parser.print_help()
        exit()

    dw = DensityWrapper()
    working_dir = tempfile.mkdtemp()
    if args.em_map:
        dw.convert_em_volume(in_em_volume=args.em_map,
                             out_binary_volume=args.binary_map_out,
                             working_dir=working_dir)

    shutil.rmtree(working_dir)


if __name__ == '__main__':
    main()
