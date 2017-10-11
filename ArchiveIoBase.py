##
# File:    ArchiveIoBase.py
# Author:  jdw
# Date:    10-Oct-2017
# Version: 0.001
#
# Updates:
#
##
"""
Base class for archive data transfer operation utilities.

"""

__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"
__version__ = "V0.001"

#
#
import logging
logger = logging.getLogger(__name__)


class ArchiveIoBase(object):
    """ A base class for for archive data transfer operation utilities.

    """

    def __init__(self, *args, **kwargs):
        self._raiseExceptions = kwargs.get('raiseExceptions', False)

    def connect(self, hostName, userName, **kwargs):
        raise NotImplementedError("To be implemented in subclass")

    def mkdir(self, path, **kwargs):
        raise NotImplementedError("To be implemented in subclass")

    def stat(self, path):
        raise NotImplementedError("To be implemented in subclass")

    def put(self, localPath, remotePath):
        raise NotImplementedError("To be implemented in subclass")

    def get(self, remotePath, localPath):
        raise NotImplementedError("To be implemented in subclass")

    def listdir(self, path):
        raise NotImplementedError("To be implemented in subclass")

    def close(self):
        raise NotImplementedError("To be implemented in subclass")
