# Author:  Chenghua Shao
# Date:    2025-11-10
# Updates:

"""
This module provides utility functions to read reference data related to metal ions,
including oxidation states, coordination numbers, and coordinate class mappings from CSV files.
"""

import csv
import os

REF_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "metal_ref")


def readRefRedOx():
    """
    The function expects a file named ``metal_oxidation_state.csv`` located in the directory specified by ``REF_PATH``.
    The CSV file should be tab-delimited and contain at least the columns ``Metals``, ``Redox active``, and ``Oxidation state``.
    :returns: A tuple containing two dictionaries:
    :rtype: tuple
    :raises FileNotFoundError: If the CSV file does not exist.
    :raises KeyError: If expected columns are missing in the CSV file.
    """

    filepath = os.path.join(REF_PATH, "metal_oxidation_state.csv")
    d_redox = {}
    d_oxi = {}
    with open(filepath) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for d_row in reader:
            metal = d_row['Metals'].strip()
            d_redox[metal] = d_row['Redox active'].strip()
            d_oxi[metal] = d_row["Oxidation state"]
    return (d_redox, d_oxi)


def readRefCoordNum():
    """
    Reads the metal coordination number reference data from a CSV file and returns a dictionary mapping metal names to their coordination numbers.
    The CSV file is expected to be located at REF_PATH/metal_coordination_number.csv, with tab-delimited columns 'Metals' and 'Coordination numbers'.
    :returns: Dictionary mapping metal names (str) to lists of coordination numbers (str).
    :rtype: dict
    """

    filepath = os.path.join(REF_PATH, "metal_coordination_number.csv")
    d_coord_num = {}
    with open(filepath) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for d_row in reader:
            metal = d_row['Metals'].strip()
            coord_num = d_row['Coordination numbers'].strip()
            d_coord_num[metal] = coord_num.split(",")
    return d_coord_num


def readRefCoordMap(program):
    """
    Reads a CSV file containing coordinate class mappings and returns a dictionary mapping geometry names to their abbreviations and PDB geometry names for a specified program.

    :param str program: The name of the program to select the appropriate columns from the CSV file.
    :returns: A dictionary where keys are geometry names (lowercase) and values are dictionaries with 'abbr' (abbreviation, uppercase) and 'pdb_geom' (PDB geometry name, lowercase).
    :rtype: dict

    .. note::
        - Skips rows where the geometry name is 'na'.
        - Prints a message if a duplicate geometry name is encountered.
        - Assumes the CSV file is located at ``REF_PATH/coord_classes_mapping_abbr.csv`` and contains columns named ``Name {program}``, ``Abbreviation {program}``, and ``Name PDB``.
    """

    filepath = os.path.join(REF_PATH, "coord_classes_mapping_abbr.csv")
    d_coord_map = {}
    geom_header = f"Name {program}"
    abbr_header = f"Abbreviation {program}"
    pdb_header = "Name PDB"
    with open(filepath) as f:
        reader = csv.DictReader(f, delimiter=",")
        for d_row in reader:
            geom = d_row[geom_header].strip().lower()
            if geom == "na":
                continue
            abbr = d_row[abbr_header].strip().upper()
            pdb_geom = d_row[pdb_header].strip().lower()
            if geom in d_coord_map:
                print("duplicate geometry %s", geom)
                continue
            d_coord_map[geom] = {}
            d_coord_map[geom]['abbr'] = abbr
            d_coord_map[geom]['pdb_geom'] = pdb_geom
    return d_coord_map


# def main():
#     d_coord_num = readRefCoordNum()
#     print(d_coord_num)
#     d_coord_map_fg = readRefCoordMap("FindGeo")
#     print(d_coord_map_fg)
#     d_coord_map_mc = readRefCoordMap("metalCoord")
#     print(d_coord_map_mc)
#     (d_redox, d_oxi) = readRefRedOx()
#     print(d_redox)
#     print(d_oxi)

# if __name__ == "__main__":
#     main()
