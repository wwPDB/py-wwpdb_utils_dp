#!/usr/bin/env python3
"""
Parse all_full_cmds.txt to extract binary and environment variable information.
"""

import re
import json
import sys
from datetime import date
from collections import OrderedDict

INPUT_FILE = "all_full_cmds.txt"
OUTPUT_DIR = "parsed"

# Known variable binaries
KNOWN_VAR_BINARIES = {
    'maxitCmd': 'maxit executable',
    'valCmd': 'validation command',
    'dbLoaderCmd': 'database loader',
    'blastp_command': 'BLAST protein search',
    'blastn_command': 'BLAST nucleotide search',
    'makeblastdb_command': 'BLAST database builder',
    'mapfix_command': 'map fix function',
}


def extract_envvars(lines):
    """Extract environment variables from cmd lines."""
    envvars = set()
    # Pattern: VARNAME= ... ; export VARNAME
    # Also handles: export VARNAME (at end of line)
    for line in lines:
        # Pattern 1: ; VARNAME= ... ; export VARNAME
        matches = re.findall(r";\s*([A-Z_][A-Z0-9_]*)\s*=.*?;\s*export\s+\1", line)
        envvars.update(matches)

        # Pattern 2: export LD_LIBRARY_PATH=... ; (at start)
        matches = re.findall(r"export\s+([A-Z_][A-Z0-9_]*)\s*=", line)
        envvars.update(matches)

    return sorted(list(envvars))


