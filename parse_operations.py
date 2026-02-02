#!/usr/bin/env python3
"""
Parse intermediary JSON files from RcsbDpUtility.py extraction and produce:
1. operations_final.json - Combined structured data for all operations
2. binaries_distinct.txt - All unique binary names
3. envvars_distinct.txt - All unique environment variable names
"""

import json
import os
import re
import sys
from datetime import date
from pathlib import Path

# Configuration
INTERMEDIARY_DIR = Path("/home/wbueno/repos/onedep/py-wwpdb_utils_dp/intermediary")
OUTPUT_DIR = Path("/home/wbueno/repos/onedep/py-wwpdb_utils_dp/parsed")

STEP_METHODS = [
    "__annotationStep",
    "__validateStep",
    "__dbStep",
    "__emStep",
    "__maxitStep",
    "__rcsbStep",
    "__pisaStep",
    "__pointsuiteStep",
    "__sequenceStep",
]

# Category mapping from method names
CATEGORY_MAP = {
    "__annotationStep": "annotation",
    "__validateStep": "validate",
    "__dbStep": "db",
    "__emStep": "em",
    "__maxitStep": "maxit",
    "__rcsbStep": "rcsb",
    "__pisaStep": "pisa",
    "__pointsuiteStep": "pointsuite",
    "__sequenceStep": "sequence",
}


def extract_envvars(cmd_text: str) -> list[str]:
    """
    Extract environment variable names from cmd text.
    Pattern: VARNAME=... ; export VARNAME
    """
    envvars = set()
    # Pattern: VARNAME=... ; export VARNAME (with optional space variations)
    pattern = r"(\w+)=.*?;\s*export\s+(\1)\b"
    for match in re.finditer(pattern, cmd_text):
        envvars.add(match.group(1))

    # Also check for direct export patterns: ; export VARNAME
    export_pattern = r";\s*export\s+(\w+)"
    for match in re.finditer(export_pattern, cmd_text):
        envvars.add(match.group(1))

    return sorted(envvars)


