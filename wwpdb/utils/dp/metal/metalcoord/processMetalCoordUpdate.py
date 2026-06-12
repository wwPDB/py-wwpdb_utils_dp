# Author:  Chenghua Shao
# Date:    2025-11-10
# Updates:

"""
This module orchestrates the execution of Acedrg, MetalCoord update mode, and Servalcat to
process the input ligand CCD file metal based on provided marcromolecular structure file,
output a ligand CIF file with updated ideal coordinates and charges,
tegether with a json report summarizing the metal coordination.
"""
# pylint: disable=duplicate-code

import argparse
import json
import logging
import os
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wwpdb.utils.dp.metal.metal_util.run_command import setup_logger  # noqa: E402
    from wwpdb.utils.dp.metal.metalcoord.parseMetalCoord import MetalCoordParseError, ParseMetalCoord  # noqa: E402
    from wwpdb.utils.dp.metal.metalcoord.runAcedrg import AcedrgCommandExecutionError, AcedrgCommandTimeoutError, AcedrgParametersError, RunAcedrg  # noqa: E402
    from wwpdb.utils.dp.metal.metalcoord.runMetalCoord import (  # noqa: E402
        MetalCoordCommandExecutionError,
        MetalCoordCommandTimeoutError,
        MetalCoordParametersError,
        RunMetalCoord,
    )
    from wwpdb.utils.dp.metal.metalcoord.runServalcat import (  # noqa: E402
        RunServalcat,
        ServalcatCommandExecutionError,
        ServalcatCommandTimeoutError,
        ServalcatParametersError,
    )
else:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from metal_util.run_command import setup_logger  # noqa: E402
    from metalcoord.parseMetalCoord import MetalCoordParseError, ParseMetalCoord  # noqa: E402
    from metalcoord.runAcedrg import AcedrgCommandExecutionError, AcedrgCommandTimeoutError, AcedrgParametersError, RunAcedrg  # noqa: E402
    from metalcoord.runMetalCoord import MetalCoordCommandExecutionError, MetalCoordCommandTimeoutError, MetalCoordParametersError, RunMetalCoord  # noqa: E402
    from metalcoord.runServalcat import RunServalcat, ServalcatCommandExecutionError, ServalcatCommandTimeoutError, ServalcatParametersError  # noqa: E402

setup_logger(name="metalcoord", log_dir=".", b_debug=False)
logger = logging.getLogger("metalcoord.processMetalCoordUpdate")


def callAcedrg(d_args_acedrg):
    """
    Call Acedrg with the provided arguments and return the output CIF file path.

    :param d_args_acedrg: Dictionary of arguments for running Acedrg.
    :type d_args_acedrg: dict
    :returns: Path to the generated CIF file if successful, otherwise None.
    :rtype: str or None
    """

    try:
        rAG = RunAcedrg(d_args_acedrg)
    except AcedrgParametersError as e:
        logger.error("Validate Parameters error: %s", e.errors)
        return None

    try:
        cmd_stdout = rAG.run()
        logger.debug(cmd_stdout)
    except AcedrgCommandTimeoutError as e:
        logger.error("Acedrg command timed out: %s", e)
        return None
    except AcedrgCommandExecutionError as e:
        logger.error("Acedrg command execution error: %s", e)
        return None

    fp_acedrg_cif = os.path.join(d_args_acedrg["out"] + ".cif")
    if not os.path.exists(fp_acedrg_cif):
        logger.error("Acedrg output CIF file not found: %s, STOP process", fp_acedrg_cif)
        return None

    return fp_acedrg_cif


