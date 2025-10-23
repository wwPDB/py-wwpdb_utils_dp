#!/usr/bin/env python3

import argparse
import logging
import os
import sys

sys.path.append(os.path.dirname(__file__))
from runFindGeo import RunFindGeo
from parseFindGeo import ParseFindGeo

logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s")
logger.setLevel(logging.DEBUG)


def main():
    """
    run FindGeo and take arguments exactly like the command line for findgeo, 
    then parse the output and generate a report json file.
    Example usages:
    > python runFindGeo.py --java_exe /path/to/java --findgeo_jar /path/to/FindGeo.jar --input 2HYV.cif
    > python runFindGeo.py --java_exe /path/to/java --findgeo_jar /path/to/FindGeo.jar --pdb 2HYV
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--excluded_donors", help="Chemical symbols of the atoms (separated by commas) excluded from metal ligands. Default is 'C,H' ", type=str, default="C,H")
    parser.add_argument("--format", help="Local file format (i.e. cif or pdb).", type=str, default="cif")
    parser.add_argument("--input", help="Local PDB/mmCIF local file.", type=str, default=None)
    parser.add_argument("--metal", help="Chemical symbol of the metal of interest. Default is all metals.", type=str, default=None)
    parser.add_argument("--overwright", help="Overwrite existing files and directories.", action="store_true", default=True)
    parser.add_argument("--pdb", help="Local input PDB file or PDB code of input PDB file to be downloaded from the web.", type=str, default=None)
    parser.add_argument("--threshold", help="Coordination distance threshold. Default is 2.8 A.", type=float, default=2.8)
    parser.add_argument("--workdir", help="Directory where to find or download the input PDB file and to write outputs. Default is findgeo subfolder in the current folder", type=str, default="findgeo")
    parser.add_argument("--java_exe", help="Java executable filepath", type=str, required=True)
    parser.add_argument("--findgeo_jar", help="FindGeo compiled jar filepath", type=str, required=True)
    args = parser.parse_args()

    l_args = ["excluded_donors", "format", "input", "metal", "overwright", "pdb", "threshold", "workdir", "java_exe", "findgeo_jar"]
    d_args = {k: getattr(args, k) for k in l_args}

    rFG = RunFindGeo(d_args)
    rFG.run()

    pFG = ParseFindGeo(d_args["workdir"], input_format=d_args["format"])
    pFG.parse()
    output_json = os.path.join(d_args["workdir"], "findgeo_report.json")
    pFG.report(output_json)

if __name__ == "__main__":
    main()
