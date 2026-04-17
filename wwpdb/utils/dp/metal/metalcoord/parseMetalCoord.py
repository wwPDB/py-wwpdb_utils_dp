# Author:  Chenghua Shao
# Date:    2025-11-10
# Updates:

"""
Wrapper to parse MetalCoord output json file
"""
# pylint: disable=duplicate-code

import json
import os
import sys
import logging
from collections import OrderedDict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wwpdb.utils.dp.metal.metal_util.readRef import readRefCoordNum, readRefCoordMap, readRefRedOx, readRefMetalCarbon, readRefCoordException
else:
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "metal_util"))
    from readRef import readRefCoordNum, readRefCoordMap, readRefRedOx, readRefMetalCarbon, readRefCoordException  # noqa: E402

logger = logging.getLogger(__name__)


class MetalCoordParseError(Exception):
    """
    Raised when there is an error in parsing MetalCoord output.
    """


class ParseMetalCoord:  # pylint: disable=too-many-instance-attributes
    """
    Wrapper to parse MetalCoord output files.
    Provides methods to read, parse, filter, amend, sort, and report MetalCoord results.
    """
    def __init__(self):
        """
        Initialize ParseMetalCoord and load reference data for annotation.
        """
        self.d_coord_num = readRefCoordNum()
        self.d_coord_map = readRefCoordMap("metalCoord")
        (self.d_redox, self.d_oxi) = readRefRedOx()
        self.l_carbon_metal = readRefMetalCarbon()
        self.d_coord_exception = readRefCoordException()
        self.data = None
        self.l_sites = []

    def read(self, fp_metalcoord):
        """
        Load JSON data from the MetalCoord output JSON file.

        :param fp_metalcoord: Path to MetalCoord output JSON file.
        :type fp_metalcoord: str
        :return: True if data loaded successfully or is non-empty, False otherwise.
        :rtype: bool
        :raises MetalCoordParseError: If file is not found, permission denied, or JSON decode fails.
        """
        try:
            with open(fp_metalcoord, "r", encoding="utf-8") as f:
                self.data = json.load(f)
                logger.debug("JSON loaded successfully from %s", fp_metalcoord)
                if self.data:
                    logger.debug("json file %s is not empty", fp_metalcoord)
                else:
                    logger.warning("json file %s is empty, no output for the ligand, continue next process", fp_metalcoord)
        except FileNotFoundError as e:
            raise MetalCoordParseError(f"File not found: {fp_metalcoord}") from e
        except PermissionError as e:
            raise MetalCoordParseError(f"Permission denied when trying to open: {fp_metalcoord}") from e
        except json.JSONDecodeError as e:
            raise MetalCoordParseError(f"Failed to decode JSON for {fp_metalcoord} — {e}") from e
        except Exception as e:  # pylint: disable=broad-exception-caught
            raise MetalCoordParseError(f"An unexpected error occurred while reading {fp_metalcoord} — {e}") from e

    def parse(self):
        """
        Parse MetalCoord output data to extract top hit coordination geometry for each site.

        1. Iterate through each site in self.data
        2. For each site, find the best coordination geometry based on procrustes score
        3. Store the results in self.l_sites
        4. Sort self.l_sites by metal, chain, residue, sequence, icode
        """
        try:
            logger.info("to extract the best geometry for each metal site based on procrustes score")
            self.filter()
            if self.l_sites:
                logger.info("to add additional metal annotation")
                self.amend()
                logger.info("to sort output for each site")
                self.sort()
            else:
                logger.warning("no metal sites parsed, continue next process")
        except Exception as e:  # pylint: disable=broad-exception-caught
            raise MetalCoordParseError(f"An unexpected error occurred during parsing: {e}") from e

    def filter(self):
        """
        Extract a compact, top-hit summary for each metal site from self.data.

        This filter method is not the one to filter Regular geometry site only.
        """
        for d_site in self.data:
            d_site_filtered = {}
            for key1 in ["metal", "metalElement", "chain", "residue", "sequence", "icode", "altloc"]:
                d_site_filtered[key1] = d_site[key1]

            # find the best coordination with lowest procruste value
            threshold = 10
            d_tophit = {}
            for d_coord in d_site["ligands"]:
                score = d_coord["procrustes"]
                if score < threshold:
                    d_tophit = d_coord
                    threshold = score

            # once best coordination is found, move class assignment one level up
            for key2 in ["class", "descriptor", "procrustes", "coordination", "count"]:
                d_site_filtered[key2] = d_tophit[key2]
            d_site_filtered["class_abbr"] = d_tophit["class_abr"]

            # record only coordination ligands in the new "sphere" record
            d_site_filtered["sphere"] = d_tophit["order"]
            logger.debug("for site %s, best coordination geometry is %s with procrustes score %s", d_site_filtered["metal"], d_site_filtered["class"], d_site_filtered["procrustes"])
            self.l_sites.append(d_site_filtered)

    def amend(self):  # pylint: disable=too-many-branches
        """
        Amend each top-hit site dictionary in self.l_sites with additional information from reference data.

        1. Add generic geometry name from the coordination class mapping reference
        2. Check whether the coordination number is allowed in the coordination number reference
        3. Add RedOx active marker, oxidation state, carbon_metal bond marker, exception marker, and tag
        """
        for d_tophit in self.l_sites:
            geom = d_tophit["class"]
            if geom in self.d_coord_map:
                pdb_geom = self.d_coord_map[geom]["pdb_geom"]
                d_tophit["class_generic"] = pdb_geom
            else:
                d_tophit["class_generic"] = ""

            metal = d_tophit["metalElement"]
            # check against allowed coordination number
            if metal in self.d_coord_num:
                allowed_coord_num = self.d_coord_num.get(metal)
                if str(d_tophit["coordination"]) in allowed_coord_num:
                    d_tophit["coordination_number_allowed"] = "YES"
                else:
                    d_tophit["coordination_number_allowed"] = "NO"
            else:
                d_tophit["coordination_number_allowed"] = ""
            # add redox marker
            if metal in self.d_redox:
                d_tophit["redox_active"] = self.d_redox.get(metal)
            else:
                d_tophit["redox_active"] = ""
            # add oxidation state
            if metal in self.d_oxi:
                d_tophit["oxidation_state"] = self.d_oxi.get(metal)
            else:
                d_tophit["oxidation_state"] = ""
            # add carbon_metal bond marker
            if metal in self.l_carbon_metal:
                d_tophit["carbon_metal"] = "YES"
            else:
                d_tophit["carbon_metal"] = "NO"
            # add exception marker
            if metal in self.d_coord_exception:
                if d_tophit["class"] in self.d_coord_exception[metal]["Geometry-exclusion-MetalCoord"]:
                    d_tophit["class_in_exception"] = "YES"
                else:
                    d_tophit["class_in_exception"] = "NO"
            # mark positive procrustes < 0.2 as regular, and rest as irregular
            try:
                procrustes = float(d_tophit["procrustes"])
                if 0 <= procrustes <= 0.2:
                    d_tophit["tag"] = "Regular"
                else:
                    d_tophit["tag"] = "Irregular"  # >0.2 or -1 marked as irregular
            except ValueError:
                d_tophit["tag"] = "Irregular"  # non-value output marked as irregular

    def sort(self):
        """
        Sort self.l_sites by a predefined key order for output consistency.
        """
        key_order = ["metal", "metalElement", "chain", "residue", "sequence", "icode", "altloc", "coordination", "class",
                     "class_abbr", "class_generic", "tag", "procrustes", "count", "descriptor", "coordination_number_allowed",
                     "redox_active", "oxidation_state", "carbon_metal", "class_in_exception", "sphere"]
        l_sorted = []
        for d_row in self.l_sites:
            d_row_sorted = OrderedDict((key, d_row[key]) for key in key_order if key in d_row)
            l_sorted.append(d_row_sorted)
        self.l_sites = l_sorted

    def report(self, filepath_json):
        """
        Write self.l_sites to a JSON file.

        :param filepath_json: Path to output JSON file.
        :type filepath_json: str
        """
        with open(filepath_json, "w", encoding="utf-8") as file:
            json.dump(self.l_sites, file, indent=4)
