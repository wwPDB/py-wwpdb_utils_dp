##
# File:    JobLoggingTests.py
#
##
"""
Hermetic tests for JobLogger
"""

import json
import logging
import os
import shutil
import tempfile
import unittest
import uuid
from typing import Any, Dict, List
from unittest import mock

if __package__ is None or __package__ == "":
    import sys
    from os import path

    sys.path.append(path.dirname(path.abspath(__file__)))
    from commonsetup import TESTOUTPUT  # pylint: disable=import-error,unused-import  # noqa: F401
else:
    from .commonsetup import TESTOUTPUT  # noqa: F401  # pylint: disable=unused-import

from wwpdb.utils.dp.JobLogging import JobLogger, RunEnvironment
from wwpdb.utils.dp.RunRemote import JobResult, JobStatus

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class JobLoggingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmpdir = tempfile.mkdtemp()
        self.__logpath = os.path.join(self.__tmpdir, "jobs.log")
        # Unique logger name per test to avoid cross-test interference
        self.__name = "joblogtest-%s" % uuid.uuid4().hex

    def tearDown(self) -> None:
        shutil.rmtree(self.__tmpdir, ignore_errors=True)

    def __readRecords(self) -> List[str]:
        with open(self.__logpath) as fh:
            return [line.rstrip("\n") for line in fh if line.strip()]

    @staticmethod
    def __payload(line: str) -> Dict[str, Any]:
        # Default format: "asctime - name - level - message"
        msg = line.split(" - ", 3)[3]
        ret: Dict[str, Any] = json.loads(msg)
        return ret

    def testLevels(self) -> None:
        """All levels are written as JSON records"""
        jl = JobLogger(self.__logpath, logger_name=self.__name)
        jl.start()
        jl.info("D_1", "op1", extra="a")
        jl.warning("D_2", "op2")
        jl.error("D_3", "op3", code=5)
        jl.debug("D_4", "op4")
        jl.stop()

        lines = self.__readRecords()
        self.assertEqual(len(lines), 4)
        self.assertIn(" - INFO - ", lines[0])
        self.assertIn(" - WARNING - ", lines[1])
        self.assertIn(" - ERROR - ", lines[2])
        self.assertIn(" - DEBUG - ", lines[3])
        for line in lines:
            self.assertIn(self.__name, line)
        self.assertEqual(self.__payload(lines[0]), {"dep_id": "D_1", "op": "op1", "extra": "a"})
        self.assertEqual(self.__payload(lines[2]), {"dep_id": "D_3", "op": "op3", "code": 5})

    def testStartIdempotentAndStopTwice(self) -> None:
        jl = JobLogger(self.__logpath, logger_name=self.__name)
        self.assertIs(jl.start(), jl)
        self.assertIs(jl.start(), jl)
        jl.info("D_1", "op")
        jl.stop()
        jl.stop()
        # After stop, messages are ignored
        jl.info("D_1", "ignored")
        self.assertEqual(len(self.__readRecords()), 1)

    def testCustomFormat(self) -> None:
        jl = JobLogger(self.__logpath, logger_name=self.__name, log_format="%(levelname)s|%(message)s")
        with jl.context() as cl:
            self.assertIs(cl, jl)
            cl.info("D_9", "fmt")
        lines = self.__readRecords()
        self.assertEqual(len(lines), 1)
        lvl, msg = lines[0].split("|", 1)
        self.assertEqual(lvl, "INFO")
        self.assertEqual(json.loads(msg), {"dep_id": "D_9", "op": "fmt"})

    def testCreatesLogDirectory(self) -> None:
        nested = os.path.join(self.__tmpdir, "a", "b", "jobs.log")
        jl = JobLogger(nested, logger_name=self.__name)
        self.assertTrue(os.path.isdir(os.path.dirname(nested)))
        with jl.context() as cl:
            cl.info("D_1", "op")
        self.assertTrue(os.path.exists(nested))

    def testJobResultFull(self) -> None:
        jr = JobResult(
            JobStatus.COMPLETED,
            job_id=1234,
            retries_used=1,
            total_time_seconds=10.12345,
            execution_time_seconds=8.556,
            queue_time_seconds=1.5,
            requested_memory_mb=2048,
            used_memory_mb=1000,
            cpu_count=4,
            cpu_time_seconds=30.333,
        )
        with JobLogger(self.__logpath, logger_name=self.__name).context() as jl:
            jl.job_result("D_1000", "someop", RunEnvironment.REMOTE, "wfhost1", jr)

        lines = self.__readRecords()
        self.assertEqual(len(lines), 1)
        self.assertEqual(
            self.__payload(lines[0]),
            {
                "dep_id": "D_1000",
                "op": "someop",
                "runenv": "REMOTE",
                "wfhost": "wfhost1",
                "job_id": 1234,
                "status": "COMPLETED",
                "retries": 1,
                "queue_time_s": 1.5,
                "exec_time_s": 8.56,
                "total_time_s": 10.12,
                "req_mem_mb": 2048,
                "used_mem_mb": 1000,
                "cpus": 4,
                "cpu_time_s": 30.33,
            },
        )

    def testJobResultMinimalNonEnumStatus(self) -> None:
        """None metrics are omitted; non-Enum status is stringified"""
        jr = JobResult(JobStatus.FAILED)
        jr.status = "weird"  # type: ignore[assignment]
        with JobLogger(self.__logpath, logger_name=self.__name).context() as jl:
            jl.job_result("D_1", "op", RunEnvironment.LOCAL, None, jr)

        payload = self.__payload(self.__readRecords()[0])
        self.assertEqual(
            payload,
            {"dep_id": "D_1", "op": "op", "runenv": "LOCAL", "wfhost": None, "job_id": None, "status": "weird", "retries": 0},
        )

    def testDisabledNotWritable(self) -> None:
        """If directory not writable, logger is disabled and calls are no-ops"""
        with mock.patch("wwpdb.utils.dp.JobLogging.os.access", return_value=False):
            jl = JobLogger(self.__logpath, logger_name=self.__name)
        jl.start()
        jl.info("D_1", "op")
        jl.warning("D_1", "op")
        jl.error("D_1", "op")
        jl.debug("D_1", "op")
        jl.job_result("D_1", "op", RunEnvironment.LOCAL, "h", JobResult(JobStatus.COMPLETED))
        jl.stop()
        self.assertFalse(os.path.exists(self.__logpath))

    def testDisabledMakedirsPermission(self) -> None:
        nested = os.path.join(self.__tmpdir, "nope", "jobs.log")
        with mock.patch("wwpdb.utils.dp.JobLogging.os.makedirs", side_effect=PermissionError("denied")):
            jl = JobLogger(nested, logger_name=self.__name)
        with jl.context() as cl:
            cl.info("D_1", "op")
        self.assertFalse(os.path.exists(os.path.dirname(nested)))

    def testRunEnvironment(self) -> None:
        self.assertEqual(RunEnvironment.LOCAL.value, "LOCAL")
        self.assertEqual(RunEnvironment.REMOTE.value, "REMOTE")


if __name__ == "__main__":
    unittest.main()
