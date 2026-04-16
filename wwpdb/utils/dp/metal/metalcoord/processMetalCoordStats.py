# Author:  Chenghua Shao
# Date:    2025-11-10
# Updates:

"""
This script runs MetalCoord in stats mode for specified ligands and PDB files,
parses the output, and generates a report JSON file.
"""

import argparse
import json
import logging
import os
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wwpdb.utils.dp.metal.metalcoord.runMetalCoord import RunMetalCoord, MetalCoordCommandExecutionError, MetalCoordCommandTimeoutError, MetalCoordParametersError  # noqa: E402
    from wwpdb.utils.dp.metal.metalcoord.parseMetalCoord import ParseMetalCoord, MetalCoordParseError  # noqa: E402
    from wwpdb.utils.dp.metal.metal_util.run_command import setup_logger  # noqa: E402
else:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from metalcoord.runMetalCoord import RunMetalCoord, MetalCoordCommandExecutionError, MetalCoordCommandTimeoutError, MetalCoordParametersError  # noqa: E402
    from metalcoord.parseMetalCoord import ParseMetalCoord, MetalCoordParseError  # noqa: E402
    from metal_util.run_command import setup_logger  # noqa: E402


setup_logger(name="metalcoord", log_dir=".", b_debug=False)
logger = logging.getLogger("metalcoord.processMetalCoordStats")


def main():
    """
    Run MetalCoord in stats mode and generate a report JSON file.

    This function takes arguments exactly like the command line for MetalCoord,
    runs MetalCoord for each ligand, parses the output, and generates a report JSON file.

    Example usages::

        python runMetalCoord.py --ligands 0KA --pdb 4DHV.cif --max_size 100

    Command-line arguments:
        -b, --metalcoord_exe: MetalCoord executable file
        -w, --workdir: Directory to write outputs
        -l, --ligands: Ligand code or comma-separated multiple codes
        -p, --pdb: PDB code or pdb file
        -x, --max_size: Maximum sample size for statistics
        -t, --threshold: Procrustes distance threshold for finding COD reference
        -z, --filter: Filter to output regular geometry only for CCD annotation
        -s, --timeout: Timeout in seconds for running MetalCoord command
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--metalcoord_exe", help="MetalCoord executable file", type=str, default=None)
    parser.add_argument("-w", "--workdir", help="Directory to write outputs. Default is metalcoord subfolder in the current folder", type=str, default="metalcoord")
    parser.add_argument("-l", "--ligands", help="Ligand code or comma-separated multiple codes, e.g. 0KA,NCO", type=str, required=True)
    parser.add_argument("-p", "--pdb", help="PDB code or pdb file", type=str, required=True)
    parser.add_argument("-x", "--max_size", help="Maximum sample size for statistics.", type=int, default=100)
    parser.add_argument("-t", "--threshold", help="Procrustes distance threshold for finding COD reference.", type=float, default=0.3)
    parser.add_argument("-z", "--filter", help="Filter to output regular geometry only for CCD annotation", action="store_true", default=False)
    parser.add_argument("-s", "--timeout", help="Timeout in seconds for running MetalCoord command, default is 3600 seconds (1 hour)", type=int, default=3600)
    args = parser.parse_args()

    l_args = ["metalcoord_exe", "workdir", "pdb", "max_size", "threshold", "timeout"]

    l_ligand = args.ligands.split(",")  # split multiple ligands if applicable
    l_json_outputs = []

    output_json = os.path.join(args.workdir, "metalcoord_report.json")
    # run MetalCoord for each ligand
    for ligand in l_ligand:
        d_args = {"ligand": ligand}
        for arg in l_args:
            d_args[arg] = getattr(args, arg)

        try:
            rMC = RunMetalCoord(d_args)
        except MetalCoordParametersError as e:
            logger.error("Validate Parameters error: %s", e.errors)
            with open(output_json, "w") as file:
                json.dump({"error": "parameters-error", "details": e.errors}, file)
            sys.exit(0)
        # no need to handle exceptions because RunMetalCoord.__init__() already handled them.

        rMC.setInputMode("stats")
        try:
            cmd_stdout = rMC.run()  # 1st MetalCoord run based on PDB model
            logger.debug(cmd_stdout)
        except MetalCoordCommandTimeoutError as e:
            logger.error("MetalCoord command timed out: %s", e)
            with open(output_json, "w") as file:
                json.dump({"error": "timeout", "details": str(e)}, file)
            sys.exit(0)
        except MetalCoordCommandExecutionError as e:
            logger.error("MetalCoord command execution error: %s", e)
            with open(output_json, "w") as file:
                json.dump({"error": "execution-error", "details": str(e)}, file)
            sys.exit(0)
        # no need to handle exceptions because RunMetalCoord.run() already handled them.

        fp_metalcoord_json = os.path.join(d_args["workdir"], d_args["ligand"] + ".json")
        if os.path.exists(fp_metalcoord_json):
            l_json_outputs.append(fp_metalcoord_json)
        else:
            logger.error("Unexpected error when running MetalCoord: cannot find output file for ligand %s", ligand)
            with open(output_json, "w") as file:
                json.dump({"error": "unexpected-error", "details": "cannot find output file for ligand %s" % ligand}, file)
            sys.exit(0)

    # parse MetalCoord results and generate report
    pMC = ParseMetalCoord()
    for fp_metalcoord_json in l_json_outputs:
        logger.info("to parse MetalCoord results from %s", fp_metalcoord_json)
        try:
            pMC.read(fp_metalcoord_json)
            pMC.parse()
        except MetalCoordParseError as e:
            logger.error("failed to read MetalCoord results at %s, no output: %s", fp_metalcoord_json, e)
            with open(output_json, "w") as file:
                json.dump({"error": "unexpected-error", "details": "failed to read MetalCoord results at %s, no output: %s" % (fp_metalcoord_json, str(e))}, file)
            sys.exit(0)
    if args.filter:
        logger.info("to filter MetalCoord results to keep regular geometry only for CCD annotation")
        l_sites_filtered = []
        for d_site in pMC.l_sites:
            # filter to keep only regular geometry for CCD annotation
            # filter out empty class
            if not d_site.get("class").strip():
                continue
            # filter out non-Regular sites
            if d_site.get("tag") != "Regular":
                continue
            # filter out sites with non-allowed coordination number
            if d_site.get("coordination_number_allowed") == "NO":
                continue
            # filter out exception class
            if d_site.get("class_in_exception") == "YES":
                continue
            # if not filtered out by any of the above criteria, add to the filtered list
            l_sites_filtered.append(d_site)
        logger.info("%s regular sites filtered out of total %s sites after applying regular geometry filter", len(l_sites_filtered), len(pMC.l_sites))
    else:
        l_sites_filtered = pMC.l_sites
        logger.info("No filtering applied, total %s sites in output", len(l_sites_filtered))

    with open(output_json, "w") as file:
        json.dump(l_sites_filtered, file, indent=4)
    logger.info("MetalCoord stats mode results written to %s", output_json)


if __name__ == "__main__":
    main()
