#!/usr/bin/env python3
"""
Parser for all_full_cmds.txt to extract operations, binaries, and environment variables.
"""

import json
import re
import sys
from datetime import date
from pathlib import Path

def parse_file(filepath):
    """Parse the all_full_cmds.txt file and extract operations."""

    with open(filepath, 'r') as f:
        content = f.read()

    # Split by --- delimiter
    blocks = content.strip().split('\n---\n')

    operations = []
    all_envvars = set()
    all_binaries = {}

    for i, block in enumerate(blocks):
        if not block.strip():
            continue

        lines = block.strip().split('\n')
        if not lines:
            continue

        # First line is operation name
        first_line = lines[0].strip()
        if first_line.endswith(':'):
            op_name = first_line[:-1]
        else:
            op_name = first_line.split(':')[0] if ':' in first_line else f"unknown_{i}"

        # Extract environment variables
        envvars = extract_envvars(block)
        all_envvars.update(envvars)

        # Extract binaries
        binaries = extract_binaries(block, op_name)

        # Track all binaries
        for binary in binaries:
            bin_key = binary['name']
            if bin_key not in all_binaries:
                all_binaries[bin_key] = binary

        # Check for special notes
        notes = None
        if 'maxitCmd' in block:
            if binaries and any(b['name'] == 'maxitCmd' for b in binaries):
                notes = "Uses maxitCmd variable"
        if 'mapfix_command' in block:
            notes = "Uses mapfix_command function"
        if any('malformed' in str(b.get('path_expr', '')).lower() for b in binaries):
            notes = "Contains malformed extraction artifacts"

        # Check for no binary
        if not binaries:
            notes = "No binary found - environment setup only or complex conditional"

        op_data = {
            "op_name": op_name,
            "envvars": sorted(envvars),
            "binaries": binaries,
            "notes": notes
        }

        operations.append(op_data)

        # Progress
        if (i + 1) % 20 == 0:
            print(f"Progress: processed {i + 1} operations", file=sys.stderr)

    return operations, all_envvars, all_binaries


def extract_envvars(block):
    """Extract environment variables from a block."""
    envvars = set()

    # Pattern: VARNAME=... ; export VARNAME
    # Look for export statements
    export_pattern = r'\bexport\s+([A-Z_][A-Z0-9_]*)\s*'
    matches = re.findall(export_pattern, block)
    envvars.update(matches)

    # Also look for pattern: ; VARNAME= ... ; export VARNAME
    assign_export_pattern = r';\s*([A-Z_][A-Z0-9_]*)\s*='
    matches2 = re.findall(assign_export_pattern, block)
    # Only add if there's a corresponding export
    for var in matches2:
        if f'export {var}' in block:
            envvars.add(var)

    return envvars


