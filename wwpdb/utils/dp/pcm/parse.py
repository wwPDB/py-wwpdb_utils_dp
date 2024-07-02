"""Utils related to mmCIF file parsing"""

import pandas as pd

from mmcif.io.IoAdapterCore import IoAdapterCore as IoAdapterCore


def mmcif_category_to_df(mmcif_obj, category_name):
    """Converts a mmCIF category into a pandas DF using OneDep mmCIF parser

    Args:
        mmcif_obj (mmcif.mmcifHandling): CIF object
        category_name (str): Name of loop (e.g. "chem_comp_atom")

    Returns:
        pd.DataFrame: Containing loop data as pandas DF

    """

    cat = mmcif_obj.get_category_list_of_dictionaries(category_name, False)
    df_cat = pd.DataFrame(cat)

    return df_cat


def replace_mmcif_category_with_df(mmcif_obj, category_name, df):
    """Replace an mmCIF category with data from a Pandas DF using OneDep mmCIF parser

    Args:
        mmcif_obj (mmcif.mmcifHandling): CIF object
        category_name (str): Name of loop (e.g. "chem_comp_atom")
        df (pd.DataFrame): Containing data to convert into a mmCIF category

    Returns:
        None

    """

    category_dict = {
        "items": df.columns,
        "values": df.values.tolist(),
    }

    # Update category in mmCIF obj
    mmcif_obj.remove_category(category_name)
    mmcif_obj.add_new_category(category_name, category_dict)


def gemmi_mmcif_category_to_df(gemmi_obj, category_name):
    """Converts a Gemmi mmCIF category into a pandas DF

    This should be avoided where possible and the in-built OneDep parser should be used
    instead of Gemmi

    Args:
        gemmi_obj (gemmi.cif.Block): CIF block object
        category_name (str): Name of loop (e.g. "_chem_comp_atom.")

    Returns:
        pd.DataFrame: Containing loop data as pandas DF

    """

    # Get category items
    category_name_len = len(category_name)

    cols = list(gemmi_obj.find_mmcif_category(category_name).tags)
    cols = [col[category_name_len:] for col in cols]

    # Convert category into DF
    cat_list = [
        list(row) for row in gemmi_obj.find_mmcif_category(category_name)
    ]
    df = pd.DataFrame(cat_list, columns=cols)

    return df


def get_polypeptide_asym_ids(mmcif_obj):
    """From a parsed mmCIF obj, get a list of all the polypeptide asym ids

    This includes polypeptide(L), polypeptide(D) and peptide nucleic acid

    Args:
        mmcif_obj (mmcif.mmcifHandling): CIF object

    Returns:
        list: Containing asym IDs of all polypeptide entities

    """

    # Read categories
    df_entity_poly = mmcif_category_to_df(mmcif_obj, "entity_poly")
    df_struct_asym = mmcif_category_to_df(mmcif_obj, "struct_asym")

    # Convert to case insensitive
    peptide_entity_types = ["polypeptide(l)", "polypeptide(d)", "peptide nucleic acid"]
    df_entity_poly["type"] = df_entity_poly["type"].str.lower()

    # Find asym ids by entity type
    polypep_entity_list = df_entity_poly.loc[
        df_entity_poly["type"].isin(peptide_entity_types), "entity_id"
    ].tolist()
    df_polypep_struct_asym = df_struct_asym[
        df_struct_asym["entity_id"].isin(polypep_entity_list)
    ]
    polypep_struct_asym_list = df_polypep_struct_asym['id'].unique().tolist()

    return polypep_struct_asym_list


def get_nonpoly_asym_ids(mmcif_obj):
    """From a parsed mmCIF obj, get a list of all the nonpoly asym ids

    Args:
        mmcif_obj (mmcif.mmcifHandling): CIF object

    Returns:
        list: Containing asym IDs of all non-polymer entities

    """

    # Read categories
    df_entity_poly = mmcif_category_to_df(mmcif_obj, "pdbx_entity_nonpoly")
    df_struct_asym = mmcif_category_to_df(mmcif_obj, "struct_asym")

    # Find asym ids by entity type
    nonpoly_entity_list = df_entity_poly["entity_id"].unique().tolist()
    df_nonpoly_struct_asym = df_struct_asym[
        df_struct_asym["entity_id"].isin(nonpoly_entity_list)
    ]
    nonpoly_struct_asym_list = df_nonpoly_struct_asym['id'].unique().tolist()

    return nonpoly_struct_asym_list
