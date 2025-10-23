import json
import os
import sys
import logging
from collections import OrderedDict

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

    def parse(self):
        """
        parse FindGeo output folder to extract top hit coordination geometry for each site.
        1. iterate through each site folder in self.folder
        2. for each site folder, parse findgeo.out to get top hit coordination geometry
        3. parse findgeo.input to get metal atom information
        4. store the results in self.l_sites
        5. sort self.l_sites by metal, chain, residue, sequence, icode
        """
        self.l_sites = []
        l_folder = os.listdir(self.folder)
        for name in l_folder:
            if name != "data" and "_" in name:
                d_tophit = self.parseOneSite(name)
                if not d_tophit:
                    continue

                logger.info("add row %s", d_tophit)
                self.l_sites.append(d_tophit)

        if self.l_sites:
            self.sort()

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

        if not t_atom:
            return None

        (ccd_id, atom_label, chain, res_num, ins, alt) = t_atom

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
        b_found_geo = False
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
                        best_geo_name = "irregular"
                    else:
                        best_geo_name = None
                    logger.info("best geoemtry is %s", best_geo_name)
            for d_hit in l_hit:
                if d_hit["class"] == best_geo_name:
                    for item in ["class_abbr", "class", "tag", "rmsd"]:
                        d_tophit[item] = d_hit[item]
                    b_found_geo = True      
        if b_found_coord and b_found_geo:
            logger.info("found both coordination number and geometry in %s", filepath)
            return d_tophit
        else:
            logger.warning("could not find best geo parameters in %s", filepath)
            return {}

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
        logger.info("to process %s", filepath)
        with open(filepath) as file:
            line = file.readline()
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

    def sort(self):
        """
        sort self.l_sites by metal, chain, residue, sequence, icode, altloc, 
        coordination, class, class_abbr, tag, rmsd
        """        
        key_order = ["metal", "metalElement", "chain", "residue",  "sequence", "icode", "altloc",
                     "coordination", "class", "class_abbr",  "tag", "rmsd"]
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
        if not self.l_sites:
            logger.warning("no data to write to %s", filepath_json)
            return

        logger.info("to write report to %s", filepath_json)
        with open(filepath_json, "w") as file:
            json.dump(self.l_sites, file, indent=4)

