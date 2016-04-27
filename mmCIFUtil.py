"""
File:    mmCIFUtil.py
Author:  Zukang Feng
Update:  21-August-2012
Version: 001  Initial version

"""

__author__  = "Zukang Feng"
__email__   = "zfeng@rcsb.rutgers.edu"
__version__ = "V0.001"

import sys

from pdbx_v2.reader.PdbxContainers     import *
from pdbx_v2.reader.PdbxReader         import PdbxReader
from pdbx_v2.writer.PdbxWriter         import PdbxWriter

class mmCIFUtil:
    """Using pdbx mmCIF utility to parse mmCIF file
    """
    def __init__(self, verbose=False, log=sys.stderr, filePath=None):
        self.__verbose   = verbose
        self.__lfh       = log
        self.__filePath  = filePath
        self.__dataList  = []
        self.__container = None
        self.__blockID   = None
        self.__read()
        #

    def __read(self):
        try:
            ifh = open(self.__filePath, 'r')
            pRd = PdbxReader(ifh)
            pRd.read(self.__dataList)
            ifh.close()
            if self.__dataList:
                self.__container = self.__dataList[0]
                self.__blockID = self.__container.getName()
        except:
            self.__lfh.write("Read %s failed.\n" % self.__filePath)
        #

    def GetBlockID(self):
        return self.__blockID
        #

    def GetValue(self, catName):
        """Get category values based on category name 'catName'. The results are stored
           in a list of dictionaries with item name as key
        """
        dList = [] 
        if not self.__container:
            return dList
        #
        catObj = self.__container.getObj(catName)
        if not catObj:
            return dList
        #
        # Get column name index
        #
        itNameList = catObj.getItemNameList()
        #
        rowList = catObj.getRowList()
        for row in rowList:
            tD = {}
            for idxIt, itName in enumerate(itNameList):
                if row[idxIt] != '?' and row[idxIt] != '.':
                    tlist = itName.split('.')
                    tD[tlist[1]] = row[idxIt]
            #
            if tD:
                dList.append(tD)
        #
        return dList
        #

    def GetSingleValue(self, catName, itemName):
        """Get the first value of item name 'itemName' from 'itemName' item in 'catName' category.
        """
        text = ''
        dlist = self.GetValue(catName)
        if dlist:
            if dlist[0].has_key(itemName):
                text = dlist[0][itemName]
        return text
        #

    def UpdateSingleRowValue(self, catName, itemName, row, value):
        """Update value in single row
        """  
        catObj = self.__container.getObj(catName)
        if not catObj:
            return
        #
        catObj.setValue(value, itemName, row)

    def UpdateMultipleRowsValue(self, catName, itemName, value):
        """Update value in multiple rows
        """  
        catObj = self.__container.getObj(catName)
        if not catObj:
            return
        #
        rowNo = catObj.getRowCount()
        for row in xrange(0, rowNo):
            catObj.setValue(value, itemName, row)
        #

    def WriteCif(self, outputFilePath=None):
        """Write out cif file
        """
        if not outputFilePath:
            return
        #
        ofh = open(outputFilePath, 'w')
        pdbxW = PdbxWriter(ofh)
        pdbxW.write(self.__dataList)
        ofh.close()