def extract_binaries(lines, op_name):
    """Extract binary information from cmd lines."""
    binaries = []
    notes = []
    full_text = '\n'.join(lines)

    # Track what we've already found
    found_binaries = set()

    for line in lines:
        # Pattern 1: os.path.join(..., 'bin', 'BINARY_NAME')
        # e.g., os.path.join(self.__annotAppsPath, 'bin', 'GetSecondStruct')
        matches = re.findall(r"os\.path\.join\((self\.__[a-zA-Z_]+(?:Path)?|[a-zA-Z_]+Path),\s*'bin',\s*'([^']+)'\)", line)
        for path_var, binary_name in matches:
            if binary_name not in found_binaries:
                # Determine type based on extension
                if binary_name.endswith('.sh') or binary_name.endswith('.csh'):
                    bin_type = "shell_script"
                else:
                    bin_type = "executable"
                binaries.append({
                    "name": binary_name,
                    "type": bin_type,
                    "path_expr": f"os.path.join({path_var}, 'bin', '{binary_name}')",
                    "path_variable": path_var
                })
                found_binaries.add(binary_name)

        # Pattern 1b: os.path.join(..., 'subdir', 'bin', 'BINARY_NAME')
        # e.g., os.path.join(self.__packagePath, 'getsite-cif', 'bin', 'getsite_cif')
        matches = re.findall(r"os\.path\.join\((self\.__[a-zA-Z_]+(?:Path)?|[a-zA-Z_]+Path),\s*'([^']+)',\s*'bin',\s*'([^']+)'\)", line)
        for path_var, subdir, binary_name in matches:
            if binary_name not in found_binaries:
                if binary_name.endswith('.sh') or binary_name.endswith('.csh'):
                    bin_type = "shell_script"
                else:
                    bin_type = "executable"
                binaries.append({
                    "name": binary_name,
                    "type": bin_type,
                    "path_expr": f"os.path.join({path_var}, '{subdir}', 'bin', '{binary_name}')",
                    "path_variable": path_var
                })
                found_binaries.add(binary_name)

        # Pattern 1c: os.path.join(..., 'dict', 'bin', 'BINARY_NAME')
        matches = re.findall(r"os\.path\.join\((self\.__[a-zA-Z_]+(?:Path)?|[a-zA-Z_]+Path),\s*'dict',\s*'bin',\s*'([^']+)'\)", line)
        for path_var, binary_name in matches:
            if binary_name not in found_binaries:
                if binary_name.endswith('.sh') or binary_name.endswith('.csh'):
                    bin_type = "shell_script"
                else:
                    bin_type = "executable"
                binaries.append({
                    "name": binary_name,
                    "type": bin_type,
                    "path_expr": f"os.path.join({path_var}, 'dict', 'bin', '{binary_name}')",
                    "path_variable": path_var
                })
                found_binaries.add(binary_name)

        # Pattern 2: Known variable binaries (maxitCmd, valCmd, etc.)
        for var_name, description in KNOWN_VAR_BINARIES.items():
            if var_name in line and var_name not in found_binaries:
                # Check it's used as a command (not just referenced)
                if re.search(rf"[;+\s]{var_name}\s*[+\)]", line) or \
                   re.search(rf"'\s*\+\s*{var_name}", line) or \
                   re.search(rf"{var_name}\s*\+\s*'", line) or \
                   re.search(rf"\({var_name}\)", line) or \
                   re.search(rf"{var_name}\([^)]*\)", line):  # Function call pattern
                    binaries.append({
                        "name": var_name,
                        "type": "variable" if "_command" not in var_name else "function",
                        "path_expr": None,
                        "path_variable": None,
                        "description": description
                    })
                    found_binaries.add(var_name)

        # Pattern 3: python -m module.name
        matches = re.findall(r"python\s+-m\s+([a-zA-Z0-9_.]+)", line)
        for module_name in matches:
            key = f"python_module:{module_name}"
            if key not in found_binaries:
                binaries.append({
                    "name": "python",
                    "type": "python_module",
                    "module": module_name,
                    "path_expr": None,
                    "path_variable": None
                })
                found_binaries.add(key)

        # Pattern 4: Java JAR files
        # e.g., self.__javaPath + ' -Xms256m -Xmx256m -jar ' + os.path.join(..., 'NAME.jar')
        if 'javaPath' in line and '.jar' in line:
            jar_matches = re.findall(r"os\.path\.join\([^)]+,\s*'([^']+\.jar)'\)", line)
            for jar_name in jar_matches:
                key = f"java:{jar_name}"
                if key not in found_binaries:
                    binaries.append({
                        "name": "java",
                        "type": "java_jar",
                        "jar": jar_name,
                        "path_expr": None,
                        "path_variable": "self.__javaPath"
                    })
                    found_binaries.add(key)

        # Pattern 5: System commands
        # convert, xmllint, wget, gunzip
        system_commands = [
            ('convert', r"convert\s+\+repage"),
            ('xmllint', r"xmllint\s+--"),
            ('wget', r"wget\s+"),
            ('gunzip', r"gunzip\s+"),
            ('gzip', r"gzip\s+-"),
        ]
        for cmd_name, pattern in system_commands:
            if re.search(pattern, line) and cmd_name not in found_binaries:
                binaries.append({
                    "name": cmd_name,
                    "type": "system",
                    "path_expr": None,
                    "path_variable": None
                })
                found_binaries.add(cmd_name)

        # Pattern 6: Shell scripts (.sh, .csh)
        sh_matches = re.findall(r"os\.path\.join\([^)]+,\s*'([^']+\.(sh|csh))'\)", line)
        for script_name, ext in sh_matches:
            if script_name not in found_binaries:
                binaries.append({
                    "name": script_name,
                    "type": "shell_script",
                    "path_expr": None,
                    "path_variable": None
                })
                found_binaries.add(script_name)

        # Pattern 6b: Direct shell script reference without os.path.join
        sh_matches = re.findall(r"'([a-zA-Z_]+\.(sh|csh))'", line)
        for script_name, ext in sh_matches:
            if script_name not in found_binaries:
                binaries.append({
                    "name": script_name,
                    "type": "shell_script",
                    "path_expr": None,
                    "path_variable": None
                })
                found_binaries.add(script_name)

        # Pattern 7: COMMANDS.sh in wrkPath
        if 'COMMANDS.sh' in line and 'COMMANDS.sh' not in found_binaries:
            binaries.append({
                "name": "COMMANDS.sh",
                "type": "shell_script",
                "path_expr": "os.path.join(self.__wrkPath, 'COMMANDS.sh')",
                "path_variable": "self.__wrkPath"
            })
            found_binaries.add('COMMANDS.sh')

        # Pattern 8: ${PTSUITE}/bin/importmats style
        suite_matches = re.findall(r"\$\{([A-Z_]+)\}/bin/([a-zA-Z_]+)", line)
        for suite_var, binary_name in suite_matches:
            if binary_name not in found_binaries:
                binaries.append({
                    "name": binary_name,
                    "type": "executable",
                    "path_expr": f"${{{suite_var}}}/bin/{binary_name}",
                    "path_variable": suite_var
                })
                found_binaries.add(binary_name)

    # Check for malformed extractions (parser artifacts with repeated parentheses)
    if "(self.__inputParamDict.get('(self.__inputParamDict" in full_text:
        notes.append("Contains malformed parser artifacts (nested parentheses)")

    # If no binaries found, mark as null
    if not binaries:
        binaries.append({
            "name": None,
            "type": "none",
            "path_expr": None,
            "path_variable": None
        })
        notes.append("No binary execution detected")

    return binaries, notes if notes else None


