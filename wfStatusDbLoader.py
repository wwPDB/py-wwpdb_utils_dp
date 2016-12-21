##
# File:  wfStatusDbLoader.py
# Date:  12-Oct-2016
# Updates:
##
"""

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project

Copyright (c) 2016 wwPDB

This software is provided under a Creative Commons Attribution 3.0 Unported
License described at http://creativecommons.org/licenses/by/3.0/.

"""
__docformat__ = "restructuredtext en"
__author__    = "Zukang Feng"
__email__     = "zfeng@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.07"

import datetime, getopt, os, sys, time
import MySQLdb

from wwpdb.api.facade.ConfigInfo         import ConfigInfo
from wwpdb.api.status.dbapi.DbConnection import DbConnection
from wwpdb.api.status.dbapi.WFEtime      import getTimeNow
from wwpdb.utils.rcsb.mmCIFUtil          import mmCIFUtil

class StatusDBLoader(object):
    def __init__(self, siteId=None, verbose=False, log=sys.stderr):
        """
        """
        self.__siteId  = siteId
        self.__verbose = verbose
        self.__lfh     = log
        self.__dbcon   = self.__getDbConnection()

    def loadListEntries(self, listFileName=None):
        if (not listFileName) or (not os.access(listFileName, os.F_OK)):
            return
        #
        f = file(listFileName, 'r')
        data = f.read()
        f.close()
        #
        fileNameList = data.split('\n')
        for fileName in fileNameList:
            self.loadSingleEntry(entryFileName=fileName)
        #

    def loadSingleEntry(self, entryFileName=None):
        if (not entryFileName) or (not os.access(entryFileName, os.F_OK)):
            return
        #
        depId,info_data = self.__getEntryInfoData(entryFileName)
        if depId and info_data:
            self.__updateTable(table = 'deposition', where = { 'dep_set_id' : depId }, data = info_data)
            self.__updateInstTables(depId)
            self.__updateCommunicationTable(depId)
        #

    def __getEntryInfoData(self, entryFileName):
        """
        """
        cifObj = mmCIFUtil(filePath=entryFileName)
        #
        depId,info_data = self.__getDataBaseIDs(cifObj)
        info_data = self.__getSingleValues(cifObj, info_data)
        info_data = self.__getMultipleValues(cifObj, info_data)
        if info_data:
            info_data['locking'] = 'DEP'
        #
        return depId,info_data

    def __getDataBaseIDs(self, cifObj):
        """
        """
        depId = ''
        info_data = {}
        #
        valList = cifObj.GetValue('database_2')
        if valList:
            for valD in valList:
                if (not valD.has_key('database_id')) or (not valD['database_id']) or (not valD.has_key('database_code')) or (not valD['database_code']):
                    continue
                #
                if valD['database_id'].upper() == 'WWPDB':
                    depId = valD['database_code'].upper()
                elif valD['database_id'].upper() == 'PDB':
                    info_data['pdb_id'] = valD['database_code'].upper()
                elif valD['database_id'].upper() == 'BMRB':
                    info_data['bmrb_id'] = valD['database_code'].upper()
                elif valD['database_id'].upper() == 'EMDB':
                    info_data['emdb_id'] = valD['database_code'].upper()
                #
            #
        #
        return depId,info_data

    def __getSingleValues(self, cifObj, info_data):
        """
        """
        ciLists = [ [ 'pdbx_database_status', \
                      [ [ 'initial_deposition_date',    'recvd_initial_deposition_date' ], \
                        [ 'annotator_initials',         'pdbx_annotator'                ], \
                        [ 'deposit_site',               'deposit_site'                  ], \
                        [ 'process_site',               'process_site'                  ], \
                        [ 'status_code',                'status_code'                   ], \
                        [ 'author_release_status_code', 'author_release_status_code'    ], \
                        [ 'status_code_exp',            'status_code_sf'                ], \
                        [ 'status_code_exp',            'status_code_mr'                ], \
                        [ 'status_code_exp',            'status_code_cs'                ] ] ], \
                    [ 'struct', \
                      [ [ 'title',                      'title'                         ] ] ], \
                    [ 'em_admin', \
                      [ [ 'title_emdb',                 'title'                         ], \
                        [ 'status_code_emdb',           'current_status'                ] ] ] ]
        #
        for cat_items in ciLists:
            valList = cifObj.GetValue(cat_items[0])
            if not valList:
                continue
            #
            for itemlist in cat_items[1]:
                if info_data.has_key(itemlist[0]) and info_data[itemlist[0]]:
                    continue
                #
                if valList[0].has_key(itemlist[1]) and valList[0][itemlist[1]]:
                    info_data[itemlist[0]] = valList[0][itemlist[1]]
                #
            # 
        #
        return info_data

    def __getMultipleValues(self, cifObj, info_data):
        """
        """
        multipleLists = [ [ "author_list",      "audit_author",   "name"   ], \
                          [ "author_list_emdb", "em_author_list", "author" ], \
                          [ "exp_method",       "exptl",          "method" ] ]
        #
        for mList in multipleLists:
            valList = cifObj.GetValue(mList[1])
            if not valList:
                continue
            #
            rList = []
            for valD in valList:
                if valD.has_key(mList[2]) and valD[mList[2]]:
                    rList.append(valD[mList[2]])
                #
            #
            if rList:
                info_data[mList[0]] = ', '.join(rList)
            #
        #
        return info_data

    def __updateInstTables(self, depId):
        """
        """
        wf_inst = {}
        wf_inst['wf_inst_id'] = 'W_001'
        wf_inst['wf_class_id'] = 'Annotate'
        wf_inst['owner'] = 'Annotation.bf.xml'
        wf_inst['inst_status'] = 'init'
        wf_inst['status_timestamp'] = str(getTimeNow())
        self.__updateTable(table = 'wf_instance', where = { 'dep_set_id' : depId }, data = wf_inst)
        self.__updateTable(table = 'wf_instance_last', where = { 'dep_set_id' : depId }, data = wf_inst)

    def __updateCommunicationTable(self, depId):
        """
        """
        communication = {}
        communication['sender'] = 'INSERT'
        communication['receiver'] = 'LOAD'
        communication['command'] = 'INIT'
        communication['status'] = 'INIT'
        communication['actual_timestamp'] = str(getTimeNow())
        communication['parent_dep_set_id'] = depId
        communication['parent_wf_class_id'] = 'Annotate'
        communication['wf_class_file'] = 'Annotation.bf.xml'
        communication['parent_wf_inst_id'] = 'W_001'
        self.__updateTable(table = 'communication', where = { 'dep_set_id' : depId }, data = communication)

    def __getDbConnection(self):
        self.__cI       = ConfigInfo(self.__siteId)
        self.__dbServer = self.__cI.get("SITE_DB_SERVER")
        self.__dbHost   = self.__cI.get("SITE_DB_HOST_NAME")
        self.__dbName   = self.__cI.get("SITE_DB_DATABASE_NAME")
        self.__dbUser   = self.__cI.get("SITE_DB_USER_NAME")
        self.__dbPw     = self.__cI.get("SITE_DB_PASSWORD")
        self.__dbSocket = self.__cI.get("SITE_DB_SOCKET")
        self.__dbPort   = int(self.__cI.get("SITE_DB_PORT_NUMBER"))
        self.__Nretry   = 5
        self.__dbState  = 0
        self.__myDb     = DbConnection(dbServer=self.__dbServer,dbHost=self.__dbHost, dbName=self.__dbName, dbUser=self.__dbUser, \
                                       dbPw=self.__dbPw, dbPort=self.__dbPort, dbSocket=self.__dbSocket)
        return self.__myDb.connect()

    def __updateTable(self, table=None, where=None, data=None):
        if not table:
            return None
        #
        if (not where) and (not data):
            return None
        #
        rowExists = False
        if where:
            sql = "select * from " + str(table) + " where " + ' and '.join(["%s = '%s'" % (k, v.replace("'", "\\'")) for k, v in where.iteritems()])
            rows = self.__runSelectSQL(sql)
            if rows and len(rows) > 0:
                rowExists = True
            #
        #
        if rowExists and (not data):
            return 'OK'
        #
        if rowExists:
            sql = "update " + str(table) + " set " + ','.join(["%s = '%s'" % (k, v.replace("'", "\\'")) for k, v in data.iteritems()])
            if where:
                sql += ' where ' + ' and '.join(["%s = '%s'" % (k, v.replace("'", "\\'")) for k, v in where.iteritems()])
            #
        else:
            sql = "insert into " + str(table) + " (" + ','.join(['%s' % (k) for k, v in where.iteritems()])
            if data:
                sql += "," + ','.join(['%s' % (k) for k, v in data.iteritems()])
            #
            sql += ") values (" + ','.join(["'%s'" % (v.replace("'", "\\'")) for k, v in where.iteritems()])
            if data:
                sql += "," + ','.join(["'%s'" % (v.replace("'", "\\'")) for k, v in data.iteritems()])
            #
            sql += ")"
        #
        return self.__runUpdateSQL(sql)

    def __runSelectSQL(self, sql):
        """ method to run a query
        """
        for retry in range(1, self.__Nretry):
            ret = self.__runSelect(sql)
            if ret == None:
                if self.__dbState > 0:
                    time.sleep(retry*2)
                    if not self.__reConnect(): return None
                else:
                    return None
                #
            else:
                for myD in ret:
                    items = myD.keys()
                    for item in items:
                        if not myD[item]:
                            del myD[item]
                        #
                    #
                #
                return ret
            #
        #
        return None

    def __runUpdateSQL(self, sql):
        """ method to run a query
        """
        for retry in range(1, self.__Nretry):
            ret = self.__runUpdate(sql)
            if ret == None:
                if self.__dbState > 0:
                    time.sleep(retry*2)
                    if not self.__reConnect(): return None
                else:
                    return None
                #
            else:
                return ret
            #
        #
        return None

    def __reConnect(self):
        """
        """
        try:
            self.__myDb.close(self.__dbcon)
        except MySQLdb.Error:
            self.__lfh.write("+DbApiUtil.reConnect() DB connection lost - cannot close\n")
            self.__lfh.write("+DbApiUtil.reConnect() Re-connecting to the database ..\n")
            self.__lfh.write("+DbApiUtil.reConnect() UTC time = %s\n" % datetime.datetime.utcnow())
 
        for i in range(1, self.__Nretry):
            try:
                self.__dbcon   = self.__myDb.connect()
                self.__dbState = 0
                return True
            except MySQLdb.Error:
                self.__lfh.write("+DbApiUtil.reConnect() Cannot get re-connection : trying again\n")
                time.sleep(2*i)
            #
        #
        return False

    def __runSelect(self, query):
        """
        """
        rows = ()
        try:
            self.__dbcon.commit()
            curs = self.__dbcon.cursor(MySQLdb.cursors.DictCursor)
            curs.execute(query)
            rows = curs.fetchall()
        except MySQLdb.Error, e:
            self.__dbState = e.args[0]
            self.__lfh.write("Database error %d: %s\n" % (e.args[0], e.args[1]))
        #
        return rows
 
    def __runUpdate(self, query):
        """
        """
        try:
            curs = self.__dbcon.cursor()
            curs.execute("set autocommit=0")
            nrows = curs.execute(query)
            self.__dbcon.commit()
            curs.execute("set autocommit=1")
            curs.close()
            return 'OK'
        except MySQLdb.Error, e:
            self.__dbcon.rollback()
            self.__dbState = e.args[0]
            self.__lfh.write("Database error %d: %s\n" % (e.args[0], e.args[1]))
        #
        return None

if __name__ == '__main__':
    #
    siteId = 'WWPDB_DEPLOY_LEGACY_RU'
    if "WWPDB_SITE_ID" in os.environ:
        siteId = os.environ["WWPDB_SITE_ID"]
    #
    opts, args = getopt.getopt(sys.argv[1:], "", ["file=", "list="])
    if opts:
        loader = StatusDBLoader(siteId = siteId, verbose = True, log = sys.stderr)
        for opt, arg in opts:
            if opt in ("--file"):
                loader.loadSingleEntry(entryFileName=arg)
            elif opt in ("--list"):
                loader.loadListEntries(listFileName=arg)
            #
        #
    else:
        print "Usage: python wfStatusDbLoader.py --file=${entry_file_name} [ --list=${list_file_name} ]"
    #
