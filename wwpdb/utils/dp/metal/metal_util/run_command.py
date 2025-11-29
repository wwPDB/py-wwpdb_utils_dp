# Author:  Chenghua Shao
# Date:    2025-11-10
# Updates:

"""
Utility functions to run metal commands with logging and error handling.
This module provides a function to execute shell commands, log their output in a separate log file
from the main application log, and handle errors by raising custom exceptions.
The command-specific log can be used for debugging the 3rd party metal tools such as MetalCoord and FindGeo.
"""

import subprocess
import logging
from datetime import datetime
import os

# logger = logging.getLogger(__name__)


class MetalCommandExecutionError(Exception):
    """Raised when a metal command execution fails, e.g. FindGeo and MetalCoord failure."""
    def __init__(self, cmd, code=None, stderr=None, stdout=None):
        self.cmd = cmd
        self.code = code
        self.stderr = stderr
        self.stdout = stdout
        message = f"Command {cmd} failed with exit code {code}"
        if stderr:
            message += f"\nStderr:\n{stderr.strip()}"
        super().__init__(message)


def setup_logger(name="command_runner", log_dir="metal_command_logs"):
    """Use this only when an existing logger is not used for run_command() function below
    Create or retrieve a configured logger.
    """
    os.makedirs(log_dir, exist_ok=True)
    logger = logging.getLogger(name)

    if not logger.handlers:  # prevent duplicate handlers if called multiple times
        logger.setLevel(logging.DEBUG)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = os.path.join(log_dir, f"cmd_{timestamp}.log")

        # File handler
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setLevel(logging.DEBUG)

        # Console handler, use for debugging
        ch = logging.StreamHandler()
        ch.setLevel(logging.WARNING)

        # Format
        fmt = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        fh.setFormatter(fmt)
        ch.setFormatter(fmt)

        logger.addHandler(fh)
        logger.addHandler(ch)

        logger.info(f"Logging to file: {log_path}")

    return logger


def run_command(cmd, logger=None):
    """Run a local command and raise CommandExecutionError on failure."""
    if logger is None:
        logger = setup_logger()

    logger.info(f"▶ Running command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        logger.debug(f"STDOUT:\n{result.stdout.strip()}")
        logger.info("✅ Command completed successfully.")
        return result.stdout

    except FileNotFoundError as e:
        logger.error(f"❌ Binary not found: {e}")
        raise MetalCommandExecutionError(cmd, None, stderr=str(e)) from e

    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Command failed (exit code {e.returncode})")
        if e.stdout:
            logger.debug(f"STDOUT:\n{e.stdout.strip()}")
        if e.stderr:
            logger.error(f"STDERR:\n{e.stderr.strip()}")
        raise MetalCommandExecutionError(e.cmd, e.returncode, e.stderr, e.stdout) from e

    except Exception as e:
        logger.exception("❌ Unexpected error during command execution")
        raise MetalCommandExecutionError(cmd, None, stderr=str(e)) from e


# def main():
#     logger = setup_logger(log_dir="log_test")
#     try:
#         output = run_command(["ls", "/nonexistent"], logger)
#     except MetalCommandExecutionError as e:
#         logger.error(f"MetalCommandExecutionError, Handled error: {e}")


# if __name__ == "__main__":
#     main()
