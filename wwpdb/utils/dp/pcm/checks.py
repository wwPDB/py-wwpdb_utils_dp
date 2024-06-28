"""Utils used to run checks, including dict/misc checks for individual files"""

import difflib
import os
import subprocess

from wwpdb.io.file.mmCIFUtil import mmCIFUtil
from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId
from wwpdb.utils.config.ConfigInfoApp import ConfigInfoAppCommon

from wwpdb.utils.dp.pcm.mmcif import mmcifHandling


def check_entries_uncompressed(entry_list):
    """Check if all the entries are in archive folder, if not raise error

    Args:
        entry_list (list): list of internal entry_ids

    Returns:
        FileNotFoundError: If an entry is not found in the archive folder
    """

    cI = ConfigInfo(getSiteId())
    entry_archive_path = cI.get("SITE_ARCHIVE_STORAGE_PATH") + "/archive"

    uncompressed_entries = [entry_id for entry_id in os.listdir(entry_archive_path)]
    compressed_entries = list(set(entry_list) - set(uncompressed_entries))

    if len(compressed_entries) != 0:
        raise FileNotFoundError(
            f"The following entries not found in the archive path and so "
            f"are likely to be compressed: {', '.join(compressed_entries)}"
        )

    return None


class dict_cif_checker:
    """Class to initialise and run CifCheck tool on local CIF files"""

    def __init__(self, file_path, first_block_only=False):
        self.file = file_path
        self.cICommon = ConfigInfoAppCommon()
        self.checker = self.cICommon.get_site_packages_path() + "/dict/bin/CifCheck"
        self.dict_path = self.cICommon.get_mmcif_dict_path() + "/mmcif_pdbx_v50.sdb"
        self.first_block_only = first_block_only


    def run(self):

        cmd = [
            self.checker,
            "-f",
            self.file,
            "-dictSdb",
            self.dict_path,
        ]

        if self.first_block_only:
            cmd.append("-checkFirstBlock")

        subprocess.call(cmd)


class misc_checker:
    """Class to initialise and run MiscChecking tool on local mmCIF files"""

    def __init__(self, file_path):
        self.file_path = file_path
        self.file_name = self._get_file_name()
        self.depID = self.file_name[:-14]
        self.siteId = getSiteId()
        self.cI = ConfigInfo(self.siteId)
        self.cICommon = ConfigInfoAppCommon()
        self.__rcsbAppsPath = self.cI.get("SITE_ANNOT_TOOLS_PATH")
        self.__ccCvsPath = self.cICommon.get_site_cc_cvs_path()
        self.checker = (
            self.cICommon.get_site_packages_path() + "/annotation/bin/MiscChecking"
        )
        self.latest_model_path = mmcifHandling(depID=self.depID).get_latest_model()

    def _get_file_name(self):
        """Find file name in file path"""

        index = self.file_path.find("D_")
        fn = self.file_path[index:]

        return fn

    def _run_cmd(self, inp, out, log):
        """Run MiscChecker cmd line tool

        Args:
            inp (str): Input file path
            out (str): Output file path
            log (str): log file path

        """
        temp_env = os.environ.copy()
        temp_env["RCSBROOT"] = self.__rcsbAppsPath
        temp_env["COMP_PATH"] = self.__ccCvsPath

        cmd = [
            self.checker,
            "-input",
            inp,
            "-output",
            out,
            "-log",
            log,
        ]
        subprocess.call(cmd, env=temp_env)

        # Remove log if no errors/warnings
        with open(log, "r") as file:
            file_str = file.read().strip()
        if file_str == "Finished!":
            os.remove(log)

    def run(self):
        """Run misc checker on current and new mmCIF and writes out differences"""

        curr_mod_output_file = self.depID + ".curr_misc_check.log"
        output_file = self.depID + ".misc_check.log"
        output_file_diff = self.depID + ".misc_check_DIFF.log"
        curr_mod_log_file = self.depID + ".curr_misc_check_run.log"
        log_file = self.depID + ".misc_check_run.log"

        # Run on existing and updated mmCIF
        self._run_cmd(self.latest_model_path, curr_mod_output_file, curr_mod_log_file)
        self._run_cmd(self.file_path, output_file, log_file)

        # Compare new misc run to existing misc run and keep only new lines
        with open(output_file, "r") as new_misc_file:
            new_misc_file_contents = new_misc_file.readlines()

        with open(curr_mod_output_file, "r") as current_misc_file:
            current_misc_file_contents = current_misc_file.readlines()

        differ = difflib.Differ()
        diff = list(differ.compare(current_misc_file_contents, new_misc_file_contents))
        lines_only_in_new_run = [line[2:] for line in diff if line.startswith("+ ")]

        with open(output_file_diff, "w") as new_misc_diff_file:
            new_misc_diff_file.writelines(lines_only_in_new_run)

        if os.path.getsize(output_file_diff) == 0:
            os.remove(output_file)
            os.remove(output_file_diff)


