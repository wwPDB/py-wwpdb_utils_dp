"""Utils used to run checks, including dict/misc checks for individual files"""

import difflib
import os
import subprocess

import pandas as pd
from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId
from wwpdb.utils.config.ConfigInfoApp import ConfigInfoAppCommon

from remediation.utils.mmcif import mmcifHandling


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

