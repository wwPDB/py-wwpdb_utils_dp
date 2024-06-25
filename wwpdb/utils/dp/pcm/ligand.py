"""Utils related to ligand definitions and file paths"""

import logging
import os
import shutil
import sys
import tempfile

from mmcif.api.DataCategory import DataCategory
from mmcif.io.IoAdapterCore import IoAdapterCore as IoAdapterCore
from wwpdb.io.locator.PathInfo import PathInfo
from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId
from wwpdb.utils.wf.dbapi.WfDbApi import WfDbApi


def get_ccd_path(ccd_id, cICommon):
    """Get the full path to a CCD file within OneDep

    This uses site-config, which holds the CCD CVS path

    Args:
        ccd_id (str): CCD ID
        cICommon (obj): Object containing the sites common OneDep config info

    Returns:
        str: Full path where the CCD file is located in OneDep

    """

    ccd_id = ccd_id.upper()
    ccd_root_path = cICommon.get_site_cc_cvs_path()
    ccd_file = os.path.join(ccd_root_path, ccd_id[0], ccd_id, f"{ccd_id}.cif")

    return ccd_file


def get_prd_path(prd_id, cICommon):
    """Get the full path to a PRD file within OneDep

    This uses site-config, which holds the PRD CVS path

    Args:
        prd_id (str): PRD ID
        cICommon (obj): Object containing the sites common OneDep config info

    Returns:
        str: Full path where the PRD file is located in OneDep

    """

    prd_id = prd_id.upper()
    prd_root_path = cICommon.get_site_prd_cvs_path()
    prd_file = os.path.join(prd_root_path, prd_id[-1], f"{prd_id}.cif")

    return prd_file


def get_prdcc_path(prd_id, cICommon):
    """Get the full path to a PRDCC file within OneDep

    This uses site-config, which holds the PRDCC CVS path

    Args:
        prd_id (str): PRD ID
        cICommon (obj): Object containing the sites common OneDep config info

    Returns:
        str: Full path where the PRDCC file is located in OneDep

    """

    prd_id = prd_id.upper()
    prdcc_root_path = cICommon.get_site_prdcc_cvs_path()
    prdcc_file = os.path.join(prdcc_root_path, prd_id[-1], f"PRDCC_{prd_id[4:]}.cif")

    return prdcc_file

