"""Functions to generate pdbx_modification_feature and has_protein_modification

To do
#####

At the moment the pcm.py code points to the local folder storing the updated CCDs and
not the CVS ligand-dict-v3 

"""

import sys

from wwpdb.utils.dp.pcm.ligand import (
    std_amino_acids,
    std_amino_acids_ACE_NH2,
    get_ccd_path,
)
from wwpdb.utils.dp.pcm.mmcif import mmcifHandling


def gen_pdbx_modification_feature(cICommon, mmcif_obj):
    """Generate and overwrite pdbx_modification_feature

    mmcif_obj is modified in place to update pdbx_modification_feature.
    Requires access to CCD files

    Args:
        cICommon (obj): Config info obj
        mmcif_obj (obj): mmcifHandling obj containing parsed mmCIF data

    Returns:
        list: 2D list containing CCDs which missing PCM definitions.
            If no CCDs are missing PCM definitions return None instead

    """

    database_2 = mmcif_obj.get_category_list_of_dictionaries("database_2", False)
    entry_id = ""
    for row in database_2:
        if row["database_id"] == "PDB":
            entry_id = row["database_code"]

    pcm_link_list = gen_pcm_link_list(mmcif_obj)
    ccd_list = gen_pcm_ccd_list(pcm_link_list)
    ccd_list += std_amino_acids

    ccd_pcm_defs_list = []
    terminal_atoms_dict = {}

    # Collect PCM data from CCD files
    for ccd_id in ccd_list:
        # When PCM data is added to CCDs in archive, use this instead
        ccd_path = get_ccd_path(ccd_id, cICommon)
        # ccd_path = f"../update_ccds_add_pcm_data/data/updated_ccd_files/{ccd_id}.cif"
        ccd_obj = mmcifHandling("")
        ccd_obj.set_input_mmcif(ccd_path)
        ccd_pdbx_pcm = ccd_obj.get_cat_item_value("chem_comp", "pdbx_pcm")
        ccd_pcm_data = ccd_obj.get_category_list_of_dictionaries(
            "pdbx_chem_comp_pcm", False
        )
        ccd_atoms = ccd_obj.get_category_list_of_dictionaries("chem_comp_atom", False)

        # Store all PCM definitions from CCD
        for row in ccd_pcm_data:
            row["pdbx_pcm"] = ccd_pdbx_pcm
            ccd_pcm_defs_list.append(row)

        # Store all terminal atoms from CCD
        terminal_atoms_dict[ccd_id] = {"N-term": [], "C-term": []}
        for row in ccd_atoms:
            # if "pdbx_n_terminal_atom_flag" not in row:
            #     continue

            if row["pdbx_n_terminal_atom_flag"] == "Y":
                terminal_atoms_dict[ccd_id]["N-term"].append(row["atom_id"])

            if row["pdbx_c_terminal_atom_flag"] == "Y":
                terminal_atoms_dict[ccd_id]["C-term"].append(row["atom_id"])

    pdbx_mod_feat = []
    ccds_missing_pcm_defs = []

    for link in pcm_link_list:
        # Track record data
        pcm_link_type = None
        are_neighb = check_sc_between_neighbors(link)
        is_bb_link = check_backbone_link(link, terminal_atoms_dict, are_neighb)
        pdbx_mod_feat_rows = []

        # Annotate Disulfide
        if link["conn_type_id"] == "disulf":
            pcm_link_type = "disulf"
            disulf_rows = gen_non_std_link_pcm_record(link, "Disulfide bridge")
            pdbx_mod_feat_rows += disulf_rows

        # Annotate Isopeptide
        elif check_isopeptide(link, terminal_atoms_dict):
            pcm_link_type = "isopeptide"
            disulf_rows = gen_non_std_link_pcm_record(link, "Isopeptide bond")
            pdbx_mod_feat_rows += disulf_rows

        # Annotate Non-standard linkage
        elif check_non_std_linkage(link, is_bb_link):
            pcm_link_type = "non_std_link"
            non_std_linkage_rows = gen_non_std_link_pcm_record(
                link, "Non-standard linkage"
            )
            pdbx_mod_feat_rows += non_std_linkage_rows

        # Annotate ACE cap modification
        if check_ace_nh2_pcm(link, "ACE", is_bb_link):
            pcm_link_type = "ace_cap_pcm"
            ace_pcm_rows = gen_ace_nh2_pcm_record(link, ccd_pcm_defs_list, "ACE")
            pdbx_mod_feat_rows += ace_pcm_rows

        # Annotate NH2 cap modification
        if check_ace_nh2_pcm(link, "NH2", is_bb_link):
            pcm_link_type = "nh2_cap_pcm"
            nh2_pcm_rows = gen_ace_nh2_pcm_record(link, ccd_pcm_defs_list, "NH2")
            pdbx_mod_feat_rows += nh2_pcm_rows

        # Annotate linked modification
        # Where 1 CCD in peptide other not in peptide
        if (link["ptnr1_in_pep"] == "Y") != (link["ptnr2_in_pep"] == "Y"):
            pcm_link_type = "linked"
            linked_pcm_rows = gen_linked_pcm_records(link, ccd_pcm_defs_list)
            pdbx_mod_feat_rows += linked_pcm_rows

        # Annotate single CCD modification
        # Where CCDs are both in peptide and are neighbours
        if link["ptnr1_in_pep"] == "Y" and link["ptnr2_in_pep"] == "Y" and are_neighb:
            pcm_link_type = "single_ccd_pcm"
            single_ccd_pcm_rows = gen_single_ccd_pcm_records(link, ccd_pcm_defs_list)
            pdbx_mod_feat_rows += single_ccd_pcm_rows

        # Find all CCDs that describe a PCM but are not in pdbx_mod_feat_rows
        ccd_missing_pcm_defs_in_row = find_ccds_missing_pcm_defs(
            link, pcm_link_type, pdbx_mod_feat_rows, entry_id
        )

        for missing_def in ccd_missing_pcm_defs_in_row:
            ccds_missing_pcm_defs.append(missing_def)

        # Add dummy record if there are missing PCM definitions
        if len(ccd_missing_pcm_defs_in_row) != 0:
            dummy_pcm_rows = gen_dummy_pcm_records(link)
            pdbx_mod_feat_rows += dummy_pcm_rows

        for row in pdbx_mod_feat_rows:
            pdbx_mod_feat.append(row)

    # Remove duplicates from pdbx_mod_feat
    pdbx_mod_feat = [
        i for n, i in enumerate(pdbx_mod_feat) if i not in pdbx_mod_feat[:n]
    ]

    # Reformat pdbx_mod_feat
    pdbx_mod_feat = reformat_pdbx_mod_feat(pdbx_mod_feat)

    # Remove existing pdbx_modification_feature category
    mmcif_obj.remove_category("pdbx_modification_feature")

    # Add new pdbx_modification_feature category
    if len(pdbx_mod_feat) != 0:
        mmcif_obj.add_new_category("pdbx_modification_feature", pdbx_mod_feat)

    # Remove duplicates from ccds_missing_pcm_defs
    ccds_missing_pcm_defs = [
        i
        for n, i in enumerate(ccds_missing_pcm_defs)
        if i not in ccds_missing_pcm_defs[:n]
    ]

    if len(ccds_missing_pcm_defs) != 0:
        return ccds_missing_pcm_defs

    return None


