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

class MetalCommandExecutionError(Exception):
    """
    Raised when a metal command execution fails, e.g. FindGeo and MetalCoord failure.

    :param cmd: The command that was executed.
    :type cmd: list or str
    :param code: The exit code returned by the command (if any).
    :type code: int or None
    :param stderr: The standard error output from the command (if any).
    :type stderr: str or None
    :param stdout: The standard output from the command (if any).
    :type stdout: str or None
    """
    def __init__(self, cmd, code=None, stderr=None, stdout=None):
        self.cmd = cmd
        self.code = code
        self.stderr = stderr
        self.stdout = stdout
        message = f"Command {cmd} failed with exit code {code}"
        if stderr:
            message += f"\nStderr:\n{stderr.strip()}"
        super().__init__(message)


class MetalCommandTimeoutError(MetalCommandExecutionError):
    """
    Raised when a metal command execution times out.
    """
    pass


def setup_logger(name="cmd", log_dir="metal_command_logs", b_debug=True):
    """
    Create or retrieve a configured logger for command execution.

    Use this only when an existing logger is not used for run_command().

    :param name: Name of the logger.
    :type name: str
    :param log_dir: Directory to store log files.
    :type log_dir: str
    :param b_debug: Whether to set debug level logging.
    :type b_debug: bool
    :return: Configured logger instance.
    :rtype: logging.Logger
    """
    os.makedirs(log_dir, exist_ok=True)
    logger = logging.getLogger(name)

    if not logger.handlers:  # prevent duplicate handlers if called multiple times
        logger.setLevel(logging.DEBUG)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = os.path.join(log_dir, f"{name}_{timestamp}.log")

        # File handler
        fh = logging.FileHandler(log_path, encoding="utf-8")
        if b_debug:
            fh.setLevel(logging.DEBUG)
        else:
            fh.setLevel(logging.INFO)

        # Console handler, use for debugging
        ch = logging.StreamHandler()
        ch.setLevel(logging.WARNING)

        # Format
        fmt = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s-%(module)s-%(funcName)s-%(lineno)d: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        fh.setFormatter(fmt)
        ch.setFormatter(fmt)

        logger.addHandler(fh)
        logger.addHandler(ch)

        logger.info(f"Logging to file: {log_path}")

    return logger


def run_command(cmd, timeout_sec, logger=None):
    """
    Run a local command and raise MetalCommandExecutionError on failure.

    :param cmd: The command to execute as a list of arguments.
    :type cmd: list
    :param timeout_sec: Timeout in seconds for the command.
    :type timeout_sec: int
    :param logger: Logger instance to use for logging (optional).
    :type logger: logging.Logger or None
    :return: The standard output from the command if successful.
    :rtype: str
    :raises MetalCommandExecutionError: If the command fails.
    :raises MetalCommandTimeoutError: If the command times out.
    """
    if logger is None:
        logger = setup_logger()

    logger.info(f"▶ Running command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout_sec
        )
        logger.debug(f"STDOUT:\n{result.stdout.strip()}")
        logger.info("✅ Command completed successfully.")

        return result.stdout

    except FileNotFoundError as e:  # binary command not found
        logger.error(f"❌ Binary not found: {e}")
        raise MetalCommandExecutionError(cmd, None, stderr=str(e)) from e

    except subprocess.CalledProcessError as e:  # command returned non-zero exit code, under check=True setting
        logger.error(f"❌ Command failed (exit code {e.returncode})")
        if e.stdout:
            logger.debug(f"STDOUT:\n{e.stdout.strip()}")
        if e.stderr:
            logger.error(f"STDERR:\n{e.stderr.strip()}")
        raise MetalCommandExecutionError(e.cmd, e.returncode, e.stderr, e.stdout) from e

    except subprocess.TimeoutExpired as e:
        logger.error(f"❌ Command timed out after {timeout_sec} seconds")
        if e.stdout:
            logger.debug(f"STDOUT before timeout:\n{e.stdout.strip()}")
        if e.stderr:
            logger.error(f"STDERR before timeout:\n{e.stderr.strip()}")
        raise MetalCommandTimeoutError(e.cmd, None, stderr="Command timed out") from e

    except Exception as e:  # catch any other exceptions, since this run is self-cotained and logged by itself
        logger.exception("❌ Unexpected error during command execution")
        raise MetalCommandExecutionError(cmd, None, stderr=str(e)) from e


# def main():
#     logger = setup_logger(log_dir="log_test")
#     try:
#         output = run_command(["ls"], 3600, logger)  # success
#         # output = run_command(["ls", "/nonexistent"], 3600, logger)  # expected to fail with non-zero exit code, but should be handled and logged by run_command
#         # output = run_command(["lss"], 3600, logger)  # expected to fail with binary not found, but should be handled and logged by run_command
#         # output = run_command(["sleep", "5"], 1, logger)  # expected to fail with timeout, but should be handled and logged by run_command
#     except MetalCommandTimeoutError as e:
#         logger.error(f"MetalCommandTimeoutError, Handled error: {e}")
#     except MetalCommandExecutionError as e:
#         logger.error(f"MetalCommandExecutionError, Handled error: {e}")


# if __name__ == "__main__":
#     main()
