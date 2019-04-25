# Common setup for tests as unittest runner loads files in any order

import sys
import os
import platform

HERE = os.path.abspath(os.path.dirname(__file__))
TOPDIR = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
TESTOUTPUT = os.path.join(HERE, 'test-output', platform.python_version())
if not os.path.exists(TESTOUTPUT):
    os.makedirs(TESTOUTPUT)
mockTopPath = os.path.join(TOPDIR, 'wwpdb', 'mock-data')
rwMockTopPath = os.path.join(TESTOUTPUT)

# Must create config file before importing ConfigInfo
from wwpdb.utils.testing.SiteConfigSetup  import SiteConfigSetup
from wwpdb.utils.testing.CreateRWTree import CreateRWTree

mockTopPath = os.path.join(TOPDIR, 'wwpdb', 'mock-data')
from wwpdb.utils.testing.SiteConfigSetup import SiteConfigSetup
SiteConfigSetup().setupEnvironment(TESTOUTPUT, mockTopPath)

from wwpdb.utils.config.ConfigInfo import ConfigInfo
cI = ConfigInfo()
packagedir = cI.get('SITE_PACKAGES_PATH')

if packagedir and os.path.exists(packagedir):
    toolsmissing = False
else:
    toolsmissing = True

dictlist = cI.get('SITE_PDBX_DICTIONARY_NAME_DICT')
if dictlist:
    dictsmissing = False
else:
    dictsmissing = True


class commonsetup(object):
    def __init__(self):
        pass
