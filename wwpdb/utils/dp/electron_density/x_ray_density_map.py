import argparse
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import gemmi

logger = logging.getLogger(__name__)


class XrayVolumeServerMap:
    def __init__(self):
        pass

    @staticmethod
    def run_command(command, output_file):
        """
        Runs a command and checks the present of the expected output file
        :param command: command to run
        :param output_file: expected output file
        :return: True if worked, False if failed
        """
        if command and output_file:
            logging.debug(command)
            logging.debug("expected output file: {}".format(output_file))
            cmd = subprocess.run(
                command,
                shell=True,
                # capture_output=True,
                # text=True
            )
            ret = cmd.returncode
            if ret == 0:
                if os.path.exists(output_file):
                    return True
                else:
                    logging.error("output file {} missing".format(output_file))
            else:
                logging.error("exit status of {}".format(ret))
                logging.error(cmd.stdout)
                logging.error(cmd.stderr)
        return False

    def gemmi_sf2map(self, coord_path, sf_mmcif_in, map_out, f_column, phi_column):
        """
        converts input mmCIF file map coefficients to map
        :param coord_path: mmCIF coordinate file in
        :param sf_mmcif_in: mmCIF structure factor input file
        :param map_out: map output file
        :param f_column: F column
        :param phi_column: PHI column
        :return: True if worked, False if failed
        """
        st = gemmi.read_structure(coord_path)
        fbox = st.calculate_fractional_box(margin=5)
        if sf_mmcif_in:
            if os.path.exists(sf_mmcif_in):
                doc = gemmi.cif.read(sf_mmcif_in)
                rblocks = gemmi.as_refln_blocks(doc)
                if (
                        f_column in rblocks[0].column_labels()
                        and phi_column in rblocks[0].column_labels()
                ):
                    ccp4 = gemmi.Ccp4Map()
                    ccp4.grid = rblocks[0].transform_f_phi_to_map(f_column, phi_column)
                    ccp4.update_ccp4_header(2, True)
                    ccp4.set_extent(fbox)
                    ccp4.write_ccp4_map(map_out)

                    if os.path.exists(map_out):
                        return True
                    else:
                        logging.error("output map file {} missing".format(map_out))
                else:
                    logging.error(
                        "{} {} columns not found in mmCIF {}".format(
                            f_column, phi_column, sf_mmcif_in
                        )
                    )
            else:
                logging.error("cannot find input file {}".format(sf_mmcif_in))

                # command = "{} sf2map -f {} -p {} {} {}".format(gemmi_path, f_column, phi_column, mmcif_in, map_out)
                # return self.run_command(command=command, output_file=map_out)
        logging.error("converting {} to {} failed".format(sf_mmcif_in, map_out))
        return False

    def make_maps_to_serve_with_volume_server(
            self,
            node_path,
            two_fofc_map_in,
            fofc_map_in,
            map_out,
            volume_server_path,
    ):
        if not node_path:
            logging.error('node path not set')
            return False
        if volume_server_path:
            return self.make_volume_server_map(
                node_path=node_path,
                volume_server_path=volume_server_path,
                two_fofc_map_in=two_fofc_map_in,
                fofc_map_in=fofc_map_in,
                map_out=map_out,
            )
        else:
            return False

    def make_volume_server_map(
            self, node_path, volume_server_path, two_fofc_map_in, fofc_map_in, map_out
    ):
        """
        make map for Volume server to serve
        :param: map_in: input map file
        :param: map_out: output map file
        :return: True if worked, False if failed
        """
        if not node_path:
            logging.error('node path not set')
            return False
        if not volume_server_path:
            logging.error("volume server executable not set")
            return False
        if not os.path.exists(volume_server_path):
            logging.error(
                "volume server executable not found at {}".format(volume_server_path)
            )
            return False
        if os.path.exists(two_fofc_map_in) and os.path.exists(fofc_map_in):
            command = "{} {} xray {} {} {}".format(
                node_path, volume_server_path, two_fofc_map_in, fofc_map_in, map_out
            )
            return self.run_command(command=command, output_file=map_out)