def gen_has_protein_modification(mmcif_obj):
    """Generate and overwrite _pdbx_entry_details.pdbx_has_protein_modification

    mmcif_obj is modified in place to update pdbx_has_protein_modification.
    If pdbx_entry_details does not exist then it is created

    Args:
        mmcif_obj (obj): mmcifHandling obj containing parsed mmCIF data

    """

    # Check entry has PCM data
    pdbx_mod_feat = mmcif_obj.get_category_list_of_dictionaries(
        "pdbx_modification_feature", False
    )

    if len(pdbx_mod_feat) != 0:
        has_pcm = "Y"
    else:
        has_pcm = "N"

    # Populate pdbx_entry_details
    pdbx_entry_details = mmcif_obj.get_category_list_of_dictionaries(
        "pdbx_entry_details", False
    )

    if len(pdbx_entry_details) != 0:
        mmcif_obj.set_item("pdbx_entry_details", "has_protein_modification", has_pcm)
    else:
        entry_id = mmcif_obj.get_cat_item_value("entry", "id")
        entry_details_dict = {
            "items": [
                "entry_id",
                "compound_details",
                "source_details",
                "nonpolymer_details",
                "sequence_details",
                "has_ligand_of_interest",
                "has_protein_modification",
            ],
            "values": [[entry_id, "?", "?", "?", "?", "?", has_pcm]],
        }

        mmcif_obj.add_new_category("pdbx_entry_details", entry_details_dict)

    return None


def gen_pcm_link_list(mmcif_obj):
    """Create a list of struct_conn records that describe all PCMs in the model

    Args:
        mmcif_obj (obj): OneDep obj containing all mmCIF model data

    Returns:
        list: List of struct_conn records that define PCMs in the model

    """

    # Find polypeptide entries and asym_ids
    pep_entity_types = ["POLYPEPTIDE(L)", "POLYPEPTIDE(D)", "PEPTIDE NUCLEIC ACID"]

    pep_entities = []
    entity_poly_cat = mmcif_obj.get_category_list_of_dictionaries("entity_poly", False)
    for row in entity_poly_cat:
        if row["type"].upper() in pep_entity_types:
            pep_entities.append(row["entity_id"])

    pep_asym_ids = []
    struct_asym_cat = mmcif_obj.get_category_list_of_dictionaries("struct_asym", False)
    for row in struct_asym_cat:
        if row["entity_id"] in pep_entities:
            pep_asym_ids.append(row["id"])

    # Find all PCM-related links
    pcm_link_list = []
    struct_conn_cat = mmcif_obj.get_category_list_of_dictionaries("struct_conn", False)
    for row in struct_conn_cat:
        if row["conn_type_id"].lower() not in ["covale", "disulf"]:
            continue

        if row["ptnr1_label_asym_id"] in pep_asym_ids:
            row["ptnr1_in_pep"] = "Y"
        else:
            row["ptnr1_in_pep"] = "N"

        if row["ptnr2_label_asym_id"] in pep_asym_ids:
            row["ptnr2_in_pep"] = "Y"
        else:
            row["ptnr2_in_pep"] = "N"

        if (row["ptnr1_in_pep"] == "Y") or (row["ptnr2_in_pep"] == "Y"):
            pcm_link_list.append(row)

    return pcm_link_list


def gen_pcm_ccd_list(pcm_link_list):
    """Create a list of CCDs that describe all PCMs in the model

    Args:
        pcm_link_list (list): 2D List of struct_conn data that defines all PCMs in
            structure

    Returns:
        list: List of all CCD IDs that contain the PCM definitions necessary to describe
          all the PCMs in the structure

    """

    pcm_ccd_list = []
    for row in pcm_link_list:
        if (row["ptnr1_in_pep"] == "N") or (
            row["ptnr1_label_comp_id"] not in std_amino_acids
        ):
            pcm_ccd_list.append(row["ptnr1_label_comp_id"])

        if (row["ptnr2_in_pep"] == "N") or (
            row["ptnr2_label_comp_id"] not in std_amino_acids
        ):
            pcm_ccd_list.append(row["ptnr2_label_comp_id"])

    # Remove duplicates and order alphabetically
    pcm_ccd_list = sorted(list(set(pcm_ccd_list)))

    return pcm_ccd_list


