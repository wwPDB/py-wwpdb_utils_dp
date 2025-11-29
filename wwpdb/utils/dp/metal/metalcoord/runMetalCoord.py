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
    from wwpdb.utils.dp.metal.metal_util.run_command import MetalCommandExecutionError, run_command  # noqa: E402
else:
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "metal_util"))
    from run_command import MetalCommandExecutionError, run_command  # noqa: E402

logger = logging.getLogger(__name__)


class RunMetalCoord:
    """Wrapper to run MetalCoord with arguments similar to command line
    Example usage:
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
        self.d_args = d_args
        self.mode = None
        if not self.d_args["metalcoord_exe"]:
            logger.info("%s is called without explicit MetalCoord executable, to find in CCP4", self.__class__.__name__)
            ccp4_dir = os.getenv("CCP4", default=None)
            if not ccp4_dir:
                raise KeyError("Environment variable 'CCP4' not found")
            metalcoord_exe = os.path.join(ccp4_dir, "bin", "metalCoord")
            if not os.path.exists(metalcoord_exe):
                raise FileNotFoundError("MetalCoord executable not found in CCP4 bin/ folder")
            self.d_args["metalcoord_exe"] = metalcoord_exe
            logger.info("use MetalCoord executable at %s", metalcoord_exe)

    def setInputMode(self, mode):
        self.mode = mode  # stats or update

    def run(self):
        if self.mode == "stats":
            return self.runStats()
        if self.mode == "update":
            return self.runUpdate()

    def runStats(self):
        """
        run MetalCoord stats mode with arguments in d_args
        example command:
            MetalCoord stats
            --ligand 1PT
            --pdb 1PG9.cif  # accept both PDB ID and PDB/mmCIF file
            --output metalcoord/1PT.json
            --max_size 100
        :return: stdout from MetalCoord if successful, otherwise None
        :rtype: str or None
        """
        l_command = [self.d_args["metalcoord_exe"], "stats"]
        l_command.extend(["--ligand", self.d_args["ligand"].upper()])  # ensure ligand code is uppercase
        l_command.extend(["--pdb", self.d_args["pdb"]])
        l_command.extend(["--max_size", str(self.d_args["max_size"])])
        l_command.extend(["--threshold", str(self.d_args["threshold"])])
        fp_out = os.path.join(self.d_args["workdir"], f"{self.d_args['ligand']}.json")
        l_command.extend(["--output", fp_out])

        logger.info("to run MetalCoord full command:\n %s", ' '.join(l_command))
        try:
            cmd_stdout = run_command(l_command)
            logger.info("finished running MetalCoord stats mode on %s of %s", self.d_args["ligand"], self.d_args["pdb"])
            return cmd_stdout
        except MetalCommandExecutionError as e:
            logger.error(f"MetalCommandExecutionError: {e}")
            return None

    def runUpdate(self):
        """
        run MetalCoord stats mode with arguments in d_args, with two options to run:
        if a PDB model reference is provided, i.e. seld.d_args["pdb"] is not empty, run update based on model;
        if a PDB model reference is NOT provided, run update by most_common option.
        example commands:
        update based on a PDB model:
            MetalCoord update
            --input acedrg/1PT.cif
            --output metalcoord/1PT.cif
            --pdb 1PG9.cif
        update by the most_common option referring to geometry observed in the PDB archive
            MetalCoord update
            --input acedrg/1PT.cif
            --output metalcoord/1PT.cif
            --cif
            --cl most_common
        :return: stdout from MetalCoord if successful, otherwise None
        :rtype: str or None
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

        logger.info("to run MetalCoord full command:\n %s", ' '.join(l_command))
        try:
            cmd_stdout = run_command(l_command)
            logger.info("finished running MetalCoord update mode on %s by %s", self.d_args["input"], self.d_args["pdb"])
            return cmd_stdout
        except MetalCommandExecutionError as e:
            logger.error(f"MetalCommandExecutionError: {e}")
            return None


def main():
    d_args = {"metalcoord_exe": None,
              "ligand": "0KA",
              "pdb": "4DHV",
              "workdir": "metalcoord",
              "max_size": 100,
              "threshold": 0.1
              }
    try:
        rMC = RunMetalCoord(d_args)
    except Exception as e:
        print(e)
        sys.exit(1)
    rMC.setInputMode("stats")
    cmd_stdout = rMC.run()
    print(cmd_stdout)


if __name__ == "__main__":
    main()
