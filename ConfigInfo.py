##
# File:    ConfigInfo.py
# Author:  jdw
# Date:    16-June-2009
#
# Updates:
#
# 21-Aug-2009  Added test data files to DEV configuration
#  5-Feb-2010  Add data processing example files -
# 08-May-2010  Add resource configuration file
# 25-Jun-2010  Add configLevel to constructor.
# 24-Feb-2011  Distinguish platforms
# 27-Feb-2011  Add support for database 
##
"""
Manage configuration information accross sites, platforms, and
        development levels. 

"""
__docformat__ = "restructuredtext en"
__author__    = "John Westbrook"
__email__     = "jwest@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.001"


import sys,os,platform
from sbkb.db.DbUtil                          import MyDbConnect

class ConfigInfo(object):
    """ Manage configuration information accross sites, platforms, and
        development levels. 
    """
    def __init__(self,configLevel="DEV", site="DEFAULT", platformType="DEFAULT",verbose=False,log=sys.stderr):
        self.__site=str(site).upper()
        self.__platform=str(platformType).upper()
        self.__configLevel=str(configLevel).upper()
        self.__verbose=verbose
        self.__lfh=log
        self.__cDict={}
        self.__sysType=platform.system()        
        self.__setup()

        
    def __setup(self):
        if (self.__configLevel.startswith("PROD")):
            self.__cDict={
                'DB_SERVER'       : 'mysql',
                'DB_HOST_PDB'  : 'pdb-k-linux-9.rutgers.edu',
                'DB_NAME_PDB'     : 'cleanv1',
                'RESOURCE_CONFIG_FILE_PATH'  : '/net/kb-data-dev/config-files/sbkb-remote-resources.xml',
                'LOAD_FILE_PATH'  : '/net/kb-data-dev/load-files',
            'RESOURCE_FILE_PATH'  : '/net/kb-data-dev/resource-files',                                
                'PDB_ID_FILE_ALL' : '/net/kb-data-dev/resource-files/pdb/all-pdb-list.txt',                                
                'PDB_TEST_ID_1'   : '2zkr',
                'PDB_TEST_ID_2'   : '2zkr',
                'PDB_TEST_ID_3'   : '1kip',
           'DB_HOST_PEPCDB'   : 'pdb-a-linux-8.rutgers.edu',
              'DB_NAME_PEPCDB'    : 'pepc',                
           'DB_HOST_TARGETDB'  : 'pdb-a-linux-8.rutgers.edu',
              'DB_NAME_TARGETDB'  : 'targetdb',
              'PUBMED_FILE_LIST'  : ['/net/kb-data-dev/resource-files/pubmed/pdb/PdbPubMedIds.list',
                                     '/net/kb-data-dev/resource-files/pubmed/mcsg/PsiMethodIds.list',
                                     '/net/kb-data-dev/resource-files/pubmed/uniprot/unp-citations-pubmed-1.tdd']
                }
        elif (self.__configLevel.startswith("BETA")):
            self.__cDict={
                'DB_SERVER'       : 'mysql',
                'DB_HOST_PDB'  : 'pdb-k-linux-9.rutgers.edu',
                'DB_NAME_PDB'     : 'cleanv1',
                'RESOURCE_CONFIG_FILE_PATH'  : '/net/kb-data-dev/config-files/sbkb-remote-resources.xml',
                'LOAD_FILE_PATH'  : '/net/kb-data-dev/load-files',
            'RESOURCE_FILE_PATH'  : '/net/kb-data-dev/resource-files',
                'PDB_ID_FILE_ALL' : '/net/kb-data-dev/resource-files/pdb/all-pdb-list.txt',                
                'PDB_TEST_ID_1'   : '2zkr',
                'PDB_TEST_ID_2'   : '2zkr',
                'PDB_TEST_ID_3'   : '1kip',
           'DB_HOST_PEPCDB'   : 'pdb-a-linux-8.rutgers.edu',
              'DB_NAME_PEPCDB'    : 'pepc',                
           'DB_HOST_TARGETDB'  : 'pdb-a-linux-8.rutgers.edu',
              'DB_NAME_TARGETDB'  : 'targetdb',
              'PUBMED_FILE_LIST'  : ['/het/kb-data-dev/resource-files/pubmed/pdb/PdbPubMedIds.list',
                                     '/net/kb-data-dev/resource-files/pubmed/mcsg/PsiMethodIds.list',
                                     '/net/kb-data-dev/resource-files/pubmed/uniprot/unp-citations-pubmed-1.tdd']
                
                }
        elif (self.__configLevel.startswith("DEV") and (self.__sysType == "Linux")):            
            self.__cDict={
                'DB_SERVER'       : 'mysql',
                'DB_HOST_PDB'  : 'pdb-k-linux-9.rutgers.edu',
                'DB_NAME_PDB'     : 'cleanv1',
                'RESOURCE_CONFIG_FILE_PATH'  : '/net/users/jwest/Source/Python/Dev-svn/sbkb/fetchers/data/sbkb-remote-resources.xml',
                # 'RESOURCE_CONFIG_FILE_PATH'  : '/net/users/jwest/Source/Python/Dev-svn/sbkb/fetchers/data/kb-remote-list-test-dev-1.xml',
                'LOAD_FILE_PATH'  : '/net/kb-data-dev/load-files',
            'RESOURCE_FILE_PATH'  : '/net/kb-data-dev/resource-files',                
                'PDB_ID_FILE_ALL' : '/net/kb-data-dev/resource-files/pdb/all-pdb-list-test.txt',
                'PDB_TEST_ID_1'   : '2zkr',
                'PDB_TEST_ID_2'   : '2zkr',
                'PDB_TEST_ID_3'   : '1kip',
             'PDB_TEST_ID_LIST'   : ['2zkr','2bna'],
           'DB_HOST_PEPCDB'   : 'pdb-a-linux-8.rutgers.edu',
              'DB_NAME_PEPCDB'    : 'pepc',
           'DB_HOST_TARGETDB'  : 'pdb-a-linux-8.rutgers.edu',
              'DB_NAME_TARGETDB'  : 'targetdb',
             'PDB_DATA_CACHE_PATH' :  '/net/kb-data-dev/resource-files/pdb-data-cache',
             'UNIPROT_TEST_ID_1'  : 'P33201',                
              'UNIPROT_DATA_PATH' : '/net/kb-data-dev/resource-files/uniprot-xml',
        'UNIPROT_DATA_CACHE_PATH' : '/net/kb-data-dev/resource-files/uniprot-xml',                                
        'UNIPROT_ID_FILE_PDB_FID' : (8,8),
         'UNIPROT_SPROT_TEXT_FID' : (27,10),
        'UNIPROT_TREMBL_TEXT_FID' : (27,12),                                
   'UNIPROT_ID_FILE_TARGETDB_FID' : (24,3),
  'STOP_UNIPROT_FETCH_FILE_PATH'  : '/net/kb-data-dev/test-files/uniprot-fetch-stop',
          'STOP_FETCH_FILE_PATH'  : '/net/kb-data-dev/test-files/fetch-stop',                
            'PDB_ID_FILE_ALL_FID' : (3,1),
       'PDB_ID_FILE_MODIFIED_FID' : (3,2),
       'PDB_ID_FILE_ADDED_FID'    : (3,7),                                
       'PUBMED_ID_UNIPROT_ID_FID' : (24,2),
           'PUBMED_ID_PDB_ID_FID' : (24,1),
    'PUBMED_ID_PUBSPORTAL_ID_FID' : (25,1),
 'PUBMED_ID_PUBMED_CENTRAL_ID_FID': (4,3),
         'PUBMED_DATA_CACHE_PATH' :  '/net/kb-data-dev/resource-files/pubmed/data-pic-hash',
        'PUBMED_LOAD_FILE_PREFIX' :  'kb-literature-feature-',
                'TEST_FILE_PATH'  : '/net/kb-data-dev/test-files',
                'TEST_FILE'       : 'TEST-FILE.DAT',
                'TEST_FILE_ZLIB'  : 'TEST-FILE.DAT.Z',
                'TEST_FILE_GZIP'  : 'TEST-FILE.DAT.gz',
                'TEST_FILE_BZIP'  : 'TEST-FILE.DAT.bz2',
                'DP_TEST_FILE_PATH'  : './data',
                'DP_TEST_FILE_CIF'   : 'rcsb033781.cif',
                'DP_TEST_FILE_CIFEPS': 'rcsb033781.cifeps',
                'LOAD_FILE_FEATURE' : 'feature-resource-entry-data.tdd',
                'LOAD_FILE_FEATURE_ANNOTATION' : 'feature-pdb-entity-data.tdd',
                'LOAD_FILE_FEATURE_LITERATURE' : 'feature-literature.tdd',                                
                'TEMPORARY_PATH'        : '/scratch/loader'
                }        
        elif (self.__configLevel.startswith("DEV") and (self.__sysType == "Darwin")):
            #
            # 
            self.__cDict={
                'DB_SERVER'       : 'mysql',
                'DB_HOST_PDB'     : 'localhost',
                'DB_NAME_PDB'     : 'cleanv1',
                'RESOURCE_CONFIG_FILE_PATH'  : '/Users/jwest/Source/Python/Dev-svn/sbkb/fetchers/data/sbkb-remote-resources.xml',
                # 'RESOURCE_CONFIG_FILE_PATH'  : '/net/users/jwest/Source/Python/Dev-svn/sbkb/fetchers/data/kb-remote-list-test-dev-1.xml',
                'LOAD_FILE_PATH'  : '/data/kb-data-dev/load-files',
            'RESOURCE_FILE_PATH'  : '/data/kb-data-dev/resource-files',                
                'PDB_ID_FILE_ALL' : '/data/kb-data-dev/resource-files/pdb/all-pdb-list-test.txt',
                'PDB_TEST_ID_1'   : '2zkr',
                'PDB_TEST_ID_2'   : '2zkr',
                'PDB_TEST_ID_3'   : '1kip',
             'PDB_TEST_ID_LIST'   : ['2zkr','2bna'],
               'DB_HOST_PEPCDB'   : 'pdb-a-linux-8.rutgers.edu',
              'DB_NAME_PEPCDB'    : 'pepc',
              'DB_HOST_TARGETDB'  : 'pdb-a-linux-8.rutgers.edu',
              'DB_NAME_TARGETDB'  : 'targetdb',
             'PDB_DATA_CACHE_PATH' :  '/data/kb-data-dev/resource-files/pdb-data-cache',
             'UNIPROT_TEST_ID_1'  : 'P33201',                
#              'UNIPROT_DATA_PATH' : '/data/kb-data-dev/resource-files/uniprot-xml',
        'UNIPROT_DATA_CACHE_PATH' : '/data/kb-data-dev/resource-files/uniprot-xml',                
        'UNIPROT_ID_FILE_PDB_FID' : (8,8),
         'UNIPROT_SPROT_TEXT_FID' : (27,10),
        'UNIPROT_TREMBL_TEXT_FID' : (27,12),                                                
   'UNIPROT_ID_FILE_TARGETDB_FID' : (24,3),
  'STOP_UNIPROT_FETCH_FILE_PATH'  : '/data/kb-data-dev/test-files/uniprot-fetch-stop',
          'STOP_FETCH_FILE_PATH'  : '/data/kb-data-dev/test-files/fetch-stop',                
            'PDB_ID_FILE_ALL_FID' : (3,1),
       'PDB_ID_FILE_MODIFIED_FID' : (3,2),
       'PDB_ID_FILE_ADDED_FID'    : (3,7),                                
       'PUBMED_ID_UNIPROT_ID_FID' : (24,2),
           'PUBMED_ID_PDB_ID_FID' : (24,1),
    'PUBMED_ID_PUBSPORTAL_ID_FID' : (25,1),
 'PUBMED_ID_PUBMED_CENTRAL_ID_FID': (4,3),
         'PUBMED_DATA_CACHE_PATH' :  '/data/kb-data-dev/resource-files/pubmed/data-pic-hash',
        'PUBMED_LOAD_FILE_PREFIX' :  'literature-features-',
                'TEST_FILE_PATH'  : '/data/kb-data-dev/test-files',
                'TEST_FILE'       : 'TEST-FILE.DAT',
                'TEST_FILE_ZLIB'  : 'TEST-FILE.DAT.Z',
                'TEST_FILE_GZIP'  : 'TEST-FILE.DAT.gz',
                'TEST_FILE_BZIP'  : 'TEST-FILE.DAT.bz2',
                'DP_TEST_FILE_PATH'  : './data',
                'DP_TEST_FILE_CIF'   : 'rcsb033781.cif',
                'DP_TEST_FILE_CIFEPS': 'rcsb033781.cifeps',
                'LOAD_FILE_FEATURE' : 'feature-resource-entry-data.tdd',
                'LOAD_FILE_FEATURE_ANNOTATION' : 'feature-pdb-entity-data.tdd',
                'LOAD_FILE_FEATURE_LITERATURE' : 'literature-features.tdd',                
                'TEMPORARY_PATH'        : '/Users/jwest/MyFiles/scratch'
                }        
        else:
            pass
    
    def get(self,infoType):
        iT= str(infoType)
        try:
            return self.__cDict[iT]
        except:
            sys.stderr.write("+ERROR(configInfo) -No information for item %s platform %s site %s level %s\n"
                             % (iT,self.__platform,self.__site,self.__configLevel))
            return None


    def getDbConnect(self,dbResource='PDB'):
        #
        try:
            self.__dbserver = self.__cDict['DB_SERVER']
            self.__dbUser   = self.getDbUser(dbResource=dbResource)
            self.__dbPw     = self.getDbPw(dbResource=dbResource)                        
            if (dbResource == 'PDB'):
                self.__dbHost   = self.__cDict['DB_HOST_PDB']
                self.__dbName   = self.__cDict['DB_NAME_PDB']
            elif (dbResource == 'TARGETDB'):
                self.__dbHost   = self.__cDict['DB_HOST_TARGETDB']
                self.__dbName   = self.__cDict['DB_NAME_TARGETDB']
            elif (dbResource == 'PEPCDB'):
                self.__dbHost   = self.__cDict['DB_HOST_PEPCDB']
                self.__dbName   = self.__cDict['DB_NAME_PEPCDB']
            else:
                self.__dbHost = ""
                self.__dbName = ""
            myDb = MyDbConnect(dbServer=self.__dbserver,dbHost=self.__dbHost,dbName=self.__dbName,dbUser=self.__dbUser,dbPw=self.__dbPw)
            return myDb.connect()
        except:
            sys.stderr.write("+ConfigInfo ERROR database connection failed for resource %s\n" % dbResource)
            raise
    
        
    def getDbTestAccess(self,dbResource):
        user   ="user0000"
        pw     ="rcsb0000"
        host   ="localhost"                
        dbName =""
        try:
            user=os.getenv("MYSQL_DB_USER")
            pw=os.getenv("MYSQL_DB_PW")            
            if (dbResource=="TARGETDB"):
                dbName="targetdb"
            elif (dbResource=="PDB"):
                dbName="cleanv1"
            elif (dbResource=="NDB"):
                dbName="ndb"                
            elif (dbResource=="PEPCDB"):
                dbName="pepc"
        except:
            sys.stderr.write("+ConfigInfo ERROR -No test database access information for %s\n" % dbResource)
            
        return (host,dbName,user,pw)


    def getDbUser(self,dbResource):
        val="user0000"
        try:
            if (dbResource=="TARGETDB"):
                val=os.getenv("MYSQL_TARGETDB_USER")
            elif (dbResource=="PDB"):
                val=os.getenv("MYSQL_PDBDB_USER")            
            elif (dbResource=="PEPCDB"):
                val=os.getenv("MYSQL_PEPCDB_USER")
        except:
            sys.stderr.write("+ERROR(configInfo) -No database user information for %s\n" % dbResource)

        return val

    def getDbPw(self,dbResource):
        val="user0000"
        try:
            if (dbResource=="TARGETDB"):
                val=os.getenv("MYSQL_TARGETDB_PW")
            elif (dbResource=="PDB"):
                val=os.getenv("MYSQL_PDBDB_PW")            
            elif (dbResource=="PEPCDB"):
                val=os.getenv("MYSQL_PEPCDB_PW")
        except:
            sys.stderr.write("+ERROR(configInfo) -No database password information for %s\n" % dbResource)

        return val

