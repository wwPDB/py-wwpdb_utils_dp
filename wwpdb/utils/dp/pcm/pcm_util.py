import os
import csv
import logging

from wwpdb.utils.config.ConfigInfoApp import ConfigInfoAppCommon

from wwpdb.utils.dp.pcm.mmcif import mmcifHandling
from wwpdb.utils.dp.pcm.pcm import (
    gen_pdbx_modification_feature,
    gen_has_protein_modification,
)


class ProteinModificationUtil:
    def __init__(self, dep_id: str, output_cif: str, output_csv: str) -> None:
        self._dep_id = dep_id
        self._output_cif = output_cif
        self._output_csv = output_csv
        self._model_handle = mmcifHandling(depID=dep_id)
        self._ci = ConfigInfoAppCommon()

        self._setup()
    
    def _setup(self):
        self._latest_model = self._model_handle.get_latest_model()

        if not os.path.exists(self._latest_model):
            raise FileNotFoundError(f"Model file {self._latest_model} not found")

    def _create_modified_mmcif(self) -> None:
        self._model_handle.set_output_mmcif(self._output_cif)
        self._model_handle.write_mmcif()

    def _create_missing_data_csv(self, data: list) -> None:
        if data is None:
            logging.warning("No missing data found")
            return

        col_names = [
            "Comp_id",
            "Modified_residue_id",
            "Type",
            "Category",
            "Position",
            "Polypeptide_position",
            "Comp_id_linking_atom",
            "Modified_residue_id_linking_atom",
            "First_instance_model_db_code",
        ]

        with open(self._output_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=col_names)
            writer.writeheader()
            writer.writerows(data)

    def run(self):
        self._model_handle.set_input_mmcif(self._latest_model)
        self._model_handle.parse_mmcif()

        gen_has_protein_modification(self._model_handle)
        missing_data = gen_pdbx_modification_feature(self._ci, self._model_handle)

        self._create_missing_data_csv(data=missing_data)
        self._create_modified_mmcif()
