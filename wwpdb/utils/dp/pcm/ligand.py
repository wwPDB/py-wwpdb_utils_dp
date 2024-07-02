"""Utils related to ligand definitions and file paths"""
import os
import sys


from mmcif.io.IoAdapterCore import IoAdapterCore as IoAdapterCore

from wwpdb.utils.dp.pcm.mmcif import mmcifHandling

# All the amino acids CCD IDs that occur naturally in polypeptides (incl. D-amino acids)
std_amino_acids = [
        "ALA",
        "ARG",
        "ASN",
        "ASP",
        "CYS",
        "GLN",
        "GLU",
        "GLY",
        "HIS",
        "ILE",
        "LEU",
        "LYS",
        "MET",
        "PHE",
        "PRO",
        "PYL",
        "SEC",
        "SER",
        "THR",
        "TRP",
        "TYR",
        "VAL",
        "DAL",
        "DAR",
        "DSG",
        "DAS",
        "DCY",
        "DGN",
        "DGL",
        "DHI",
        "DIL",
        "DLE",
        "DLY",
        "MED",
        "DPN",
        "DPR",
        "DSN",
        "DTH",
        "DTR",
        "DTY",
        "DVA",
    ]

# All amino acids CCD IDs + ACE/NH2 that occur naturally in polypeptides
# (incl. D-amino acids)
std_amino_acids_ACE_NH2 = [
        "ACE",
        "ALA",
        "ARG",
        "ASN",
        "ASP",
        "CYS",
        "GLN",
        "GLU",
        "GLY",
        "HIS",
        "ILE",
        "LEU",
        "LYS",
        "MET",
        "NH2",
        "PHE",
        "PRO",
        "PYL",
        "SEC",
        "SER",
        "THR",
        "TRP",
        "TYR",
        "VAL",
        "DAL",
        "DAR",
        "DSG",
        "DAS",
        "DCY",
        "DGN",
        "DGL",
        "DHI",
        "DIL",
        "DLE",
        "DLY",
        "MED",
        "DPN",
        "DPR",
        "DSN",
        "DTH",
        "DTR",
        "DTY",
        "DVA",
    ]


def get_ccd_path(ccd_id, cICommon, relative_path=False):
    """Get the full path to a CCD file within OneDep

    This uses site-config, which holds the CCD CVS path

    Args:
        ccd_id (str): CCD ID
        cICommon (obj): Object containing the sites common OneDep config info
        relative_path (bool): If True, return relative path from ligand-dict-v3 root dir

    Returns:
        str: Full path where the CCD file is located in OneDep

    """

    ccd_id = ccd_id.upper()

    if relative_path:
        ccd_root_path = ""
    else:
        ccd_root_path = cICommon.get_site_cc_cvs_path()

    if len(ccd_id) <= 3:
        ccd_file = os.path.join(ccd_root_path, ccd_id[0], ccd_id, f"{ccd_id}.cif")

    elif len(ccd_id) == 5:
        ccd_file = os.path.join(ccd_root_path, ccd_id[3:], ccd_id, f"{ccd_id}.cif")

    return ccd_file


def read_ccd(path):
    """Opens CCD CIF file.

    Args:
        path (str): Path to CCD CIF file.

    Returns:
        cif (mmCIF_handling.mmcifHandling): CCD CIF object.

    """

    cif = mmcifHandling("")
    cif.set_input_mmcif(path)
    cif.parse_mmcif()

    return cif


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


