# wwpdb.utils.dp.metal

This package provides utilities for handling metal coordination and related analyses within the wwPDB data processing pipeline.


## Structure
- `findgeo/`: Handles running the FindGeo command and parsing its output for metal geometry analysis.
- `metalcoord/`: Handles running the MetalCoord command and related processing for metal coordination analysis.
- `metal_ref/`: Reference data files for metal coordination, oxidation states, and exceptions.
- `metal_util/`: Utility functions for reading references and running commands related to metal analysis.
- `tests/`: Unit tests for the metal utilities.

## Main Features
- Parsing and processing of metal coordination data.
- Integration with FindGeo for geometry analysis.
- Reference lookups for coordination numbers, oxidation states, and exceptions.
- Utilities for running external commands and reading reference data.

## Usage
Import the relevant modules in your Python code:

```python
from wwpdb.utils.dp.metal.findgeo import runFindGeo
from wwpdb.utils.dp.metal.metal_util import readRef
```

## Reference Data
The `metal_ref` directory contains CSV files with curated reference data for:
- Carbon-metal bonds
- Coordination class mappings
- Metal coordination numbers
- Metal oxidation states
- Threshold exceptions for CCD annotation

## Testing
Unit tests are provided in the `tests/` directory. Run them using your preferred test runner (e.g., pytest or unittest).

## License
See the main repository LICENSE file for details.