def gen_non_std_link_pcm_record(sc_rec, pcm_category):
    """Generate Non-standard link PCM records from struct_conn record

    This includes Disulfide bridges, Isopeptide bonds and Non-standard linkages

    Args:
        sc_rec (dict): struct_conn record describing a non-standard linkage
        pcm_category (str): type of non-std link ("Disulfide bridge", "Isopeptide bond"
                or "Non-standard linkage")

    Returns:
        list: Non-standard link in pdbx_modification_feature records format

    """

    pdbx_mod_feat_recs = [
        {
            "label_comp_id": sc_rec["ptnr1_label_comp_id"],
            "label_asym_id": sc_rec["ptnr1_label_asym_id"],
            "label_seq_id": sc_rec["ptnr1_label_seq_id"],
            "label_alt_id": sc_rec["pdbx_ptnr1_label_alt_id"],
            "modified_residue_label_comp_id": sc_rec["ptnr2_label_comp_id"],
            "modified_residue_label_asym_id": sc_rec["ptnr2_label_asym_id"],
            "modified_residue_label_seq_id": sc_rec["ptnr2_label_seq_id"],
            "modified_residue_label_alt_id": sc_rec["pdbx_ptnr2_label_alt_id"],
            "auth_comp_id": sc_rec["ptnr1_auth_comp_id"],
            "auth_asym_id": sc_rec["ptnr1_auth_asym_id"],
            "auth_seq_id": sc_rec["ptnr1_auth_seq_id"],
            "PDB_ins_code": sc_rec["pdbx_ptnr1_PDB_ins_code"],
            "symmetry": sc_rec[f"ptnr1_symmetry"],
            "modified_residue_auth_comp_id": sc_rec["ptnr2_auth_comp_id"],
            "modified_residue_auth_asym_id": sc_rec["ptnr2_auth_asym_id"],
            "modified_residue_auth_seq_id": sc_rec["ptnr2_auth_seq_id"],
            "modified_residue_PDB_ins_code": sc_rec["pdbx_ptnr2_PDB_ins_code"],
            "modified_residue_symmetry": sc_rec[f"ptnr2_symmetry"],
            "comp_id_linking_atom": sc_rec["ptnr1_label_atom_id"],
            "modified_residue_id_linking_atom": sc_rec["ptnr2_label_atom_id"],
            "modified_residue_id": ".",
            "ref_pcm_id": ".",
            "ref_comp_id": ".",
            "type": "None",
            "category": pcm_category,
        }
    ]

    return pdbx_mod_feat_recs


def gen_ace_nh2_pcm_record(sc_rec, pcm_defs, cap_id):
    """Generate ACE/NH2 PCM records from struct_conn record

    Args:
        sc_rec (dict): struct_conn record
        pcm_defs (list): list of all CCD PCM definition records relating to model
        cap_id (str): value can be "ACE" or "NH2"

    Returns:
        list: ACE/NH2 PCM in pdbx_modification_feature records format

    """

    # Assign order of ptnr data
    if sc_rec["ptnr1_label_comp_id"] == cap_id:
        cap_res_ptnr = "ptnr1"
        capped_res_ptnr = "ptnr2"

    elif sc_rec["ptnr2_label_comp_id"] == cap_id:
        cap_res_ptnr = "ptnr2"
        capped_res_ptnr = "ptnr1"

    capped_res_id = sc_rec[f"{capped_res_ptnr}_label_comp_id"]

    # Find rows of CCD PCM definitions that match struct_conn record
    specific_cap_def = None
    generic_cap_def = None
    for pcm_def in pcm_defs:
        if (
            pcm_def["modified_residue_id"] == capped_res_id
            and pcm_def["comp_id"] == cap_id
        ):
            specific_cap_def = pcm_def

        elif pcm_def["modified_residue_id"] == "?" and pcm_def["comp_id"] == cap_id:
            generic_cap_def = pcm_def

    # If no specific parent matches, return the generic match
    if specific_cap_def:
        pcm_defs_in_model = [specific_cap_def]
    else:
        pcm_defs_in_model = [generic_cap_def]

    # For each PCM definition match, create pdbx_modification_feature record
    pdbx_mod_feat_recs = []

    for pcm_def in pcm_defs_in_model:
        pdbx_mod_feat_rec = {
            "label_comp_id": sc_rec[f"{cap_res_ptnr}_label_comp_id"],
            "label_asym_id": sc_rec[f"{cap_res_ptnr}_label_asym_id"],
            "label_seq_id": sc_rec[f"{cap_res_ptnr}_label_seq_id"],
            "label_alt_id": sc_rec[f"pdbx_{cap_res_ptnr}_label_alt_id"],
            "modified_residue_label_comp_id": sc_rec[
                f"{capped_res_ptnr}_label_comp_id"
            ],
            "modified_residue_label_asym_id": sc_rec[
                f"{capped_res_ptnr}_label_asym_id"
            ],
            "modified_residue_label_seq_id": sc_rec[f"{capped_res_ptnr}_label_seq_id"],
            "modified_residue_label_alt_id": sc_rec[
                f"pdbx_{capped_res_ptnr}_label_alt_id"
            ],
            "auth_comp_id": sc_rec[f"{cap_res_ptnr}_auth_comp_id"],
            "auth_asym_id": sc_rec[f"{cap_res_ptnr}_auth_asym_id"],
            "auth_seq_id": sc_rec[f"{cap_res_ptnr}_auth_seq_id"],
            "PDB_ins_code": sc_rec[f"pdbx_{cap_res_ptnr}_PDB_ins_code"],
            "symmetry": sc_rec[f"{cap_res_ptnr}_symmetry"],
            "modified_residue_auth_comp_id": sc_rec[f"{capped_res_ptnr}_auth_comp_id"],
            "modified_residue_auth_asym_id": sc_rec[f"{capped_res_ptnr}_auth_asym_id"],
            "modified_residue_auth_seq_id": sc_rec[f"{capped_res_ptnr}_auth_seq_id"],
            "modified_residue_PDB_ins_code": sc_rec[
                f"pdbx_{capped_res_ptnr}_PDB_ins_code"
            ],
            "modified_residue_symmetry": sc_rec[f"{capped_res_ptnr}_symmetry"],
            "comp_id_linking_atom": ".",
            "modified_residue_id_linking_atom": ".",
            "modified_residue_id": pcm_def["modified_residue_id"],
            "ref_pcm_id": pcm_def["pcm_id"],
            "ref_comp_id": pcm_def["comp_id"],
            "type": pcm_def["type"],
            "category": pcm_def["category"],
        }

        pdbx_mod_feat_recs.append(pdbx_mod_feat_rec)

    return pdbx_mod_feat_recs


