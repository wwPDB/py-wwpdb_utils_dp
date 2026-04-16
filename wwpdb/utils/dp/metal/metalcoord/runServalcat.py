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
    from wwpdb.utils.dp.metal.metal_util.run_command import run_command, MetalCommandExecutionError, MetalCommandTimeoutError  # noqa: E402
else:
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "metal_util"))
    from run_command import run_command, MetalCommandExecutionError, MetalCommandTimeoutError  # noqa: E402

logger = logging.getLogger(__name__)

class ServalcatParametersError(Exception):
    """
    Raised when there is a parameter validation error for Servalcat.

    :param errors: Dictionary of parameter errors.
    :type errors: dict
    """
    def __init__(self, errors: dict):
        self.errors = errors
        super().__init__(str(errors))


class ServalcatCommandExecutionError(MetalCommandExecutionError):
    """
    Raised when Servalcat command execution fails.
    """
    pass


class ServalcatCommandTimeoutError(MetalCommandTimeoutError):
    """
    Raised when Servalcat command execution times out.
    """
    pass


class RunServalcat:
    """
    Wrapper to run Servalcat with arguments.
    """
    def __init__(self, d_args):
        """
        Initialize RunServalcat with arguments and validate them.

        :param d_args: Dictionary of arguments for running Servalcat.
        :type d_args: dict
        """
        self.d_args = d_args
        self.validateArgs()

    def validateArgs(self):
        """
        Validate arguments in d_args.

        :raises ServalcatParametersError: If any validation fails, with a dictionary of errors.
        """
        errors = {}
        if self.d_args["servalcat_exe"]:
            if os.path.exists(self.d_args["servalcat_exe"]):
                logger.info("use explicit Servalcat executable at %s", self.d_args["servalcat_exe"])
            else:
                errors["servalcat_exe"] = f"explicit Servalcat executable not found at {self.d_args['servalcat_exe']}"
        else:
            # if not explicitly provided, try to find Servalcat executable from CCP4 bin/ folder using CCP4 environment variable
            ccp4_dir = os.getenv("CCP4", default=None)
            if ccp4_dir:
                servalcat_exe = os.path.join(ccp4_dir, "bin", "servalcat")
                if os.path.exists(servalcat_exe):
                    self.d_args["servalcat_exe"] = servalcat_exe
                    logger.info("use CCP4 Servalcat executable at %s", servalcat_exe)
                else:
                    errors["servalcat_exe"] = f"CCP4 Servalcat executable not found in {servalcat_exe}"
            else:
                errors["servalcat_exe"] = "explicitly Servalcat executable not provided, and cannot find CCP4 Servalcat, Env var 'CCP4' is missing"

        if not os.path.exists(self.d_args["update_dictionary"]):
            errors["update_dictionary"] = f"failed to find update dictionary input file at: {self.d_args['update_dictionary']}"

        if errors:
            raise ServalcatParametersError(errors)

    def run(self):
        """
        Run Servalcat with arguments in d_args.

        Example command::

            servalcat refine_geom --update_dictionary 1PT.cif --output_prefix 1PT_servalcat

        :return: stdout from Servalcat if successful, otherwise None
        :rtype: str or None
        :raises ServalcatCommandTimeoutError: If the command times out.
        :raises ServalcatCommandExecutionError: If the command fails.
        """
        l_command = [self.d_args["servalcat_exe"], "refine_geom"]
        l_command.extend(["--update_dictionary", self.d_args["update_dictionary"]])
        l_command.extend(["--output_prefix", self.d_args["output_prefix"]])

        logger.info("to run servalcat full command:\n %s", ' '.join(l_command))
        try:
            cmd_stdout = run_command(l_command, self.d_args.get("timeout"))
            return cmd_stdout
        except MetalCommandTimeoutError as e:
            raise ServalcatCommandTimeoutError(f"Servalcat command timed out after {self.d_args.get('timeout')} seconds: {e}") from e
        except MetalCommandExecutionError as e:
            raise ServalcatCommandExecutionError(f"Servalcat command execution error: {e}") from e


# def main():
#     fp_in = "metalcoord/metalcoord.cif"
#     fp_out_root = "servalcat"

#     d_args = {"servalcat_exe": None,
#               "update_dictionary": fp_in,
#               "output_prefix": fp_out_root,
#               }

#     try:
#         rST = RunServalcat(d_args)
#     except Exception as e:
#         print(e)
#         sys.exit(1)
#     cmd_stdout = rST.run()
#     print(cmd_stdout)


# if __name__ == "__main__":
#     main()
