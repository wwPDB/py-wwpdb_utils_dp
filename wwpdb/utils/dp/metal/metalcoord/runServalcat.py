# Author:  Chenghua Shao
# Date:    2025-11-10
# Updates:

"""
Wrapper to run Servalcat with arguments
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


class RunServalcat:
    """Wrapper to run servalcat with arguments
    """
    def __init__(self, d_args):
        self.d_args = d_args
        if not self.d_args["servalcat_exe"]:
            logger.info("%s is called without explicit servalcat executable, to find in CCP4", self.__class__.__name__)
            ccp4_dir = os.getenv("CCP4", default=None)
            if not ccp4_dir:
                raise KeyError("Environment variable 'CCP4' not found")
            servalcat_exe = os.path.join(ccp4_dir, "bin", "servalcat")
            if not os.path.exists(servalcat_exe):
                raise FileNotFoundError("servalcat executable not found in CCP4 bin/ folder")
            self.d_args["servalcat_exe"] = servalcat_exe
            logger.info("use servalcat executable at %s", servalcat_exe)

    def run(self):
        """
        run servalcat with arguments in d_args
        example command:
            servalcat
            --update_dictionary 1PT.cif
            --output_prefix 1PT_servalcat  # name root of the output files
        :return: stdout from MetalCoord if successful, otherwise None
        :rtype: str or None
        """
        l_command = [self.d_args["servalcat_exe"], "refine_geom"]
        l_command.extend(["--update_dictionary", self.d_args["update_dictionary"]])
        l_command.extend(["--output_prefix", self.d_args["output_prefix"]])

        logger.info("to run servalcat full command:\n %s", ' '.join(l_command))
        try:
            cmd_stdout = run_command(l_command)
            logger.info("finished running servalcat on %s", self.d_args["update_dictionary"])
            return cmd_stdout
        except MetalCommandExecutionError as e:
            logger.error(f"MetalCommandExecutionError: {e}")
            return None


def main():
    fp_in = "metalcoord/metalcoord.cif"
    fp_out_root = "servalcat"

    d_args = {"servalcat_exe": None,
              "update_dictionary": fp_in,
              "output_prefix": fp_out_root,
              }

    try:
        rST = RunServalcat(d_args)
    except Exception as e:
        print(e)
        sys.exit(1)
    cmd_stdout = rST.run()
    print(cmd_stdout)


if __name__ == "__main__":
    main()
