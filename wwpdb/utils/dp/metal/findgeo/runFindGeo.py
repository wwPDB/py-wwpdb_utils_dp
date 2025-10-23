import argparse
import logging
import os
import subprocess
import sys

logger = logging.getLogger(__name__)

class RunFindGeo:
    """Wrapper to run FindGeo with arguments similar to command line
    Example usage:
    d_args = {
        "excluded_donors": "C,H",
        "format": "cif",
        "input": "2HYV.cif",  # or None if using pdb
        "metal": None,
        "overwright": True,
        "pdb": None,          # or "2HYV" if using pdb
        "threshold": 2.8,
        "workdir": "./findgeo",
        "java_exe": "/path/to/java/executable",
        "findgeo_jar": "/path/to/FindGeo.jar"
    }
    rFG = RunFindGeo(d_args)
    rFG.run()
    """
    def __init__(self, d_args):
        """d_args should contain all parameters listed in the docstring of main()"""
        self.d_args = d_args
        if not self.validateArgs():
            logger.error("invalid arguments")
            sys.exit(1)

    def validateArgs(self):
        """
        validate arguments in d_args
        required keys in d_args:
        excluded_donors, format, input, metal, overwright, pdb, threshold, workdir, java_exe, findgeo_jar
        1. java_exe and findgeo_jar must exist as files
        2. format must be either 'cif' or 'pdb'
        3. if metal is specified, it must be a valid chemical symbol (1 or 2 letters)
        4. threshold must be a float between 1.0 and 4.0
        5. workdir must be a valid directory, create it if it does not exist
        6. either input or pdb must be specified, but not both
        7. if input is specified, it must exist as a file
        8. if pdb is specified, it must be a valid PDB code (4 alphanumeric characters)
        Return True if all validations pass, otherwise False

        :return: True if all validations pass, otherwise False
        :rtype: bool
        """
        if not os.path.exists(self.d_args['java_exe']):
            logger.error("java executable not found: %s", self.d_args['java_exe'])
            return False
        if not os.path.exists(self.d_args['findgeo_jar']):
            logger.error("FindGeo jar file not found: %s", self.d_args['findgeo_jar'])
            return False
        if self.d_args['format'] not in ['cif', 'pdb']:
            logger.error("invalid format: %s", self.d_args['format'])
            return False
        if self.d_args['metal'] and len(self.d_args['metal']) > 2:
            logger.error("invalid metal symbol: %s", self.d_args['metal'])
            return False
        if self.d_args['threshold'] <= 1.0 or self.d_args['threshold'] >= 4.0:
            logger.error("invalid threshold: %s", self.d_args['threshold'])
            return False
        if not os.path.exists(self.d_args['workdir']):
            try:
                os.makedirs(self.d_args['workdir'])
            except Exception as e:
                logger.error("cannot create workdir: %s", self.d_args['workdir'])
                return False

        # validate input and pdb arguments and pick the non-empty one to use as input
        self.input = []
        if self.d_args['input']:
            if not os.path.exists(self.d_args['input']):
                logger.error("input file not found: %s", self.d_args['input'])
                return False
            if self.d_args['pdb']:
                logger.error("cannot specify both input file and pdb id")
                return False
            logger.info("using input file: %s", self.d_args['input'])
            self.input = ["--input", self.d_args['input']]
        elif self.d_args['pdb']:
            if len(self.d_args['pdb']) not in [4,12]:
                logger.error("invalid pdb id: %s", self.d_args['pdb'])
                return False
            logger.info("using pdb id: %s", self.d_args['pdb'])
            self.input = ["--pdb", self.d_args['pdb'].lower()]
        else:
            logger.error("must specify either input file or pdb id")
            return False
        
        return True

    def run(self):
        """
        run FindGeo with arguments in d_args and self.input as input file or pdb id
        example command with local input file:
            /usr/local/opt/openjdk/bin/java
            -jar /Users/chenghua/Projects/RunFindGeo/py-run_findgeo/packages/FindGeo/FindGeo-1.1.jar
            --input 2HYV.cif
            --excluded_donors C,H 
            --format cif 
            --threshold 2.8 
            --workdir findgeo 
            --overwrite
        example command with pdb id:
            /usr/local/opt/openjdk/bin/java
            -jar /Users/chenghua/Projects/RunFindGeo/py-run_findgeo
            /packages/FindGeo/FindGeo-1.1.jar
            --pdb 2HYV
            --excluded_donors C,H 
            --format cif 
            --threshold 2.8 
            --workdir findgeo 
            --overwrite
            
        :return: stdout from FindGeo if successful, otherwise None
        :rtype: str or None
        """
        l_command = [self.d_args["java_exe"], "-jar", self.d_args["findgeo_jar"]]
        l_command.extend(self.input)  # get input from either --input or --pdb
        for arg in ['excluded_donors', 'format', 'threshold', 'workdir', 'metal']:
            if self.d_args[arg]:
                l_command.extend([f'--{arg}', str(self.d_args[arg])])
        if self.d_args['overwright']:
            l_command.append('--overwrite')

        logger.info("to run FindGeo full command:\n %s", ' '.join(l_command))
        try:
            result = subprocess.run(l_command, capture_output=True, text=True, check=True)
            if result.returncode == 0:
                logger.info("succeeded in running FindGeo on %s", self.input)
                return result.stdout
            else:
                logger.error("failed to run FindGeo on %s with returncode %s", self.input, result.returncode)
                return None
        except Exception as e:
            logger.exception("failed to run FindGeo on %s with exception", self.input)
            return None