def gen_linked_pcm_records(sc_rec, pcm_defs):
    """Generate linked PCM records from struct_conn record

    This includes the PCM categories "Covalent chemical modification",
    "Lipid/lipid-like"", "Carbohydrate", "Heme/heme-like" etc.

    Args:
        sc_rec (dict): struct_conn record describing a linked PCM
        pcm_defs (list): list of all CCD PCM definition records relating to model

    Returns:
        list: Linked PCM in pdbx_modification_feature records format

    """

    # Identify modified residue and linked mod
    if (sc_rec["ptnr1_in_pep"] == "Y") and (sc_rec["ptnr2_in_pep"] == "N"):
        mod_res = "ptnr1"
        linked_mod = "ptnr2"
    elif (sc_rec["ptnr1_in_pep"] == "N") and (sc_rec["ptnr2_in_pep"] == "Y"):
        mod_res = "ptnr2"
        linked_mod = "ptnr1"

    # Assign CCD and atom ID values
    mod_res_comp_id = sc_rec[f"{mod_res}_label_comp_id"]
    mod_res_atom_id = sc_rec[f"{mod_res}_label_atom_id"]
    linked_mod_comp_id = sc_rec[f"{linked_mod}_label_comp_id"]
    linked_mod_atom_id = sc_rec[f"{linked_mod}_label_atom_id"]

    # Find rows of CCD PCM definitions that match struct_conn record
    pcm_defs_in_model = []
    for pcm_def in pcm_defs:
        if (
            pcm_def["modified_residue_id"] == mod_res_comp_id
            and pcm_def["comp_id"] == linked_mod_comp_id
            and pcm_def["modified_residue_id_linking_atom"] == mod_res_atom_id
            and pcm_def["comp_id_linking_atom"] == linked_mod_atom_id
        ):
            pcm_defs_in_model.append(pcm_def)

    # For each PCM definition match, create pdbx_modification_feature record
    pdbx_mod_feat_recs = []
    for pcm_def in pcm_defs_in_model:
        pdbx_mod_feat_rec = {
            "label_comp_id": sc_rec[f"{linked_mod}_label_comp_id"],
            "label_asym_id": sc_rec[f"{linked_mod}_label_asym_id"],
            "label_seq_id": sc_rec[f"{linked_mod}_label_seq_id"],
            "label_alt_id": sc_rec[f"pdbx_{linked_mod}_label_alt_id"],
            "modified_residue_label_comp_id": sc_rec[f"{mod_res}_label_comp_id"],
            "modified_residue_label_asym_id": sc_rec[f"{mod_res}_label_asym_id"],
            "modified_residue_label_seq_id": sc_rec[f"{mod_res}_label_seq_id"],
            "modified_residue_label_alt_id": sc_rec[f"pdbx_{mod_res}_label_alt_id"],
            "auth_comp_id": sc_rec[f"{linked_mod}_auth_comp_id"],
            "auth_asym_id": sc_rec[f"{linked_mod}_auth_asym_id"],
            "auth_seq_id": sc_rec[f"{linked_mod}_auth_seq_id"],
            "PDB_ins_code": sc_rec[f"pdbx_{linked_mod}_PDB_ins_code"],
            "symmetry": sc_rec[f"{linked_mod}_symmetry"],
            "modified_residue_auth_comp_id": sc_rec[f"{mod_res}_auth_comp_id"],
            "modified_residue_auth_asym_id": sc_rec[f"{mod_res}_auth_asym_id"],
            "modified_residue_auth_seq_id": sc_rec[f"{mod_res}_auth_seq_id"],
            "modified_residue_PDB_ins_code": sc_rec[f"pdbx_{mod_res}_PDB_ins_code"],
            "modified_residue_symmetry": sc_rec[f"{mod_res}_symmetry"],
            "comp_id_linking_atom": sc_rec[f"{linked_mod}_label_atom_id"],
            "modified_residue_id_linking_atom": sc_rec[f"{mod_res}_label_atom_id"],
            "modified_residue_id": pcm_def["modified_residue_id"],
            "ref_pcm_id": pcm_def["pcm_id"],
            "ref_comp_id": pcm_def["comp_id"],
            "type": pcm_def["type"],
            "category": pcm_def["category"],
        }

        pdbx_mod_feat_recs.append(pdbx_mod_feat_rec)

    return pdbx_mod_feat_recs


