import csv
import os
import sys

REF_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "metal_ref")

def readRefRedOx():
    filepath = os.path.join(REF_PATH, "metal_oxidation_state.csv")
    d_redox = {}
    with open(filepath) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for d_row in reader:
            metal = d_row['Metals'].strip()
            d_redox[metal] = d_row['Redox active'].strip()
    return d_redox

def readRefCoordNum():
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

if __name__ == "__main__":
    d_coord_num = readRefCoordNum()
    print(d_coord_num)
    d_coord_map_fg = readRefCoordMap("FindGeo")
    print(d_coord_map_fg)
    d_coord_map_mc = readRefCoordMap("metalCoord")
    print(d_coord_map_mc)
    d_redox = readRefRedOx()
    print(d_redox)