def callMetalCoord(d_args_metalcoord):  # pylint: disable=too-many-return-statements
    """
    Run MetalCoord in "update" mode and return output file paths.

    Initializes a RunMetalCoord instance with the provided argument dictionary,
    runs MetalCoord in "update" mode, and if the expected CIF output is not
    produced, retries with a fallback option (clearing the 'pdb' input in the
    RunMetalCoord arguments). The function then checks for the presence of the
    files "metalcoord.cif" and "metalcoord.cif.json" in the supplied work directory
    and returns their paths when both are present.

    :param d_args_metalcoord: Dictionary of arguments for RunMetalCoord. Must
        include at least the "workdir" key indicating where output files are
        written; other keys are passed to RunMetalCoord.
    :type d_args_metalcoord: dict
    :returns: A tuple (fp_metalcoord_cif, fp_metalcoord_json) with full paths to
        the CIF and JSON output files if both exist; (None, None) if the expected
        files are not both present; or None if initializing RunMetalCoord raises
        an exception (the exception is logged).
    :rtype: tuple(str, str) or (None, None) or None
    :side-effects: Invokes external MetalCoord runs, writes output files to the
        given workdir, and logs command output and any errors.
    """

    try:
        rMC = RunMetalCoord(d_args_metalcoord)
    except MetalCoordParametersError as e:
        logger.error("Validate Parameters error: %s", e.errors)
        return (None, None)

    rMC.setInputMode("update")
    try:
        cmd_stdout1 = rMC.run()  # 1st MetalCoord run based on PDB model
        logger.debug(cmd_stdout1)
    except MetalCoordCommandTimeoutError as e:
        logger.error("MetalCoord command timed out: %s", e)
        return (None, None)
    except MetalCoordCommandExecutionError as e:
        logger.error("MetalCoord command execution error: %s", e)
        return (None, None)

    fp_metalcoord_cif = os.path.join(d_args_metalcoord["workdir"], "metalcoord.cif")
    if not os.path.exists(fp_metalcoord_cif) and d_args_metalcoord.get("pdb"):
        logger.warning("MetalCoord update mode with PDB model did not produce output CIF, retrying with 'most_common' option by clearing the 'pdb' argument")
        rMC.d_args["pdb"] = None
        try:
            cmd_stdout2 = rMC.run()  # 2nd MetalCoord run by the option 'most_common'
            logger.debug(cmd_stdout2)
        except MetalCoordCommandTimeoutError as e:
            logger.error("MetalCoord command timed out: %s", e)
            return (None, None)
        except MetalCoordCommandExecutionError as e:
            logger.error("MetalCoord command execution error: %s", e)
            return (None, None)

    if not os.path.exists(fp_metalcoord_cif):
        logger.error("MetalCoord update mode failed to produce output CIF at %s, STOP process", fp_metalcoord_cif)
        return (None, None)

    fp_metalcoord_json = os.path.join(d_args_metalcoord["workdir"], "metalcoord.cif.json")
    if not os.path.exists(fp_metalcoord_json):
        logger.error("MetalCoord update mode failed to produce output JSON at %s, STOP process", fp_metalcoord_json)
        return (None, None)

    return (fp_metalcoord_cif, fp_metalcoord_json)


def callServalcat(d_args_servalcat):
    """
    Call Servalcat to process and update a CIF file.

    This function constructs and runs a RunServalcat instance using the provided
    argument dictionary. It logs the command output and then checks for an output
    CIF file based on the ``output_prefix`` entry in ``d_args_servalcat``.

    :param d_args_servalcat: Dictionary of arguments forwarded to RunServalcat.
        Must include the key ``output_prefix`` whose value is used to form the
        expected output filename "<output_prefix>_updated.cif".
    :type d_args_servalcat: dict
    :returns: Path to the updated CIF file if it exists after running Servalcat,
        otherwise ``None``.
    :rtype: str or None
    :raises: Exceptions raised during RunServalcat construction are logged and
        suppressed; the function returns ``None`` in that case.
    :notes: The function logs errors and info via the module logger and does not
        raise exceptions for run failures.
    """

    try:
        rST = RunServalcat(d_args_servalcat)
    except ServalcatParametersError as e:
        logger.error("Validate Parameters error: %s", e.errors)
        return None

    try:
        cmd_stdout = rST.run()
        logger.debug(cmd_stdout)
    except ServalcatCommandTimeoutError as e:
        logger.error("Servalcat command timed out: %s", e)
        return None
    except ServalcatCommandExecutionError as e:
        logger.error("Servalcat command execution error: %s", e)
        return None

    fp_servalcat_cif = d_args_servalcat["output_prefix"] + "_updated.cif"
    if not os.path.exists(fp_servalcat_cif):
        logger.error("Servalcat failed to produce output at %s, STOP process", fp_servalcat_cif)
        return None

    return fp_servalcat_cif


