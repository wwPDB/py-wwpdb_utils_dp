##
# File:    RcsbDpUtilityEmTests.py
# Author:  J. Westbrook
# Date:    May 26,2014
# Version: 0.001
#
# Update:

##
"""
Test cases for EM map annotation tools --

"""

import json
import logging
import math
import os
import sys
import unittest

try:
    import matplotlib
    import matplotlib.pyplot as plt
    import pygal
    from pygal.style import LightColorizedStyle, LightGreenStyle
    skiptest = False
except ImportError:
    skiptest = True


if __package__ is None or __package__ == '':
    from os import path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT, TOPDIR, toolsmissing
else:
    from .commonsetup import TESTOUTPUT, TOPDIR, toolsmissing

from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId
from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility

if not skiptest:
    matplotlib.use('Agg')

skipnodisplay = True
if os.getenv('DISPLAY'):
    skipnodisplay = True

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class RcsbDpUtilityEmTests(unittest.TestCase):

    def setUp(self):
        self.__siteId = getSiteId(defaultSiteId=None)
        logger.info("\nTesting with site environment for:  %s\n" % self.__siteId)
        #
        self.__cI = ConfigInfo(self.__siteId)
        #
        self.__tmpPath = TESTOUTPUT
        self.__testFilePath = os.path.join(TOPDIR, 'wwpdb', 'mock-data', 'dp-utils')

        self.__testMapSpider = "testmap.spi"
        #
        # Brian's protein dna complex 3IYD
        self.__testMapEmd = 'emd_5127.map'
        self.__testMapNormal = self.__testMapEmd
        # XML header
        self.__testXMLHeader = 'emd_8137_v2.xml'

    def tearDown(self):
        pass

    @unittest.skipIf(toolsmissing, "Tools not available for testing")
    def testMapFix(self):
        """  Test mapfix utility
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            #
            inpPath = os.path.join(self.__testFilePath, self.__testMapNormal)
            of = self.__testMapNormal + "-fix.map"
            dp.imp(inpPath)
            dp.op("mapfix-big")
            dp.expLog("mapfix-big.log")
            dp.exp(of)
            # dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    @unittest.skipIf(skiptest, "Matplotlib")
    @unittest.skipIf(toolsmissing, "Tools not available for testing")
    @unittest.skipIf(skipnodisplay, "DISPLAY environment not set")
    def testReadMapHeader(self):
        """  Test read map header -- export JSON packet and plot density distribution -
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            dp.setDebugMode(flag=True)
            #
            inpPath = os.path.join(self.__testFilePath, self.__testMapNormal)
            of = self.__testMapNormal + "_map-header-data_P1.json"
            dp.imp(inpPath)
            dp.op("annot-read-map-header")
            dp.expLog("annot-read-map-header.log")
            dp.exp(of)
            # dp.cleanup()
            #
            mD = json.load(open(of, 'r'))
            logger.info("Map header keys: %r\n" % mD.keys())
            logger.info("Map header: %r\n" % mD.items())

            logger.info("Input  header keys: %r\n" % mD['input_header'].keys())
            logger.info("Output header keys: %r\n" % mD['output_header'].keys())
            #
            x = mD['input_histogram_categories']
            y = mD['input_histogram_values']
            logy = []
            for v in y:
                if float(v) <= 0.0:
                    logy.append(math.log10(.1))
                else:
                    logy.append(math.log10(float(v)))

            #
            width = float(x[-1] - x[0]) / float(len(x))
            # width = 2.0
            logger.info("Starting plot\n")
            plt.bar(x, y, width, color="r", log=True)
            logger.info("Loaded data\n")
            plt.title('Map density distribution')
            logger.info("set title\n")
            plt.ylabel('Voxels (log(10))')
            plt.xlabel('Density')
            logger.info("set labels\n")
            plotFileName = "map-density-plot-mpl.svg"
            plt.savefig(plotFileName, format="svg")
            logger.info("saved figure\n")

        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    @unittest.skipIf(skiptest, "Matplotlib")
    @unittest.skipIf(toolsmissing, "Tools not available for testing")
    def testReadMapHeaderPygal(self):
        """  Test read map header -- export JSON packet and plot density distribution -
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            #
            inpPath = os.path.join(self.__testFilePath, self.__testMapNormal)
            of = self.__testMapNormal + "_map-header-data_P1.json"
            dp.imp(inpPath)
            dp.op("annot-read-map-header")
            dp.expLog("annot-read-map-header.log")
            dp.exp(of)
            dp.cleanup()
            #
            mD = json.load(open(of, 'r'))
            logger.info("Map header keys: %r\n" % mD.keys())
            logger.info("Map header: %r\n" % mD.items())

            logger.info("Input  header keys: %r\n" % mD['input_header'].keys())
            logger.info("Output header keys: %r\n" % mD['output_header'].keys())
            #
            x = mD['input_histogram_categories']
            y = mD['input_histogram_values']
            logy = []
            for v in y:
                if float(v) <= 0.0:
                    logy.append(math.log10(.1))
                else:
                    logy.append(math.log10(float(v)))

            # width = float(x[-1] - x[0]) / float(len(x))
            # width = 2.0

            logger.info("Starting plot len x %d len y %d \n" % (len(x), len(logy)))
            nL = int(len(x) / 10)
            #
            if False:
                bar_chart = pygal.Bar(x_label_rotation=20, show_minor_x_labels=False, style=LightColorizedStyle)
            bar_chart = pygal.Bar(x_label_rotation=20, show_minor_x_labels=False, style=LightGreenStyle)
            bar_chart.title = 'Map density distribution'
            bar_chart.x_labels = map(str, [int(t) for t in x])
            bar_chart.x_labels_major = map(str, [int(t) for t in x[::nL]])

            bar_chart.add('Voxels (log(10)', logy)
            plotFileName = "map-density-plot-pygal.svg"
            bar_chart.render_to_file(plotFileName)

        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def myround(self, x, base=5):
        return int(base * round(float(x) / base))

    @unittest.skipIf(toolsmissing, "Tools not available for testing")
    def testEm2EmSpider(self):
        """  Test mapfix utility
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:

            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            #
            inpPath = os.path.join(self.__testFilePath, self.__testMapSpider)
            of = self.__testMapSpider + "-spider-cnv.map"
            dp.imp(inpPath)
            pixelSize = 2.54
            dp.addInput(name="pixel-spacing-x", value=pixelSize)
            dp.addInput(name="pixel-spacing-y", value=pixelSize)
            dp.addInput(name="pixel-spacing-z", value=pixelSize)
            dp.op("em2em-spider")
            dp.expLog("em2em-spider.log")
            dp.exp(of)
            # dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    @unittest.skipIf(toolsmissing, "Tools not available for testing")
    def testXmlHeaderCheck(self):
        """  Test xmllint
        """
        logger.info("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:

            dp = RcsbDpUtility(tmpPath=self.__tmpPath, siteId=self.__siteId, verbose=True)
            #
            # dp.setDebugMode()
            inpPath = os.path.join(self.__testFilePath, self.__testXMLHeader)
            # of = self.__testXMLHeader + ".check"
            dp.imp(inpPath)
            dp.op("xml-header-check")
            dp.expLog("xml-header-check.log")
            # dp.cleanup()
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()


def suiteAnnotEmTests():
    suiteSelect = unittest.TestSuite()
    # suiteSelect.addTest(RcsbDpUtilityEmTests("testReadMapHeader"))
    suiteSelect.addTest(RcsbDpUtilityEmTests("testXmlHeaderCheck"))
    # suiteSelect.addTest(RcsbDpUtilityEmTests("testReadMapHeaderPygal"))
    # suiteSelect.addTest(RcsbDpUtilityEmTests("testMapFix"))
    # suiteSelect.addTest(RcsbDpUtilityEmTests("testEm2EmSpider"))
    return suiteSelect


if __name__ == '__main__':
    # Run all tests --
    # unittest.main()
    #
    doAll = False
    if (doAll):

        mySuite = suiteAnnotEmTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)

    else:
        pass

    mySuite = suiteAnnotEmTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)
