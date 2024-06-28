"""Functions to fix unstandardised PCM data in PDB entries

TODO:

Will need to make sure it works for when the CCD is split into two non-standard CCDs
- Struct_ref_seq_dif might not be updated for these cases e.g. O12 to ORN + DAO

- SeqMod and AnnMod might need to be run after each split/merge/replace
    - There are some categories that definitely need updating
    - This includes struct_ref_seq_dif

Try the same process but for a merge example
- I think this might work using the UpdateEntry flag -merge_polymer_residue

Essential - Add logs so that when errors occur during these processes they can be caught

"""

import os


def run_split(
    annot_pack_path,
    dep_id,
    input_entry_path,
    output_entry_path,
    resid_details,
    mapping_template,
):
    """Within a PDB entry split 1 polymer CCD instance into two CCDs

    Where there are multiple instances this must be run multiple times
    Writes output entry file to disk.

    Args:
        annot_pack_path (str): Annotation pack absolute path
        dep_id (str): Dep ID
        input_entry_path (str): PDB entry to remediate relative path
        output_entry_path (str): Output path for PDB entry
        resid_details (str): Details of residue to remediate
            - Format is {auth_asym_id}_{ccd_id}_{auth_seq_id}_{empty or PDB ins code}
            - e.g. B_MYK_9_
        mapping_template (str): Path for mapping template in .cif format

    Returns:
        None
    """

    # Prepare files for update script
    get_combine_coord_cmd = (
        f"{annot_pack_path}/bin/GetCombineCoord "
        f"-input {input_entry_path} "
        f"-output_orig {resid_details}.orig.cif "
        f"-output_merge {resid_details}.merge.cif "
        f"-output_comp {resid_details}.comp.cif "
        f"-group {resid_details} "
        f"-log split_{dep_id}_{resid_details}_GetCombineCoord_1.log "
        f">& split_{dep_id}_{resid_details}_GetCombineCoord_2.log"
    )

    os.system(get_combine_coord_cmd)

    gen_mapping_cmd = (
        f"{annot_pack_path}/bin/GenMappingFile "
        f"-orig_cif {resid_details}.orig.cif "
        f"-merge_cif {resid_details}.merge.cif "
        f"-comp_cif {resid_details}.comp.cif "
        f"-chopper_cif {mapping_template} "
        f"-output {resid_details}.mapping.cif "
        f"-option split "
        f"-log split_{dep_id}_{resid_details}_GenMappingFile_1.log "
        f">& split_{dep_id}_{resid_details}_GenMappingFile_2.log"
    )

    os.system(gen_mapping_cmd)

    # Run update and save output to disk
    update_entry_cmd = (
        f"{annot_pack_path}/bin/UpdateEntry "
        f"-input {input_entry_path} "
        f"-output {output_entry_path} "
        f"-mapping {resid_details}.mapping.cif "
        f"-split_polymer_residue "
        f"-log split_{dep_id}_{resid_details}_UpdateEntry_1.log "
        f">& split_{dep_id}_{resid_details}_UpdateEntry_2.log"
    )

    os.system(update_entry_cmd)

    # Here run SeqMod to update struct_ref_seq_dif and other categories

    # Here maybe run AnnMod tools to update other categories


def run_merge(
    annot_pack_path,
    dep_id,
    input_entry_path,
    output_entry_path,
    resid_details,
    mapping_template,
):
    """Within a PDB entry merge 2 CCDs into 1 polymer CCD

    Writes output entry file to disk

    Args:
        annot_pack_path (str): Annotation pack absolute path
        dep_id (str): Dep ID
        input_entry_path (str): PDB entry to remediate relative path
        output_entry_path (str): Output path for PDB entry
        resid_details (str): NOT SURE ABOUT FORMAT YET
        mapping_template (str): Path for mapping template in .cif format

    Returns:
        None
    """

    get_combine_coord_cmd = (
        f"{annot_pack_path}/bin/GetCombineCoord "
        f"-input {input_entry_path} "
        f"-output_orig {resid_details}.orig.cif "
        f"-output_merge {resid_details}.merge.cif "
        f"-output_comp {resid_details}.comp.cif "
        f"-group {resid_details} "
        f"-log merge_{dep_id}_{resid_details}_GetCombineCoord_1.log "
        f">& merge_{dep_id}_{resid_details}_GetCombineCoord_2.log"
    )

    os.system(get_combine_coord_cmd)

    gen_mapping_cmd = (
        f"{annot_pack_path}/bin/GenMappingFile "
        f"-orig_cif {resid_details}.orig.cif "
        f"-merge_cif {resid_details}.merge.cif "
        f"-comp_cif {resid_details}.comp.cif "
        f"-chopper_cif {mapping_template} "
        f"-output {resid_details}.mapping.cif "
        f"-option merge "
        f"-log merge_{dep_id}_{resid_details}_GenMappingFile_1.log "
        f">& merge_{dep_id}_{resid_details}_GenMappingFile_2.log"
    )

    os.system(gen_mapping_cmd)

    update_entry_cmd = (
        f"{annot_pack_path}/bin/UpdateEntry "
        f"-input {input_entry_path} "
        f"-output {output_entry_path} "
        f"-mapping {resid_details}.mapping.cif "
        f"-merge_polymer_residue "
        f"-log merge_{dep_id}_{resid_details}_UpdateEntry_1.log "
        f">& merge_{dep_id}_{resid_details}_UpdateEntry_2.log"
    )

    os.system(update_entry_cmd)

    # Here run SeqMod to update struct_ref_seq_dif and other categories

    # Here maybe run AnnMod tools to update other categories


def run_replace(
    annot_pack_path, dep_id, input_entry_path, output_entry_path, mappings_template
):
    """Within a PDB entry all instances of 1 CCD with another CCD

    Writes output entry file to disk

    Args:
        annot_pack_path (str): Annotation pack absolute path
        dep_id (str): Dep ID
        input_entry_path (str): PDB entry to remediate relative path
        output_entry_path (str): Output path for PDB entry
        mapping_template (str): Path for mapping template in .cif format

    Returns:
        None

    """

    update_instance_cmd = (
        f"{annot_pack_path}/bin/updateInstance "
        f"-i {input_entry_path} "
        f"-o {output_entry_path} "
        f"-assign {mappings_template} "
        f"-log replace_{dep_id}_updateInstance_1.log "
        f">& replace_{dep_id}_updateInstance_2.log"
    )

    os.system(update_instance_cmd)
