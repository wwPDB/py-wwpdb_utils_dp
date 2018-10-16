"""

File:    RcsbDpUtilExamples.py
Author:  jdw
Date:    5-Feb-2010
Version: 0.001

"""
import sys, unittest, os, os.path, traceback

from wwpdb.api.facade.ConfigInfo          import ConfigInfo
from wwpdb.utils.rcsb.DataFile            import DataFile
from wwodb.utils.rcsb.RcsbDpUtil          import RcsbDpUtil

def unitTest1():
    """ Simple test of import & export 
    """
    print "+++  Starting  unitTest1() +++"    
    dp = RcsbDpUtil(True)
    dp.imp("./data/1kip.cif")
    dp.op("cif2pdb")
    dp.exp("./data1/1kip.pdb.gz")
    dp.expLog("./data1/1kip.log.Z")    


def unitTest2():
    """ Test returning/exporting a list of results from cif2pdb-assembly
    """
#
    print "+++  Starting  unitTest2() +++"
    dp = RcsbDpUtil(True)
    dp.imp("./data/2qil.cif")
    dp.op("cif2pdb-assembly")
    iList=dp.getResultPathList()
    oList=[]
    for f in iList:
        (h,t)=os.path.split(f)
        fn = "./data1/" + t + ".gz"
        oList.append(fn)
    dp.expList(oList)
    dp.expLog("./data1/2qil.log.Z")    

def unitTest4():
    """ Create a load file and exchange file from an internal cif
    """
    print "+++  Starting  unitTest4() +++"    
    dp = RcsbDpUtil(True)
    dp.imp("./data/rcsb000500.cif.gz")
    dp.op("cif2cif-pdbx")
    dp.exp("./data1/1b90-load.cif")
    dp.expLog("./data1/1b90-load.log")
    dp.op("cif2pdbx")
    dp.exp("./data1/1b90.cif")
    dp.expLog("./data1/1b90.log")           

def unitTest3():
    """ Test the remediation pipeline  - 
    """
#
    print "+++  Starting  unitTest3() +++"
    dp = RcsbDpUtil(True)
    dp.imp("./data/2qil.cif")
    dp.op("switch-dna")
    dp.op("rename-atoms")
    dp.setRcsbAppsPathAlt()
    dp.op("cif2cif-remove")
    dp.op("cif2cif")
    istep=dp.saveResult()
    dp.exp("./data1/2qil-load.cif")
    dp.op("cif2pdb")
    istepPdb=dp.saveResult()
    dp.exp("./data1/2qil.pdb.gz")
    dp.useResult(istep)
    dp.op("cif2pdbx")
    istepPdbx=dp.saveResult()
    dp.exp("./data1/2qil-pdbx.cif.gz")
    dp.useResult(istepPdbx)
    dp.op("pdbx2xml")
    
    iList=dp.getResultPathList()
    oList=[]
    for f in iList:
        (h,t)=os.path.split(f)
        #print t
        if (str(t).endswith(".xml")):
            fn="./data1/2qil.xml.gz"
        elif (str(t).endswith(".xml-extatom")):
            fn="./data1/2qil-extatom.xml.gz"
        elif (str(t).endswith(".xml-noatom")):
            fn="./data1/2qil-noatom.xml.gz"            
        oList.append(fn)
    dp.expList(oList)
    #
    dp.useResult(istepPdbx)    
    dp.op("cif2pdb-assembly")
    iList=dp.getResultPathList()
    oList=[]
    for f in iList:
        (h,t)=os.path.split(f)
        fn = "./data1/" + t + ".gz"
        oList.append(fn)
    dp.expList(oList)

    dp.useResult(istepPdbx)    
    dp.op("pdbx2deriv")
    dp.exp("./data1/2qil-deriv.cif.gz")    

    dp.useResult(istepPdb)
    dp.op("pdb2dssp")
    dp.exp("./data1/2qil.dssp")
    
    dp.useResult(istepPdb)
    dp.op("pdb2stride")
    dp.exp("./data1/2qil.stride")            

    
    
    dp.expLogAll("./data1/2qil.log")    