def check_ccd_pcm_category(ccd_path):  # noqa
    """Check the CCD PCM Category is consistently annotated

    Checks performed:
        - chem_comp.pdbx_pcm and pdbx_chem_comp_pcm are consistent
        - PCMs handled as residues do not have linking atom values
        - Linked modifications must have linking atom values
        - Linked modifications must have modified residue ID values
        - PCM type should not be None unless the PCM category allows this
        - PCM category must be populated
        - Type and category items must not mismatch
          (e.g. Phosphorylation and Lipid/lipid-like mismatch)
        - modified_residue_id item must not be empty when the CCD has a parent
        - CCDs that have PCMs handled as linked cannot also describe PCMs handled as
          residue (excl. 'Covalent chemical modifications' and 'Crosslinker' categories)

    Args:
        ccd_path (str): Path to CCD file to check

    Returns:
        str: Warning message for CCD. If no warning returns ""

    """

    pcm_type_category_map = {
        "(3-Aminopropyl)(5'-adenosyl)phosphono amidation": "Named protein modification",
        "2-Aminoadipylation": "Named protein modification",
        "2-Aminoethylphosphorylation": "Named protein modification",
        "2-Cholinephosphorylation": "Named protein modification",
        "2-Hydroxyisobutyrylation": "Named protein modification",
        "2-Oxo-5,5-dimethylhexanoylation": "Named protein modification",
        "2-Oxobutanoic acid": "Named protein modification",
        "2,3-Dicarboxypropylation": "Named protein modification",
        "3-Oxoalanine": "Named protein modification",
        "3-Phenyllactic acid": "Named protein modification",
        "(3R)-3-Hydroxybutyrylation": "Named protein modification",
        "4-Phosphopantetheine": "Named protein modification",
        "ADP-riboxanation": "Named protein modification",
        "Acetamidation": "Named protein modification",
        "Acetamidomethylation": "Named protein modification",
        "Acetylation": "Named protein modification",
        "Allysine": "Named protein modification",
        "Amination": "Named protein modification",
        "Arsenylation": "Named protein modification",
        "Bacillithiolation": "Named protein modification",
        "Benzoylation": "Named protein modification",
        "Benzylation": "Named protein modification",
        "Beta-amino acid": "Named protein modification",
        "Beta-hydroxybutyrylation": "Named protein modification",
        "Beta-lysylation": "Named protein modification",
        "Beta-mercaptoethanol": "Named protein modification",
        "Bromination": "Named protein modification",
        "Butyrylation": "Named protein modification",
        "Carbamoylation": "Named protein modification",
        "Carboxyethylation": "Named protein modification",
        "Carboxylation": "Named protein modification",
        "Carboxymethylation": "Named protein modification",
        "Chlorination": "Named protein modification",
        "Citrullination": "Named protein modification",
        "Crotonylation": "Named protein modification",
        "Cyanation": "Named protein modification",
        "Deamidation": "Named protein modification",
        "Decarboxylation": "Named protein modification",
        "Dehydroamino acid": "Named protein modification",
        "Dehydrocoelenterazination": "Named protein modification",
        "Dehydrogenation": "Named protein modification",
        "Dehydroxylation": "Named protein modification",
        "Deoxidation": "Named protein modification",
        "Deoxyhypusine": "Named protein modification",
        "Dihydroxyacetonation": "Named protein modification",
        "Diphosphorylation": "Named protein modification",
        "Diphthamide": "Named protein modification",
        "Dipyrromethane methylation": "Named protein modification",
        "D-lactate": "Named protein modification",
        "Dopaminylation": "Named protein modification",
        "Ethylation": "Named protein modification",
        "Ethylsulfanylation": "Named protein modification",
        "Fluorination": "Named protein modification",
        "Formylation": "Named protein modification",
        "Glutarylation": "Named protein modification",
        "Glutathionylation": "Named protein modification",
        "Glycerophosphorylation": "Named protein modification",
        "Glycerylphosphorylethanolamination": "Named protein modification",
        "Histaminylation": "Named protein modification",
        "Hydrogenation": "Named protein modification",
        "Hydroperoxylation": "Named protein modification",
        "Hydroxyamination": "Named protein modification",
        "Hydroxyethylation": "Named protein modification",
        "Hydroxylation": "Named protein modification",
        "Hydroxymethylation": "Named protein modification",
        "Hydroxysulfanylation": "Named protein modification",
        "Hypusine": "Named protein modification",
        "Iodination": "Named protein modification",
        "Lactoylation": "Named protein modification",
        "L-lactate": "Named protein modification",
        "Malonylation": "Named protein modification",
        "Methoxylation": "Named protein modification",
        "Methylamination": "Named protein modification",
        "Methylation": "Named protein modification",
        "Methylsulfanylation": "Named protein modification",
        "Methylsulfation": "Named protein modification",
        "N-pyruvic acid 2-iminylation": "Named protein modification",
        "N-methylcarbamoylation": "Named protein modification",
        "Nitration": "Named protein modification",
        "Nitrosylation": "Named protein modification",
        "Noradrenylation": "Named protein modification",
        "Norleucine": "Named protein modification",
        "Norvaline": "Named protein modification",
        "Ornithine": "Named protein modification",
        "Oxidation": "Named protein modification",
        "Phosphoenolpyruvate": "Named protein modification",
        "Phosphorylation": "Named protein modification",
        "Propionylation": "Named protein modification",
        "Pyridoxal phosphate": "Named protein modification",
        "Pyrrolidone carboxylic acid": "Named protein modification",
        "Pyruvic acid": "Named protein modification",
        "Selanylation": "Named protein modification",
        "Selenomethionine": "Named protein modification",
        "Serotonylation": "Named protein modification",
        "Stereoisomerisation": "Named protein modification",
        "Succinamide ring": "Named protein modification",
        "Succination": "Named protein modification",
        "Succinylation": "Named protein modification",
        "Sulfanylmethylation": "Named protein modification",
        "Sulfation": "Named protein modification",
        "Sulfhydration": "Named protein modification",
        "Tert-butylation": "Named protein modification",
        "Tert-butyloxycarbonylation": "Named protein modification",
        "Thyroxine": "Named protein modification",
        "Triiodothyronine": "Named protein modification",
        "12-Hydroxyfarnesylation": "Lipid/lipid-like",
        "12-Oxomyristoylation": "Lipid/lipid-like",
        "12R-Hydroxymyristoylation": "Lipid/lipid-like",
        "14-Hydroxy-10,13-dioxo-7-heptadecenoic acid": "Lipid/lipid-like",
        "Arachidoylation": "Lipid/lipid-like",
        "Archaeol": "Lipid/lipid-like",
        "Cholesterylation": "Lipid/lipid-like",
        "Decanoylation": "Lipid/lipid-like",
        "Diacylglycerol": "Lipid/lipid-like",
        "Farnesylation": "Lipid/lipid-like",
        "Geranylgeranylation": "Lipid/lipid-like",
        "Heptanoylation": "Lipid/lipid-like",
        "Hexanoylation": "Lipid/lipid-like",
        "Laurylation": "Lipid/lipid-like",
        "Lipoylation": "Lipid/lipid-like",
        "Myristoylation": "Lipid/lipid-like",
        "Octanoylation": "Lipid/lipid-like",
        "Oleoylation": "Lipid/lipid-like",
        "Palmitoleoylation": "Lipid/lipid-like",
        "Palmitoylation": "Lipid/lipid-like",
        "Pentadecanoylation": "Lipid/lipid-like",
        "Pentanoylation": "Lipid/lipid-like",
        "Phosphatidylethanolamine amidation": "Lipid/lipid-like",
        "Retinoylation": "Lipid/lipid-like",
        "Stearoylation": "Lipid/lipid-like",
        "AMPylation": "Nucleotide monophosphate",
        "cGMPylation": "Nucleotide monophosphate",
        "GMPylation": "Nucleotide monophosphate",
        "UMPylation": "Nucleotide monophosphate",
        "Biotinylation": "Biotin",
        "ADP-ribosylation": "ADP-ribose",
        "Alanylation": "Amino acid",
        "Arginylation": "Amino acid",
        "Asparaginylation": "Amino acid",
        "Aspartylation": "Amino acid",
        "Cysteinylation": "Amino acid",
        "Glutaminylation": "Amino acid",
        "Glutamylation": "Amino acid",
        "Glycylation": "Amino acid",
        "Histidinylation": "Amino acid",
        "Isoleucylation": "Amino acid",
        "Leucylation": "Amino acid",
        "Lysylation": "Amino acid",
        "Methionylation": "Amino acid",
        "Phenylalanylation": "Amino acid",
        "Prolylation": "Amino acid",
        "Serylation": "Amino acid",
        "Threoninylation": "Amino acid",
        "Tryptophanylation": "Amino acid",
        "Tyrosination": "Amino acid",
        "Valylation": "Amino acid",
        "D-alanylation": "Amino acid",
        "D-arginylation": "Amino acid",
        "D-asparaginylation": "Amino acid",
        "D-aspartylation": "Amino acid",
        "D-cysteinylation": "Amino acid",
        "D-glutaminylation": "Amino acid",
        "D-glutamylation": "Amino acid",
        "D-histidinylation": "Amino acid",
        "D-isoleucylation": "Amino acid",
        "D-leucylation": "Amino acid",
        "D-lysylation": "Amino acid",
        "D-methionylation": "Amino acid",
        "D-phenylalanylation": "Amino acid",
        "D-prolylation": "Amino acid",
        "D-serylation": "Amino acid",
        "D-threoninylation": "Amino acid",
        "D-tryptophanylation": "Amino acid",
        "D-tyrosination": "Amino acid",
        "D-valylation": "Amino acid",
    }

    categories_that_allow_none_type = [
        "Chromophore/chromophore-like",
        "Nucleotide monophosphate"
        "Heme/heme-like",
        "Carbohydrate",
        "Crosslinker",
        "Flavin",
        "Terminal acetylation",
        "Terminal amidation",
        "Covalent chemical modification",
        "Non-standard residue",
        "Lipid/lipid-like",
    ]

    category_handling = {
        "ADP-Ribose": "linked",
        "Biotin": "linked",
        "Carbohydrate": "linked",
        "Chromophore/chromophore-like": "residue",
        "Covalent chemical modification": "linked",
        "Crosslinker": "linked",
        "Flavin": "linked",
        "Heme/heme-like": "linked",
        "Lipid/lipid-like": "linked",
        "Named protein modification": "residue",
        "Non-standard residue": "residue",
        "Nucleotide monophosphate": "linked",
        "Amino acid": "linked",
        "Terminal acetylation": "residue",
        "Terminal amidation": "residue",
    }

    cifObj = mmCIFUtil(filePath=ccd_path)

    pdbx_pcm = cifObj.GetSingleValue("chem_comp", "pdbx_pcm")
    chem_comp_pcm = cifObj.GetValue("pdbx_chem_comp_pcm")

    chem_comp_parent = cifObj.GetSingleValue("chem_comp", "mon_nstd_parent_comp_id")

    # lists of rows in chem_comp_pcm that fail the checks
    pdbx_pcm_unexpected_y = False
    pdbx_pcm_unexpected_n = False
    pdbx_pcm_unexpected_none = False
    residue_pcm_has_linking_atoms = []
    linked_pcm_missing_linking_atoms = []
    linked_pcm_missing_modified_residue_id = []
    pcm_missing_category_value = []
    pcm_missing_type_value = []
    pcm_type_category_mismatch = []
    pcm_modified_residue_id_missing = []
    pcm_category_mixes_linked_and_residue_pcms = []

    # Check if chem_comp.pdbx_pcm consistent with pdbx_chem_comp_pcm
    if (len(chem_comp_pcm) == 0) and (pdbx_pcm == "Y"):
        pdbx_pcm_unexpected_y = True
    elif (len(chem_comp_pcm) != 0) and (pdbx_pcm == "N"):
        pdbx_pcm_unexpected_n = True
    elif (len(chem_comp_pcm) != 0) and not pdbx_pcm:
        pdbx_pcm_unexpected_none = True

    if len(chem_comp_pcm) != 0:
        # Track the types of PCM handling in chem_comp_pcm
        handling_in_chem_comp_pcm = []

        for row in chem_comp_pcm:
            if 'category' not in row:
                pcm_missing_category_value.append(int(row["pcm_id"]))
                continue

            if (
                row["category"] in category_handling
                and category_handling[row["category"]] == "residue"
                and (
                    "comp_id_linking_atom" in row
                    or "modified_residue_id_linking_atom" in row
                )
            ):
                residue_pcm_has_linking_atoms.append(int(row["pcm_id"]))

            if (
                row["category"] in category_handling
                and category_handling[row["category"]] == "linked"
                and (
                    "comp_id_linking_atom" not in row
                    or "modified_residue_id_linking_atom" not in row
                )
            ):
                linked_pcm_missing_linking_atoms.append(int(row["pcm_id"]))

            if (
                row["category"] in category_handling
                and category_handling[row["category"]] == "linked"
                and "modified_residue_id" not in row
            ):
                linked_pcm_missing_modified_residue_id.append(int(row["pcm_id"]))

            if (
                row["type"] == "None"
                and row["category"] not in categories_that_allow_none_type
            ):
                pcm_missing_type_value.append(int(row["pcm_id"]))

            if row["type"] != "None" and (
                row["type"] not in pcm_type_category_map
                or pcm_type_category_map[row["type"]] != row["category"]
            ):
                pcm_type_category_mismatch.append(int(row["pcm_id"]))

            if "modified_residue_id" not in row and chem_comp_parent:
                pcm_modified_residue_id_missing.append(int(row["pcm_id"]))

            if row["category"] in category_handling and row["category"] not in (
                "Covalent chemical modification",
                "Crosslinker",
            ):
                handling_in_chem_comp_pcm.append(category_handling[row["category"]])

        handling_in_chem_comp_pcm = set(handling_in_chem_comp_pcm)

        if len(handling_in_chem_comp_pcm) > 1:
            pcm_category_mixes_linked_and_residue_pcms = True

    # Set error message
    error_message = ""

    if pdbx_pcm_unexpected_y:
        error_message += (
            "Warning - There is a mismatch between chem_comp.pdbx_pcm and "
            "pdbx_chem_comp_pcm. chem_comp.pdbx_pcm is set to 'Y' but "
            "pdbx_chem_comp_pcm is empty."
            "\n\n"
        )

    if pdbx_pcm_unexpected_n:
        error_message += (
            "Warning - There is a mismatch between chem_comp.pdbx_pcm and "
            "pdbx_chem_comp_pcm. chem_comp.pdbx_pcm is set to 'N' but "
            "pdbx_chem_comp_pcm is not empty."
            "\n\n"
        )

    if pdbx_pcm_unexpected_none:
        error_message += (
            "Warning - There is a mismatch between chem_comp.pdbx_pcm and "
            "pdbx_chem_comp_pcm. chem_comp.pdbx_pcm is set to '?' but "
            "pdbx_chem_comp_pcm is not empty."
            "\n\n"
        )

    if residue_pcm_has_linking_atoms:
        error_message += (
            f"Warning - Row(s) {residue_pcm_has_linking_atoms} in pdbx_chem_comp_pcm "
            f"describes a PCM category that is always part of the polypeptide sequence "
            f"but this row has the 'linking_atom' items populated. This PCM should "
            f"either be re-categorised or the 'linking_atom' items cleared."
            f"\n\n"
        )

    if linked_pcm_missing_linking_atoms:
        error_message += (
            f"Warning - Row(s) {linked_pcm_missing_linking_atoms} in "
            f"pdbx_chem_comp_pcm describes a PCM category that is always linked to the "
            f"polypeptide sequence but this row has the 'linking_atom' items empty. "
            f"This PCM should either be re-categorised or the 'linking_atom' items "
            f"populated."
            "\n\n"
        )

    if linked_pcm_missing_modified_residue_id:
        error_message += (
            f"Warning - Row(s) {linked_pcm_missing_modified_residue_id} in "
            f"pdbx_chem_comp_pcm describes a PCM category that is always linked to the "
            f"polypeptide sequence but this row has the 'modified_residue_id' item "
            f"empty. This PCM should either be re-categorised or the "
            f"'modified_residue_id' item populated with the polypeptide residue it is "
            f"linked to.\n\n"
        )

    if pcm_missing_category_value:
        error_message += (
            f"Warning - Row(s) {pcm_missing_category_value} in pdbx_chem_comp_pcm has "
            f"the PCM category value missing"
            f"\n\n"
        )

    if pcm_missing_type_value:
        error_message += (
            f"Warning - Row(s) {pcm_missing_type_value} in pdbx_chem_comp_pcm has the "
            f"PCM type set to 'None' but the PCM category in this row must have PCM "
            f"type set."
            f"\n\n"
        )

    if pcm_type_category_mismatch:
        error_message += (
            f"Warning - Row(s) {pcm_type_category_mismatch} in pdbx_chem_comp_pcm has "
            f"a PCM type that does not match with the PCM category."
            "\n\n"
        )

    if pcm_modified_residue_id_missing:
        error_message += (
            f"Warning - Row(s) {pcm_modified_residue_id_missing} in pdbx_chem_comp_pcm "
            f"has the item modified_residue_id empty but "
            f"chem_comp.mon_nstd_parent_comp_id is populated. The item "
            f"modified_residue_id should be populated or "
            f"chem_comp.mon_nstd_parent_comp_id cleared"
            "\n\n"
        )

    if pcm_category_mixes_linked_and_residue_pcms:
        error_message += (
            "Warning - pdbx_chem_comp_pcm contains a mix of rows that describe a "
            "linked protein modification and rows that describe a peptide residue."
            "\n\n"
        )

    return error_message