def extract_binaries(block, op_name):
    """Extract binary information from a block."""
    binaries = []
    seen_binaries = set()

    # Pattern 1: os.path.join(..., 'bin', 'NAME')
    join_pattern = r"os\.path\.join\(([^,]+),\s*'bin',\s*'([^']+)'\)"
    for match in re.finditer(join_pattern, block):
        path_var = match.group(1).strip()
        binary_name = match.group(2)
        full_expr = match.group(0)

        if binary_name not in seen_binaries:
            seen_binaries.add(binary_name)
            binaries.append({
                "name": binary_name,
                "type": "executable",
                "path_expr": full_expr,
                "path_variable": path_var
            })

    # Pattern 2: os.path.join(..., 'subdirectory', 'bin', 'NAME') - for tools in subdirs
    subdir_join_pattern = r"os\.path\.join\(([^,]+),\s*'([^']+)',\s*'bin',\s*'([^']+)'\)"
    for match in re.finditer(subdir_join_pattern, block):
        path_var = match.group(1).strip()
        subdir = match.group(2)
        binary_name = match.group(3)
        full_expr = match.group(0)

        if binary_name not in seen_binaries:
            seen_binaries.add(binary_name)
            binaries.append({
                "name": binary_name,
                "type": "executable",
                "path_expr": full_expr,
                "path_variable": path_var
            })

    # Pattern 3: Shell scripts (.sh, .csh)
    shell_pattern = r"os\.path\.join\([^)]+,\s*'([^']+\.(?:sh|csh))'\)"
    for match in re.finditer(shell_pattern, block):
        script_name = match.group(1)
        if script_name not in seen_binaries:
            seen_binaries.add(script_name)
            binaries.append({
                "name": script_name,
                "type": "shell_script",
                "path_expr": match.group(0),
                "path_variable": None
            })

    # Pattern 4: JAR files
    jar_pattern = r"os\.path\.join\([^)]+,\s*'([^']+\.jar)'\)"
    for match in re.finditer(jar_pattern, block):
        jar_name = match.group(1)
        if f"java_{jar_name}" not in seen_binaries:
            seen_binaries.add(f"java_{jar_name}")
            binaries.append({
                "name": "java",
                "type": "java_jar",
                "jar": jar_name,
                "path_expr": match.group(0),
                "path_variable": None
            })

    # Pattern 5: Python modules - python -m module.name
    python_module_pattern = r"python\s+-m\s+([a-zA-Z0-9_.]+)"
    for match in re.finditer(python_module_pattern, block):
        module_name = match.group(1)
        if f"python_{module_name}" not in seen_binaries:
            seen_binaries.add(f"python_{module_name}")
            binaries.append({
                "name": "python",
                "type": "python_module",
                "module": module_name,
                "path_expr": None,
                "path_variable": None
            })

    # Pattern 6: Variable binaries
    variable_binaries = {
        'maxitCmd': ('maxit', 'variable'),
        'valCmd': ('validation', 'variable'),
        'dbLoaderCmd': ('db_loader', 'variable'),
        'blastp_command': ('blastp', 'variable'),
        'blastn_command': ('blastn', 'variable'),
        'makeblastdb_command': ('makeblastdb', 'variable'),
    }

    for var_name, (desc, bin_type) in variable_binaries.items():
        # Check if variable is used (not just set)
        if re.search(rf'\b{var_name}\b', block):
            # Look for actual usage patterns - command execution contexts
            usage_patterns = [
                rf"[;+]\s*{var_name}\s*[+\s]",  # ; maxitCmd + or ; maxitCmd
                rf"format\({var_name}\)",         # format(blastp_command)
                rf"\({var_name}\)",               # (blastp_command)
                rf"'\s*\+\s*{var_name}",          # ' + dbLoaderCmd
                rf"{var_name}\s*\+",              # dbLoaderCmd +
            ]
            if any(re.search(p, block) for p in usage_patterns):
                if var_name not in seen_binaries:
                    seen_binaries.add(var_name)
                    binaries.append({
                        "name": var_name,
                        "type": "variable",
                        "path_expr": None,
                        "path_variable": None
                    })

    # Pattern 7: System commands (convert, wget, gunzip, etc.)
    # Only add if not already found as an executable from os.path.join
    system_cmds = ['convert', 'wget', 'gunzip', 'gzip', 'tar']
    for cmd in system_cmds:
        if re.search(rf"['\s;]{cmd}\s", block):
            if cmd not in seen_binaries:
                seen_binaries.add(cmd)
                binaries.append({
                    "name": cmd,
                    "type": "system",
                    "path_expr": None,
                    "path_variable": None
                })

    # Pattern 7b: StdInParse from localAppsPath
    if "'StdInParse'" in block and 'StdInParse' not in seen_binaries:
        seen_binaries.add('StdInParse')
        binaries.append({
            "name": "StdInParse",
            "type": "executable",
            "path_expr": "os.path.join(self.__localAppsPath, 'bin', 'StdInParse')",
            "path_variable": "self.__localAppsPath"
        })

    # Special handling for xmllint - use specific patterns
    # Pattern: os.path.join(self.__localAppsPath, 'bin', 'xmllint')
    xmllint_join = r"os\.path\.join\([^)]*'xmllint'\)"
    if re.search(xmllint_join, block) and 'xmllint' not in seen_binaries:
        seen_binaries.add('xmllint')
        binaries.append({
            "name": "xmllint",
            "type": "executable",
            "path_expr": "os.path.join(self.__localAppsPath, 'bin', 'xmllint')",
            "path_variable": "self.__localAppsPath"
        })
    # Pattern for fsc_check using xmllint directly (system)
    elif "'xmllint --format" in block or "xmllint --" in block:
        if 'xmllint' not in seen_binaries:
            seen_binaries.add('xmllint')
            binaries.append({
                "name": "xmllint",
                "type": "system",
                "path_expr": None,
                "path_variable": None
            })

    # Pattern 8: Function calls like mapfix_command(...)
    func_pattern = r'\b(mapfix_command)\s*\('
    for match in re.finditer(func_pattern, block):
        func_name = match.group(1)
        if func_name not in seen_binaries:
            seen_binaries.add(func_name)
            binaries.append({
                "name": func_name,
                "type": "function",
                "path_expr": None,
                "path_variable": None
            })

    # Pattern 9: Direct executable paths like dssp, stride, pisa
    direct_execs = ['dssp', 'stride', 'pisa', 'cifexch2', 'mmcif2XML', 'CifCheck',
                    'cifexch-v3.2']
    for exe in direct_execs:
        # Look for pattern in os.path.join
        if f"'{exe}'" in block or f'"{exe}"' in block:
            if exe not in seen_binaries:
                seen_binaries.add(exe)
                binaries.append({
                    "name": exe,
                    "type": "executable",
                    "path_expr": None,
                    "path_variable": None
                })

    # Pattern 9b: Pointsuite binaries using ${PTSUITE}/bin/name pattern
    ptsuite_pattern = r'\$\{PTSUITE\}/bin/(\w+)'
    for match in re.finditer(ptsuite_pattern, block):
        exe_name = match.group(1)
        if exe_name not in seen_binaries:
            seen_binaries.add(exe_name)
            binaries.append({
                "name": exe_name,
                "type": "executable",
                "path_expr": f"${{PTSUITE}}/bin/{exe_name}",
                "path_variable": "PTSUITE"
            })

    # Pattern 10: COMMANDS.sh special case for em2em-spider
    if 'COMMANDS.sh' in block:
        if 'COMMANDS.sh' not in seen_binaries:
            seen_binaries.add('COMMANDS.sh')
            binaries.append({
                "name": "COMMANDS.sh",
                "type": "shell_script",
                "path_expr": "os.path.join(self.__wrkPath, 'COMMANDS.sh')",
                "path_variable": "self.__wrkPath"
            })

    return binaries


