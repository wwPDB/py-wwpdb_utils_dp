# This script comments out a bad typing definition for
# validate_merged_intensities in gemmi 0.7.1

import os

import gemmi

try:
    loc = gemmi.__file__
    if loc:
        pyifile = loc + "i"
        if os.path.exists(pyifile):
            print(f"Correcting {pyifile}")
            with open(pyifile) as fin:
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
except Exception as e:  # noqa: BLE001
    print("Exception ", e)
