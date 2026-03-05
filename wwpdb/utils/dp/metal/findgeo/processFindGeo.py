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
import json
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


def readJsonSiteList(fp):
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
        with open(fp, "r") as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        logger.warning("cannot find %s", fp)
        return []
    except json.JSONDecodeError as e:
        logger.error("invalid JSON in file %s: %s", fp, e)
        return []
    except OSError as e:
        logger.error("error reading file %s: %s", fp, e)
        return []


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
    else:
        return "include_carbon"


def compareResults(json_exclude_carbon, json_include_carbon):
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
    :param json_exclude_carbon: Path to or object containing the FindGeo JSON output produced with carbon donors excluded.
    :type json_exclude_carbon: str or mapping
    :param json_include_carbon: Path to or object containing the FindGeo JSON output produced with carbon donors included.
    :type json_include_carbon: str or mapping
    :returns: List of selected site dictionaries (one entry per metal site) chosen according to the rules above.
    :rtype: list
    :notes: The function relies on readJsonSiteList, readSites and compareRmsd helper routines and emits informational logs.
    """
    logger.info("compare results of two runs with and without excluding Carbon donors")
    # read json output of the run with Carbon excluded, if not found, set it to empty list
    l_exclude_carbon = readJsonSiteList(json_exclude_carbon)
    # read json output of the run with Carbon included, if not found, set it to empty list
    l_include_carbon = readJsonSiteList(json_include_carbon)
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
        # logger.debug("result with Carbon excluded: %s", d_site_exc)
        d_site_inc = d_site_include_carbon.get(t_atom, {})
        # logger.debug("result with Carbon included: %s", d_site_inc)
        # check if the metal-Carbon bond type is allowed, skip if not
        if d_site_inc and d_site_inc.get("carbon_metal") == "NO":
            logger.debug("Carbon is not allowed for metal site %s, skip results from including carbon donor", t_atom)
            d_site_inc = {}  # set to empty dict if Carbon is not allowed, which essentiall skips the results
        # start selection based on chemical logic:
        # 1. If only one method (with carbon or without carbon) gives any output, that output is selected.
        if d_site_exc and not d_site_inc:
            logger.debug("only valid FindGeo hit found for %s with Carbon excluded", t_atom)
            l_sites.append(d_site_exc)
            continue
        elif not d_site_exc and d_site_inc:
            logger.debug("only valid FindGeo hit found for %s with Carbon included", t_atom)
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
            elif coord_allowed_exc != "YES" and coord_allowed_inc == "YES":
                l_sites.append(d_site_inc)
                continue
            # if neither coordination numbers is allowed, select the one with lower RMSD
            if coord_allowed_exc != "YES" and coord_allowed_inc != "YES":
                if compareRmsd(d_site_exc, d_site_inc) == "exclude_carbon":
                    l_sites.append(d_site_exc)
                    continue
                else:
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
                elif coord_num_exc < coord_num_inc:
                    l_sites.append(d_site_inc)
                    continue
                else:  # if both have the same allowed coordination number, select the one with lower RMSD
                    if compareRmsd(d_site_exc, d_site_inc) == "exclude_carbon":
                        l_sites.append(d_site_exc)
                        continue
                    else:
                        l_sites.append(d_site_inc)
                        continue
        # 5. If both results are Irregular, check if both coordination numbers are allowed.
        # If only one is allowed, select the allowed coordination.
        if (tag_exc == "Irregular" and tag_inc == "Irregular"):
            coord_allowed_exc = d_site_exc.get("coordination_number_allowed")
            coord_allowed_inc = d_site_inc.get("coordination_number_allowed")
            if coord_allowed_exc == "YES" and coord_allowed_inc != "YES":
                l_sites.append(d_site_exc)
                continue
            elif coord_allowed_exc != "YES" and coord_allowed_inc == "YES":
                l_sites.append(d_site_inc)
                continue
            # if both or neither coordination number is allowed, select the one with lower RMSD
            if compareRmsd(d_site_exc, d_site_inc) == "exclude_carbon":
                l_sites.append(d_site_exc)
                continue
            else:
                l_sites.append(d_site_inc)
                continue
    return l_sites


def runCompare(d_args):
    l_exclude_donors = d_args["excluded-donors"].split(",")
    if "C" in l_exclude_donors:
        l_exclude_carbon = l_exclude_donors
        l_include_carbon = [d for d in l_exclude_donors if d != "C"]
    else:
        l_exclude_carbon = ["C"] + l_exclude_donors
        l_include_carbon = l_exclude_donors
    # 1st run with Carbon donor excluded
    logger.info("run FindGeo with Carbon donor excluded")
    d_args_exclude_carbon = d_args.copy()
    d_args_exclude_carbon["excluded-donors"] = ",".join(l_exclude_carbon)
    d_args_exclude_carbon["workdir"] = d_args["workdir"] + "_exclude_carbon"
    rt_exclude_carbon = runOne(d_args_exclude_carbon)
    # 2nd run with Carbon donor included
    logger.info("run FindGeo with Carbon donor included")
    d_args_include_carbon = d_args.copy()
    d_args_include_carbon["excluded-donors"] = ",".join(l_include_carbon)
    d_args_include_carbon["workdir"] = d_args["workdir"] + "_include_carbon"
    rt_include_carbon = runOne(d_args_include_carbon)
    if (not rt_exclude_carbon) and (not rt_include_carbon):
        logger.error("both runs with and without excluding Carbon donors failed, no output json generated, STOP")
        return False
    # compare results of the two runs
    json_exclude_carbon = os.path.join(d_args_exclude_carbon["workdir"], "findgeo_report.json")
    json_include_carbon = os.path.join(d_args_include_carbon["workdir"], "findgeo_report.json")
    l_sites = compareResults(json_exclude_carbon, json_include_carbon)
    try:
        os.makedirs(d_args['workdir'], exist_ok=True)
    except Exception as e:
        logger.error("cannot create workdir: %s with error %s", d_args['workdir'], e)
        return False
    filepath_json = os.path.join(d_args["workdir"], "findgeo_report.json")
    logger.info("to write report to %s", filepath_json)
    with open(filepath_json, "w") as file:
        json.dump(l_sites, file, indent=4)
    return True


def runOne(d_args):
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
        return True
    else:
        logger.error("run FindGeo failed, no output json")
        return False


def main():
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
    args = parser.parse_args()

    l_args = ["excluded-donors", "format", "input", "metal", "overwright", "pdb", "threshold", "workdir", "excluded-metals", "java-exe", "findgeo-jar"]
    d_args = {}
    for arg in l_args:
        key = arg.replace("-", "_")  # CLI arguments with - are converted to _ in argparse, e.g. --a-b args.a_b
        d_args[arg] = getattr(args, key)
    if args.compare_donors:
        # run with and without Carbon donor, then compare the results
        logger.info("run comparison between excluding Carbon donors or not")
        runCompare(d_args)
    else:
        # run FindGeo once with the provided arguments without comparison
        logger.info("run FindGeo with provided arguments without comparison between excluding Carbon donors or not")
        runOne(d_args)
    if args.filter:
        # filter output for CCD annotation
        logger.info("filter output for CCD annotation")
        fp_json = os.path.join(d_args["workdir"], "findgeo_report.json")
        if not os.path.exists(fp_json):
            logger.error("cannot find FindGeo report json at %s, no filtering applied", fp_json)
            return
        with open(fp_json, "r") as f:
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
        if l_sites_filtered != l_sites:
            logger.info("filtered out %d sites that do not meet CCD annotation criteria", len(l_sites) - len(l_sites_filtered))
            fp_json_filtered = os.path.join(d_args["workdir"], "findgeo_report.json")
            with open(fp_json_filtered, "w") as f:
                json.dump(l_sites_filtered, f, indent=4)
            logger.info("filtered report written to %s", fp_json_filtered)


if __name__ == "__main__":
    main()
