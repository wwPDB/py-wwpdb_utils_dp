# Author:  Chenghua Shao
# Date:    2025-11-10
# Updates:

"""
Wrapper to run Acedrg with arguments
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


class RunAcedrg:
    """Wrapper to run Acedrg with arguments
    """
    def __init__(self, d_args):
        self.d_args = d_args
        if not self.d_args["acedrg_exe"]:
            logger.info("%s is called without explicit Acedrg executable, to find in CCP4", self.__class__.__name__)
            ccp4_dir = os.getenv("CCP4", default=None)
            if not ccp4_dir:
                raise KeyError("Environment variable 'CCP4' not found")
            acedrg_exe = os.path.join(ccp4_dir, "bin", "acedrg")
            if not os.path.exists(acedrg_exe):
                raise FileNotFoundError("Acedrg executable not found in CCP4 bin/ folder")
            self.d_args["acedrg_exe"] = acedrg_exe
            logger.info("use Acedrg executable at %s", acedrg_exe)

    def run(self):
        """
        run Acedrg with arguments in d_args
        example command:
            Acedrg
            --mmcif 1PT.cif
            --out 1PT_acedrg  # name root of the output files
        :return: stdout from MetalCoord if successful, otherwise None
        :rtype: str or None
        """
        l_command = [self.d_args["acedrg_exe"]]
        l_command.extend(["--mmcif", self.d_args["mmcif"]])
        l_command.extend(["--out", self.d_args["out"]])

        logger.info("to run Acedrg full command:\n %s", ' '.join(l_command))
        try:
            cmd_stdout = run_command(l_command)
            logger.info("finished running Acedrg on %s", self.d_args["mmcif"])
            return cmd_stdout
        except MetalCommandExecutionError as e:
            logger.error(f"MetalCommandExecutionError: {e}")
            return None


def main():
    fp_in = "0KA.cif"
    fp_out_root = "acedrg/acedrg"

    d_args = {"acedrg_exe": None,
              "mmcif": fp_in,
              "out": fp_out_root,
              }

    try:
        rAG = RunAcedrg(d_args)
    except Exception as e:
        print(e)
        sys.exit(1)
    cmd_stdout = rAG.run()
    print(cmd_stdout)


if __name__ == "__main__":
    main()
