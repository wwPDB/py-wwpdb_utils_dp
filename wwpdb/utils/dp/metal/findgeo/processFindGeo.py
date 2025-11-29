# Author:  Chenghua Shao
# Date:    2025-11-10
# Update:

"""
Run FindGeo and parse results.
Summary:
1. Run FindGeo with user provided arguments.
2. Parse FindGeo output files.
3. Generate a report json file summarizing the results.
"""

import argparse
import logging
import os
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wwpdb.utils.dp.metal.findgeo.runFindGeo import RunFindGeo  # noqa: E402
    from wwpdb.utils.dp.metal.findgeo.parseFindGeo import ParseFindGeo  # noqa: E402
else:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from runFindGeo import RunFindGeo  # noqa: E402
    from parseFindGeo import ParseFindGeo  # noqa: E402

logger = logging.getLogger(__name__)
# logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s")
# logger.setLevel(logging.DEBUG)


def main():
    """
    run FindGeo and take arguments exactly like the command line for findgeo,
    then parse the output and generate a report json file.
    Example usages:
    > python runFindGeo.py --java-exe /path/to/java --findgeo-jar /path/to/FindGeo.jar --input 2HYV.cif
    > python runFindGeo.py --java-exe /path/to/java --findgeo-jar /path/to/FindGeo.jar --pdb 2HYV
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--excluded-donors", help="Chemical symbols of the atoms (separated by commas) excluded from metal ligands. Default is 'C,H' ", type=str, default="C,H")
    parser.add_argument("-f", "--format", help="Local file format (i.e. cif or pdb).", type=str, default="cif")
    parser.add_argument("-i", "--input", help="Local PDB/mmCIF local file.", type=str, default=None)
    parser.add_argument("-m", "--metal", help="Chemical symbol of the metal of interest. Default is all metals.", type=str, default="All")
    parser.add_argument("-o", "--overwright", help="Overwrite existing files and directories.", action="store_true", default=True)
    parser.add_argument("-p", "--pdb", help="Local input PDB file or PDB code of input PDB file to be downloaded from the web.", type=str, default=None)
    parser.add_argument("-t", "--threshold", help="Coordination distance threshold. Default is 2.8 A.", type=float, default=2.8)
    parser.add_argument("-w", "--workdir", help="Directory to write outputs. Default is findgeo subfolder in the current folder", type=str, default="findgeo")
    parser.add_argument("-x", "--excluded-metals", help="Metal symbols (separated by commas) excluded from the analysis.", type=str, default="None")
    parser.add_argument("-b", "--java-exe", help="Java executable filepath", type=str, required=True)
    parser.add_argument("-a", "--findgeo-jar", help="FindGeo compiled jar filepath", type=str, required=True)
    args = parser.parse_args()

    l_args = ["excluded-donors", "format", "input", "metal", "overwright", "pdb", "threshold", "workdir", "excluded-metals", "java-exe", "findgeo-jar"]
    d_args = {}
    for arg in l_args:
        key = arg.replace("-", "_")
        d_args[arg] = getattr(args, key)

    logger.info("run FindGeo with %s", d_args)
    rFG = RunFindGeo(d_args)
    cmd_stdout = rFG.run()

    if cmd_stdout:
        logger.info(cmd_stdout)
        logger.info("run FindGeo finished")
        logger.info("parse FindGeo results")
        pFG = ParseFindGeo(d_args["workdir"], input_format=d_args["format"])
        pFG.parse()
        output_json = os.path.join(d_args["workdir"], "findgeo_report.json")
        pFG.report(output_json)
        logger.info("FindGeo results written to %s", output_json)
    else:
        logger.error("run FindGeo failed, no output json")


if __name__ == "__main__":
    main()