def run_process_with_gemmi(
        node_path,
        coord_file,
        two_fofc_mmcif_map_coeff_in,
        fofc_mmcif_map_coeff_in,
        volume_server_map_out,
        volume_server_path=None,
        keep_working=False,
):
    """
    Process 2fo-fc and fo-fc mmCIF files and convert to maps for volume server
    :param node_path: path to node executable
    :param coord_file: path to mmCIF coordinate file
    :param volume_server_path: path to volume server executable
    :param volume_server_map_out: path to volume server out map file
    :param two_fofc_mmcif_map_coeff_in: input 2Fo-Fc map coefficient mmCIF file
    :param fofc_mmcif_map_coeff_in: input Fo-Fc map coefficient mmCIF file
    :param keep_working: Keep working directory - for debugging
    :return: True if worked, False if failed
    """

    if not volume_server_path:
        logging.error("volume_server_path must be set")
        return False

    if not coord_file:
        logging.error('coordinate file must be provided')
        return False

    if not node_path:
        logging.error('node not set')
        return False

    if not os.path.exists(node_path):
        logging.error('node not found: {}'.format(node_path))
        return False

    if not os.path.exists(two_fofc_mmcif_map_coeff_in) or not os.path.exists(fofc_mmcif_map_coeff_in):
        logging.error(
            'input mmcif files not found: {} or {}'.format(two_fofc_mmcif_map_coeff_in, fofc_mmcif_map_coeff_in))
        return False

    ok = False
    run_working_directory = tempfile.mkdtemp()
    logging.debug("working directory: {}".format(run_working_directory))
    two_fo_fc_map = os.path.join(run_working_directory, "2fofc.map")
    fo_fc_map = os.path.join(run_working_directory, "fofc.map")
    xrsm = XrayVolumeServerMap()
    ok1 = xrsm.gemmi_sf2map(
        sf_mmcif_in=two_fofc_mmcif_map_coeff_in,
        map_out=two_fo_fc_map,
        f_column="pdbx_FWT",
        phi_column="pdbx_PHWT",
        coord_path=coord_file
    )
    ok2 = xrsm.gemmi_sf2map(
        sf_mmcif_in=fofc_mmcif_map_coeff_in,
        map_out=fo_fc_map,
        f_column="pdbx_DELFWT",
        phi_column="pdbx_DELPHWT",
        coord_path=coord_file
    )
    if ok1 and ok2:
        ok = xrsm.make_maps_to_serve_with_volume_server(
            node_path=node_path,
            volume_server_path=volume_server_path,
            two_fofc_map_in=two_fo_fc_map,
            fofc_map_in=fo_fc_map,
            map_out=volume_server_map_out,
        )
    else:
        logging.error("making maps failed")
    if not keep_working:
        shutil.rmtree(run_working_directory, ignore_errors=True)
    return ok


def main():  # pragma: no cover
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--two_fofc_mmcif_map_coeff_in",
        help="2fofc mmCIF containing map coefficients",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--fofc_mmcif_map_coeff_in",
        help="fofc mmCIF containing map coefficients",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--volume_server_map_out",
        help="volume server map output file name",
        type=str,
        required=True,
    )
    parser.add_argument("--node", help="node program path", type=str, required=True)
    parser.add_argument("--coord_file", help="mmCIF coordinate file", type=str, required=True)
    parser.add_argument("--volume_server_path", help="volume server path", type=str)
    parser.add_argument(
        "--keep_working", help="Keep working directory", action="store_true"
    )
    parser.add_argument(
        "-d",
        "--debug",
        help="debugging",
        action="store_const",
        dest="loglevel",
        const=logging.DEBUG,
        default=logging.INFO,
    )

    args = parser.parse_args()
    logger = logging.getLogger()
    logger.setLevel(args.loglevel)

    ok = run_process_with_gemmi(
        node_path=args.node,
        volume_server_path=args.volume_server_path,
        two_fofc_mmcif_map_coeff_in=args.two_fofc_mmcif_map_coeff_in,
        fofc_mmcif_map_coeff_in=args.fofc_mmcif_map_coeff_in,
        volume_server_map_out=args.volume_server_map_out,
        keep_working=args.keep_working,
    )

    if not ok:
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