def gen_single_ccd_pcm_records(sc_rec, pcm_defs):
    """Generate single CCD PCM records from struct_conn record

    This includes the PCM categories "Named protein modifications",
    "Non-standard residue", "Chromophore/chromophore-like" etc.

    Args:
        sc_rec (dict): struct_conn record describing a single CCD PCM
        pcm_defs (list): list of all CCD PCM definition records relating to model

    Returns:
        list: Single CCD PCMs in pdbx_modification_feature records format

    """

    nstd_ptnrs = []

    # Which ptnrs are non-standard residues
    if sc_rec["ptnr1_label_comp_id"] not in std_amino_acids_ACE_NH2:
        nstd_ptnrs.append("ptnr1")

    if sc_rec["ptnr2_label_comp_id"] not in std_amino_acids_ACE_NH2:
        nstd_ptnrs.append("ptnr2")

    # Create output lists
    pdbx_mod_feat_recs = []

    # For each ptnr, find PCM definition matches and create pdbx_mod_feat rows
    for ptnr in nstd_ptnrs:
        # Find rows of CCD PCM definitions that match struct_conn record
        pcm_defs_in_model = []
        first_parent = None
        for pcm_def in pcm_defs:
            # Does pcm_def describe a single CCD PCM
            if pcm_def["comp_id_linking_atom"] not in [".", "?"]:
                is_single_ccd_pcm = False
            else:
                is_single_ccd_pcm = True

            # Does pcm_def match CCD ID
            if pcm_def["comp_id"] == sc_rec[f"{ptnr}_label_comp_id"]:
                row_ccd_match = True
            else:
                row_ccd_match = False

            if row_ccd_match and is_single_ccd_pcm:
                # Only add row if modified_residue_id is the same as the first row added
                if not first_parent:
                    first_parent = pcm_def["modified_residue_id"]

                if pcm_def["modified_residue_id"] == first_parent:
                    pcm_defs_in_model.append(pcm_def)

        # For each PCM definition match, create pdbx_modification_feature record
        for pcm_def in pcm_defs_in_model:
            pdbx_mod_feat_rec = {
                "label_comp_id": sc_rec[f"{ptnr}_label_comp_id"],
                "label_asym_id": sc_rec[f"{ptnr}_label_asym_id"],
                "label_seq_id": sc_rec[f"{ptnr}_label_seq_id"],
                "label_alt_id": sc_rec[f"pdbx_{ptnr}_label_alt_id"],
                "modified_residue_label_comp_id": ".",
                "modified_residue_label_asym_id": ".",
                "modified_residue_label_seq_id": ".",
                "modified_residue_label_alt_id": ".",
                "auth_comp_id": sc_rec[f"{ptnr}_auth_comp_id"],
                "auth_asym_id": sc_rec[f"{ptnr}_auth_asym_id"],
                "auth_seq_id": sc_rec[f"{ptnr}_auth_seq_id"],
                "PDB_ins_code": sc_rec[f"pdbx_{ptnr}_PDB_ins_code"],
                "symmetry": sc_rec[f"{ptnr}_symmetry"],
                "modified_residue_auth_comp_id": ".",
                "modified_residue_auth_asym_id": ".",
                "modified_residue_auth_seq_id": ".",
                "modified_residue_PDB_ins_code": ".",
                "modified_residue_symmetry": ".",
                "comp_id_linking_atom": ".",
                "modified_residue_id_linking_atom": ".",
                "modified_residue_id": pcm_def["modified_residue_id"],
                "ref_pcm_id": pcm_def["pcm_id"],
                "ref_comp_id": pcm_def["comp_id"],
                "type": pcm_def["type"],
                "category": pcm_def["category"],
            }

            pdbx_mod_feat_recs.append(pdbx_mod_feat_rec)

    return pdbx_mod_feat_recs


def gen_dummy_pcm_records(sc_rec):
    """Generate dummy PCM record from struct_conn record

    This is performed when a struct_conn describes a PCM, but no PCM record has been
    created for this struct_conn. Usually it is added because there is no PCM data in a
    CCD that describes this modification.

    Args:
        sc_rec (dict): struct_conn record describing a PCM that isn't fully annotated

    Returns:
        list: Dummy PCM in pdbx_modification_feature records format

    """

    pdbx_mod_feat_recs = [
        {
            "label_comp_id": sc_rec["ptnr1_label_comp_id"],
            "label_asym_id": sc_rec["ptnr1_label_asym_id"],
            "label_seq_id": sc_rec["ptnr1_label_seq_id"],
            "label_alt_id": sc_rec["pdbx_ptnr1_label_alt_id"],
            "modified_residue_label_comp_id": sc_rec["ptnr2_label_comp_id"],
            "modified_residue_label_asym_id": sc_rec["ptnr2_label_asym_id"],
            "modified_residue_label_seq_id": sc_rec["ptnr2_label_seq_id"],
            "modified_residue_label_alt_id": sc_rec["pdbx_ptnr2_label_alt_id"],
            "auth_comp_id": sc_rec["ptnr1_auth_comp_id"],
            "auth_asym_id": sc_rec["ptnr1_auth_asym_id"],
            "auth_seq_id": sc_rec["ptnr1_auth_seq_id"],
            "PDB_ins_code": sc_rec["pdbx_ptnr1_PDB_ins_code"],
            "symmetry": sc_rec[f"ptnr1_symmetry"],
            "modified_residue_auth_comp_id": sc_rec["ptnr2_auth_comp_id"],
            "modified_residue_auth_asym_id": sc_rec["ptnr2_auth_asym_id"],
            "modified_residue_auth_seq_id": sc_rec["ptnr2_auth_seq_id"],
            "modified_residue_PDB_ins_code": sc_rec["pdbx_ptnr2_PDB_ins_code"],
            "modified_residue_symmetry": sc_rec[f"ptnr2_symmetry"],
            "comp_id_linking_atom": sc_rec["ptnr1_label_atom_id"],
            "modified_residue_id_linking_atom": sc_rec["ptnr2_label_atom_id"],
            "modified_residue_id": ".",
            "ref_pcm_id": ".",
            "ref_comp_id": ".",
            "type": "None",
            "category": "PCM INCORRECTLY HANDLED OR CCD MISSING PCM OR BACKBONE DATA",
        }
    ]

    return pdbx_mod_feat_recs


