"""
Pretty print a nest structure of dictionaries and lists such as
a the object collection produced by the entryFactory.

File:    FormatOut.py
Author:  jdw
Date:    24-Mar-2006
Version: 0.001
Split off from utils.py and converted to a class with string buffer.

Update:  5-Feb-2010
         Add stream method -

"""
import sys

MAX_INDENT=100
SPACE=' '*MAX_INDENT

class FormatOut:
    """ 
    """
    def __init__(self):
        self.__buffer = []

    def writeStream(self,fObj):
        fObj.writelines(self.__buffer)
        
    def write(self,filename):
        fH = open(filename,'w')
        fH.writelines(self.__buffer)
        fH.close()
        
    def clear(self):
        self.__buffer=[]
        
    def indent(self,strIn,indent=0):
        if (indent > 0 and indent < MAX_INDENT): 
            self.__buffer.append("%s%s" % (SPACE[1:indent],strIn))
        else:
            self.__buffer.append(strIn)
        
    def autoFormat(self,name,thing,indent=0,indentIncr=3):
        """ Print utility for dictionaries of factory data.
        """
        inOt = str(type(thing)).lower()
        ind = indent + 0
        indInc = indentIncr
        if (inOt.find('str') > 0 or inOt.find('int') > 0 or inOt.find('unicode') > 0 or \
            inOt.find('float') > 0 or inOt.find('long') > 0 or \
            inOt.find('date') > 0 or inOt.find('time') > 0):
            if (len( str(thing)) > 0 ) :
                str1 = "%-20s = %s\n" % (name,str(thing))
                self.indent(str1,ind)
        elif (inOt.find('list') > 0 or inOt.find('tuple') > 0):
            if (len(thing) > 0):
                if (name != None and len(name) > 0):
                    self.indent("\n",ind)
                    str1 = "CONTENTS OF: %s\n" % name
                    self.indent(str1,ind)        
                iEl = 0
                for el in thing:
                    iEl += 1
                    lab = name + '[' + str(iEl) + ']'
                    self.autoFormat(lab,el,ind+indInc)
        elif (inOt.find('dict') > 0):
            if (len(thing) > 0):
                if (name != None and len(name) > 0):
                    self.indent("\n",ind)                                    
                    str1 = "CONTENTS OF: %s\n" % name
                    self.indent(str1,ind)                
                keys = thing.keys()
                keys.sort()
                for k in keys:
                    self.autoFormat(str(k),thing[k],ind+indInc)
        elif (inOt.find('module') > 0 or inOt.find('instance') > 0):
            if (name != None and len(name) > 0):
                self.indent("\n",ind)
                str1 = "CONTENTS OF: %s\n" % name
                self.indent(str1,ind)
            #
            # check if exists and is_callable..
            #
            thing.writeDetails(self,ind+indInc)
        elif (inOt.find('nonetype') > 0 ):
            pass
        else:
            self.indent("\nAUTOFORMAT: CANNOT PRINT %s TYPE %s\n" % (name, inOt),ind )

def unitTest1(fileName='formatOut.log'):

    list = ['L1','L2','L3','L4','L5']
    tuple = ('T1', 'T2', 'T3', 'T4', 'T5')
    dict = {}
    for i in range(1,10):
        t = ['D1',list,tuple]
        dict[i] = t
    
    out = FormatOut()
    out.autoFormat("unitTest1 results",dict,3,3)
    out.write(fileName)
    
    
if __name__ == '__main__':
    unitTest1('formatOut.log')
