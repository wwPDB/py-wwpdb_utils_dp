# This script comments out a bad typing definition for
# validate_merged_intensities in gemmi 0.7.1

import os
import gemmi
import shutil

try:
    loc = gemmi.__file__
    if loc:
        pyifile = loc + "i"
        if os.path.exists(pyifile):
            print(f"Correcting {pyifile}")
            with open(pyifile, "r") as fin:
                lines = fin.readlines()
            changed = False
            for row in range(len(lines)):
                if "validate_merged_intensities" in lines[row]:
                    lines[row] = "# " + lines[row]
                    changed = True
            if changed:
                os.rename(pyifile, pyifile + ".old")
                with open(pyifile, "w") as fout:
                    fout.writelines(lines)
                print("File updated")
except Exception as e:
    print("Exception ", e)
    pass
