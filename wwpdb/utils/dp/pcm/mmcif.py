"""Utils related to mmCIF file handling"""

import logging
import os
import shutil
import sys
import tempfile

from mmcif.api.DataCategory import DataCategory
from mmcif.io.IoAdapterCore import IoAdapterCore as IoAdapterCore
from wwpdb.io.locator.PathInfo import PathInfo
from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId
from wwpdb.utils.wf.dbapi.WfDbApi import WfDbApi


def get_depid_from_pdb(pdbid):
    sql = """select dep_set_id from status.deposition where pdb_id = '%s'""" % pdbid
    sql_result = WfDbApi().runSelectSQL(sql)
    for row in sql_result:
        return row[0]

    return None


def get_pdbid_from_depid(depid):
    sql = """select pdb_id from status.deposition where dep_set_id = '%s'""" % depid
    sql_result = WfDbApi().runSelectSQL(sql)
    for row in sql_result:
        return row[0]

    return None


def get_exp_method_from_depid(depid):
    sql = """select exp_method from status.deposition where dep_set_id = '%s'""" % depid
    sql_result = WfDbApi().runSelectSQL(sql)
    for row in sql_result:
        return row[0]

    return None


def return_lastest_mmcif_from_pdb(pdbid):
    depid = get_depid_from_pdb(pdbid=pdbid)
    if depid:
        mh = mmcifHandling(depID=depid)
        latest_model = mh.get_latest_model()
        return latest_model
    return None


def get_config_info_variable(variable):
    cI = ConfigInfo(getSiteId())
    return cI.get(variable.upper())


