"""Utils relating to cvs commit and checkout"""

import subprocess


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

