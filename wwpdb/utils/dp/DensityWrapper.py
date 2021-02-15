from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId
from wwpdb.utils.dp.electron_density.x_ray_density_map import XrayVolumeServerMap
from wwpdb.utils.dp.electron_density.em_density_map import EmVolumes

class DensityWrapper:

    def __init__(self):
        site_id = getSiteId()
        self.cI = ConfigInfo(siteId=site_id)
        self.node_path = self.cI.get('NODE')
        self.volume_server_pack = self.cI.get('VOLUME_SERVER_PACK')
        self.volume_server_query = self.cI.get('VOLUME_SERVER_QUERY')

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
        em_conversion = EmVolumes(em_map=in_em_volume,
                                  binary_map_out=out_binary_volume,
                                  node_path=self.node_path,
                                  volume_server_pack_path=self.volume_server_pack,
                                  volume_server_query_path=self.volume_server_query,
                                  working_dir=working_dir)
        return em_conversion.run_conversion()

