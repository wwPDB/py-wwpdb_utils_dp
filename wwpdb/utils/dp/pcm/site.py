"""Utils related to obtaining site data"""


def select_sites(site):
    """Select all the site IDs to filter by based on wwPDB site

    Args:
        site (str): wwPDB site (PDBE/PDBJ/RCSB/ALL)

    Returns:
        list: all process sites to filter data with
    """

    if site == "ALL":
        site_list = ["PDBE", "PDBJ", "RCSB", "NDB", "", "OSAKA", "BNL", "PDBC"]
    elif site == "PDBE":
        site_list = ["PDBE"]
    elif site == "PDBJ":
        site_list = ["PDBJ", "OSAKA", "PDBC"]
    elif site == "RCSB":
        site_list = ["RCSB", "NDB", "", "BNL"]
    else:
        site_list = ["PDBE", "PDBJ", "RCSB", "NDB", "", "OSAKA", "BNL", "PDBC"]

    return site_list
