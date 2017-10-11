##
# File:    ArchiveIoSftp.py
# Author:  jdw
# Date:    10-Oct-2017
# Version: 0.001
#
# Updates:
#
##
"""
Archive data transfer operation utilities using SFTP protocol
        site_archive_host_name_1 = rdi2-drs.rdi2.rutgers.edu
        site_archive_host_username_1 = pdb
        site_archive_host_port_1 = 22
        site_archive_host_protocol_1 = sftp
        site_archive_host_key_file_path_1 = %(top_wwpdb_site_config_dir)s/secure/rdi2_rsa
        site_archive_host_key_file_type_1 = RSA
        #
"""

__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"
__version__ = "V0.001"

#
#
import sys
import os.path
import time
import unittest
import logging
logger = logging.getLogger(__name__)
#
from wwpdb.api.facade.ConfigInfo import ConfigInfo, getSiteId
from wwpdb.utils.rcsb.ArchiveIoSftp import ArchiveIoSftp


class ArchiveIoSftpTests(unittest.TestCase):

    def setUp(self):
        self.__lfh = sys.stderr
        self.__verbose = False
        #
        self.__cI = ConfigInfo(siteId=getSiteId(), verbose=self.__verbose, log=self.__lfh)
        self.__hostName = self.__cI.get('SITE_ARCHIVE_HOST_NAME_1')
        self.__userName = self.__cI.get('SITE_ARCHIVE_HOST_USERNAME_1')
        self.__hostPort = int(self.__cI.get('SITE_ARCHIVE_HOST_PORT_1'))
        self.__protocol = self.__cI.get('SITE_ARCHIVE_HOST_PROTOCOL_1')
        self.__rootPath = self.__cI.get('SITE_ARCHIVE_HOST_ROOT_PATH_1')
        self.__keyFilePath = self.__cI.get('SITE_ARCHIVE_HOST_KEY_FILE_PATH_1')
        self.__keyFileType = self.__cI.get('SITE_ARCHIVE_HOST_KEY_FILE_TYPE_1')
        #
        self.__testLocalFilePath = './data/TEST-FILE.DAT'
        self.__startTime = time.time()
        logger.debug("Starting %s at %s" % (self.id(),
                                            time.strftime("%Y %m %d %H:%M:%S", time.localtime())))

    def tearDown(self):
        endTime = time.time()
        logger.debug("Completed %s at %s (%.4f seconds)\n" % (self.id(),
                                                              time.strftime("%Y %m %d %H:%M:%S", time.localtime()),
                                                              endTime - self.__startTime))

    def testSftpConnect(self):
        """Test case - for connection-
        """

        try:
            aio = ArchiveIoSftp()
            ok = aio.connect(self.__hostName, self.__userName, self.__hostPort, keyFilePath=self.__keyFilePath, keyFileType=self.__keyFileType)
            aio.close()
            self.assertEqual(ok, True)
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()
#

    def testSftpStatOps(self):
        """Test case -  get directory list and stat details-
        """
        try:
            aio = ArchiveIoSftp()
            ok = aio.connect(self.__hostName, self.__userName, self.__hostPort, keyFilePath=self.__keyFilePath, keyFileType=self.__keyFileType)
            result = aio.listdir('.')
            logger.info("listdir: %r" % result)
            result = aio.stat('.')
            logger.info("stat: %r" % result)
            ok = aio.close()
            self.assertEqual(ok, True)
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testSftpDirOps(self):
        """Test case -  get directory list and stat details-
        """
        try:
            aio = ArchiveIoSftp()
            ok = aio.connect(self.__hostName, self.__userName, self.__hostPort, keyFilePath=self.__keyFilePath, keyFileType=self.__keyFileType)
            testPath = os.path.join(self.__rootPath, 'test')
            ok = aio.mkdir(testPath)
            result = aio.listdir(self.__rootPath)
            logger.info("listdir: %r" % result)
            result = aio.stat(testPath)
            logger.info("stat: %r" % result)
            ok = aio.rmdir(testPath)
            result = aio.listdir(self.__rootPath)
            logger.info("listdir after remove: %r" % result)
            ok = aio.close()
            self.assertEqual(ok, True)
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testSftpTransferOps(self):
        """Test case -  get directory list and stat details-
        """
        try:
            aio = ArchiveIoSftp()
            ok = aio.connect(self.__hostName, self.__userName, self.__hostPort, keyFilePath=self.__keyFilePath, keyFileType=self.__keyFileType)
            testDirPath = os.path.join(self.__rootPath, 'test')
            testFilePath1 = os.path.join(testDirPath, 'TEST-FILE-1.DAT')
            testFilePath2 = os.path.join(testDirPath, 'TEST-FILE-2.DAT')
            ok = aio.mkdir(testDirPath)
            ok = aio.put(self.__testLocalFilePath, testFilePath1)
            ok = aio.put(self.__testLocalFilePath, testFilePath2)
            #
            result = aio.listdir(testDirPath)
            logger.info("listdir: %r" % result)
            #ok = aio.remove(testFilePath1)
            #ok = aio.remove(testFilePath2)
            #
            result = aio.listdir(testDirPath)
            logger.info("listdir: %r" % result)
            #
            ok = aio.rmdir(testDirPath)
            result = aio.listdir(self.__rootPath)
            logger.info("listdir after remove: %r" % result)
            ok = aio.close()
            self.assertEqual(ok, True)
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()


def suiteSftpTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(ArchiveIoSftpTests("testSftpConnect"))
    suiteSelect.addTest(ArchiveIoSftpTests("testSftpStatOps"))
    suiteSelect.addTest(ArchiveIoSftpTests("testSftpDirOps"))
    suiteSelect.addTest(ArchiveIoSftpTests("testSftpTransferOps"))
    return suiteSelect

if __name__ == '__main__':
    if (True):
        mySuite = suiteSftpTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)
    #
