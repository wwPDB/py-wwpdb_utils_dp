##
# File:    PdbxChemShiftReport.py
# Author:  jdw
# Date:    11-Sep-2014
# Version: 0.001
#
# Updated:
#
##
"""  Read diagnostics in the chemical shift diagnostics report.

"""

__docformat__ = "restructuredtext en"
__author__    = "John Westbrook"
__email__     = "jwest@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.01"

import sys, traceback
import time, os, os.path  

from pdbx_v2.reader.PdbxReader        import PdbxReader
from pdbx_v2.reader.PdbxContainers    import *


class PdbxChemShiftReport(object):
    def __init__(self,inputPath,verbose=False,log=sys.stderr):
        self.__lfh=log
        self.__verbose=verbose
        self.__myContainerList=[]            
        self.__read(inputPath)

    def __read(self,inputPath): 
        """ Read status file 
        """
        try:
            self.__myContainerList=[]            
            ifh = open(inputPath, "r")
            pRd=PdbxReader(ifh)
            pRd.read(self.__myContainerList)
            ifh.close()            
            return True
        except:
            traceback.print_exc(file=self.__lfh)
            return False

    def getStatus(self):
        return self.__get('pdbx_shift_check','status')

    def getWarnings(self):
        return self.__get('pdbx_shift_check_warning_message','text')

    def getErrors(self):
        return self.__get('pdbx_shift_check_error_message','text')

    def __get(self,categoryName,attributeName):
        retVal=[]        
        try:
            c0=self.__myContainerList[0]
            #
            catObj=c0.getObj(categoryName)
            if catObj is None:
                return retVal
            nm,aList,rList=catObj.get()

            if attributeName in aList:
                idx=aList.index(attributeName)
                for r in rList:
                    retVal.append(str(r[idx]).strip())
        except:
            pass

        return retVal
        
if __name__ == '__main__':
    pass