def extract_binary_info(cmd_text: str, branches: list = None) -> dict:
    """
    Extract binary information from cmd text.
    Returns dict with binary details.
    """
    result = {
        "binary": None,
        "binary_type": None,
        "binary_path": None,
        "binary_path_variable": None,
        "module": None,
        "jar": None,
        "parsing_notes": None,
    }

    # Include branch content in search
    full_text = cmd_text
    if branches:
        for branch in branches:
            if branch.get("if_cmd"):
                full_text += f"\n{branch['if_cmd']}"
            if branch.get("else_cmd"):
                full_text += f"\n{branch['else_cmd']}"

    # Priority 1: os.path.join pattern (most common)
    # os.path.join(self.__annotAppsPath, 'bin', 'GetSecondStruct')
    join_pattern = r"os\.path\.join\(([^,]+),\s*['\"]bin['\"],\s*['\"]([^'\"]+)['\"]\)"
    match = re.search(join_pattern, cmd_text)
    if match:
        result["binary_path_variable"] = match.group(1).strip()
        result["binary"] = match.group(2)
        result["binary_type"] = "executable"
        result["binary_path"] = f"os.path.join({match.group(1).strip()}, 'bin', '{match.group(2)}')"
        return result

    # Also check for os.path.join with other directory structures
    # os.path.join(self.__packagePath, 'getsite-cif', 'bin', 'getsite_cif')
    join_pattern2 = r"os\.path\.join\(([^,]+),\s*['\"]([^'\"]+)['\"],\s*['\"]bin['\"],\s*['\"]([^'\"]+)['\"]\)"
    match = re.search(join_pattern2, cmd_text)
    if match:
        result["binary_path_variable"] = match.group(1).strip()
        result["binary"] = match.group(3)
        result["binary_type"] = "executable"
        result["binary_path"] = f"os.path.join({match.group(1).strip()}, '{match.group(2)}', 'bin', '{match.group(3)}')"
        return result

    # os.path.join(self.__packagePath, 'dict', 'bin', 'CifCheck')
    join_pattern3 = r"os\.path\.join\(([^)]+)['\"],\s*['\"]([^'\"]+)['\"]\)"
    # Try to find any os.path.join that ends in a binary-like name
    join_generic = r"os\.path\.join\(([^)]+)\)"
    for match in re.finditer(join_generic, cmd_text):
        join_args = match.group(1)
        # Check if this looks like a binary path
        parts = re.findall(r"['\"]([^'\"]+)['\"]", join_args)
        if parts and "bin" in parts:
            bin_idx = parts.index("bin")
            if bin_idx < len(parts) - 1:
                result["binary"] = parts[bin_idx + 1]
                result["binary_type"] = "executable"
                result["binary_path"] = f"os.path.join({join_args})"
                # Extract path variable
                var_match = re.search(r"(self\.__\w+)", join_args)
                if var_match:
                    result["binary_path_variable"] = var_match.group(1)
                return result

    # Priority 2: Python module calls - check both main cmd and branches
    # python -m wwpdb.utils.dp.metal.findgeo.processFindGeo
    module_pattern = r"python\s+-m\s+([\w.]+)"
    match = re.search(module_pattern, full_text)
    if match:
        result["binary"] = "python"
        result["binary_type"] = "python_module"
        result["module"] = match.group(1)
        return result

    # Priority 3: Java jar calls
    # self.__javaPath + ' -Xms256m -Xmx256m -jar ' + os.path.join(..., 'mapFixAnot.jar')
    jar_pattern = r"['\"]([^'\"]*\.jar)['\"]"
    match = re.search(jar_pattern, cmd_text)
    if match:
        result["binary"] = "java"
        result["binary_type"] = "java_jar"
        result["jar"] = match.group(1)
        # Check for java path variable
        java_var = re.search(r"(self\.__javaPath|self\.__\w*[Jj]ava\w*)", cmd_text)
        if java_var:
            result["binary_path_variable"] = java_var.group(1)
        return result

    # Priority 4: Shell variable binary path
    # ${PTSUITE}/bin/importmats or ${VAR}/bin/name
    shell_var_pattern = r"\$\{(\w+)\}/bin/(\w+)"
    match = re.search(shell_var_pattern, full_text)
    if match:
        result["binary"] = match.group(2)
        result["binary_type"] = "shell_variable_path"
        result["binary_path_variable"] = f"${{{match.group(1)}}}"
        result["binary_path"] = f"${{{match.group(1)}}}/bin/{match.group(2)}"
        return result

    # Priority 5: Variable binary (edge case)
    # maxitCmd + ' -o 8 -i ' + iPath  or  dbLoaderCmd) + ' -server
    var_binary_pattern = r"\+\s*(\w+Cmd)\s*\)"
    match = re.search(var_binary_pattern, cmd_text)
    if match:
        result["binary"] = match.group(1)
        result["binary_type"] = "variable"
        result["parsing_notes"] = f"Uses {match.group(1)} variable instead of direct path"
        return result

    var_binary_pattern2 = r"\+\s*(\w+Cmd)\s*\+\s*['\"]"
    match = re.search(var_binary_pattern2, cmd_text)
    if match:
        result["binary"] = match.group(1)
        result["binary_type"] = "variable"
        result["parsing_notes"] = f"Uses {match.group(1)} variable instead of direct path"
        return result

    # Also check at start of cmd
    var_binary_pattern3 = r"^\s*(\w+Cmd)\s*\+"
    match = re.search(var_binary_pattern3, cmd_text, re.MULTILINE)
    if match:
        result["binary"] = match.group(1)
        result["binary_type"] = "variable"
        result["parsing_notes"] = f"Uses {match.group(1)} variable instead of direct path"
        return result

    # Priority 6: Variable command names like blastp_command, makeblastdb_command
    # ; ' + (blastp_command) + ' or .format(makeblastdb_command)
    var_cmd_pattern = r"\(\s*(\w+_command)\s*\)"
    match = re.search(var_cmd_pattern, cmd_text)
    if match:
        result["binary"] = match.group(1)
        result["binary_type"] = "variable"
        result["parsing_notes"] = f"Uses {match.group(1)} variable for command"
        return result

    # Priority 7: Direct system commands at start of concatenation
    # Look for patterns like: ('convert +repage or 'xmllint --format
    system_cmd_pattern = r"['\(]['\"]\s*(\w+)\s+[+-]"
    match = re.search(system_cmd_pattern, cmd_text)
    if match:
        cmd_name = match.group(1).lower()
        if cmd_name in ["convert", "xmllint", "gzip", "gunzip", "tar", "wget"]:
            result["binary"] = cmd_name
            result["binary_type"] = "system"
            return result

    # Priority 8: Look for common patterns like: ; command args
    system_commands = [
        "convert", "xmllint", "gzip", "gunzip", "tar", "wget"
    ]
    for cmd in system_commands:
        # Check for ; command or 'command
        pattern = rf"(?:;\s*|['\"])\s*{cmd}\b"
        if re.search(pattern, full_text, re.IGNORECASE):
            result["binary"] = cmd
            result["binary_type"] = "system"
            return result

    # Check for .csh scripts
    csh_pattern = r"['\"]([^'\"]+\.csh)['\"]"
    match = re.search(csh_pattern, cmd_text)
    if match:
        result["binary"] = os.path.basename(match.group(1))
        result["binary_type"] = "shell_script"
        return result

    # Check for function calls like mapfix_command()
    func_pattern = r"(\w+_command)\s*\("
    match = re.search(func_pattern, cmd_text)
    if match:
        result["binary"] = match.group(1)
        result["binary_type"] = "function"
        result["parsing_notes"] = f"Uses {match.group(1)} function to generate command"
        return result

    # If no binary found
    result["parsing_notes"] = "No binary detected - may be shell redirections only"
    return result