class mmcifHandling:
    def __init__(
        self,
        depID,
        IoAdapter=IoAdapterCore(),  # noqa: B008
        log=sys.stderr,
        filesource="archive",
        milestone=None,
        instance_id=None,
        siteId=getSiteId(),  # noqa: B008
        skip_working_path=False,
    ):
        self.depid = depID
        self.io = IoAdapter
        self.logFileHandler = log
        self.fileSource = filesource
        self.mileStone = milestone
        self.instance_id = instance_id
        self.siteId = siteId
        logging.debug(self.siteId)
        self.pathInfo = PathInfo(
            siteId=self.siteId, sessionPath=".", verbose=True, log=self.logFileHandler
        )
        self.cI = ConfigInfo(self.siteId)
        self.mmcif = None
        self.output_cif = None
        self.cList = None
        self.mmcif_data = None
        self.dcObj = None
        self.__siteWebAppsSessionsPath = self.cI.get("SITE_WEB_APPS_SESSIONS_PATH")
        if not skip_working_path:
            try:
                self.working_path = tempfile.mkdtemp(dir=self.__siteWebAppsSessionsPath)
            except:  # noqa: B001, E722
                self.working_path = tempfile.mkdtemp()

    def get_archive_path(self):
        return self.pathInfo.getArchivePath(dataSetId=self.depid)

    def get_latest_model(self):
        self.mmcif = self.pathInfo.getModelPdbxFilePath(
            dataSetId=self.depid,
            fileSource=self.fileSource,
            versionId="latest",
            mileStone=self.mileStone,
        )

        logging.debug("latest mmcif file path: %s" % self.mmcif)
        return self.mmcif

    def get_first_model(self):
        self.mmcif = self.pathInfo.getModelPdbxFilePath(
            dataSetId=self.depid,
            fileSource=self.fileSource,
            versionId="original",
            mileStone=self.mileStone,
        )

        logging.debug("first mmcif file path: %s" % self.mmcif)
        return self.mmcif

    def get_next_model(self):
        self.mmcif = self.pathInfo.getModelPdbxFilePath(
            dataSetId=self.depid,
            fileSource=self.fileSource,
            versionId="next",
            mileStone=self.mileStone,
        )

        logging.debug("next mmcif file path: %s" % self.mmcif)
        return self.mmcif

    def get_latest_sf(self):
        ret = self.pathInfo.getStructureFactorsPdbxFilePath(
            dataSetId=self.depid,
            fileSource=self.fileSource,
            versionId="latest",
            mileStone=self.mileStone,
        )
        logging.debug("latest sf file path: %s" % ret)
        return ret

    def get_next_sf(self):
        ret = self.pathInfo.getStructureFactorsPdbxFilePath(
            dataSetId=self.depid,
            fileSource=self.fileSource,
            versionId="next",
            mileStone=self.mileStone,
        )
        logging.debug("next sf file path: %s" % ret)
        return ret

    def get_latest_cs(self):
        ret = self.pathInfo.getChemcialShiftsFilePath(
            dataSetId=self.depid,
            fileSource=self.fileSource,
            versionId="latest",
            mileStone=self.mileStone,
            formatType="pdbx",
        )
        logging.debug("latest cs file path: %s" % ret)
        return ret

    def get_next_cs(self):
        ret = self.pathInfo.getChemcialShiftsFilePath(
            dataSetId=self.depid,
            fileSource=self.fileSource,
            versionId="next",
            mileStone=self.mileStone,
            formatType="pdbx",
        )
        logging.debug("next cs file path: %s" % ret)
        return ret

    def get_latest_mr(self):
        ret = self.pathInfo.getMolecularRestraintsFilePath(
            dataSetId=self.depid,
            fileSource=self.fileSource,
            versionId="latest",
            mileStone=self.mileStone,
            formatType="mr",
        )
        logging.debug("latest mr file path: %s" % ret)
        return ret

    def get_next_mr(self):
        ret = self.pathInfo.getMolecularRestraintsFilePath(
            dataSetId=self.depid,
            fileSource=self.fileSource,
            versionId="next",
            mileStone=self.mileStone,
            formatType="mr",
        )
        logging.debug("next mr file path: %s" % ret)
        return ret

    def get_latest_str(self):
        ret = self.pathInfo.getNMRCombinedFilePath(
            dataSetId=self.depid,
            fileSource=self.fileSource,
            versionId="latest",
            mileStone=self.mileStone,
            formatType="pdbx",
        )
        logging.debug("latest str file path: %s" % ret)
        return ret

    def get_next_str(self):
        ret = self.pathInfo.getNMRCombinedFilePath(
            dataSetId=self.depid,
            fileSource=self.fileSource,
            versionId="next",
            mileStone=self.mileStone,
            formatType="pdbx",
        )
        logging.debug("next str file path: %s" % ret)
        return ret

    def get_latest_em_vol(self):
        ret = self.pathInfo.getEmVolumeFilePath(
            dataSetId=self.depid,
            fileSource=self.fileSource,
            versionId="latest",
            mileStone=self.mileStone,
        )
        logging.debug("latest em volume file path: %s" % ret)
        return ret

    def get_latest_pdbx_for_content_type(self, content_type):
        ret = self.get_latest_for_content_type_format(
            content_type=content_type, file_format="pdbx"
        )

        logging.debug(
            "latest file path for content type: %s - %s" % (content_type, ret)
        )
        return ret

    def get_latest_for_content_type_format(
        self, content_type, file_format, partition="1"
    ):
        latest_file = self.pathInfo.getFilePath(
            dataSetId=self.depid,
            fileSource=self.fileSource,
            versionId="latest",
            mileStone=self.mileStone,
            contentType=content_type,
            formatType=file_format,
            partNumber=partition,
        )

        logging.debug(
            "latest file path for content type and file format: %s %s - %s"
            % (content_type, file_format, latest_file)
        )
        return latest_file

    def get_first_for_content_type_format(
        self, content_type, file_format, partition="1"
    ):
        first_file = self.pathInfo.getFilePath(
            dataSetId=self.depid,
            fileSource=self.fileSource,
            versionId="original",
            mileStone=self.mileStone,
            contentType=content_type,
            formatType=file_format,
            partNumber=partition,
        )

        logging.debug(
            "first file path for content type and file format: %s %s - %s"
            % (content_type, file_format, first_file)
        )
        return first_file

    def get_next_for_content_type_format(
        self, content_type, file_format, partition="1"
    ):
        # TODO check parition argument in this command
        next_file = self.pathInfo.getFilePath(
            dataSetId=self.depid,
            fileSource=self.fileSource,
            versionId="next",
            mileStone=self.mileStone,
            contentType=content_type,
            formatType=file_format,
            partNumber=partition,
        )

        logging.debug(
            "next file path for content type and file format: %s %s - %s"
            % (content_type, file_format, next_file)
        )
        return next_file

    def get_latest_filename_for_content_type_format(
        self, content_type, file_format, partition="1"
    ):
        latest_file = self.pathInfo.getFileName(
            dataSetId=self.depid,
            fileSource=self.fileSource,
            versionId="latest",
            mileStone=self.mileStone,
            contentType=content_type,
            formatType=file_format,
            partNumber=partition,
        )

        logging.debug(
            "latest file path for content type and file format: %s %s - %s"
            % (content_type, file_format, latest_file)
        )
        return latest_file

    def copy_first_model_to_working(self):
        first_model = self.get_first_model()
        if os.path.exists(first_model):
            file_name = os.path.basename(first_model)
            self.output_cif = os.path.join(self.working_path, file_name)
            logging.debug("copying first model to %s" % self.output_cif)
            shutil.copy(first_model, self.output_cif)
            return self.output_cif
        logging.error("no first model to copy")
        return False

    def copy_latest_model_to_working(self):
        latest_model = self.get_latest_model()
        if os.path.exists(latest_model):
            file_name = os.path.basename(latest_model)
            self.output_cif = os.path.join(self.working_path, file_name)
            logging.debug("copying latest model to %s" % self.output_cif)
            shutil.copy(latest_model, self.output_cif)
            return self.output_cif
        logging.error("no latest model to copy")
        return False

    def copy_latest_sf_to_working(self):
        latest_sf = self.get_latest_sf()
        if os.path.exists(latest_sf):
            file_name = os.path.basename(latest_sf)
            self.output_cif = os.path.join(self.working_path, file_name)
            logging.debug("copying latest SF to %s" % self.output_cif)
            shutil.copy(latest_sf, self.output_cif)
            return self.output_cif
        logging.error("no latest SF to copy")
        return False

    def copy_latest_cs_to_working(self):
        latest_cs = self.get_latest_cs()
        if os.path.exists(latest_cs):
            file_name = os.path.basename(latest_cs)
            self.output_cif = os.path.join(self.working_path, file_name)
            logging.debug("copying latest CS to %s" % self.output_cif)
            shutil.copy(latest_cs, self.output_cif)
            return self.output_cif
        logging.error("no latest CS to copy")
        return False

    def copy_latest_mr_to_working(self):
        latest_mr = self.get_latest_mr()
        if os.path.exists(latest_mr):
            file_name = os.path.basename(latest_mr)
            self.output_cif = os.path.join(self.working_path, file_name)
            logging.debug("copying latest MR to %s" % self.output_cif)
            shutil.copy(latest_mr, self.output_cif)
            return self.output_cif
        logging.error("no latest MR to copy")
        return False

    def copy_latest_str_to_working(self):
        latest_str = self.get_latest_str()
        if os.path.exists(latest_str):
            file_name = os.path.basename(latest_str)
            self.output_cif = os.path.join(self.working_path, file_name)
            logging.debug("copying latest STR to %s" % self.output_cif)
            shutil.copy(latest_str, self.output_cif)
            return self.output_cif
        logging.error("no latest STR to copy")
        return False

    def copy_output_to_next_model(self):
        next_model = self.get_next_model()
        if self.output_cif:
            logging.debug(
                "copying output cif from: %s to %s" % (self.output_cif, next_model)
            )
            shutil.copy(self.output_cif, next_model)
            return True
        logging.error("no output cif to copy")
        return False

    def copy_output_to_next_cs(self):
        next_cs = self.get_next_cs()
        if self.output_cif:
            logging.debug(
                "copying output cif from: %s to %s" % (self.output_cif, next_cs)
            )
            shutil.copy(self.output_cif, next_cs)
            return True
        logging.error("no output cif to copy")
        return False

    def copy_output_to_next_mr(self):
        next_mr = self.get_next_mr()
        if self.output_cif:
            logging.debug(
                "copying output cif from: %s to %s" % (self.output_cif, next_mr)
            )
            shutil.copy(self.output_cif, next_mr)
            return True
        logging.error("no output cif to copy")
        return False

    def copy_output_to_next_str(self):
        next_str = self.get_next_str()
        if self.output_cif:
            logging.debug(
                "copying output cif from: %s to %s" % (self.output_cif, next_str)
            )
            shutil.copy(self.output_cif, next_str)
            return True
        logging.error("no output cif to copy")
        return False

    def copy_output_to_next(self, in_file, content_type, file_format, partition):
        next_file = self.get_next_for_content_type_format(
            content_type, file_format, partition
        )
        if os.path.exists(in_file):
            logging.debug("copying from: %s to %s" % (in_file, next_file))
            shutil.copy(in_file, next_file)
            return True
        else:
            logging.error("no file to copy")
            return False

    def set_input_mmcif(self, input_path):
        self.mmcif = input_path

    def set_output_mmcif(self, output_path):
        self.output_cif = output_path

    def parse_mmcif(self):
        if self.mmcif:
            try:
                logging.debug("parsing {}".format(self.mmcif))
                self.cList = self.io.readFile(self.mmcif)
                self.mmcif_data = self.cList[0]
                return self.mmcif_data
            except Exception as e:
                logging.error("failed to parse: %s" % self.mmcif)
                logging.error(e)

        return None

    def get_category(self, category):
        if not self.mmcif_data:
            self.parse_mmcif()
        if self.mmcif_data:
            self.dcObj = self.mmcif_data.getObj(category)
            return self.dcObj
        return None

    def get_category_keys(self, category):
        cat_dict = {}
        if self.mmcif_data:
            self.dcObj = self.get_category(category)
            if self.dcObj is not None:
                keys_in_list_of_sets = self.dcObj.getAttributeListWithOrder()
                for key in keys_in_list_of_sets:
                    cat_dict[key[0]] = key[1]
        return cat_dict

    def get_category_list_of_dictionaries(self, category):
        return_list = []
        cat_items = self.get_category_keys(category=category)
        cat_data = self.get_category(category=category)
        if cat_data is not None:
            for row in range(len(cat_data.data)):
                row_dict = {}
                for item in cat_items:
                    value = cat_data.getValueOrDefault(
                        attributeName=item, defaultValue="", rowIndex=row
                    )
                    row_dict[item] = value
                return_list.append(row_dict)
        return return_list

    def get_cat_item_value(self, category, item, row=0):
        value = self.get_cat_item_values_row(category=category, item=item, row=row)
        return value

    def get_cat_item_values(self, category, item):
        value_list = []
        cat = self.get_category(category=category)
        if cat is not None:
            for row in range(len(cat.data)):
                value = cat.getValueOrDefault(
                    attributeName=item, defaultValue="", rowIndex=row
                )
                value_list.append(value)

        return value_list

    def get_cat_item_values_row(self, category, item, row):
        value = ""
        cat = self.get_category(category=category)
        if cat is not None:
            try:
                value = cat.getValueOrDefault(
                    attributeName=item, defaultValue="", rowIndex=row
                )
            except Exception as e:
                logging.error(e)
                pass
        return value

    def get_cat_items_values(self, category, item_list):
        value_list = []
        cat = self.get_category(category=category)
        if cat is not None:
            for row in range(len(cat.data)):
                row_list = []
                for item in item_list:
                    value = self.get_cat_item_values_row(
                        category=category, item=item, row=row
                    )
                    row_list.append(value)
                value_list.append(row_list)

        return value_list

    def remove_category(self, category):
        dcObj = self.get_category(category)
        logging.debug("removing category: %s" % category)
        indices_to_remove = []
        if dcObj is not None:
            for row in range(len(dcObj.data)):
                indices_to_remove.append(row)
            indices_to_remove = sorted(indices_to_remove, reverse=True)
            for row in indices_to_remove:
                self.remove_row(category=category, row=row)

    def remove_row(self, category, row=0):
        dcObj = self.get_category(category)
        if dcObj is not None:
            row_removed = dcObj.removeRow(row)
            if not row_removed:
                logging.debug("failed to remove row from %s: %s" % (category, row))

    def set_item(self, category, item, value, row_index=0):
        if category:
            dcObj = self.get_category(category)
            if dcObj is not None and item:
                logging.debug(
                    "setting %s.%s to %s on row %s" % (category, item, value, row_index)
                )
                if dcObj.getAttributeIndex(item) < 0:
                    dcObj.appendAttribute(item)
                dcObj.setValue(value, attributeName=item, rowIndex=row_index)
            else:
                logging.error(
                    'no item given: category "{}", item "{}", value "{}"'.format(
                        category, item, value
                    )
                )
        else:
            logging.error("no category given")

    def set_item_where(
        self,
        category,
        item_to_set,
        value_to_set,
        item_to_test,
        value_to_test,
        item_to_test2=None,
        value_to_test2=None,
    ):
        dcObj = self.get_category(category)
        logging.debug(
            "looking for row where %s.%s = %s" % (category, item_to_test, value_to_test)
        )
        if dcObj is not None:
            for row in range(len(dcObj.data)):
                value1 = dcObj.getValueOrDefault(
                    attributeName=item_to_test, defaultValue="", rowIndex=row
                )
                if item_to_test2:
                    value2 = dcObj.getValueOrDefault(
                        attributeName=item_to_test2, defaultValue="", rowIndex=row
                    )
                    if value1 == value_to_test and value2 == value_to_test2:
                        logging.debug(
                            "found %s and %s on row %s"
                            % (item_to_test, item_to_test2, row)
                        )
                        logging.debug(
                            "setting %s.%s to %s on row %s"
                            % (category, item_to_set, value_to_set, row)
                        )
                        dcObj.setValue(
                            value_to_set, attributeName=item_to_set, rowIndex=row
                        )
                elif value1 == value_to_test:
                    logging.debug("found %s on row %s" % (item_to_test, row))
                    logging.debug(
                        "setting %s.%s to %s on row %s"
                        % (category, item_to_set, value_to_set, row)
                    )
                    dcObj.setValue(
                        value_to_set, attributeName=item_to_set, rowIndex=row
                    )
        else:
            cat_dict = dict()
            cat_dict[category] = {
                "items": [item_to_set, item_to_test],
                "values": [[value_to_set, value_to_test]],
            }
            if item_to_test2 and value_to_test2:
                cat_dict[category]["items"].append(item_to_test2)
                cat_dict[category]["values"][0].append(value_to_test2)

            self.add_new_category(
                category=category, cat_item_value_dict=cat_dict[category]
            )

    def add_new_category(self, category, cat_item_value_dict):
        logging.info('adding category "{}" to the mmcif'.format(category))
        myCat = DataCategory(
            category, cat_item_value_dict["items"], cat_item_value_dict["values"]
        )
        logging.debug(myCat)
        self.mmcif_data.append(myCat)

    def add_data_to_category(self, cat_dict):
        ok = self.check_cif_dict_format(cat_dict)

        if ok:
            for category in cat_dict:
                dcObj = self.get_category(category)
                if dcObj is not None:
                    for item in cat_dict[category]["items"]:
                        if item:
                            if dcObj.getAttributeIndex(item) < 0:
                                dcObj.appendAttributeExtendRows(item)

                    complete_current_row = list(dcObj.getFullRow(index=0))

                    for row in cat_dict[category]["values"]:
                        list_to_modify = list(complete_current_row)
                        for instance, value in enumerate(row):
                            if value is not None:
                                item_index = dcObj.getAttributeIndex(
                                    cat_dict[category]["items"][instance]
                                )
                                list_to_modify[item_index] = value
                        dcObj.data.append(list_to_modify)

                else:
                    self.add_new_category(
                        category=category, cat_item_value_dict=cat_dict[category]
                    )

    def check_cif_dict_format(self, cif_dict):
        """
        expected format
        cat_dict =  {category: {
            'items': ['db_id', 'db_name', 'content_type', 'details'],
            'values': [["bmrb_id", "database_name", "db_code_content_type", "details"]]
            }
        }
        :param cat_dict:
        :return:
        """
        ok = False
        try:
            if cif_dict:
                for category in cif_dict:
                    items = cif_dict[category].get("items", False)
                    values_list = cif_dict[category].get("values", False)
                    if (
                        items
                        and values_list
                        and isinstance(items, list)
                        and isinstance(values_list, list)
                    ):
                        for values in values_list:
                            if len(items) == len(values):
                                ok = True
                            else:
                                ok = False
                    else:
                        ok = False
        except Exception as e:
            logging.error(e)
            ok = False

        logging.debug("cat_dict = {}".format(ok))
        return ok

    def write_mmcif(self):
        logging.debug("writing out: %s" % self.output_cif)
        self.io.writeFile(self.output_cif, self.cList)

    def remove_working_path(self):
        shutil.rmtree(self.working_path)
