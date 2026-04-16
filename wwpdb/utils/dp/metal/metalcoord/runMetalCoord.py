# Author:  Chenghua Shao
# Date:    2025-11-10
# Updates:

"""
Wrapper to run MetalCoord with arguments similar to command line
Two modes are supported: stats and update
"""

import logging
import os
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wwpdb.utils.dp.metal.metal_util.run_command import run_command, MetalCommandExecutionError, MetalCommandTimeoutError  # noqa: E402
else:
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "metal_util"))
    from run_command import run_command, MetalCommandExecutionError, MetalCommandTimeoutError  # noqa: E402

logger = logging.getLogger(__name__)

class MetalCoordParametersError(Exception):
    """
    Raised when there is a parameter validation error for MetalCoord.

    :param errors: Dictionary of parameter errors.
    :type errors: dict
    """
    def __init__(self, errors: dict):
        self.errors = errors
        super().__init__(str(errors))


class MetalCoordCommandExecutionError(MetalCommandExecutionError):
    """
    Raised when MetalCoord command execution fails.
    """
    pass


class MetalCoordCommandTimeoutError(MetalCommandTimeoutError):
    """
    Raised when MetalCoord command execution times out.
    """
    pass


class RunMetalCoord:
    """
    Wrapper to run MetalCoord with arguments similar to command line.

    Example usage::

        d_args = {
            "metalcoord_exe": "/path/to/metalcoord/MetalCoord",
            "ligand": "1PT",
            "pdb": "1PG9.cif",
            "workdir": "metalcoord",
            "max_size": 100,
        }
        rMC = RunMetalCoord(d_args)
        rMC.run()
    """
    def __init__(self, d_args):
        """
        Initialize RunMetalCoord with arguments and validate them.

        :param d_args: Dictionary of arguments for running MetalCoord.
        :type d_args: dict
        """
        self.d_args = d_args
        self.mode = None
        self.validateArgs()

    def validateArgs(self):
        """
        Validate arguments in d_args.

        :raises MetalCoordParametersError: If any validation fails, with a dictionary of errors.
        """
        errors = {}
        if self.d_args["metalcoord_exe"]:
            if os.path.exists(self.d_args["metalcoord_exe"]):
                logger.info("use explicit MetalCoord executable at %s", self.d_args["metalcoord_exe"])
            else:
                errors["metalcoord_exe"] = f"explicit MetalCoord executable not found at {self.d_args['metalcoord_exe']}"
        else:
            # if not explicitly provided, try to find MetalCoord executable from CCP4 bin/ folder using CCP4 environment variable
            ccp4_dir = os.getenv("CCP4", default=None)
            if ccp4_dir:
                metalcoord_exe = os.path.join(ccp4_dir, "bin", "metalCoord")
                if os.path.exists(metalcoord_exe):
                    self.d_args["metalcoord_exe"] = metalcoord_exe
                    logger.info("use CCP4 MetalCoord executable at %s", metalcoord_exe)
                else:
                    errors["metalcoord_exe"] = f"CCP4 MetalCoord executable not found in {metalcoord_exe}"
            else:
                errors["metalcoord_exe"] = "explicity MetalCoord excecutable not provided, and cannot find CCP4 MetalCoord, Env var 'CCP4' is missing"

        if self.d_args["pdb"]:
            if os.path.exists(self.d_args["pdb"]):
                logger.info("run on PDB file found at %s", self.d_args["pdb"])
            elif len(self.d_args["pdb"]) in (4, 12) and self.d_args["pdb"].isalnum():
                logger.info("run on PDB ID provided: %s", self.d_args["pdb"])
            else:
                errors["pdb"] = f"invalid PDB reference: {self.d_args['pdb']}, must be a valid PDB ID or an existing PDB/mmCIF file"

        if "ligand" in self.d_args and self.d_args["ligand"]:
            if self.d_args["ligand"] and self.d_args["ligand"].isalnum() and len(self.d_args["ligand"]) in (1,2,3,5):
                logger.info("ligand code provided: %s", self.d_args["ligand"])
            else:
                errors["ligand"] = f"invalid ligand code: {self.d_args['ligand']}, must be alphanumeric and 1, 2, 3, or 5 characters long"

        if "max_size" in self.d_args and self.d_args["max_size"]:
            if not isinstance(self.d_args["max_size"], int) or self.d_args["max_size"] <= 10:
                errors["max_size"] = f"invalid max_size: {self.d_args['max_size']}, must be a positive integer greater than 10"

        if "input" in self.d_args and self.d_args["input"]:
            if os.path.exists(self.d_args["input"]):
                logger.info("run on input cif file found at %s", self.d_args["input"])
            else:
                errors["input"] = f"failed to find input cif file at: {self.d_args['input']}"

        if "threshold" in self.d_args and self.d_args["threshold"]:
            if not isinstance(self.d_args["threshold"], (int, float)) or self.d_args["threshold"] < 0:
                errors["threshold"] = f"invalid threshold: {self.d_args['threshold']}, must be a non-negative number"                

        try:
            os.makedirs(self.d_args['workdir'], exist_ok=True)
        except Exception as e:
            errors["workdir"] = f"cannot create workdir: {self.d_args['workdir']} with error {e}"

        if errors:
            raise MetalCoordParametersError(errors)

    def setInputMode(self, mode):
        """
        Set the input mode for MetalCoord ("stats" or "update").

        :param mode: Mode to set ("stats" or "update").
        :type mode: str
        """
        self.mode = mode  # stats or update

    def run(self):
        """
        Run MetalCoord in the selected mode ("stats" or "update").

        :return: Output from MetalCoord if successful, otherwise None.
        :rtype: str or None
        """
        if self.mode == "stats":
            return self.runStats()
        if self.mode == "update":
            return self.runUpdate()

    def runStats(self):
        """
        Run MetalCoord in stats mode with arguments in d_args.

        Example command::

            MetalCoord stats --ligand 1PT --pdb 1PG9.cif --output metalcoord/1PT.json --max_size 100 --timeout 3600

        :return: stdout from MetalCoord if successful, otherwise None
        :rtype: str or None
        :raises MetalCoordCommandTimeoutError: If the command times out.
        :raises MetalCoordCommandExecutionError: If the command fails.
        """
        l_command = [self.d_args["metalcoord_exe"], "stats"]
        l_command.extend(["--ligand", self.d_args["ligand"].upper()])  # ensure ligand code is uppercase
        l_command.extend(["--pdb", self.d_args["pdb"]])
        l_command.extend(["--max_size", str(self.d_args["max_size"])])
        l_command.extend(["--threshold", str(self.d_args["threshold"])])
        fp_out = os.path.join(self.d_args["workdir"], f"{self.d_args['ligand']}.json")
        l_command.extend(["--output", fp_out])

        logger.info("to run MetalCoord stats mode full command:\n %s", ' '.join(l_command))
        try:
            cmd_stdout = run_command(l_command, self.d_args["timeout"])
            return cmd_stdout
        except MetalCommandTimeoutError as e:
            raise MetalCoordCommandTimeoutError(f"MetalCoord stats command timed out after {self.d_args['timeout']} seconds: {e}") from e
        except MetalCommandExecutionError as e:
            raise MetalCoordCommandExecutionError(f"MetalCoord stats command execution error: {e}") from e
        except Exception as e:
            raise MetalCoordCommandExecutionError(f"Unexpected error while running MetalCoord stats command: {e}") from e

    def runUpdate(self):
        """
        Run MetalCoord in update mode with arguments in d_args.

        Two options:
            - If a PDB model reference is provided, run update based on model.
            - If not, run update by most_common option.

        Example commands::

            MetalCoord update --input acedrg/1PT.cif --output metalcoord/1PT.cif --pdb 1PG9.cif
            MetalCoord update --input acedrg/1PT.cif --output metalcoord/1PT.cif --cif --cl most_common

        :return: stdout from MetalCoord if successful, otherwise None
        :rtype: str or None
        :raises MetalCoordCommandTimeoutError: If the command times out.
        :raises MetalCoordCommandExecutionError: If the command fails.
        """
        l_command = [self.d_args["metalcoord_exe"], "update"]
        l_command.extend(["--input", self.d_args["input"]])
        fp_out = os.path.join(self.d_args["workdir"], "metalcoord.cif")
        l_command.extend(["--output", fp_out])
        l_command.extend(["--threshold", str(self.d_args["threshold"])])
        if self.d_args["pdb"]:
            logger.info("to run MetalCoord update mode based on model of %s", self.d_args["pdb"])
            l_command.extend(["--pdb", self.d_args["pdb"]])
        else:
            logger.info("to run MetalCoord update mode by most_common option without model")
            l_command.extend(["--cif", "--cl", "most_common"])

        logger.info("to run MetalCoord update mode full command:\n %s", ' '.join(l_command))
        try:
            cmd_stdout = run_command(l_command, self.d_args["timeout"])
            return cmd_stdout
        except MetalCommandTimeoutError as e:
            raise MetalCoordCommandTimeoutError(f"MetalCoord update command timed out after {self.d_args['timeout']} seconds: {e}") from e
        except MetalCommandExecutionError as e:
            raise MetalCoordCommandExecutionError(f"MetalCoord update command execution error: {e}") from e
        except Exception as e:
            raise MetalCoordCommandExecutionError(f"Unexpected error while running MetalCoord update command: {e}") from e


# def main():
#     d_args = {"metalcoord_exe": "/Users/chenghua/Projects/RunMetalCoord/py-run_metalCoord/venv/bin/metalCoord",
#               "ligand": "0KA",
#               "pdb": "4DHV",
#               "workdir": "metalcoord",
#               "max_size": 100,
#               "threshold": 0.1,
#               "timeout": 3600,
#               }
#     try:
#         rMC = RunMetalCoord(d_args)
#     except Exception as e:
#         print(e)
#         sys.exit(1)
#     rMC.setInputMode("stats")
#     cmd_stdout = rMC.run()
#     print(cmd_stdout)


# if __name__ == "__main__":
#     main()
