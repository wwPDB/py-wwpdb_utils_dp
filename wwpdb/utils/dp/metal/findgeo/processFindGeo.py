# Author:  Chenghua Shao
# Date:    2025-11-10
# Update:

"""
Run FindGeo and parse results.
Summary:
1. Run FindGeo with user provided arguments. Run FindGeo twice if comparison between excluding carbon donors or not is requested.
2. Parse FindGeo output files.
3. Generate a report json file summarizing the results.
4. If comparison between excluding carbon donors or not is requested, compare the results of the two runs and select the
best result for each metal site based on chemical rules, and generate a report json file for the selected results.
"""
# pylint: disable=duplicate-code

import argparse
import logging
import json
import os
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wwpdb.utils.dp.metal.findgeo.runFindGeo import RunFindGeo, FindGeoCommandExecutionError, FindGeoCommandTimeoutError, ValidateParametersError  # noqa: E402
    from wwpdb.utils.dp.metal.findgeo.parseFindGeo import ParseFindGeo  # noqa: E402
    from wwpdb.utils.dp.metal.metal_util.run_command import setup_logger  # noqa: E402
else:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from findgeo.runFindGeo import RunFindGeo, FindGeoCommandExecutionError, FindGeoCommandTimeoutError, ValidateParametersError  # noqa: E402
    from findgeo.parseFindGeo import ParseFindGeo  # noqa: E402
    from metal_util.run_command import setup_logger  # noqa: E402

setup_logger(name="findgeo", log_dir=".", b_debug=False)
logger = logging.getLogger("findgeo.processFindGeo")


class jsonValidationError(Exception):
    """Raised when a JSON file cannot be read or parsed."""


