import argparse
import logging
import sys
import os
import gemmi
from wwpdb.io.locator.PathInfo import PathInfo
from wwpdb.utils.config.ConfigInfo import getSiteId

logger = logging.getLogger()

def get_model_file(depid, version_id, mileStone=None):
    pi = PathInfo(siteId=getSiteId(), sessionPath='.', verbose=True, log=sys.stderr)
    mmcif = pi.getModelPdbxFilePath(dataSetId=depid, fileSource='archive',
                                    versionId=version_id, mileStone=mileStone)
    logging.debug("mmcif file path: %s" % mmcif)
    return mmcif

def get_center_of_mass(data_block):
    st = gemmi.make_structure_from_block(data_block)
    model = st[0]
    center_of_mass = model.calculate_center_of_mass()
    return center_of_mass

def get_deposition_ids(file):
    deposition_ids = []
    with open(file) as f:
        for line in f:
            deposition_ids.append(line)
    return deposition_ids

def process_entry(file_in, file_out):
    try:
        cif_file = gemmi.cif.read(file)
        data_block = cif_file[0]
    except Exception as e:
        logger.error("Failed to read cif file in Gemmi")
        logger.error(e)

    logging.info("Finding Centre of Mass")
    com = get_center_of_mass(data_block)
    data = {'pdbx_center_of_mass_x': [com.x],
            'pdbx_center_of_mass_y': [com.y],
            'pdbx_center_of_mass_z': [com.z]
            }
    logging.info("Writing mmcif file")
    try:
        data_block.set_mmcif_category('_struct.', data)
        cif_file.write_file(args.model_file_out)
    except Exception as e:
        logger.error("Failed to write cif file in Gemmi")
        logger.error(e)

def calculate_for_list():
    logging.info("Calculating for a list of entry")
    deposition_ids = get_deposition_ids(args.list)
    for depid in deposition_ids:
        latest_model = get_model_file(depid, 'latest')
        next_model = get_model_file(depid, 'next')
        process_entry(latest_model, next_model )

def calculate_for_file():
    logging.info("Calculating for a single file")
    process_entry(args.model_file_in, args.model_file_out)

def main():
    if args.list and os.path.isfile(args.list):
        calculate_for_list()

    elif os.path.isfile(args.model_file_in):
        calculate_for_file()
    else:
        logger.error("Input model file doesn't exists")
        return 1


if '__main__' in __name__:
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--model-file-in', help='Coordinate file to add centre of Mass', type=str)
    parser.add_argument('-o', '--model-file-out', help='Output Coordinate file, with added items', type=str)
    parser.add_argument('-l', '--list', help='list of Deposition Ids to calculate and append centre of Mass', type=str)

    args = parser.parse_args()
    logger.setLevel(args.loglevel)

    if not sys.argv[1:]:
        parser.print_help()
        exit()

    main()
