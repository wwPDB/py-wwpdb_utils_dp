"""Utils related to mmCIF file parsing"""

import pandas as pd

from mmcif.api.DataCategory import DataCategory
from mmcif.io.IoAdapterCore import IoAdapterCore as IoAdapterCore
from wwpdb.io.locator.PathInfo import PathInfo
from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId
from wwpdb.utils.wf.dbapi.WfDbApi import WfDbApi


def gemmi_mmcif_category_to_df(gemmi_obj, category_name):
    """Converts a Gemmi mmCIF category into a pandas DF

    This should be avoided where possible and the in-built OneDep parser should be used
    instead of Gemmi

    Args:
        gemmi_obj (gemmi.cif.Block): CIF block object containing CCD data
        category_name (str): Name of loop (e.g. "_chem_comp_atom.")

    Returns:
        pd.DataFrame: Containing loop data as pandas DF

    """

    # Get category items
    category_name_len = len(category_name)

    cols = list(gemmi_obj.find_mmcif_category(category_name).tags)
    cols = [col[category_name_len:] for col in cols]

    # Convert category into DF
    chem_comp_atom_list = [
        list(row) for row in gemmi_obj.find_mmcif_category(category_name)
    ]
    df = pd.DataFrame(chem_comp_atom_list, columns=cols)

    return df