def readJson(fp):
    """
    Read a JSON file containing a list of site entries and return the parsed content.
    Attempt to open and parse the JSON file at the given path. Any exception returns a empty list,
    and this is intentional to avoid failure when a file is not generated from the previous step.
    :param fp: Path to the JSON file.
    :type fp: str or os.PathLike
    :returns: Parsed JSON content (typically a list of site dictionaries). Returns [] if file not found.
    :rtype: list
    """
    try:
        with open(fp, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data
    except FileNotFoundError as e:
        raise jsonValidationError(f"JSON file not found: {fp}") from e
    except json.JSONDecodeError as e:
        raise jsonValidationError(f"Invalid JSON in file {fp}: {e}") from e
    except OSError as e:
        raise jsonValidationError(f"Error reading file {fp}: {e}") from e
    except Exception as e:  # pylint: disable=broad-exception-caught
        raise jsonValidationError(f"Unexpected error reading JSON file {fp}: {e}") from e


def readSites(l_sites):
    """
    Create a mapping from a site-identifying tuple to the original site dictionary.
    The key tuple is used for identifying a unique metal site, and for comparision of results from different runs.
    :param l_sites: Iterable of site dictionaries. Each dictionary may contain the keys
                    "residue", "metal", "chain", "sequence", "icode", and "altloc".
                    Missing keys are treated as empty strings.
    :type l_sites: Iterable[dict]
    :returns: Dictionary mapping a tuple
              (ccd_id, atom_label, chain, res_num, ins, alt)
              to the corresponding site dictionary.
    :rtype: dict
    """
    d_sites = {}
    for d_one in l_sites:
        ccd_id = d_one.get("residue", "")
        atom_label = d_one.get("metal", "")
        chain = d_one.get("chain", "")
        res_num = d_one.get("sequence", "")
        ins = d_one.get("icode", "")
        alt = d_one.get("altloc", "")
        t_atom = (ccd_id, atom_label, chain, res_num, ins, alt)
        d_sites[t_atom] = d_one
    return d_sites


def compareRmsd(d_site_exc, d_site_inc):
    """
    Compare RMSD values from two site dictionaries and decide carbon handling.
    :param d_site_exc: Dictionary expected to contain key 'rmsd' for the exclude candidate.
    :type d_site_exc: dict
    :param d_site_inc: Dictionary expected to contain key 'rmsd' for the include candidate.
    :type d_site_inc: dict
    :returns: 'exclude_carbon' if rmsd(d_site_exc) <= rmsd(d_site_inc), else 'include_carbon'.
    :rtype: str
    :notes: RMSD values are converted to float; missing or non-numeric values are treated as 99.0.
    """

    rmsd_exc = d_site_exc.get("rmsd")
    rmsd_inc = d_site_inc.get("rmsd")
    try:
        rmsd_exc = float(rmsd_exc)
    except ValueError:
        rmsd_exc = 99.0
    try:
        rmsd_inc = float(rmsd_inc)
    except ValueError:
        rmsd_inc = 99.0
    if rmsd_exc <= rmsd_inc:
        return "exclude_carbon"
    return "include_carbon"


def compareResults(l_exclude_carbon, l_include_carbon):  # pylint: disable=too-many-branches,too-many-statements
    """
    Compare results of two runs (excluding vs including carbon donors)s, and select based on the following chemical rules:
    If the metal-C bond type is allowed, then choose between the two results based on the following:
    1. If only one method (with carbon or without carbon) gives any output, that output is selected.
    2. If one method gives Regular result and the other gives non-Regular (Distorted or Irregular) then the Regular result is selected.
    3. If one method gives Distorted result and the other gives Irregular result, then the Distorted result is selected.
    4. If both results are Regular or both are Distorted, check if both coordination numbers are allowed. If only one is allowed,
    select the allowed coordination. If both are allowed, select the output with the higher coordination number. If both are allowed
    and the coordination number is the same in both results, select the result with the lowest RMSD. If neither coordination number
    is allowed, select the output with the lowest RMSD.
    5. If both results are Irregular, check if both coordination numbers are allowed. If only one is allowed, select the allowed coordination.
    If both or neither coordination number is allowed, select the output with the lowest RMSD.

    The function reads two FindGeo JSON outputs (one produced with carbon donors excluded and one
    with carbon donors included), converts them into site dictionaries and selects a single best
    result per metal site using the above rules.
    :param l_exclude_carbon: List of site dicts from the FindGeo run with carbon donors excluded.
    :type l_exclude_carbon: list
    :param l_include_carbon: List of site dicts from the FindGeo run with carbon donors included.
    :type l_include_carbon: list
    :returns: List of selected site dictionaries (one entry per metal site) chosen according to the rules above.
    :rtype: list
    :notes: The function relies on readJson, readSites and compareRmsd helper routines and emits informational logs.
    """
    # convert the list of sites into a dict with key as the site-identifying tuple and value as the original site dict
    # for both runs, which allows easy comparision between the two runs for the same metal site
    d_site_exclude_carbon = readSites(l_exclude_carbon)
    d_site_include_carbon = readSites(l_include_carbon)
    # combine all metal sites tuple keys from both runs to make sure all sites are included in the comparision, even if a site only has results in one run but not the other
    l_atom = list(set(d_site_exclude_carbon.keys()) | set(d_site_include_carbon.keys()))
    # initialize list of sites
    l_sites = []
    # enumerate through each metal site identified by the tuple key
    for t_atom in l_atom:
        logger.debug("compare results for metal site %s", t_atom)
        # read both results for the same metal site, exclude Carbon donors and include Carbon donors, if any
        d_site_exc = d_site_exclude_carbon.get(t_atom, {})
        d_site_inc = d_site_include_carbon.get(t_atom, {})
        # check if the metal-Carbon bond type is allowed, skip if not
        if d_site_inc and d_site_inc.get("carbon_metal") == "NO":
            d_site_inc = {}  # set to empty dict if Carbon is not allowed, which essentiall skips the results
        # start selection based on chemical logic:
        # 1. If only one method (with carbon or without carbon) gives any output, that output is selected.
        if d_site_exc and not d_site_inc:
            l_sites.append(d_site_exc)
            continue
        if not d_site_exc and d_site_inc:
            l_sites.append(d_site_inc)
            continue
        # start geometry-based selection
        tag_exc = d_site_exc.get("tag", "")
        tag_inc = d_site_inc.get("tag", "")
        # 2. If one method gives Regular result and the other gives non-Regular (Distorted or Irregular) then the Regular result is selected.
        if tag_exc == "Regular" and tag_inc != "Regular":
            l_sites.append(d_site_exc)
            continue
        if tag_exc != "Regular" and tag_inc == "Regular":
            l_sites.append(d_site_inc)
            continue
        # 3. If one method gives Distorted result and the other gives Irregular result, then the Distorted result is selected.
        # this must be run after #2 above Regular vs non-Regular selection, because Regular is higher priority.
        if tag_exc == "Distorted" and tag_inc != "Distorted":
            l_sites.append(d_site_exc)
            continue
        if tag_exc != "Distorted" and tag_inc == "Distorted":
            l_sites.append(d_site_inc)
            continue
        # 4. If both results are Regular or both are Distorted, check if both coordination numbers are allowed.
        # If only one is allowed, select the allowed coordination.
        # If both are allowed, select the output with the higher coordination number.
        # If both are allowed and the coordination number is the same in both results, select the result with the lowest RMSD.
        # If neither coordination number is allowed, select the output with the lowest RMSD.
        if (tag_exc == "Regular" and tag_inc == "Regular") or (tag_exc == "Distorted" and tag_inc == "Distorted"):
            # if only one coordination number is allowed, select the allowed one
            coord_allowed_exc = d_site_exc.get("coordination_number_allowed")
            coord_allowed_inc = d_site_inc.get("coordination_number_allowed")
            if coord_allowed_exc == "YES" and coord_allowed_inc != "YES":
                l_sites.append(d_site_exc)
                continue
            if coord_allowed_exc != "YES" and coord_allowed_inc == "YES":
                l_sites.append(d_site_inc)
                continue
            # if neither coordination numbers is allowed, select the one with lower RMSD
            if coord_allowed_exc != "YES" and coord_allowed_inc != "YES":
                if compareRmsd(d_site_exc, d_site_inc) == "exclude_carbon":
                    l_sites.append(d_site_exc)
                    continue
                l_sites.append(d_site_inc)
                continue
            # if both coordination numbers are allowed
            if coord_allowed_exc == "YES" and coord_allowed_inc == "YES":
                coord_num_exc = d_site_exc.get("coordination")
                coord_num_inc = d_site_inc.get("coordination")
                try:
                    coord_num_exc = int(coord_num_exc)
                except ValueError:
                    coord_num_exc = 0
                try:
                    coord_num_inc = int(coord_num_inc)
                except ValueError:
                    coord_num_inc = 0
                if coord_num_exc > coord_num_inc:
                    l_sites.append(d_site_exc)
                    continue
                if coord_num_exc < coord_num_inc:
                    l_sites.append(d_site_inc)
                    continue
                # if both have the same allowed coordination number, select the one with lower RMSD
                if compareRmsd(d_site_exc, d_site_inc) == "exclude_carbon":
                    l_sites.append(d_site_exc)
                    continue
                l_sites.append(d_site_inc)
                continue
        # 5. If both results are Irregular, check if both coordination numbers are allowed.
        # If only one is allowed, select the allowed coordination.
        if tag_exc == "Irregular" and tag_inc == "Irregular":
            coord_allowed_exc = d_site_exc.get("coordination_number_allowed")
            coord_allowed_inc = d_site_inc.get("coordination_number_allowed")
            if coord_allowed_exc == "YES" and coord_allowed_inc != "YES":
                l_sites.append(d_site_exc)
                continue
            if coord_allowed_exc != "YES" and coord_allowed_inc == "YES":
                l_sites.append(d_site_inc)
                continue
            # if both or neither coordination number is allowed, select the one with lower RMSD
            if compareRmsd(d_site_exc, d_site_inc) == "exclude_carbon":
                l_sites.append(d_site_exc)
                continue
            l_sites.append(d_site_inc)
            continue
    return l_sites


def runCompare(d_args):  # pylint: disable=too-many-statements
    """
    Run FindGeo twice (with and without Carbon donors) and compare results.

    :param d_args: Dictionary of arguments for running FindGeo.
    :type d_args: dict
    :returns: True if both runs succeed, False otherwise.
    :rtype: bool
    """
    filepath_json = os.path.join(d_args["workdir"], "findgeo_report.json")  # final output json file path
    try:
        os.makedirs(d_args['workdir'], exist_ok=True)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.exception("cannot create workdir: %s with error %s", d_args['workdir'], e)
        print(f"ERROR: cannot create workdir: {d_args['workdir']} with error {e}", file=sys.stderr)
        sys.exit(1)

    l_exclude_donors = d_args["excluded-donors"].split(",")
    if "C" in l_exclude_donors:
        l_exclude_carbon = l_exclude_donors
        l_include_carbon = [d for d in l_exclude_donors if d != "C"]
    else:
        l_exclude_carbon = ["C"] + l_exclude_donors
        l_include_carbon = l_exclude_donors

    # 1st run with Carbon donor excluded
    logger.info("to run FindGeo with Carbon donor EXCLUDED")
    d_args_exclude_carbon = d_args.copy()
    d_args_exclude_carbon["excluded-donors"] = ",".join(l_exclude_carbon)
    d_args_exclude_carbon["workdir"] = d_args["workdir"] + "_exclude_carbon"
    rt_exclude_carbon = runOne(d_args_exclude_carbon)
    json_exclude_carbon = os.path.join(d_args_exclude_carbon["workdir"], "findgeo_report.json")

    # check 1st run result
    if not rt_exclude_carbon:
        try:
            d_exception = readJson(json_exclude_carbon)
            with open(filepath_json, "w", encoding="utf-8") as file:
                json.dump(d_exception, file, indent=4)
            logger.error("FindGeo run with Carbon excluded did not produce valid results: %s", d_exception.get("error", "unknown error"))
        except jsonValidationError as e:
            with open(filepath_json, "w", encoding="utf-8") as file:
                json.dump({"error": "json-error", "details": str(e)}, file, indent=4)
            logger.error("JSON validation error: %s", e)
        return False
    logger.info("FindGeo run with Carbon donor excluded finished successfully, results in %s", json_exclude_carbon)

    # 2nd run with Carbon donor included
    logger.info("to run FindGeo with Carbon donor INCLUDED")
    d_args_include_carbon = d_args.copy()
    d_args_include_carbon["excluded-donors"] = ",".join(l_include_carbon)
    d_args_include_carbon["workdir"] = d_args["workdir"] + "_include_carbon"
    rt_include_carbon = runOne(d_args_include_carbon)
    json_include_carbon = os.path.join(d_args_include_carbon["workdir"], "findgeo_report.json")

    # check 2nd run result
    if not rt_include_carbon:
        try:
            d_exception = readJson(json_include_carbon)
            with open(filepath_json, "w", encoding="utf-8") as file:
                json.dump(d_exception, file, indent=4)
            logger.error("FindGeo run with Carbon included did not produce valid results: %s", d_exception.get("error", "unknown error"))
        except jsonValidationError as e:
            with open(filepath_json, "w", encoding="utf-8") as file:
                json.dump({"error": "json-error", "details": str(e)}, file, indent=4)
            logger.error("JSON validation error: %s", e)
        return False
    logger.info("FindGeo run with Carbon donor included finished successfully, results in %s", json_include_carbon)

    # if both runs are good, compare two runs and generate report for the selected best results based on chemical rules.
    logger.info("compare results of two runs with and without excluding Carbon donors")
    l_exclude_carbon = readJson(json_exclude_carbon)
    l_include_carbon = readJson(json_include_carbon)
    l_sites = compareResults(l_exclude_carbon, l_include_carbon)
    with open(filepath_json, "w", encoding="utf-8") as file:
        json.dump(l_sites, file, indent=4)
    logger.info("comparison finished, selected results written to %s", filepath_json)

    return True


def runOne(d_args):
    """
    Run FindGeo once with the given arguments and write results to a JSON file.

    :param d_args: Dictionary of arguments for running FindGeo.
    :type d_args: dict
    :returns: True if run and parse succeed, False otherwise.
    :rtype: bool
    """
    logger.info("processFindGeo input parameters %s", d_args)
    output_json = os.path.join(d_args["workdir"], "findgeo_report.json")

    try:
        rFG = RunFindGeo(d_args)
    except ValidateParametersError as e:
        logger.error("Validate Parameters error: %s", e.errors)
        with open(output_json, "w", encoding="utf-8") as file:
            json.dump({"error": "parameters-error", "details": e.errors}, file)
        return False
    # no need to handle other exceptions because RunFindGeo.__init__() already handled them.

    try:
        cmd_stdout = rFG.run()
        logger.debug("FindGeo command stdout:\n %s", cmd_stdout)
        logger.info("run FindGeo finished successfully")
        logger.info("to parse FindGeo results")
        pFG = ParseFindGeo(d_args["workdir"], input_format=d_args["format"])
        pFG.parse()
        pFG.report(output_json)
        logger.info("FindGeo results written to %s", output_json)
        return True
    except FindGeoCommandTimeoutError as e:
        logger.error("FindGeo command timed out: %s", e)
        with open(output_json, "w", encoding="utf-8") as file:
            json.dump({"error": "timeout", "details": f"Timeout after {d_args.get('timeout', 3600)} seconds"}, file)
        return False
    except FindGeoCommandExecutionError as e:
        logger.error("FindGeo command execution error: %s", e)
        with open(output_json, "w", encoding="utf-8") as file:
            json.dump({"error": "execution-error", "details": str(e)}, file)
        return False
    # no need to handle other exceptions because RunFindGeo.run() already handled them.


def main():  # pylint: disable=too-many-statements
    """
    run FindGeo and take arguments exactly like the command line for findgeo,
    then parse the output and generate a report json file.
    Example usages:
    > python runFindGeo.py --java-exe /path/to/java --findgeo-jar /path/to/FindGeo.jar --input 2HYV.cif
    > python runFindGeo.py --java-exe /path/to/java --findgeo-jar /path/to/FindGeo.jar --pdb 2HYV
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--excluded-donors", help="Chemical symbols of the atoms (separated by commas) excluded from metal ligands. Default is 'H,D' ", type=str, default="H,D")
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
    parser.add_argument("-c", "--compare-donors", help="Run comparison between excluding carbon donors or not", action="store_true", default=False)
    parser.add_argument("-z", "--filter", help="Filter to output regular geometry only for CCD annotation", action="store_true", default=False)
    parser.add_argument("-s", "--timeout", help="Timeout in seconds for running FindGeo command, default is 3600 seconds (1 hour)", type=int, default=3600)
    args = parser.parse_args()

    l_args = ["excluded-donors", "format", "input", "metal", "overwright", "pdb", "threshold", "workdir", "excluded-metals", "java-exe", "findgeo-jar", "timeout"]
    d_args = {}
    for arg in l_args:
        key = arg.replace("-", "_")  # CLI arguments with - are converted to _ in argparse, e.g. --a-b args.a_b
        d_args[arg] = getattr(args, key)
    if args.compare_donors:
        # run with and without Carbon donor, then compare the results
        logger.info("request to run FindGeo with comparison between excluding Carbon donors or not")
        runCompare(d_args)
    else:
        # run FindGeo once with the provided arguments without comparison
        logger.info("request to run FindGeo without comparison between excluding Carbon donors or not")
        runOne(d_args)

    # examine the results and exit if not found
    fp_json = os.path.join(d_args["workdir"], "findgeo_report.json")
    if not os.path.exists(fp_json):
        print(f"ERROR: cannot find FindGeo report json at {fp_json}", file=sys.stderr)
        sys.exit(1)

    # no exception handling below as the file and folder permission were just checked in methods above
    if args.filter:
        # filter output for CCD annotation
        logger.info("to filter FindGeo results to keep regular geometry only for CCD annotation")
        with open(fp_json, "r", encoding="utf-8") as f:
            l_sites = json.load(f)
        l_sites_filtered = []
        for d_site in l_sites:
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
            logger.info("%s regular sites filtered out of total %s sites after applying regular geometry filter", len(l_sites_filtered), len(l_sites))
        if l_sites_filtered != l_sites:
            fp_json_filtered = os.path.join(d_args["workdir"], "findgeo_report.json")
            with open(fp_json_filtered, "w", encoding="utf-8") as f:
                json.dump(l_sites_filtered, f, indent=4)
            logger.info("filtered report replacing the previous report at %s", fp_json_filtered)


if __name__ == "__main__":
    main()