def main():  # pylint: disable=too-many-statements
    """
    Run Acedrg-MetalCoord-Servalcat, then parse the output and generate a report JSON file in stats mode.

    Example usages::

        python runMetalCoordUpdate.py --input 0KA.cif --pdb 4DHV.cif

    Command-line arguments:
        -a, --acedrg_exe: Acedrg executable file
        -b, --metalcoord_exe: MetalCoord executable file
        -c, --servalcat_exe: Servalcat executable file
        -w, --workdir: Directory to write outputs
        -i, --input: Ligand cif file
        -p, --pdb: PDB code or pdb file
        -t, --threshold: Procrustes distance threshold
        -s, --timeout: Timeout in seconds for running MetalCoord command
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--acedrg_exe", help="Acedrg executable file", type=str, default=None)
    parser.add_argument("-b", "--metalcoord_exe", help="MetalCoord executable file", type=str, default=None)
    parser.add_argument("-c", "--servalcat_exe", help="Servalcat executable file", type=str, default=None)
    parser.add_argument(
        "-w", "--workdir", help="Directory to write outputs. Default is metalcoord subfolder in the current folder", type=str, default="metalcoord"
    )
    parser.add_argument("-i", "--input", help="Ligand cif file", type=str, required=True)
    parser.add_argument("-p", "--pdb", help="PDB code or pdb file", type=str, default=None)
    parser.add_argument("-t", "--threshold", help="Procrustes distance threshold.", type=float, default=0.3)
    parser.add_argument("-s", "--timeout", help="Timeout in seconds for running MetalCoord command, default is 3600 seconds (1 hour)", type=int, default=3600)
    args = parser.parse_args()

    output_json = os.path.join(args.workdir, "metalcoord_report.json")  # use this json file to save MetalCoord results and also status

    # run Acedrg
    logger.info("to run Acedrg with input cif file %s to generate ideal coordinates and charges for the ligand", args.input)
    d_args_acedrg = {}
    d_args_acedrg["acedrg_exe"] = args.acedrg_exe
    d_args_acedrg["mmcif"] = args.input
    d_args_acedrg["out"] = os.path.join(args.workdir, "acedrg")
    d_args_acedrg["timeout"] = args.timeout
    fp_acedrg_cif = callAcedrg(d_args_acedrg)
    if not fp_acedrg_cif:
        with open(output_json, "w", encoding="utf-8") as file:
            json.dump({"error": "acedrg-failed", "details": "Acedrg failed to produce output CIF"}, file)
        sys.exit(0)

    # run MetalCoord
    logger.info(
        "to run MetalCoord update mode with Acedrg output %s as input to update distance and angle restraints for ServalCat, and generate metal coordination report",
        fp_acedrg_cif,
    )
    d_args_metalcoord = {}
    d_args_metalcoord["metalcoord_exe"] = args.metalcoord_exe
    d_args_metalcoord["workdir"] = args.workdir
    d_args_metalcoord["input"] = fp_acedrg_cif  # use Acedrg output as input
    d_args_metalcoord["pdb"] = args.pdb
    d_args_metalcoord["threshold"] = args.threshold
    d_args_metalcoord["timeout"] = args.timeout
    (fp_metalcoord_cif, fp_metalcoord_json) = callMetalCoord(d_args_metalcoord)
    if not fp_metalcoord_cif:
        logger.error("MetalCoord update mode failed, STOP without output")
        with open(output_json, "w", encoding="utf-8") as file:
            json.dump({"error": "metalcoord-failed", "details": "Acedrg succeeded; MetalCoord failed to produce output CIF"}, file)
        sys.exit(0)

    # run Servalcat
    logger.info("to run Servalcat with the MetalCoord output %s to further optimize ideal coordinates for the ligand", fp_metalcoord_cif)
    d_args_servalcat = {}
    d_args_servalcat["servalcat_exe"] = None
    d_args_servalcat["update_dictionary"] = fp_metalcoord_cif  # use MetalCoord output as input
    d_args_servalcat["output_prefix"] = os.path.join(args.workdir, "servalcat")
    d_args_servalcat["timeout"] = args.timeout
    fp_servalcat_cif = callServalcat(d_args_servalcat)
    if not fp_servalcat_cif:
        logger.error("Servalcat failed, STOP without output")
        with open(output_json, "w", encoding="utf-8") as file:
            json.dump({"error": "servalcat-failed", "details": "Acedrg and MetalCoord succeeded; Servalcat failed to produce output CIF"}, file)
        sys.exit(0)

    logger.info("Final ligand CIF successfully produced at %s", fp_servalcat_cif)

    logger.info("to parse MetalCoord results from %s", fp_metalcoord_json)
    pMC = ParseMetalCoord()
    try:
        pMC.read(fp_metalcoord_json)
        pMC.parse()
    except MetalCoordParseError as e:
        logger.error("failed to read MetalCoord results at %s, no output: %s", fp_metalcoord_json, e)
        with open(output_json, "w", encoding="utf-8") as file:
            json.dump({"error": "unexpected-error", "details": f"failed to read MetalCoord results at {fp_metalcoord_json}, no output: {e}"}, file)
        sys.exit(0)

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

    with open(output_json, "w", encoding="utf-8") as file:
        json.dump(l_sites_filtered, file, indent=4)
    logger.info("MetalCoord update mode geometry results written to %s", output_json)


if __name__ == "__main__":
    main()
