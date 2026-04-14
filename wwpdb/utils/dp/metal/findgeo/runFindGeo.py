# Author:  Chenghua Shao
# Date:    2025-11-10
# Updates:

"""
Wrapper to run FindGeo with arguments similar to command line
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


class ValidateParametersError(Exception):
    def __init__(self, errors: dict):
        self.errors = errors
        super().__init__(str(errors))


class FindGeoCommandExecutionError(MetalCommandExecutionError):
    pass


class FindGeoCommandTimeoutError(MetalCommandTimeoutError):
    pass


class RunFindGeo:
    """Wrapper to run FindGeo with arguments similar to command line
    Example usage:
    d_args = {
        "excluded-donors": "C,H",
        "format": "cif",
        "input": "2HYV.cif",  # or None if using pdb
        "metal": None,
        "overwright": True,
        "pdb": None,          # or "2HYV" if using pdb
        "threshold": 2.8,
        "workdir": "./findgeo",
        "excluded-metals": Mg,Ca",
        "java-exe": "/path/to/java/executable",
        "findgeo-jar": "/path/to/FindGeo.jar"
        "timeout": 3600
    }
    rFG = RunFindGeo(d_args)
    rFG.run()
    """
    def __init__(self, d_args):
        self.d_args = d_args
        self.validateArgs()

    def validateArgs(self):
        """
        validate arguments in d_args
        required keys in d_args:
        excluded-donors, format, input, metal, overwright, pdb, threshold, workdir, excluded-metals, java-exe, findgeo-jar
        1. java-exe and findgeo-jar must exist as files
        2. format must be either 'cif' or 'pdb'
        3. if metal is specified, it must be a valid chemical symbol (1 or 2 letters)
        4. threshold must be a float between 1.0 and 4.0
        5. workdir must be a valid directory, create it if it does not exist
        6. either input or pdb must be specified, but not both
        7. if input is specified, it must exist as a file
        8. if pdb is specified, it must be a valid PDB code (4 alphanumeric characters)
        raise ValidateParametersError with a dictionary of errors if any validation fails
        """
        errors = {}
        if not os.path.exists(self.d_args['java-exe']):
            errors["java-exe"] = "java executable not found: %s" % self.d_args['java-exe']
        if not os.path.exists(self.d_args['findgeo-jar']):
            errors["findgeo-jar"] = "FindGeo jar file not found: %s" % self.d_args['findgeo-jar']
        if self.d_args['format'] not in ['cif', 'pdb']:
            errors["format"] = "invalid format: %s" % self.d_args['format']
        if self.d_args['metal'].lower() != 'all':
            if self.d_args['metal'] and len(self.d_args['metal']) > 2:
                errors["metal"] = "invalid metal symbol: %s" % self.d_args['metal']
        if self.d_args['excluded-metals'] != 'None':
            l_metal = self.d_args['excluded-metals'].split(',')
            for metal in l_metal:
                if len(metal) > 2:
                    errors["excluded-metals"] = "invalid excluded-metals symbol: %s" % self.d_args['excluded-metals']
        if self.d_args['threshold'] <= 1.0 or self.d_args['threshold'] >= 4.0:
            errors["threshold"] = "invalid threshold: %s" % self.d_args['threshold']
        try:
            os.makedirs(self.d_args['workdir'], exist_ok=True)
        except Exception as e:
            errors["workdir"] = "cannot create workdir: %s with error %s" % (self.d_args['workdir'], e)

        # validate input and pdb arguments and pick the non-empty one to use as input
        self.input = []
        if self.d_args['input'] and os.path.exists(self.d_args['input']):
            self.input = ["--input", self.d_args['input']]
        else:
            # try to check pdb id if input file is not valid
            if self.d_args['pdb']:
                if len(self.d_args['pdb']) not in [4, 12]:
                    errors["pdb"] = "invalid pdb id: %s" % self.d_args['pdb']
                self.input = ["--pdb", self.d_args['pdb'].lower()]
            else:
                errors["input"] = "must specify either input file or pdb id"
        if errors:
            raise ValidateParametersError(errors)

    def run(self):
        """
        run FindGeo with arguments in d_args and self.input as input file or pdb id
        example command with local input file:
            /usr/local/opt/openjdk/bin/java
            -jar FindGeo.jar
            --input 2HYV.cif
            --excluded-donors C,H
            --format cif
            --threshold 2.8
            --workdir findgeo
            --excluded-metals Mg,Ca
            --overwrite
            --timeout 3600
        example command with pdb id:
            /usr/local/opt/openjdk/bin/java
            -jar FindGeo.jar
            --pdb 2HYV
            --excluded-donors C,H
            --format cif
            --threshold 2.8
            --workdir findgeo
            --excluded-metals Mg,Ca
            --overwrite
            --timeout 3600

        :return: stdout from FindGeo if successful, otherwise None
        :rtype: str or None
        """
        l_command = [self.d_args["java-exe"], "-jar", self.d_args["findgeo-jar"]]
        l_command.extend(self.input)  # get input from either --input or --pdb
        for arg in ['format', 'threshold', 'workdir']:
            if self.d_args[arg]:
                l_command.extend([f'--{arg}', str(self.d_args[arg])])
        if self.d_args["metal"] and self.d_args["metal"].lower() != 'all':
            l_command.extend(['--metal', self.d_args["metal"]])
        if self.d_args['overwright']:
            l_command.append('--overwrite')
        if self.d_args['excluded-donors'] != "C,H":
            l_command.extend(['--excluded-donors', self.d_args["excluded-donors"]])
        if self.d_args['excluded-metals'] != "None":
            l_command.extend(['--excluded-metals', self.d_args["excluded-metals"]])

        logger.info("to run FindGeo command:\n %s", ' '.join(l_command))
        try:
            cmd_stdout = run_command(l_command, self.d_args['timeout'])
            return cmd_stdout
        except MetalCommandTimeoutError as e:
            raise FindGeoCommandTimeoutError(f"FindGeo command timed out after {self.d_args['timeout']} seconds: {e}") from e
        except MetalCommandExecutionError as e:
            raise FindGeoCommandExecutionError(f"FindGeo command execution error: {e}") from e
        except Exception as e:
            logger.exception("Unexpected error when running FindGeo: %s", e)
            raise FindGeoCommandExecutionError(f"Unexpected error when running FindGeo: {e}") from e