def check_sc_between_neighbors(sc_rec):
    """Check if the struct_conn record is between two neighboring residues in a sequence

    Args:
        sc_rec (dict): struct_conn record

    Returns:
        bool: True if ptnr1 and ptnr2 are neighbors

    """

    same_asym_id = False
    sequential_seq_ids = False

    # If ptnr not in a sequence
    if (sc_rec["ptnr1_label_seq_id"] in [".", "?"]) or (
        sc_rec["ptnr2_label_seq_id"] in [".", "?"]
    ):
        return False

    # Check same asym id
    if sc_rec["ptnr1_label_asym_id"] == sc_rec["ptnr2_label_asym_id"]:
        same_asym_id = True

    # Check 1 residue apart
    diff_seq_ids = abs(
        int(sc_rec["ptnr1_label_seq_id"]) - int(sc_rec["ptnr2_label_seq_id"])
    )
    if diff_seq_ids == 1:
        sequential_seq_ids = True

    if same_asym_id and sequential_seq_ids:
        neighbors = True
    else:
        neighbors = False

    return neighbors


def check_backbone_link(sc_rec, terminal_atoms_dict, are_neighb):
    """Check if the link is backbone peptide bond

    A backbone peptide bond is a struct_conn between two neighboring peptide residues
    where the linking atoms are between a C-terminal and N-terminal atoms (as defined
    by chem_comp_atom in the CCD).

    Args:
        sc_rec (dict): struct_conn record
        terminal_atoms_dict (dict): dict containing N-/C-terminal atoms for each CCD
        are_neighb (bool): If true ptnrs are neighbouring residues in same peptide

    Returns:
        bool: True if link is non-standard linkage

    """

    ptnr1_ccd_id = sc_rec["ptnr1_label_comp_id"]
    ptnr2_ccd_id = sc_rec["ptnr2_label_comp_id"]
    ptnr1_atom_id = sc_rec["ptnr1_label_atom_id"]
    ptnr2_atom_id = sc_rec["ptnr2_label_atom_id"]

    # Check if link is peptide backbone link
    if (
        are_neighb
        and (ptnr1_atom_id in terminal_atoms_dict[ptnr1_ccd_id]["N-term"])
        and (ptnr2_atom_id in terminal_atoms_dict[ptnr2_ccd_id]["C-term"])
    ):
        is_bb_link = True

    elif (
        are_neighb
        and (ptnr1_atom_id in terminal_atoms_dict[ptnr1_ccd_id]["C-term"])
        and (ptnr2_atom_id in terminal_atoms_dict[ptnr2_ccd_id]["N-term"])
    ):
        is_bb_link = True

    else:
        is_bb_link = False

    return is_bb_link


