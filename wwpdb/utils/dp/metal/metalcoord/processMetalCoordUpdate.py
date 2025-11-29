# Author:  Chenghua Shao
# Date:    2025-11-10
# Updates:

"""
This module orchestrates the execution of Acedrg, MetalCoord update mode, and Servalcat to
process the input ligand CCD file metal based on provided marcromolecular structure file,
output a ligand CIF file with updated ideal coordinates and charges,
tegether with a json report summarizing the metal coordination.
"""

import argparse
import logging
import os
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wwpdb.utils.dp.metal.metalcoord.runAcedrg import RunAcedrg  # noqa: E402
    from wwpdb.utils.dp.metal.metalcoord.runMetalCoord import RunMetalCoord  # noqa: E402
    from wwpdb.utils.dp.metal.metalcoord.runServalcat import RunServalcat  # noqa: E402
    from wwpdb.utils.dp.metal.metalcoord.parseMetalCoord import ParseMetalCoord  # noqa: E402
else:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from runAcedrg import RunAcedrg  # noqa: E402
    from runMetalCoord import RunMetalCoord  # noqa: E402
    from runServalcat import RunServalcat  # noqa: E402
    from parseMetalCoord import ParseMetalCoord  # noqa: E402

logger = logging.getLogger(__name__)
# logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s")
# logger.setLevel(logging.DEBUG)


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
    except Exception as e:
        logger.error(e)
        return None

    cmd_stdout = rAG.run()
    logger.info(cmd_stdout)

    fp_acedrg_cif = os.path.join(d_args_acedrg["out"] + ".cif")
    if os.path.exists(fp_acedrg_cif):
        return fp_acedrg_cif
    else:
        return None


def callMetalCoord(d_args_metalcoord):
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
    except Exception as e:
        logger.error(e)
        return None
    rMC.setInputMode("update")
    cmd_stdout1 = rMC.run()  # 1st MetalCoord run based on PDB model
    logger.info(cmd_stdout1)

    fp_metalcoord_cif = os.path.join(d_args_metalcoord["workdir"], "metalcoord.cif")
    if not os.path.exists(fp_metalcoord_cif):
        rMC.d_args["pdb"] = None
        cmd_stdout2 = rMC.run()  # 2nd MetalCoord run by the option 'most_common'
        logger.info(cmd_stdout2)

    fp_metalcoord_json = os.path.join(d_args_metalcoord["workdir"], "metalcoord.cif.json")

    if os.path.exists(fp_metalcoord_cif) and os.path.exists(fp_metalcoord_json):
        return (fp_metalcoord_cif, fp_metalcoord_json)
    else:
        return (None, None)


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
    except Exception as e:
        logger.error(e)
        return None
    cmd_stdout = rST.run()
    logger.info(cmd_stdout)
    fp_servalcat_cif = d_args_servalcat["output_prefix"] + "_updated.cif"

    if os.path.exists(fp_servalcat_cif):
        return fp_servalcat_cif
    else:
        return None


def main():
    """
    run Acedrg-MetalCoord-Servalcat, then parse the output and generate a report json file in stats mode.
    Example usages:
    > python runMetalCoordUpdate.py --input 0KA.cif --pdb 4DHV.cif
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--acedrg_exe", help="Acedrg executable file", type=str, default=None)
    parser.add_argument("-b", "--metalcoord_exe", help="MetalCoord executable file", type=str, default=None)
    parser.add_argument("-c", "--servalcat_exe", help="Servalcat executable file", type=str, default=None)
    parser.add_argument("-w", "--workdir", help="Directory to write outputs. Default is metalcoord subfolder in the current folder", type=str, default="metalcoord")
    parser.add_argument("-i", "--input", help="Ligand cif file", type=str, required=True)
    parser.add_argument("-p", "--pdb", help="PDB code or pdb file", type=str, default=None)
    parser.add_argument("-t", "--threshold", help="Procrustes distance threshold.", type=float, default=0.3)
    args = parser.parse_args()

    # run Acedrg
    d_args_acedrg = {}
    d_args_acedrg["acedrg_exe"] = args.acedrg_exe
    d_args_acedrg["mmcif"] = args.input
    d_args_acedrg["out"] = os.path.join(args.workdir, "acedrg")
    fp_acedrg_cif = callAcedrg(d_args_acedrg)
    if not fp_acedrg_cif:
        logger.error("Acedrg failed, STOP without output")
        sys.exit(1)

    # run MetalCoord
    d_args_metalcoord = {}
    d_args_metalcoord["metalcoord_exe"] = args.metalcoord_exe
    d_args_metalcoord["workdir"] = args.workdir
    d_args_metalcoord["input"] = fp_acedrg_cif  # use Acedrg output as input
    d_args_metalcoord["pdb"] = args.pdb
    d_args_metalcoord["threshold"] = args.threshold
    (fp_metalcoord_cif, fp_metalcoord_json) = callMetalCoord(d_args_metalcoord)
    if not fp_metalcoord_cif:
        logger.error("MetalCoord update mode failed, STOP without output")
        sys.exit(1)

    # run Servalcat
    d_args_servalcat = {}
    d_args_servalcat["servalcat_exe"] = None
    d_args_servalcat["update_dictionary"] = fp_metalcoord_cif  # use MetalCoord output as input
    d_args_servalcat["output_prefix"] = os.path.join(args.workdir, "servalcat")
    fp_servalcat_cif = callServalcat(d_args_servalcat)
    if not fp_servalcat_cif:
        logger.error("Servalcat failed, STOP without output")
        sys.exit(1)

    if not fp_metalcoord_json:
        logger.error("No MetalCoord output json")
        sys.exit(1)

    logger.info("to parse MetalCoord results from %s", fp_metalcoord_json)
    pMC = ParseMetalCoord()
    if pMC.read(fp_metalcoord_json):
        pMC.parse()
        output_json = os.path.join(args.workdir, "metalcoord_report.json")
        pMC.report(output_json)
        logger.info("MetalCoord results written to %s", output_json)
    else:
        logger.error("failed to read MetalCoord results at %s, no output", fp_metalcoord_json)


if __name__ == "__main__":
    main()