def format_binary_for_list(binary):
    """Format a binary entry for the distinct list."""
    name = binary['name']
    bin_type = binary['type']

    if bin_type == 'variable':
        return f"{name} (variable)"
    elif bin_type == 'shell_script':
        return f"{name} (shell_script)"
    elif bin_type == 'function':
        return f"{name} (function)"
    elif bin_type == 'java_jar':
        jar = binary.get('jar', '')
        return f"java (jar: {jar})"
    elif bin_type == 'python_module':
        return "python (module)"
    elif bin_type == 'system':
        # For system commands, annotate only if it's a common shell command
        system_shell_cmds = {'convert', 'wget', 'gunzip', 'gzip', 'tar'}
        if name in system_shell_cmds:
            return f"{name} (system)"
        else:
            return name  # xmllint etc - just use the name
    else:
        return name


def main():
    input_file = Path(__file__).parent.parent / 'all_full_cmds.txt'
    output_dir = Path(__file__).parent

    print(f"Parsing {input_file}...", file=sys.stderr)

    operations, all_envvars, all_binaries = parse_file(input_file)

    # Sort operations by name
    operations.sort(key=lambda x: x['op_name'])

    # Count statistics
    total_ops = len(operations)
    ops_with_no_binary = [op for op in operations if not op['binaries']]

    print(f"\nTotal operations: {total_ops}", file=sys.stderr)
    print(f"Operations with no binary: {len(ops_with_no_binary)}", file=sys.stderr)
    for op in ops_with_no_binary:
        print(f"  - {op['op_name']}", file=sys.stderr)

    print(f"Unique environment variables: {len(all_envvars)}", file=sys.stderr)
    print(f"Unique binaries: {len(all_binaries)}", file=sys.stderr)

    # Create operations_final.json
    output_json = {
        "metadata": {
            "source_file": "all_full_cmds.txt",
            "total_operations": total_ops,
            "extraction_date": str(date.today())
        },
        "operations": operations
    }

    json_path = output_dir / 'operations_final.json'
    with open(json_path, 'w') as f:
        json.dump(output_json, f, indent=2)
    print(f"Wrote {json_path}", file=sys.stderr)

    # Create binaries_distinct.txt
    binary_list = set()
    for op in operations:
        for binary in op['binaries']:
            binary_list.add(format_binary_for_list(binary))

    binaries_path = output_dir / 'binaries_distinct.txt'
    with open(binaries_path, 'w') as f:
        for name in sorted(binary_list):
            f.write(name + '\n')
    print(f"Wrote {binaries_path}", file=sys.stderr)

    # Create envvars_distinct.txt
    envvars_path = output_dir / 'envvars_distinct.txt'
    with open(envvars_path, 'w') as f:
        for var in sorted(all_envvars):
            f.write(var + '\n')
    print(f"Wrote {envvars_path}", file=sys.stderr)


if __name__ == '__main__':
    main()
