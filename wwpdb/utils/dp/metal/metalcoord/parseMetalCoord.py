# Author:  Chenghua Shao
# Date:    2025-11-10
# Updates:

"""
Wrapper to parse MetalCoord output json file
"""

import json
import os
import sys
import logging
from collections import OrderedDict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wwpdb.utils.dp.metal.metal_util.readRef import readRefCoordNum, readRefCoordMap, readRefRedOx
else:
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "metal_util"))
    from readRef import readRefCoordNum, readRefCoordMap, readRefRedOx  # noqa: E402

logger = logging.getLogger(__name__)


class ParseMetalCoord:
    """Wrapper to parse MetalCoord output files
    """
    def __init__(self):
        self.d_coord_num = readRefCoordNum()
        self.d_coord_map = readRefCoordMap("metalCoord")
        (self.d_redox, self.d_oxi) = readRefRedOx()
        self.data = None
        self.l_sites = []

    def read(self, fp_metalcoord):
        """load json data from the MetalCoord output json file
        :param fp_metalcoord: MetalCoord output json file
        :return: bool True for successful loading or non-empty data
        """
        try:
            with open(fp_metalcoord, "r") as f:
                self.data = json.load(f)
                logger.info("JSON loaded successfully from %s", fp_metalcoord)
                if self.data:
                    logger.info("json file %s is not empty", fp_metalcoord)
                    return True
                else:
                    logger.warning("json file %s is empty, STOP process", fp_metalcoord)
                    return False
        except FileNotFoundError:
            logger.error("Error: File not found at %s", fp_metalcoord)
            return False

        except PermissionError:
            logger.error("Error: Permission denied when trying to open %s.", fp_metalcoord)
            return False

        except json.JSONDecodeError as e:
            logger.error("Error: Failed to decode JSON for %s — %s", fp_metalcoord, e)
            return False

        except Exception as e:
            logger.error("Unexpected error in loading data from %s: %s", fp_metalcoord, e)
            return False

    def parse(self):
        """
        parse MetalCoord output folder to extract top hit coordination geometry for each site.
        1. iterate through each site folder in self.folder
        2. for each site folder, parse MetalCoord.out to get top hit coordination geometry
        3. parse MetalCoord.input to get metal atom information
        4. store the results in self.l_sites
        5. sort self.l_sites by metal, chain, residue, sequence, icode
        """
        self.filter()
        logger.info("finished filtering the MetalCoord output json")
        if self.l_sites:
            self.amend()
            logger.info("finished adding info to the output json")
            self.sort()
        else:
            logger.warning("no metal sites parsed")

    def filter(self):
        """
        Extract a compact, top-hit summary for each metal site from self.data.
        """
        for d_site in self.data:
            d_site_filtered = {}
            for key1 in ["metal", "metalElement", "chain", "residue", "sequence", "icode", "altloc"]:
                d_site_filtered[key1] = d_site[key1]

            # find the best coordination with lowest procruste value
            threshold = 1.0
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

            self.l_sites.append(d_site_filtered)

    def amend(self):
        """
        amend d_tophit with additional information from reference data
        1. add generic geometry name from the coordination class mapping reference
        2. check whether the coordination number is allowd in the coordination number reference
        3. add RedOx active marker

        :param d_tophit: dict with top hit information
        :return: amended dict with additional information
        """
        for d_tophit in self.l_sites:
            geom = d_tophit["class"]
            if geom in self.d_coord_map:
                pdb_geom = self.d_coord_map[geom]["pdb_geom"]
                d_tophit["class_generic"] = pdb_geom
            else:
                d_tophit["class_generic"] = ""

            metal = d_tophit["metalElement"]
            if metal in self.d_coord_num:
                allowed_coord_num = self.d_coord_num.get(metal)
                if str(d_tophit["coordination"]) in allowed_coord_num:
                    d_tophit["coordination_number_allowed"] = "YES"
                else:
                    d_tophit["coordination_number_allowed"] = "NO"
            else:
                d_tophit["coordination_number_allowed"] = ""

            if metal in self.d_redox:
                d_tophit["redox_active"] = self.d_redox.get(metal)
            else:
                d_tophit["redox_active"] = ""

            if metal in self.d_oxi:
                d_tophit["oxidation_state"] = self.d_oxi.get(metal)
            else:
                d_tophit["oxidation_state"] = ""

    def sort(self):
        """
        sort self.l_sites
        """
        key_order = ["metal", "metalElement", "chain", "residue", "sequence", "icode", "altloc",
                     "coordination", "class", "class_abbr", "class_generic", "descriptor", "procrustes", "count",
                     "coordination_number_allowed", "redox_active", "oxidation_state", "sphere"]
        l_sorted = []
        for d_row in self.l_sites:
            d_row_sorted = OrderedDict((key, d_row[key]) for key in key_order if key in d_row)
            l_sorted.append(d_row_sorted)
        self.l_sites = l_sorted

    def report(self, filepath_json):
        """
        write self.l_sites to a json file

        :param filepath_json: path to output json file
        """
        logger.info("to write report to %s", filepath_json)
        with open(filepath_json, "w") as file:
            json.dump(self.l_sites, file, indent=4)