def extract_input_params(cmd_text: str) -> list[str]:
    """
    Extract all input parameter keys used in the cmd text.
    Looks for self.__inputParamDict['key'] or self.__inputParamDict["key"]
    Also checks branch conditions.
    """
    params = set()

    # Pattern: self.__inputParamDict['key'] or self.__inputParamDict["key"]
    pattern = r"self\.__inputParamDict\[['\"]([^'\"]+)['\"]\]"
    for match in re.finditer(pattern, cmd_text):
        params.add(match.group(1))

    # Pattern: self.__inputParamDict.get('key') or self.__inputParamDict.get("key")
    pattern2 = r"self\.__inputParamDict\.get\(['\"]([^'\"]+)['\"]"
    for match in re.finditer(pattern2, cmd_text):
        params.add(match.group(1))

    # Pattern: 'key' in self.__inputParamDict (branch conditions)
    pattern3 = r"['\"]([^'\"]+)['\"]\s+in\s+self\.__inputParamDict"
    for match in re.finditer(pattern3, cmd_text):
        params.add(match.group(1))

    return sorted(params)


def process_operation(op: dict, method: str, preamble_cmd: str) -> dict:
    """
    Process a single operation and extract all relevant information.
    """
    op_name = op["op_name"]
    line_range = op["line_range"]
    cmd_additions = op.get("cmd_additions", "")
    full_cmd = op.get("full_cmd", "")
    branches = op.get("branches", [])

    # Combine all cmd text for analysis
    all_cmd_text = f"{preamble_cmd}\n{full_cmd}"

    # Also include branch conditions and commands
    branch_text = ""
    for branch in branches:
        branch_text += f"\n{branch.get('condition', '')}"
        if branch.get("if_cmd"):
            branch_text += f"\n{branch['if_cmd']}"
        if branch.get("else_cmd"):
            branch_text += f"\n{branch['else_cmd']}"
    all_cmd_text += branch_text

    # Extract environment variables
    envvars = extract_envvars(all_cmd_text)

    # Extract binary info
    binary_info = extract_binary_info(full_cmd, branches)

    # Extract input params
    input_params = extract_input_params(all_cmd_text)

    # Determine if has conditional args
    has_conditional_args = len(branches) > 0

    return {
        "op_name": op_name,
        "category": CATEGORY_MAP.get(method, "unknown"),
        "method": method,
        "line_range": line_range,
        "envvars": envvars,
        "binary": binary_info["binary"],
        "binary_type": binary_info["binary_type"],
        "binary_path": binary_info["binary_path"],
        "binary_path_variable": binary_info["binary_path_variable"],
        "module": binary_info.get("module"),
        "jar": binary_info.get("jar"),
        "input_params_used": input_params,
        "has_conditional_args": has_conditional_args,
        "parsing_notes": binary_info.get("parsing_notes"),
    }


