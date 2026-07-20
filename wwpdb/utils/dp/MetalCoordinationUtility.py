##
# File: MetalCoordinationUtility.py
# Date: 28-Jan-2026
#
# Updates:
##
"""
Wrapper class for running FindGeo/MetalCoord APIs
"""

import json
import os
import sys

from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility


class MetalCoordinationUtility:
    """Wrapper class for running FindGeo/MetalCoord APIs"""

    def __init__(self, wrkPath="/scratch", siteId="DEV", verbose=False, log=sys.stderr):
        """ """
        self.__wrkPath = wrkPath
        self.__siteId = siteId
        self.__verbose = verbose
        self.__lfh = log
        #
        self.__hasTimeoutErrorFlag = False
        self.__modelCoordinatesFilePath = None
        self.__ccIdList = []
        self.__atomList = []
        # self.__ligandNumber = 0
        self.__FindGeoOutputFilePath = None
        self.__MetalCoordOutputFilePath = None
        self.__annotationFilePath = None

    def setModelCoordinatesFilePath(self, inputFilePath):
        """Set input model coordinates file path"""
        self.__modelCoordinatesFilePath = inputFilePath

    def setPolyAtomicMetalLigandIdList(self, ccIdList):
        """Set polyatomic metal ligand Ids list"""
        self.__ccIdList = ccIdList

    def setPolyAtomicMetalLigandInfoWithFilePath(self, inputFilePath):
        """Set polyatomic metal ligand residue information file path"""
        if (not inputFilePath) or (not os.access(inputFilePath, os.F_OK)):
            self.__lfh.write("+MetalCoordinationUtility %r file does not exist\n" % inputFilePath)
            return
        #
        lineList = self.__readFileAsLineList(inputFilePath)
        if len(lineList) == 0:
            self.__lfh.write("+MetalCoordinationUtility %r file does not contain metal-containing residue.\n" % inputFilePath)
            return
        #
        residueList = []
        for line in lineList:
            atomTupl = line.split(" ")
            self.__atomList.append(atomTupl)
            if atomTupl[1] not in self.__ccIdList:
                self.__ccIdList.append(atomTupl[1])
            #
            res = "_".join(atomTupl[:4])
            if res not in residueList:
                residueList.append(res)
            #
        #
        # self.__ligandNumber = len(residueList)

    def setFindGeoOutputFilePath(self, outputFilePath):
        """Set FindGeo software output json file path"""
        self.__FindGeoOutputFilePath = outputFilePath
        self.__lfh.write("+MetalCoordinationUtility FindGeoOutputFilePath=%s\n" % self.__FindGeoOutputFilePath)

    def setMetalCoordOutputFilePath(self, outputFilePath):
        """Set MetalCoord software output json file path"""
        self.__MetalCoordOutputFilePath = outputFilePath
        self.__lfh.write("+MetalCoordinationUtility MetalCoordOutputFilePath=%s\n" % self.__MetalCoordOutputFilePath)

    def setMetalAnnotationOutputFilePath(self, outputFilePath):
        """Set FindGeo/MetalCoord annotation output file path"""
        self.__annotationFilePath = outputFilePath
        self.__lfh.write("+MetalCoordinationUtility MetalAnnotationOutputFilePath=%s\n" % self.__annotationFilePath)

    def runUpdate(self, pdbxPath=None, csvPath=None, noTimeOut=False):
        """Run FindGeo/MetalCoord APIs and merging API"""
        if (pdbxPath is None) or (csvPath is None):
            return
        #
        ret = self.run(noTimeOutFlag=noTimeOut)
        if not ret:
            return
        #
        self.readJsonOutputFiles()
        #
        if (self.__annotationFilePath is None) or (not os.access(self.__annotationFilePath, os.F_OK)):
            return
        #
        dp = RcsbDpUtility(tmpPath=self.__wrkPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
        dp.imp(self.__modelCoordinatesFilePath)
        dp.addInput(name="metal_coordination_file_path", value=self.__annotationFilePath, type="file")
        if self.__hasTimeoutErrorFlag:
            dp.addInput(name="add_timeout_skip", value="add")
        #
        dp.op("annot-merge-metal-coordination")
        dp.expList(dstPathList=[pdbxPath, csvPath])
        dp.cleanup()

    def run(self, noTimeOutFlag=False, regularFilter=""):
        """Run FindGeo/MetalCoord APIs"""
        missingInfoFlag = False
        #
        if self.__modelCoordinatesFilePath is None:
            self.__lfh.write("+MetalCoordinationUtility.run()  - The input model coordinates file path is not defined.\n")
            missingInfoFlag = True
        #
        if len(self.__ccIdList) == 0:
            self.__lfh.write("+MetalCoordinationUtility.run()  - The polyatomic metal ligand Ids list is not defined.\n")
            missingInfoFlag = True
        #
        if self.__FindGeoOutputFilePath is None:
            self.__lfh.write("+MetalCoordinationUtility.run()  - The output file path for 'FindGeo' software is not defined.\n")
            missingInfoFlag = True
        #
        if self.__MetalCoordOutputFilePath is None:
            self.__lfh.write("+MetalCoordinationUtility.run()  - The output file path for 'MetalCoord' software is not defined.\n")
            missingInfoFlag = True
        #
        if missingInfoFlag:
            return False
        #
        for filePath in (self.__FindGeoOutputFilePath, self.__MetalCoordOutputFilePath):
            if os.access(filePath, os.F_OK):
                os.remove(filePath)
            #
        #
        for programTuple in (
            ("FindGeo", "metal-findgeo", self.__FindGeoOutputFilePath),
            ("MetalCoord", "metal-metalcoord-stats", self.__MetalCoordOutputFilePath),
        ):
            dp = RcsbDpUtility(tmpPath=self.__wrkPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.imp(self.__modelCoordinatesFilePath)
            if programTuple[0] == "MetalCoord":
                if len(self.__ccIdList) > 1:
                    dp.addInput(name="ligands", value=self.__ccIdList)
                else:
                    dp.addInput(name="ligands", value=self.__ccIdList[0])
                #
            #
            if noTimeOutFlag:
                dp.addInput(name="timeout", value=36000)
            #
            ret = dp.op(programTuple[1] + regularFilter)
            if ret == 0:
                dp.exp(programTuple[2])
                # Check if the output file exists
                if os.access(programTuple[2], os.F_OK):
                    with open(programTuple[2]) as DATA:
                        jsonObj = json.load(DATA)
                        # Clean up the temporary RcsbDpUtility session directory if calculation is successful.
                        if len(jsonObj) > 0:
                            dp.cleanup()
                        #
                    #
                #
            #
        #
        return True

    def readJsonOutputFiles(self):
        """Read the output json files from FindGeo/MetalCoord programs and write out the results to text file for merging into
        the model coordinate file.
        """
        if self.__annotationFilePath and os.access(self.__annotationFilePath, os.F_OK):
            os.remove(self.__annotationFilePath)
        #
        coordinationItem = (
            "chain",
            "residue",
            "sequence",
            "icode",
            "metal",
            "altloc",
            "metalElement",
            "coordination",
            "class",
            "tag",
            "class_generic",
            "class_abbr",
            "provenance",
            "coordination_number_allowed",
            "descriptor",
            "sphere",
        )
        #
        sphereItem = ("chain", "residue", "sequence", "icode", "name", "altloc", "element", "operator", "atom_place")
        #
        resultListMap = {}
        #
        try:
            for programTuple in (("FindGeo", self.__FindGeoOutputFilePath), ("MetalCoord", self.__MetalCoordOutputFilePath)):
                josnFilePath = programTuple[1]
                if not os.access(josnFilePath, os.F_OK):
                    continue
                #
                with open(josnFilePath) as DATA:
                    jsonObj = json.load(DATA)
                    if len(jsonObj) == 0:
                        self.__lfh.write("+MetalCoordinationUtility.readJsonOutputFiles() - Run %s failed: empty json output file.\n" % programTuple[0])
                    #
                    if "error" in jsonObj:
                        self.__lfh.write("+MetalCoordinationUtility.readJsonOutputFiles() - Run %s failed: %s\n" % (programTuple[0], jsonObj["error"]))
                        if jsonObj["error"] == "timeout":
                            self.__hasTimeoutErrorFlag = True
                        #
                    #
                    for coordObj in jsonObj:
                        dataList = []
                        tag_val = ""
                        for item in coordinationItem:
                            val = ""
                            if item == "sphere":
                                val = []
                                if item in coordObj:
                                    for sphereObj in coordObj[item]:
                                        sphereList = []
                                        for item1 in sphereItem:
                                            val1 = ""
                                            if item1 in sphereObj:
                                                val1 = str(sphereObj[item1])
                                                if (val1 == "?") or (val1 == "."):
                                                    val1 = ""
                                                #
                                                if (len(val1) < 2) and (item1 == "symmetry"):
                                                    val1 = ""
                                                #
                                            #
                                            if item1 == "atom_place":
                                                val1 = str(len(val) + 1)
                                            #
                                            sphereList.append(val1)
                                        #
                                        val.append(sphereList)
                                    #
                                #
                                dataList.append(val)
                            elif item == "provenance":
                                dataList.append(programTuple[0])
                            else:
                                val = ""
                                if item in coordObj:
                                    val = str(coordObj[item])
                                    if (val == "?") or (val == "."):
                                        val = ""
                                    #
                                    if val != "":
                                        if item == "tag":
                                            val = val.lower()
                                            tag_val = val
                                        elif item == "coordination_number_allowed":
                                            if (tag_val == "regular") and (val.upper() == "YES"):
                                                val = "Expected"
                                            else:
                                                val = "Unexpected"
                                            #
                                        #
                                    #
                                #
                                dataList.append(val)
                            #
                        #
                        if (dataList[8] == "") and (dataList[10] == "") and (dataList[11] == ""):
                            continue
                        #
                        key = "|".join(dataList[:6])
                        if key in resultListMap:
                            resultListMap[key].append(dataList)
                        else:
                            resultListMap[key] = [dataList]
                        #
                    #
                #
            #
        except Exception as e:  # noqa: BLE001
            self.__lfh.write("+MetalCoordinationUtility.readJsonOutputFiles() - %s\n" % str(e))
        #
        if len(resultListMap) == 0:
            self.__lfh.write("+MetalCoordinationUtility.readJsonOutputFiles() - Missing metal coordination annotation from FindGeo/MetalCoord programs.\n")
            return
        #
        if self.__annotationFilePath is None:
            self.__annotationFilePath = os.path.join(self.__wrkPath, "D_xxxxxxxxxx.annotation.txt")
        #
        coord = 0
        fth = open(self.__annotationFilePath, "w")
        for atomTupl in self.__atomList:
            if atomTupl[3] == "?":
                atomTupl[3] = ""
            #
            if atomTupl[5] == "?":
                atomTupl[5] = ""
            #
            key = "|".join(atomTupl)
            if key in resultListMap:
                for resultList in resultListMap[key]:
                    coord += 1
                    fth.write("coord_%d|%s\n" % (coord, "|".join(resultList[:-1])))
                    if len(resultList[-1]) > 0:
                        sphere = 0
                        for sphereList in resultList[-1]:
                            sphere += 1  # noqa: SIM113
                            fth.write("sphere_%d_%d|%s\n" % (coord, sphere, "|".join(sphereList)))
                        #
                    #
                #
            #
        #
        fth.close()

    def __readFileAsLineList(self, inputFilePath):
        """Read input file and return a list"""
        returnList = []
        if os.access(inputFilePath, os.F_OK):
            fin = open(inputFilePath)
            data = fin.read()
            fin.close()
            #
            for line in data.split("\n"):
                sline = line.strip()
                if not sline:
                    continue
                #
                returnList.append(sline)
            #
        #
        return returnList
