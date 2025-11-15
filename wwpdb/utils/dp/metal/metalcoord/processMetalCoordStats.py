#!/usr/bin/env python3

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
    > python runMetalCoord.py --ligand 0KA --pdb 4DHV.cif --max_size 100
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--metalcoord_exe", help="MetalCoord executable file", type=str, default=None)
    parser.add_argument("-w", "--workdir", help="Directory to write outputs. Default is metalcoord subfolder in the current folder", type=str, default="metalcoord")
    parser.add_argument("-l", "--ligand", help="Ligand code", type=str, required=True)
    parser.add_argument("-p", "--pdb", help="PDB code or pdb file", type=str, required=True)
    parser.add_argument("-x", "--max_size", help="Maximum sample size for statistics.", type=int, default=100)
    parser.add_argument("-t", "--threshold", help="Procrustes distance threshold for finding COD reference.", type=float, default=0.3)
    args = parser.parse_args()

    l_args = ["metalcoord_exe", "workdir", "ligand", "pdb", "max_size", "threshold"]
    d_args = {}
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
    if not fp_metalcoord_json:
        logger.error("MetalCoord stats mode failed, STOP without output")
        sys.exit(1)

    logger.info("to parse MetalCoord results from %s", fp_metalcoord_json)
    pMC = ParseMetalCoord()
    if pMC.read(fp_metalcoord_json):
        pMC.parse()
        output_json = os.path.join(d_args["workdir"], "metalcoord_report.json")
        pMC.report(output_json)
        logger.info("MetalCoord results written to %s", output_json)
    else:
        logger.error("failed to read MetalCoord results at %s, no output", fp_metalcoord_json)


if __name__ == "__main__":
    main()
