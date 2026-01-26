"""
Job execution and metrics logging module.

Provides safe multi-process logging with time-based rotation (30 days).
Integrates with RemoteJobResult to log job execution metrics.

Features:
- Queue-based handler for multi-process safety
- Time-based rotation (every 30 days at midnight)
- Structured logging of RemoteJobResult metrics
- Standard library only (no external dependencies)
"""

import json
import logging
import logging.handlers
import os
from datetime import datetime, timedelta
from queue import Queue
from threading import Thread
from contextlib import contextmanager
from typing import Optional
from enum import Enum

class RunEnvironment(Enum):
    LOCAL = "LOCAL"
    REMOTE = "REMOTE"


class JobLogger:
    """
    Thread-safe logger for job execution and metrics.
    
    Uses QueueHandler with QueueListener to safely handle concurrent
    writes from multiple processes to a single log file with 30-day
    time-based rotation.
    """

    def __init__(
        self,
        log_file_path: str,
        logger_name: str = "job_execution",
        log_format: Optional[str] = None,
    ):
        """
        Initialize the job logger.

        Args:
            log_file_path: Path where log file will be written
            logger_name: Name for the logger (appears in log records)
            log_format: Custom log format string. If None, uses default.
        """
        self.log_file_path = log_file_path
        self.logger_name = logger_name
        self._queue: Optional[Queue] = None
        self._listener: Optional[logging.handlers.QueueListener] = None
        self._logger: Optional[logging.Logger] = None

        # Ensure log directory exists
        log_dir = os.path.dirname(os.path.abspath(log_file_path))
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        # Default format includes timestamp, level, and message
        if log_format is None:
            log_format = (
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        self._log_format = log_format
        self._formatter = logging.Formatter(log_format)

    def _setup_listener(self) -> None:
        """Set up the queue-based logger with time-based rotation."""
        self._queue = Queue(-1)  # Unlimited queue size
        
        # Create handler with 30-day time-based rotation
        # when='midnight' rotates at midnight, interval=30 means every 30 days
        handler = logging.handlers.TimedRotatingFileHandler(
            self.log_file_path,
            when="midnight",
            interval=30,
            backupCount=12,  # Keep ~1 year of backups
        )
        handler.setFormatter(self._formatter)

        # Create queue listener that writes to the handler
        self._listener = logging.handlers.QueueListener(
            self._queue, handler, respect_handler_level=True
        )
        self._listener.start()

    def _setup_logger(self) -> logging.Logger:
        """Set up the logger with queue handler."""
        logger = logging.getLogger(self.logger_name)
        logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers to avoid duplicates
        logger.handlers.clear()

        # Create queue handler (all records go to queue, not directly to file)
        queue_handler = logging.handlers.QueueHandler(self._queue)
        queue_handler.setLevel(logging.DEBUG)
        logger.addHandler(queue_handler)

        return logger

    def start(self) -> "JobLogger":
        """
        Start the logger with listener thread.

        Returns:
            self for context manager pattern
        """
        if self._listener is None:
            self._setup_listener()
        
        if self._logger is None:
            self._logger = self._setup_logger()

        return self

    def stop(self) -> None:
        """Stop the listener thread and close handlers."""
        if self._listener:
            self._listener.stop()
            self._listener = None
        
        if self._logger:
            for handler in self._logger.handlers[:]:
                self._logger.removeHandler(handler)
                handler.close()
            self._logger = None

    def info(self, dep_id: str, op: str, **kwargs) -> None:
        """Log an info level message."""
        if self._logger:
            self._logger.info(json.dumps({"dep_id": dep_id, "op": op, **kwargs}))

    def warning(self, dep_id: str, op: str, **kwargs) -> None:
        """Log a warning level message."""
        if self._logger:
            self._logger.warning(json.dumps({"dep_id": dep_id, "op": op, **kwargs}))

    def error(self, dep_id: str, op: str, **kwargs) -> None:
        """Log an error level message."""
        if self._logger:
            self._logger.error(json.dumps({"dep_id": dep_id, "op": op, **kwargs}))

    def debug(self, dep_id: str, op: str, **kwargs) -> None:
        """Log a debug level message."""
        if self._logger:
            self._logger.debug(json.dumps({"dep_id": dep_id, "op": op, **kwargs}))

    def job_result(self, dep_id, op, runenv: RunEnvironment, job_result) -> None:
        """
        Log a JobResult as a single JSON record for Loki ingestion.

        Args:
            job_result: JobResult instance from RunRemote.run()
        
        Output format:
            {"job_id": 12345, "status": "COMPLETED", "retries": 0, ...}
        """
        if not self._logger:
            return

        # Build metrics dict, only including non-None values
        metrics = {
            "dep_id": dep_id,
            "type": runenv.value,
            "op": op,
            "job_id": job_result.job_id,
            "status": job_result.status.value,
            "retries": job_result.retries_used,
        }
        
        # Timing metrics (seconds)
        if job_result.queue_time_seconds is not None:
            metrics["queue_time_s"] = round(job_result.queue_time_seconds, 2)
        if job_result.execution_time_seconds is not None:
            metrics["exec_time_s"] = round(job_result.execution_time_seconds, 2)
        if job_result.total_time_seconds is not None:
            metrics["total_time_s"] = round(job_result.total_time_seconds, 2)
        
        # Resource metrics
        if job_result.requested_memory_mb is not None:
            metrics["req_mem_mb"] = job_result.requested_memory_mb
        if job_result.used_memory_mb is not None:
            metrics["used_mem_mb"] = job_result.used_memory_mb
        if job_result.cpu_count is not None:
            metrics["cpus"] = job_result.cpu_count
        if job_result.cpu_time_seconds is not None:
            metrics["cpu_time_s"] = round(job_result.cpu_time_seconds, 2)
        
        # Log as JSON
        self._logger.info(json.dumps(metrics))

    @contextmanager
    def context(self):
        """
        Context manager for automatic start/stop of logger.

        Usage:
            with JobLogger(path).context() as logger:
                logger.info("dep_id", "op", message="Message")
        """
        try:
            self.start()
            yield self
        finally:
            self.stop()
