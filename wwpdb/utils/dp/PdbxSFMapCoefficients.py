#
# File:    PdbxSFMapCoefficients.py
##
"""  lasses to aid in conversion and manipulation of SF files from the validation package.
"""

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peosach"
__email__ = "ezra.peisach@rcsb.org"
__license__ = "Apache 2.0"

import logging
import copy

from mmcif.io.IoAdapterCore import IoAdapterCore
from mmcif.api.PdbxContainers import DataContainer

logger = logging.getLogger(__name__)


class PdbxSFMapCoefficients(object):
    def __init__(self):
        self.__sf = None

    def read_mmcif_sf(self, pathin):
        """Reads PDBx/mmCIF structure file

            Return True on success, otherwise False
        """

        logger.debug("Starting read %s" % pathin)
        try:
            io = IoAdapterCore()
            self.__sf = io.readFile(pathin)
            return True
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.__sf = None
            return False

    def write_mmcif_coef(self, fopathout, twofopathout, entry_id='xxxx'):
        """Writes out two structure factor files with only fo-fc or 2fo-fc coefficients

            Output files are dictionary compliant

            entry.id will be set to entry_id
        """
        ret = self.__write_mmcif(fopathout, 'fo', entry_id)
        ret = self.__write_mmcif(twofopathout, '2fo', entry_id)
        pass

    def __write_mmcif(self, pathout, coef, entry_id):
        """Writes out the specific map coefficients

        """

        # Categories that will not be copied
        _striplist = ['audit',
                      'diffrn_radiation_wavelength',
                      'exptl_crystal',
                      'reflns_scale'
                      ]

        # refln attributes to keep
        _keepattr = ['index_h', 'index_k', 'index_l', 'fom']
        if coef == 'fo':
            _keepattr.extend(['pdbx_DELFWT', 'pdbx_DELPHWT'])
        else:
            _keepattr.extend(['pdbx_FWT', 'pdbx_PHWT'])



        # Datablockname
        blkname = "{}{}".format(entry_id, coef)
        new_cont = DataContainer(blkname)

        # Only care about first block
        blockin = self.__sf[0]

        for objname in blockin.getObjNameList():
            if objname in _striplist:
                continue

            myobj = blockin.getObj(objname)

            # Make a copy of the original - as likely will need to modify
            modobj = copy.deepcopy(myobj)
            if objname == 'entry':
                modobj.setValue(entry_id, 'id', 0)
            if objname in ['cell', 'symmetry']:
                modobj.setValue(entry_id, 'entry_id', 0)
            if objname == 'refln':
                # Remove all but what we want
                # Make a copy to ensure not messed with during operation
                for attr in list(modobj.getAttributeList()):
                    if attr not in _keepattr:
                        modobj.removeAttribute(attr)

            new_cont.append(modobj)


        #new_cont.printIt()
        io = IoAdapterCore()
        # Write out a single block
        io.writeFile(pathout, [new_cont])


if __name__ == '__main__':
    psf = PdbxSFMapCoefficients()
    ret = psf.read_mmcif_sf('eds.mtz.mmcif')
    print("File read %s" % ret)
    ret = psf.write_mmcif_coef('fo.cif', '2fo.cif', 'zyxw')
