##
# File:    WebRequest.py
# Date:    18-Jan-2010  J. Westbrook
#
# Updated:
# 20-Apr-2010 Ported to seqmodule package
# 25-Jul-2010 Ported to ccmodule package
# 24-Aug-2010 Add dictionary update for content request object.
#
# 26-Feb-2012 jdw  add support location redirects in response object-
# 20-Feb-2013 jdw  This application neutral version moved to utils/rcsb.
#                  Make dictionary in ResponseContent inheritable.
##
"""
WebRequest provides containers and accessors for managing request parameter information.

This is an application neutral version shared by UI modules --

"""
__docformat__ = "restructuredtext en"
__author__    = "John Westbrook"
__email__     = "jwest@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.07"


import sys, os, traceback
from simplejson import loads, dumps

from wwpdb.utils.rcsb.SessionManager import SessionManager

class WebRequest(object):
    """ Base container and accessors for input and output parameters and control information. 
    """
    def __init__(self,paramDict={},verbose=False):
        self.__verbose=verbose
        #
        #  Input and storage model is dictionary of lists (e.g. dict[myKey] = [,,,])
        #  Single values are stored in the leading element of the list (e.g. dict[myKey][0])
        #
        self.__dict=paramDict
        

    def printIt(self,ofh=sys.stdout):
        try:
            ofh.write("\n--------------------------------------------:\n")                         
            ofh.write("\nWebRequest.printIt() Request Dictionary Contents:\n")             
            for k,vL in self.__dict.items():
                ofh.write("  Key: %s  value(s): " % k)
                for v in vL:
                    ofh.write(" %s " % v)
                ofh.write("\n")
            ofh.write("\n--------------------------------------------\n\n")                                         
        except:
            pass


    def dump(self,format='text'):
        oL=[]
        try:
            if (format == 'html'):
                oL.append('<pre>\n')
            oL.append("\n--------------------------------------------:\n")                         
            oL.append("\nWebRequest.dump() Request Dictionary Contents:\n")             
            for k,vL in self.__dict.items():
                oL.append("  Key: %s  value(s): " % k)
                for v in vL:
                    oL.append(" %r " % v)
                oL.append("\n")
            oL.append("\n--------------------------------------------\n\n")
            if (format == 'html'):
                oL.append('</pre>\n')
        except:
            pass
        
        return oL        

    def getJSON(self):
        return dumps(self.__dict)

    def setJSON(self,JSONString):
        self.__dict = loads(JSONString)
                    
    def getValue(self,myKey):
        return(self._getStringValue(myKey))

    def getValueList(self,myKey):
        return(self._getStringList(myKey))

    def getRawValue(self,myKey):
        return(self._getRawValue(myKey))
    
    #
    def setValue(self,myKey,aValue):
        self.__dict[myKey]=[aValue]

    def setValueList(self,myKey,valueList):
        self.__dict[myKey]=valueList        

    
    def exists(self,myKey):
        try:
            return self.__dict.has_key(myKey)
        except:
            return False

    #
    def _getRawValue(self,myKey):
        try:
            return self.__dict[myKey][0]
        except:
            return None
        
    def _getStringValue(self,myKey):
        try:
            return str(self.__dict[myKey][0]).strip()
        except:
            return ''


    def _getIntegerValue(self,myKey):
        try:
            return int(self.__dict[myKey][0])
        except:
            return None

    def _getDoubleValue(self,myKey):
        try:
            return double(self.__dict[myKey][0])
        except:
            return None

    def _getStringList(self,myKey):
        try:
            return self.__dict[myKey]
        except:
            return []
            
class InputRequest(WebRequest):
    def __init__(self,paramDict,verbose=False,log=sys.stderr):
        super(InputRequest,self).__init__(paramDict,verbose)
        self.__verbose = verbose
        self.__lfh=log
        self.__returnFormatDefault=''

    def setDefaultReturnFormat(self,return_format="html"):
        self.__returnFormatDefault=return_format
        if (not self.exists("return_format")):
            self.setValue('return_format',self.__returnFormatDefault)
        
    def getRequestPath(self):
        return (self._getStringValue('request_path'))

    def getReturnFormat(self):
        if (not self.exists("return_format")):
            self.setValue('return_format',self.__returnFormatDefault)            
        return (self._getStringValue('return_format'))        

    def setReturnFormat(self,return_format='html'):
        return (self.setValue('return_format',return_format))
    
    def getSessionId(self):
        return (self._getStringValue('sessionid'))

    def getSessionPath(self):
        return (os.path.join(self._getStringValue('TopSessionPath'),'sessions'))    

    def getTopSessionPath(self):
        return (self._getStringValue('TopSessionPath'))

    def getSemaphore(self):
        return (self._getStringValue('semaphore'))        

    def getSessionObj(self):
        if (self.exists("TopSessionPath")):
            sObj=SessionManager(topPath=self._getStringValue("TopSessionPath"))
        else:
            sObj=SessionManager()
        sObj.setId(uid=self._getStringValue("sessionid"))
        return sObj

    def newSessionObj(self,forceNew=False):
        if (self.exists("TopSessionPath")):
            sObj=SessionManager(topPath=self._getStringValue("TopSessionPath"))
        else:
            sObj=SessionManager()

        sessionId = self._getStringValue("sessionid")

        if (forceNew):
            sObj.assignId()
            sObj.makeSessionPath()
            self.setValue('sessionid',sObj.getId())            
        elif (len(sessionId) > 0):
            sObj.setId(sessionId)
            sObj.makeSessionPath()
        else:
            sObj.assignId()
            sObj.makeSessionPath()
            self.setValue('sessionid',sObj.getId())
        
        return sObj

