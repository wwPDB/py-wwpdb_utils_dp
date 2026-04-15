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
    from wwpdb.utils.dp.metal.metal_util.run_command import run_command, MetalCommandExecutionError, MetalCommandTimeoutError  # noqa: E402
else:
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "metal_util"))
    from run_command import run_command, MetalCommandExecutionError, MetalCommandTimeoutError  # noqa: E402

logger = logging.getLogger(__name__)


class AcedrgParametersError(Exception):
    def __init__(self, errors: dict):
        self.errors = errors
        super().__init__(str(errors))


class AcedrgCommandExecutionError(MetalCommandExecutionError):
    pass


class AcedrgCommandTimeoutError(MetalCommandTimeoutError):
    pass


class RunAcedrg:
    """Wrapper to run Acedrg with arguments
    """
    def __init__(self, d_args):
        self.d_args = d_args
        self.validateArgs()

    def validateArgs(self):
        """
        validate arguments in d_args
        raise AcedrgParametersError with a dictionary of errors if any validation fails
        """
        errors = {}
        if self.d_args["acedrg_exe"]:
            if os.path.exists(self.d_args["acedrg_exe"]):
                logger.info("use explicit Acedrg executable at %s", self.d_args["acedrg_exe"])
            else:
                errors["acedrg_exe"] = f"explicit Acedrg executable not found at {self.d_args['acedrg_exe']}"
        else:
            # if not explicitly provided, try to find Acedrg executable from CCP4 bin/ folder using CCP4 environment variable
            ccp4_dir = os.getenv("CCP4", default=None)
            if ccp4_dir:
                acedrg_exe = os.path.join(ccp4_dir, "bin", "acedrg")
                if os.path.exists(acedrg_exe):
                    self.d_args["acedrg_exe"] = acedrg_exe
                    logger.info("use CCP4 Acedrg executable at %s", acedrg_exe)
                else:
                    errors["acedrg_exe"] = f"CCP4 Acedrg executable not found in {acedrg_exe}"
            else:
                errors["acedrg_exe"] = "explicitly Acedrg executable not provided, and cannot find CCP4 Acedrg, Env var 'CCP4' is missing"

        if not os.path.exists(self.d_args["mmcif"]):
            errors["mmcif"] = f"failed to find mmCIF input file at: {self.d_args['mmcif']}"

        if errors:
            raise AcedrgParametersError(errors)

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
            cmd_stdout = run_command(l_command, self.d_args.get("timeout"))
            return cmd_stdout
        except MetalCommandTimeoutError as e:
            raise AcedrgCommandTimeoutError(f"Acedrg command timed out after {self.d_args.get('timeout')} seconds: {e}") from e
        except MetalCommandExecutionError as e:
            raise AcedrgCommandExecutionError(f"Acedrg command execution error: {e}") from e


# def main():
#     fp_in = "0KA.cif"
#     fp_out_root = "acedrg/acedrg"

#     d_args = {"acedrg_exe": None,
#               "mmcif": fp_in,
#               "out": fp_out_root,
#               }

#     try:
#         rAG = RunAcedrg(d_args)
#     except Exception as e:
#         print(e)
#         sys.exit(1)
#     cmd_stdout = rAG.run()
#     print(cmd_stdout)


# if __name__ == "__main__":
#     main()