def parse_operations(content):
    """Parse all operations from the file content."""
    operations = []
    blocks = content.strip().split('---')

    for i, block in enumerate(blocks):
        block = block.strip()
        if not block:
            continue

        lines = block.split('\n')
        if not lines:
            continue

        # First line should be operation name (ends with :)
        first_line = lines[0].strip()
        if not first_line.endswith(':'):
            print(f"WARNING: Block {i+1} doesn't start with operation name: {first_line[:50]}...", file=sys.stderr)
            continue

        op_name = first_line[:-1]  # Remove trailing colon
        cmd_lines = lines[1:]  # Rest are cmd += lines

        # Progress reporting
        if (len(operations) + 1) % 20 == 0:
            print(f"Processing operation {len(operations) + 1}: {op_name}", file=sys.stderr)

        # Extract data
        envvars = extract_envvars(cmd_lines)
        binaries, notes = extract_binaries(cmd_lines, op_name)

        # Clean up notes
        final_notes = None
        if notes:
            final_notes = "; ".join(notes) if isinstance(notes, list) else notes

        operations.append({
            "op_name": op_name,
            "envvars": envvars,
            "binaries": binaries,
            "notes": final_notes
        })

    return operations


def get_distinct_binaries(operations):
    """Get distinct binary names with annotations."""
    binaries_info = {}  # name -> info

    for op in operations:
        for binary in op['binaries']:
            name = binary['name']
            if name is None:
                continue

            btype = binary['type']

            if name not in binaries_info:
                binaries_info[name] = {
                    'name': name,
                    'type': btype,
                    'modules': set(),
                    'jars': set()
                }

            # Collect additional info
            if btype == 'python_module' and 'module' in binary:
                binaries_info[name]['modules'].add(binary['module'])
            if btype == 'java_jar' and 'jar' in binary:
                binaries_info[name]['jars'].add(binary['jar'])

    # Format output lines
    output_lines = []
    for name in sorted(binaries_info.keys(), key=str.lower):
        info = binaries_info[name]
        btype = info['type']

        annotation = ""
        if btype == 'variable':
            annotation = " (variable)"
        elif btype == 'system':
            annotation = " (system)"
        elif btype == 'shell_script':
            annotation = " (shell_script)"
        elif btype == 'python_module':
            annotation = " (module)"
        elif btype == 'java_jar':
            jars = ', '.join(sorted(info['jars']))
            annotation = f" (jar: {jars})"
        elif btype == 'function':
            annotation = " (function)"

        output_lines.append(f"{name}{annotation}")

    return output_lines


def get_distinct_envvars(operations):
    """Get distinct environment variable names."""
    all_envvars = set()
    for op in operations:
        all_envvars.update(op['envvars'])
    return sorted(list(all_envvars))


def main():
    # Read input file
    with open(INPUT_FILE, 'r') as f:
        content = f.read()

    # Count delimiters
    delimiter_count = content.count('---')
    print(f"Found {delimiter_count} delimiter blocks in input file", file=sys.stderr)

    # Parse operations
    operations = parse_operations(content)
    print(f"Parsed {len(operations)} operations", file=sys.stderr)

    # Sort operations by name
    operations_sorted = sorted(operations, key=lambda x: x['op_name'])

    # Create output JSON
    output = {
        "metadata": {
            "source_file": INPUT_FILE,
            "total_operations": len(operations),
            "extraction_date": str(date.today())
        },
        "operations": operations_sorted
    }

    # Write operations_final.json
    with open(f"{OUTPUT_DIR}/operations_final.json", 'w') as f:
        json.dump(output, f, indent=2)
    print(f"Wrote {OUTPUT_DIR}/operations_final.json", file=sys.stderr)

    # Write binaries_distinct.txt
    distinct_binaries = get_distinct_binaries(operations)
    with open(f"{OUTPUT_DIR}/binaries_distinct.txt", 'w') as f:
        f.write('\n'.join(distinct_binaries) + '\n')
    print(f"Wrote {OUTPUT_DIR}/binaries_distinct.txt ({len(distinct_binaries)} entries)", file=sys.stderr)

    # Write envvars_distinct.txt
    distinct_envvars = get_distinct_envvars(operations)
    with open(f"{OUTPUT_DIR}/envvars_distinct.txt", 'w') as f:
        f.write('\n'.join(distinct_envvars) + '\n')
    print(f"Wrote {OUTPUT_DIR}/envvars_distinct.txt ({len(distinct_envvars)} entries)", file=sys.stderr)

    # Verification
    print(f"\n=== VERIFICATION ===", file=sys.stderr)
    print(f"Input delimiter blocks: {delimiter_count}", file=sys.stderr)
    print(f"Output operations: {len(operations)}", file=sys.stderr)

    # List operations with no binary
    no_binary_ops = [op['op_name'] for op in operations
                     if len(op['binaries']) == 1 and op['binaries'][0]['name'] is None]
    if no_binary_ops:
        print(f"\nOperations with no binary detected ({len(no_binary_ops)}):", file=sys.stderr)
        for op in no_binary_ops:
            print(f"  - {op}", file=sys.stderr)

    # Cross-reference envvars
    json_envvars = set()
    for op in operations:
        json_envvars.update(op['envvars'])
    print(f"\nUnique envvars in JSON: {len(json_envvars)}", file=sys.stderr)
    print(f"Unique envvars in distinct file: {len(distinct_envvars)}", file=sys.stderr)


if __name__ == '__main__':
    main()
