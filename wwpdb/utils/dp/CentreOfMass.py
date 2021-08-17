import argparse
import logging
import sys
import os
import gemmi

logger = logging.getLogger()

def get_center_of_mass(data_block):
    st = gemmi.make_structure_from_block(data_block)
    model = st[0]
    center_of_mass = model.calculate_center_of_mass()
    return center_of_mass


def main():

    if not os.path.isfile(args.model_file_in):
        logger.error("Input model file doesn't exists")
        return 1

    try:
        cif_file = gemmi.cif.read(args.model_file_in)
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
    data_block.set_mmcif_category('_struct.', data)
    cif_file.write_file(args.model_file_out)

if '__main__' in __name__:
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--model-file-in', help='Coordinate file to add centre of Mass', type=str)
    parser.add_argument('-o', '--model-file-out', help='Output Coordinate file, with added items', type=str)

    args = parser.parse_args()
    logger.setLevel(args.loglevel)

    if not sys.argv[1:]:
        parser.print_help()
        exit()

    main()
