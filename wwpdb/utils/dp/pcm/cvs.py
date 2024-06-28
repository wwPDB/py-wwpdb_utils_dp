"""Utils relating to cvs commit and checkout"""
import subprocess

from wwpdb.utils.config.ConfigInfoApp import ConfigInfoAppCommon

from wwpdb.utils.dp.pcm.ligand import get_ccd_path


def run_cvs_commit(file_id, file_path, message, output_log_path, suppress_errors=False):
    """Run cvs commit

    The CWD must be already within the CVS repo for this to work

    Args:
        file_id (str): CCD/PRD ID for the file
        file_path (str): file path of file to commit to CVS
        message (str): commit message
        output_log_path (str): file path of the log file
        suppress_errors (bool): if True, commit errors do not terminate script

    Returns:
        bool: True if successful, False if error occurs

    """

    command_commit = ["cvs", "commit", "-m", message, file_path]

    fcommit = subprocess.run(command_commit)
    if fcommit.returncode == 0:
        with open(output_log_path, "a") as file:
            file.write(f"{file_id} successfully committed \n")

        return True

    else:
        with open(output_log_path, "a") as file:
            file.write(f"Error occurred during CVS commit of {file_id} \n")

            if not suppress_errors:
                raise RuntimeError(f"Error occurred during CVS commit of {file_id}")

        return False


def run_cvs_add(file_id, file_path, message, output_log_path, suppress_errors=False):
    """Run cvs add

    The CWD must be already within the CVS repo for this to work

    Args:
        file_id (str): CCD/PRD ID for the file
        file_path (str): file path of file to add to CVS
        message (str): message
        output_log_path (str): file path of the log file
        suppress_errors (bool): if True, errors do not terminate script

    Returns:
        bool: True if successful, False if error occurs

    """

    command_add = ["cvs", "add", "-m", message, file_path]

    fadd = subprocess.run(command_add)
    if fadd.returncode == 0:
        with open(output_log_path, "a") as file:
            file.write(f"{file_id} successfully added\n")

        return True

    else:
        with open(output_log_path, "a") as file:
            file.write(f"Error occurred during CVS add of {file_id} \n")

            if not suppress_errors:
                raise RuntimeError(f"Error occurred during CVS add of {file_id}")

        return False


def copy_ccd_files_to_cvs_local(list_to_copy_file, ccd_dir_path):
    """Copy CCD files in local directory to local OneDep ligand-dict-v3 instance

    Args:
        list_to_copy_file (str): Path to file containing list of CCDs to copy in
                                    line-separated format with no header
        ccd_dir_path (str): Path to directory containing CCDs to copy to ligand-dict-v3

    Returns:
        None
    """

    # Get site OneDep config info
    cICommon = ConfigInfoAppCommon()

    # Read list of CCDs to commit
    ccd_ids_to_update = []
    with open(list_to_copy_file, "r") as file:
        for line in file:
            ccd_ids_to_update.append(line.strip())

    for ccd_id in ccd_ids_to_update:
        updated_file_path = f"{ccd_dir_path}/{ccd_id}.cif"
        ccd_cvs_path = get_ccd_path(ccd_id, cICommon)
        # shutil.copy2(updated_file_path, ccd_cvs_path)
        print(updated_file_path, ccd_cvs_path)