def check_isopeptide(sc_rec, terminal_atoms_dict):
    """Check if the link is an isopeptide bond

    An isopeptide bond is any peptide bond that is between two peptide residues but not
    a backbone-to-backbone peptide bond. This carboxyl group can be the backbone or side
    chain carboxyl group.

    These are found with the following logic:
        - Both residues must be part of peptide sequence
        - LYS NZ to GLU/GLN/ASP/ASN side chain carboxyl
        - LYS NZ to backbone C-terminal carboxyl group
        - GLU/GLN/ASP/ASN side chain carboxyl to backbone N-terminal amino group
        - Includes D-amino acid versions of these residues

    Args:
        sc_rec (dict): struct_conn record
        terminal_atoms_dict (dict): dict containing N-/C-terminal atoms for each CCD

    Returns:
        bool: True if link is an Isopeptide bond

    """

    ptnr1_ccd_id = sc_rec["ptnr1_label_comp_id"]
    ptnr2_ccd_id = sc_rec["ptnr2_label_comp_id"]
    ptnr1_atom_id = sc_rec["ptnr1_label_atom_id"]
    ptnr2_atom_id = sc_rec["ptnr2_label_atom_id"]

    # Both residues must be in peptide sequences
    if not (sc_rec["ptnr1_in_pep"] == "Y" and sc_rec["ptnr2_in_pep"] == "Y"):
        is_isopeptide = False

    # LYS NZ - GLU/GLN CD
    elif (
        ptnr1_ccd_id in ["LYS", "DLY"]
        and ptnr1_atom_id == "NZ"
        and ptnr2_ccd_id in ["GLU", "GLN", "DGL", "DGN"]
        and ptnr2_atom_id == "CD"
    ) or (
        ptnr1_ccd_id in ["GLU", "GLN", "DGL", "DGN"]
        and ptnr1_atom_id == "CD"
        and ptnr2_ccd_id in ["LYS", "DLY"]
        and ptnr2_atom_id == "NZ"
    ):
        is_isopeptide = True

    # LYS NZ - ASP/ASN CG
    elif (
        ptnr1_ccd_id in ["LYS", "DLY"]
        and ptnr1_atom_id == "NZ"
        and ptnr2_ccd_id in ["ASP", "ASN", "DAS", "DSG"]
        and ptnr2_atom_id == "CG"
    ) or (
        ptnr1_ccd_id in ["ASP", "ASN", "DAS", "DSG"]
        and ptnr1_atom_id == "CG"
        and ptnr2_ccd_id in ["LYS", "DLY"]
        and ptnr2_atom_id == "NZ"
    ):
        is_isopeptide = True

    # LYS NZ  - Backbone Carboxyl
    elif (
        ptnr1_ccd_id in ["LYS", "DLY"]
        and ptnr1_atom_id == "NZ"
        and ptnr2_atom_id.startswith("C")
        and ptnr2_atom_id in terminal_atoms_dict[ptnr2_ccd_id]["C-term"]
    ) or (
        ptnr1_atom_id.startswith("C")
        and ptnr1_atom_id in terminal_atoms_dict[ptnr1_ccd_id]["C-term"]
        and ptnr2_ccd_id in ["LYS", "DLY"]
        and ptnr2_atom_id == "NZ"
    ):
        is_isopeptide = True

    # GLU/GLN CD - Backbone Amino
    elif (
        ptnr1_ccd_id in ["GLU", "GLN", "DGL", "DGN"]
        and ptnr1_atom_id == "CD"
        and ptnr2_atom_id.startswith("N")
        and ptnr2_atom_id in terminal_atoms_dict[ptnr2_ccd_id]["N-term"]
    ) or (
        ptnr1_atom_id.startswith("N")
        and ptnr1_atom_id in terminal_atoms_dict[ptnr1_ccd_id]["N-term"]
        and ptnr2_ccd_id in ["GLU", "GLN", "DGL", "DGN"]
        and ptnr2_atom_id == "CD"
    ):
        is_isopeptide = True

    # ASP/ASN CG - Backbone Amino
    elif (
        ptnr1_ccd_id in ["ASP", "ASN", "DAS", "DSG"]
        and ptnr1_atom_id == "CG"
        and ptnr2_atom_id.startswith("N")
        and ptnr2_atom_id in terminal_atoms_dict[ptnr2_ccd_id]["N-term"]
    ) or (
        ptnr1_atom_id.startswith("N")
        and ptnr1_atom_id in terminal_atoms_dict[ptnr1_ccd_id]["N-term"]
        and ptnr2_ccd_id in ["ASP", "ASN", "DAS", "DSG"]
        and ptnr2_atom_id == "CG"
    ):
        is_isopeptide = True

    else:
        is_isopeptide = False

    return is_isopeptide


def check_non_std_linkage(sc_rec, is_bb_link):
    """Check if the link is a non-standard linkage

    A non-standard linkage is a struct_conn between two peptide residues that is not
    a disulfide bridge or a peptide bond backbone link

    Args:
        sc_rec (dict): struct_conn record
        is_bb_link (bool): If True, the struct_conn record describes a backbone link

    Returns:
        bool: True if link is non-standard linkage

    """

    # Check if non-std link
    if (
        sc_rec["ptnr1_in_pep"] == "Y"
        and sc_rec["ptnr2_in_pep"] == "Y"
        and not is_bb_link
        and sc_rec["conn_type_id"] == "covale"
    ):
        return True

    else:
        return False


def check_ace_nh2_pcm(sc_rec, cap_id, is_bb_link):
    """Check if the link describes an ACE/NH2 capping residue

    Args:
        sc_rec (dict): struct_conn record
        cap_id (str): value can be "ACE" or "NH2"
        is_bb_link (bool): If True, the struct_conn record describes a backbone link

    Returns:
        bool: True if link describes ACE/NH2 capping PCM record

    """

    ptnr1_ccd_id = sc_rec["ptnr1_label_comp_id"]
    ptnr2_ccd_id = sc_rec["ptnr2_label_comp_id"]

    if (ptnr1_ccd_id == cap_id or ptnr2_ccd_id == cap_id) and is_bb_link:
        return True
    else:
        return False


