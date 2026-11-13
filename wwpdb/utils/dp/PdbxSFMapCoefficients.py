#
# File:    PdbxSFMapCoefficients.py
##
"""Classes to aid in conversion and manipulation of SF map coefficient files from the validation package."""

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "ezra.peisach@rcsb.org"
__license__ = "Apache 2.0"

import copy
import logging
import os
import shutil
import tempfile
from typing import List, Literal, Optional

from mmcif.api.PdbxContainers import DataContainer
from mmcif.io.IoAdapterCore import IoAdapterCore
from wwpdb.utils.config.ConfigInfo import getSiteId

from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility

logger = logging.getLogger(__name__)


class PdbxSFMapCoefficients:
    def __init__(self, siteid: Optional[str] = None, tmppath: Optional[str] = "/tmp", cleanup: bool = True) -> None:  # noqa: S108
        self.__sf: Optional[List[DataContainer]] = None
        self.__siteid = getSiteId(siteid)
        self.__cleanup = cleanup
        self.__tmppath = tmppath

    def read_mmcif_sf(self, pathin: str) -> bool:
        """Reads PDBx/mmCIF structure factor file with map coefficients

        Return True on success, otherwise False
        """

        logger.debug("Starting read %s", pathin)
        try:
            io = IoAdapterCore()
            self.__sf = io.readFile(pathin)
            return True
        except Exception as e:
            logger.exception("Failing with %s", str(e))
            self.__sf = None
            return False

    def has_map_coeff(self) -> bool:
        """Returns True if read in SF file has map coefficients, else returns False"""
        if self.__sf is None:
            return False

        if len(self.__sf) == 0:
            return False

        # Check first block
        b0 = self.__sf[0]

        c0 = b0.getObj("refln")
        if c0 is None:
            return False

        alist = c0.getAttributeList()
        for att in ["index_h", "index_k", "index_l", "fom", "pdbx_DELFWT", "pdbx_DELPHWT", "pdbx_FWT", "pdbx_PHWT"]:
            if att not in alist:
                logger.debug("Missing %s from sf file", att)
                return False

        return True

    def read_mtz_sf(self, pathin: str) -> bool:
        """Reads MTZ structure factor file

        Return True on success, otherwise False
        """

        logger.debug("Starting mtz read %s", pathin)

        suffix = "-dir"
        prefix = "rcsb-"
        if self.__tmppath is not None and os.path.isdir(self.__tmppath):
            workpath = tempfile.mkdtemp(suffix, prefix, self.__tmppath)
        else:
            workpath = tempfile.mkdtemp(suffix, prefix)

        diagfn = os.path.join(workpath, "sf-convert-diags.cif")
        ciffn = os.path.join(workpath, "sf-convert-datafile.cif")
        dmpfn = os.path.join(workpath, "sf-convert-mtzdmp.log")
        logfn = os.path.join(workpath, "sf-convert.log")

        dp = RcsbDpUtility(siteId=self.__siteid, tmpPath=self.__tmppath)
        dp.imp(pathin)
        dp.op("annot-sf-convert")
        dp.expLog(logfn)
        dp.expList(dstPathList=[ciffn, diagfn, dmpfn])
        if os.path.exists(ciffn):
            ret = self.read_mmcif_sf(ciffn)
        else:
            ret = False

        if self.__cleanup:
            dp.cleanup()
            shutil.rmtree(workpath, ignore_errors=True)
        return ret

    def write_mmcif_coef(self, fopathout: str, twofopathout: str, entry_id: str = "xxxx") -> bool:
        """Writes out two structure factor files with only fo-fc or 2fo-fc coefficients

        Output files are dictionary compliant

        entry.id will be set to entry_id
        """
        if self.__sf is None or len(self.__sf) == 0:
            logger.error("No structure factor data to write")
            return False
        ret1 = self.__write_mmcif(fopathout, "fo", entry_id)
        ret2 = self.__write_mmcif(twofopathout, "2fo", entry_id)
        return ret1 and ret2

    def __write_mmcif(self, pathout: str, coef: Literal["fo", "2fo"], entry_id: str) -> bool:
        """Writes out the specific map coefficients"""

        # Categories that will not be copied
        _striplist: List[str] = ["audit", "diffrn_radiation_wavelength", "exptl_crystal", "reflns_scale"]

        # refln attributes to keep
        _keepattr: List[str] = ["index_h", "index_k", "index_l", "fom"]
        if coef == "fo":
            _keepattr.extend(["pdbx_DELFWT", "pdbx_DELPHWT"])
        else:
            _keepattr.extend(["pdbx_FWT", "pdbx_PHWT"])

        # Datablockname
        blkname = f"{entry_id}{coef}"
        new_cont = DataContainer(blkname)

        if not self.__sf:
            logger.error("No structure factor data to write")
            return False

        # Only care about first block
        blockin = self.__sf[0]

        for objname in blockin.getObjNameList():
            if objname in _striplist:
                continue

            myobj = blockin.getObj(objname)

            # Make a copy of the original - as likely will need to modify
            modobj = copy.deepcopy(myobj)
            if objname == "entry":
                modobj.setValue(entry_id, "id", 0)
            if objname in ["cell", "symmetry"]:
                modobj.setValue(entry_id, "entry_id", 0)
            if objname == "refln":
                # Remove all but what we want
                # Make a copy to ensure not messed with during operation
                for attr in list(modobj.getAttributeList()):
                    if attr not in _keepattr:
                        modobj.removeAttribute(attr)

            new_cont.append(modobj)

        # new_cont.printIt()
        io = IoAdapterCore()
        # Write out a single block
        ret: bool = io.writeFile(pathout, [new_cont])
        return ret