def load_intermediary_file(method: str) -> dict | None:
    """Load an intermediary JSON file for a given method."""
    filepath = INTERMEDIARY_DIR / f"{method}.json"
    if not filepath.exists():
        print(f"  Warning: {filepath} not found", file=sys.stderr)
        return None

    with open(filepath) as f:
        return json.load(f)


def main():
    print("Parsing intermediary JSON files...")

    all_operations = []
    edge_cases = []
    all_binaries = set()
    all_envvars = set()

    for method in STEP_METHODS:
        print(f"\nProcessing {method}...")
        data = load_intermediary_file(method)
        if not data:
            continue

        preamble_cmd = data.get("preamble_cmd", "")
        operations = data.get("operations", [])

        print(f"  Found {len(operations)} operations")

        for op in operations:
            processed = process_operation(op, method, preamble_cmd)
            all_operations.append(processed)

            # Collect binaries
            if processed["binary"]:
                if processed["binary_type"] == "python_module":
                    all_binaries.add(f"python (module: {processed['module']})")
                elif processed["binary_type"] == "java_jar":
                    all_binaries.add(f"java (jar: {processed['jar']})")
                elif processed["binary_type"] == "variable":
                    all_binaries.add(f"{processed['binary']} (variable)")
                else:
                    all_binaries.add(processed["binary"])

            # Collect envvars
            all_envvars.update(processed["envvars"])

            # Check for edge cases
            if processed["parsing_notes"]:
                edge_cases.append({
                    "op_name": processed["op_name"],
                    "issue": processed["binary_type"] or "no_binary",
                    "details": processed["parsing_notes"],
                })

    # Sort operations by category, then by op_name
    all_operations.sort(key=lambda x: (x["category"], x["op_name"]))

    # Build final output
    output = {
        "metadata": {
            "source_file": "RcsbDpUtility.py",
            "extraction_date": str(date.today()),
            "total_operations": len(all_operations),
        },
        "operations": all_operations,
        "edge_cases": edge_cases,
    }

    # Write operations_final.json
    output_path = OUTPUT_DIR / "operations_final.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nWrote {output_path}")

    # Write binaries_distinct.txt
    binaries_path = OUTPUT_DIR / "binaries_distinct.txt"
    with open(binaries_path, "w") as f:
        for binary in sorted(all_binaries):
            f.write(f"{binary}\n")
    print(f"Wrote {binaries_path} ({len(all_binaries)} binaries)")

    # Write envvars_distinct.txt
    envvars_path = OUTPUT_DIR / "envvars_distinct.txt"
    with open(envvars_path, "w") as f:
        for envvar in sorted(all_envvars):
            f.write(f"{envvar}\n")
    print(f"Wrote {envvars_path} ({len(all_envvars)} envvars)")

    print(f"\nTotal operations: {len(all_operations)}")
    print(f"Edge cases: {len(edge_cases)}")


if __name__ == "__main__":
    main()