def find_ccds_missing_pcm_defs(sc_rec, pcm_link_type, pdbx_mod_feat_rows, entry_id):
    """Find all CCDs that should describe a PCM but did not contain PCM data to do this

    Args:
        sc_rec (dict): struct_conn record
        pcm_link_type (str): what type of PCM does the link describe
        pdbx_mod_feat_rows (list): list of all the rows to be added to
            pdbx_modification_feature based on the struct_conn record
        entry_id (str): entry id

    Returns:
        list: List of dicts describing all the CCDs that are missing PCM definitions
            required for the annotation of PCMs described by struct_conn record

    """

    # Track which ptnr should contain PCM data
    pcm_ptnrs = []
    res_ptnr = ""
    direct_links = ["Disulfide bridge", "Isopeptide bond", "Non-standard linkage"]

    # If one is in peptide and the other not just keep info for linked one
    if pcm_link_type == "linked":
        # Identify modified residue and linked mod
        if (sc_rec["ptnr1_in_pep"] == "Y") and (sc_rec["ptnr2_in_pep"] == "N"):
            pcm_ptnrs.append("ptnr2")
            res_ptnr = "ptnr1"
        elif (sc_rec["ptnr1_in_pep"] == "N") and (sc_rec["ptnr2_in_pep"] == "Y"):
            pcm_ptnrs.append("ptnr1")
            res_ptnr = "ptnr2"

    # If both CCDs are in peptide keep only the non-std ones and add two rows
    if pcm_link_type == "single_ccd_pcm":
        if sc_rec["ptnr1_label_comp_id"] not in std_amino_acids_ACE_NH2:
            pcm_ptnrs.append("ptnr1")

        if sc_rec["ptnr2_label_comp_id"] not in std_amino_acids_ACE_NH2:
            pcm_ptnrs.append("ptnr2")

    # For each ptnr that should have a pdbx_mod_feat row try to find a match
    # If no match, add to list of missing PCMs
    missing_pcm_rows = []
    for ptnr in pcm_ptnrs:
        match_found = False

        # Ignore UNL and UNX linked modifications
        if sc_rec[f"{ptnr}_label_comp_id"] in ["UNL", "UNX", "UNK", "ASX", "GLX"]:
            continue

        # Check if ptnr in pdbx_mod_feat_rows (excl. direct links)
        for row in pdbx_mod_feat_rows:
            if (
                sc_rec[f"{ptnr}_label_comp_id"] == row["label_comp_id"]
                and sc_rec[f"{ptnr}_label_asym_id"] == row["label_asym_id"]
                and sc_rec[f"{ptnr}_label_seq_id"] == row["label_seq_id"]
                and row["category"] not in direct_links
            ):
                match_found = True

        if (not match_found) & (pcm_link_type == "linked"):
            missing_pcm_row = {
                "Comp_id": sc_rec[f"{ptnr}_label_comp_id"],
                "Modified_residue_id": sc_rec[f"{res_ptnr}_label_comp_id"],
                "Type": "missing",
                "Category": "missing",
                "Position": "missing",
                "Polypeptide_position": "missing",
                "Comp_id_linking_atom": sc_rec[f"{ptnr}_label_atom_id"],
                "Modified_residue_id_linking_atom": sc_rec[f"{res_ptnr}_label_atom_id"],
                "First_instance_model_db_code": entry_id,
            }

            missing_pcm_rows.append(missing_pcm_row)

        elif (not match_found) & (pcm_link_type == "single_ccd_pcm"):
            missing_pcm_row = {
                "Comp_id": sc_rec[f"{ptnr}_label_comp_id"],
                "Modified_residue_id": "missing",
                "Type": "missing",
                "Category": "missing",
                "Position": "missing",
                "Polypeptide_position": "missing",
                "Comp_id_linking_atom": ".",
                "Modified_residue_id_linking_atom": ".",
                "First_instance_model_db_code": entry_id,
            }

            missing_pcm_rows.append(missing_pcm_row)

    return missing_pcm_rows


def reformat_pdbx_mod_feat(pdbx_mod_feat_list_dicts):
    """Reformat pdbx_mod_feat from list of dicts to mmcifHandling input format

    During this process the category is ordered and ordinals added

    Args:
        pdbx_mod_feat_list_dicts (list): pdbx_mod_feat in list of dicts format

    Returns:
        dict: Dictionary of pdbx_mod_feat in mmcifHandling input format
    """

    pcm_category_order = {
        "Named protein modification": 1,
        "Chromophore/chromophore-like": 2,
        "Non-standard residue": 3,
        "Terminal acetylation": 4,
        "Terminal amidation": 5,
        "Carbohydrate": 6,
        "Heme/heme-like": 7,
        "Lipid/lipid-like": 8,
        "Nucleotide monophosphate": 9,
        "Flavin": 10,
        "ADP-ribose": 11,
        "Biotin": 12,
        "Crosslinker": 13,
        "Covalent chemical modification": 14,
        "Disulfide bridge": 15,
        "Isopeptide bond": 16,
        "Non-standard linkage": 17,
    }

    # Sort by priority
    pdbx_mod_feat_list_dicts = sorted(
        pdbx_mod_feat_list_dicts,
        key=lambda d: (
            pcm_category_order.get(d["category"], float("inf")),
            d["label_asym_id"],
            int(d["label_seq_id"]) if d["label_seq_id"].isdigit() else 0,
            d["label_alt_id"],
            d["ref_comp_id"],
            int(d["ref_pcm_id"]) if d["ref_pcm_id"].isdigit() else 0,
        ),
    )

    # Add ordinals
    for i, d in enumerate(pdbx_mod_feat_list_dicts, start=1):
        d["ordinal"] = i

    # Define key order
    keys = [
        "ordinal",
        "label_comp_id",
        "label_asym_id",
        "label_seq_id",
        "label_alt_id",
        "modified_residue_label_comp_id",
        "modified_residue_label_asym_id",
        "modified_residue_label_seq_id",
        "modified_residue_label_alt_id",
        "auth_comp_id",
        "auth_asym_id",
        "auth_seq_id",
        "PDB_ins_code",
        "symmetry",
        "modified_residue_auth_comp_id",
        "modified_residue_auth_asym_id",
        "modified_residue_auth_seq_id",
        "modified_residue_PDB_ins_code",
        "modified_residue_symmetry",
        "comp_id_linking_atom",
        "modified_residue_id_linking_atom",
        "modified_residue_id",
        "ref_pcm_id",
        "ref_comp_id",
        "type",
        "category",
    ]

    # Reformat to mmcifHandling format
    output_dict = {
        "items": keys,
        "values": [[d[key] for key in keys] for d in pdbx_mod_feat_list_dicts],
    }

    return output_dict
