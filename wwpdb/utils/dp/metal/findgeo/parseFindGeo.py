# Author:  Chenghua Shao
# Date:    2025-11-10
# Updates:

"""
Wrapper to parse FindGeo output files
"""

import json
import os
import sys
import logging
from collections import OrderedDict
from mmcif.io.IoAdapterCore import IoAdapterCore
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wwpdb.utils.dp.metal.metal_util.readRef import readRefCoordNum, readRefCoordMap, readRefRedOx
else:
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "metal_util"))
    from readRef import readRefCoordNum, readRefCoordMap, readRefRedOx  # noqa: E402

logger = logging.getLogger(__name__)


class ParseFindGeo:
    """Wrapper to parse FindGeo output files
    Example usage:
    pFG = ParseFindGeo(/path/to/findgeo/output/folder, input_format="cif")
    pFG.parse()
    pFG.report("findgeo_report.json")
    """
    def __init__(self, folder, input_format="cif"):
        self.folder = folder
        self.input_format = input_format
        self.l_sites = []
        self.d_coord_num = readRefCoordNum()
        self.d_coord_map = readRefCoordMap("FindGeo")
        (self.d_redox, self.d_oxi) = readRefRedOx()

    def parse(self):
        """
        parse FindGeo output folder to extract top hit coordination geometry for each site.
        1. iterate through each site folder in self.folder
        2. for each site folder, parse findgeo.out to get top hit coordination geometry
        3. parse findgeo.input to get metal atom information
        4. store the results in self.l_sites
        5. sort self.l_sites by metal, chain, residue, sequence, icode
        """
        l_folder = os.listdir(self.folder)
        for name in l_folder:
            if name != "data" and "_" in name:
                d_tophit = self.parseOneSite(name)
                if not d_tophit:
                    continue
                d_tophit = self.amend(d_tophit)
                logger.info("add row %s", d_tophit)
                self.l_sites.append(d_tophit)

        if self.l_sites:
            self.sort()
        else:
            logger.warning("no metal sites parsed in %s", self.folder)

    def amend(self, d_tophit):
        """
        amend d_tophit with additional information from reference data
        1. add generic geometry name from the coordination class mapping reference
        2. check whether the coordination number is allowd in the coordination number reference

        :param d_tophit: dict with top hit information
        :return: amended dict with additional information
        """
        geom = d_tophit["class"]
        if geom in self.d_coord_map:
            pdb_geom = self.d_coord_map[geom]["pdb_geom"]
            d_tophit["class_generic"] = pdb_geom
        else:
            d_tophit["class_generic"] = ""

        metal = d_tophit["metalElement"]
        if metal in self.d_coord_num:
            allowed_coord_num = self.d_coord_num.get(metal)
            if d_tophit["coordination"] in allowed_coord_num:
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

        return d_tophit

    def parseOneSite(self, site_name):
        """
        parse one site folder to extract top hit coordination geometry and metal atom information

        :param site_name: site folder name, e.g. Cm_201__8907_DA/
        :return: dict with top hit information, None if parsing fails
        """
        subfolder = os.path.join(self.folder, site_name)
        if not os.path.isdir(subfolder):
            return None

        logger.info("to process subfolder %s", subfolder)
        l_subfolder = os.listdir(subfolder)
        if ("findgeo.out" not in l_subfolder):
            logger.warning("failed to find findgeo.out in %s", subfolder)
            return None

        d_tophit = self.parseFindGeoOutPut(os.path.join(subfolder, "findgeo.out"))
        if not d_tophit:
            return None

        t_atom = ()
        filepath_input = os.path.join(subfolder, "findgeo.input")
        if not os.path.isfile(filepath_input):
            logger.error("failed to find %s in %s", "findgeo.input", subfolder)
            return None
        if self.input_format == "pdb":
            t_atom = self.parseFindGeoPdbInput(filepath_input)
        elif self.input_format == "cif":
            t_atom = self.parseFindGeoCifInput(filepath_input)
        else:
            logger.error("unsupported input format: %s", self.input_format)
            t_atom = ()

        if not t_atom or len(t_atom) != 6:
            return None
        else:
            (ccd_id, atom_label, chain, res_num, ins, alt) = t_atom  # pylint: disable=unbalanced-tuple-unpacking

        element = site_name.split("_")[0]
        d_tophit["metal"] = atom_label
        d_tophit["metalElement"] = element.capitalize()
        d_tophit["chain"] = chain
        d_tophit["residue"] = ccd_id
        d_tophit["sequence"] = res_num
        d_tophit["icode"] = ins
        d_tophit["altloc"] = alt
        return d_tophit

    def parseFindGeoOutPut(self, filepath):
        """
        parse findgeo.out file to extract top hit coordination geometry
        1. coordination number
        2. best geometry class, class abbreviation, tag, rmsd

        :param filepath: path to findgeo.out file
        :return: dict with top hit information, empty dict if parsing fails
        """
        b_found_coord = False
        best_geo_name = None
        if not os.path.isfile(filepath):
            logger.error("failed to access %s", filepath)
            return {}
        logger.info("to process %s", filepath)
        d_tophit = {}
        with open(filepath) as file:
            l_hit = []
            for line in file:
                if line.startswith("Coordination number"):
                    l_line = line.strip().split(':')
                    d_tophit["coordination"] = l_line[-1].strip()
                    logger.info("found coordination number %s", d_tophit["coordination"])
                    b_found_coord = True
                if "-" in line and "|" in line:
                    l_line = line.strip().split("|")
                    if len(l_line) == 3:
                        d_hit = {}
                        d_hit["class_abbr"] = l_line[0].split("-")[0].strip().upper()
                        d_hit["class"] = l_line[0].split("-")[1].strip().lower()
                        d_hit["tag"] = l_line[1].strip()
                        d_hit["rmsd"] = l_line[2].strip()
                        logger.info("found coordination geometry %s, %s with tag %s RMSD %s",
                                    d_hit["class_abbr"], d_hit["class"], d_hit["tag"], d_hit["rmsd"])
                        l_hit.append(d_hit)
                if line.startswith("Best geometry"):
                    _tmp = line.strip().split(":")[1]
                    if "(Regular)" in _tmp:
                        best_geo_name = _tmp.split("(Regular)")[0].strip().lower()
                    elif "(Distorted)" in _tmp:
                        best_geo_name = _tmp.split("(Distorted)")[0].strip().lower()
                    elif "(Irregular)" in _tmp:
                        # best_geo_name = _tmp.split("(Irregular)")[0].strip().lower()
                        logger.info("best geometry is irregular in %s, use 'irregular' and ignore geometry parameters", filepath)
                        best_geo_name = "irregular"
                    else:
                        logger.warning("cannot find best geometry format in %s, use 'undetected' by default", filepath)
                        best_geo_name = "undetected"
                    logger.info("best geoemtry is %s", best_geo_name)

            if not b_found_coord:
                logger.warning("could not find coordination number in %s", filepath)
                return None

            if not l_hit:
                logger.warning("could not find any geometry hits in %s", filepath)
                return None

            if not best_geo_name:
                logger.warning("could not find best geometry in %s", filepath)
                return None

            if best_geo_name == "undetected":
                d_tophit["class"] = "undetected"
                d_tophit["class_abbr"] = ""
                d_tophit["tag"] = "None"
                d_tophit["rmsd"] = ""
                logger.warning("best geometry is undetected in %s, no geometry parameters output", filepath)
                return d_tophit

            if best_geo_name == "irregular":
                d_tophit["class"] = "irregular"
                d_tophit["class_abbr"] = ""
                d_tophit["tag"] = "Irregular"
                d_tophit["rmsd"] = ""
                logger.warning("best geometry is irregular in %s, no geometry parameters output", filepath)
                return d_tophit

            for d_hit in l_hit:
                if d_hit["class"] == best_geo_name:
                    for item in ["class_abbr", "class", "tag", "rmsd"]:
                        d_tophit[item] = d_hit[item]
                    logger.info("found best geometry %s in %s", best_geo_name, filepath)
                    return d_tophit

            logger.warning("could not find best geometry %s in hits in %s", best_geo_name, filepath)
            return None

    def parseFindGeoPdbInput(self, filepath):
        """
        parse findgeo.input file in pdb format to extract metal atom information

        :param filepath: path to findgeo.input file, if the input was in pdb format
        :return: tuple (ccd_id, atom_label, chain, res_num, ins, alt), empty tuple if parsing fails
        """
        logger.info("to process %s", filepath)
        with open(filepath) as file:
            line = file.readline()
            if line.startswith("ATOM") or line.startswith("HETATM"):
                if len(line.strip()) >= 54:
                    atom_label = line[12:16].strip()
                    alt = line[16:17]
                    ccd_id = line[17:20].strip()
                    chain = line[21:22]
                    res_num = line[22:26].strip()
                    ins = line[26:27]
                    logger.info("found ccd_id %s", ccd_id)
                    return (ccd_id, atom_label, chain, res_num, ins, alt)
        logger.error("failed to process %s", filepath)
        return ()

    def parseFindGeoCifInput(self, filepath):
        """
        parse findgeo.input file in cif format to extract metal atom information

        :param filepath: path to findgeo.input file, if the input was in cif format
        :return: tuple (ccd_id, atom_label, chain, res_num, ins, alt), empty tuple if parsing fails
        """
        logger.info("to run mmCIF parser on findgeo.input %s", filepath)
        d_metal_row = self.parseMmcif(filepath)
        if d_metal_row:
            atom_label = d_metal_row.get("label_atom_id", "").strip()
            alt = d_metal_row.get("label_alt_id", "").strip()
            ccd_id = d_metal_row.get("label_comp_id", "").strip()
            ins = d_metal_row.get("pdbx_PDB_ins_code", "").strip()
            res_num = d_metal_row.get("auth_seq_id", "").strip()
            chain = d_metal_row.get("auth_asym_id", "").strip()
            logger.info("found ccd_id %s", ccd_id)
            return (ccd_id, atom_label, chain, res_num, ins, alt)
        else:
            logger.info("to parse findgeo.input by column guess on: %s", filepath)
            with open(filepath) as file:
                for line in file:
                    if line.startswith("ATOM") or line.startswith("HETATM"):
                        l_line = line.strip().split()
                        atom_label = l_line[3]
                        alt = l_line[4]
                        ccd_id = l_line[5]
                        ins = l_line[9]
                        res_num = l_line[15]
                        chain = l_line[17]
                        logger.info("found ccd_id %s", ccd_id)
                        return (ccd_id, atom_label, chain, res_num, ins, alt)
        logger.error("failed to process %s", filepath)
        return ()

    def parseMmcif(self, fp):
        """
        parse mmcif file to extract atom site information

        :param fp: file path to mmcif file
        :return: dict with 1st row (metal atom) atom site information
        """
        io = IoAdapterCore()
        l_dc = io.readFile(fp)
        if not l_dc:
            logger.error("failed to read mmcif file: %s", fp)
            return {}
        dc0 = l_dc[0]

        if 'atom_site' not in dc0.getObjNameList():
            logger.error("no atom_site category found in mmcif file: %s", fp)
            return {}
        c_atom_site = dc0.getObj('atom_site')
        d_metal_row = c_atom_site.getRowAttributeDict(0)

        if "auth_asym_id" not in d_metal_row:
            logger.error("failed to find auth_asym_id in atom_site category in mmcif file: %s", fp)
            return {}

        return d_metal_row

    def sort(self):
        """
        sort self.l_sites by metal, chain, residue, sequence, icode, altloc,
        coordination, class, class_abbr, tag, rmsd
        """
        key_order = ["metal", "metalElement", "chain", "residue", "sequence", "icode", "altloc",
                     "coordination", "class", "class_abbr", "class_generic", "tag", "rmsd",
                     "coordination_number_allowed", "redox_active", "oxidation_state"]
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
