# Author:  Chenghua Shao
# Date:    2025-11-10
# Updates:

"""
This script runs MetalCoord in stats mode for specified ligands and PDB files,
parses the output, and generates a report JSON file.
"""

import argparse
import logging
import os
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wwpdb.utils.dp.metal.metalcoord.runMetalCoord import RunMetalCoord  # noqa: E402
    from wwpdb.utils.dp.metal.metalcoord.parseMetalCoord import ParseMetalCoord  # noqa: E402
else:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from runMetalCoord import RunMetalCoord  # noqa: E402
    from parseMetalCoord import ParseMetalCoord  # noqa: E402

logger = logging.getLogger(__name__)
# logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s")
# logger.setLevel(logging.DEBUG)


def main():
    """
    run MetalCoord and take arguments exactly like the command line for MetalCoord,
    then parse the output and generate a report json file in stats mode.
    Example usages:
    > python runMetalCoord.py --ligands 0KA --pdb 4DHV.cif --max_size 100
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--metalcoord_exe", help="MetalCoord executable file", type=str, default=None)
    parser.add_argument("-w", "--workdir", help="Directory to write outputs. Default is metalcoord subfolder in the current folder", type=str, default="metalcoord")
    parser.add_argument("-l", "--ligands", help="Ligand code or comma-separated multiple codes, e.g. 0KA,NCO", type=str, required=True)
    parser.add_argument("-p", "--pdb", help="PDB code or pdb file", type=str, required=True)
    parser.add_argument("-x", "--max_size", help="Maximum sample size for statistics.", type=int, default=100)
    parser.add_argument("-t", "--threshold", help="Procrustes distance threshold for finding COD reference.", type=float, default=0.3)
    args = parser.parse_args()

    l_args = ["metalcoord_exe", "workdir", "pdb", "max_size", "threshold"]

    l_ligand = args.ligands.split(",")  # split multiple ligands if applicable
    l_json_outputs = []

    # run MetalCoord for each ligand
    for ligand in l_ligand:
        d_args = {"ligand": ligand}
        for arg in l_args:
            d_args[arg] = getattr(args, arg)

        try:
            rMC = RunMetalCoord(d_args)
        except Exception as e:
            logger.error(e)
            sys.exit(1)
        rMC.setInputMode("stats")
        cmd_stdout = rMC.run()  # 1st MetalCoord run based on PDB model
        logger.info(cmd_stdout)

        fp_metalcoord_json = os.path.join(d_args["workdir"], d_args["ligand"] + ".json")
        if fp_metalcoord_json:
            l_json_outputs.append(fp_metalcoord_json)
        else:
            logger.error("MetalCoord stats mode failed, STOP without output")
            sys.exit(1)

    # parse MetalCoord results and generate report
    pMC = ParseMetalCoord()
    for fp_metalcoord_json in l_json_outputs:
        logger.info("to parse MetalCoord results from %s", fp_metalcoord_json)
        if pMC.read(fp_metalcoord_json):
            pMC.parse()
        else:
            logger.error("failed to read MetalCoord results at %s, no output", fp_metalcoord_json)
        output_json = os.path.join(d_args["workdir"], "metalcoord_report.json")
        pMC.report(output_json)
        logger.info("MetalCoord results written to %s", output_json)


if __name__ == "__main__":
    main()