#
class ResponseContent(object):
    def __init__(self, reqObj=None, verbose=False,log=sys.stderr):
        """
        Manage content items to be transfered as part of the application response.
        
        """
        self.__verbose=verbose
        self.__lfh=log
        self.__reqObj=reqObj
        #
        self._cD={}
        self.__setup()
        
    def __setup(self):
        """ Default response content is set here.
        """
        self._cD['htmllinkcontent']=''        
        self._cD['htmlcontent']=''
        self._cD['textcontent']=''
        self._cD['location']=''
        #
        self._cD['datacontent']=None
        self._cD['errorflag']=False
        self._cD['statustext']=''
        # legacy setting -- 
        self._cD['errortext']=''
        if self.__reqObj is not None:
            self._cD['sessionid']=self.__reqObj.getSessionId()
            self._cD['semaphore']=self.__reqObj.getSemaphore()
        else:
            self._cD['sessionid']=''
            self._cD['semaphore']=''

    def setData(self,dataObj=None):
        self._cD['datacontent']=dataObj

    def set(self,key,val):
        self._cD[key]=val
        
    def setHtmlList(self,htmlList=[]):
        self._cD['htmlcontent']='\n'.join(htmlList)

    def setHtmlText(self,htmlText=''):
        self._cD['htmlcontent']=htmlText

    def setHtmlLinkText(self,htmlText=''):
        self._cD['htmllinkcontent']=htmlText        

    def setText(self,text=''):
        self._cD['textcontent']=text

    def setLocation(self,url=''):
        self._cD['location']=url            

    def addDictionaryItems(self,cD={}):
        for k,v in cD.items():
            self._cD[k]=v

    def setTextFile(self,filePath):
        try:
            if os.path.exists(filePath):            
                self._cD['textcontent']=open(filePath).read()            
        except:
            self.__lfh.write("+setTextFile() File read failed %s\n" % filePath )        
            traceback.print_exc(file=self.__lfh)                                        


    def setTextFileO(self,filePath):
        self._cD['textcontent']=open(filePath).read()
        
    def setStatus(self,statusMsg='',semaphore=''):
        self._cD['errorflag']=False
        self._cD['statustext']=statusMsg
        self._cD['semaphore']=semaphore
        
    def setError(self,errMsg='',semaphore=''):
        self._cD['errorflag']=True
        self._cD['statustext']=errMsg
        # legacy setting -
        self._cD['errortext']=errMsg
        self._cD['semaphore']=semaphore

    def setStatusCode(self,aCode):
        self._cD['statuscode']=aCode

    def setHtmlContentPath(self,aPath):
        self._cD['htmlcontentpath']=aPath

    def dump(self):
        retL=[]
        retL.append("+ResponseContent.dump() - response content object\n")
        for k,v in self._cD.items():
            retL.append(" key = %s " % k)
            retL.append(" value(1-1024): %s\n" %   str(v)[:1024] )
        return retL

    def get(self):
        """Repackage the response for Apache according to the input return_format='html|json|text|...'
        """
        rD={}
        if (self.__reqObj.getReturnFormat() == 'html'):
            if (self._cD['errorflag']==False):
                rD=self.__initHtmlResponse(self._cD['htmlcontent'])
            else:
                rD=self.__initHtmlResponse(self._cD['statustext'])                
        elif (self.__reqObj.getReturnFormat() == 'text'):
            if (self._cD['errorflag']==False):
                rD=self.__initTextResponse(self._cD['textcontent'])
            else:
                rD=self.__initHtmlResponse(self._cD['statustext'])                
        elif (self.__reqObj.getReturnFormat() == 'json'):
            rD=self.__initJsonResponse(self._cD)
        elif (self.__reqObj.getReturnFormat() == 'jsonText'):
            rD=self.__initJsonResponseInTextArea(self._cD)
        elif (self.__reqObj.getReturnFormat() == 'jsonData'):
            rD=self.__initJsonResponse(self._cD['datacontent'])
        elif (self.__reqObj.getReturnFormat() == 'location'):
            rD=self.__initLocationResponse(self._cD['location'])                                    
        else:
            pass
        #
        return rD

    def __initLocationResponse(self,url):
        rspDict={}
        rspDict['CONTENT_TYPE']  = 'location'
        rspDict['RETURN_STRING'] = url 
        return rspDict

    def __initJsonResponse(self,myD={}):
        rspDict={}
        rspDict['CONTENT_TYPE']  = 'application/json'
        rspDict['RETURN_STRING'] = dumps(myD)
        return rspDict

    def __initJsonResponseInTextArea(self,myD={}):
        rspDict={}
        rspDict['CONTENT_TYPE']  = 'text/html'
        rspDict['RETURN_STRING'] = '<textarea>'+dumps(myD)+'</textarea>'
        return rspDict

    def __initHtmlResponse(self,myHtml=''):
        rspDict={}
        rspDict['CONTENT_TYPE']  = 'text/html'
        rspDict['RETURN_STRING'] = myHtml
        return rspDict

    def __initTextResponse(self, myText=''):
        rspDict={}
        rspDict['CONTENT_TYPE']  = 'text/plain'
        rspDict['RETURN_STRING'] = myText
        return rspDict

if __name__ == '__main__':
    rC=ResponseContent()








