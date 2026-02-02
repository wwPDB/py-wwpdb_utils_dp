#!/usr/bin/env python3
"""
Extract operations from RcsbDpUtility.py using AST.

This script parses the RcsbDpUtility.py file and extracts operation definitions
from the various __*Step methods, outputting JSON files with the full cmd strings.
"""

import ast
import json
import os
from typing import Any

# Source file path
SOURCE_FILE = "/home/wbueno/repos/onedep/py-wwpdb_utils_dp/wwpdb/utils/dp/RcsbDpUtility.py"

# Output directory
OUTPUT_DIR = "/home/wbueno/repos/onedep/py-wwpdb_utils_dp/intermediary"

# Methods to process with their line ranges
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


class VariableTracker:
    """Track variable assignments and classify them as raw or non_raw."""

    def __init__(self):
        self.raw = {}  # String literals, os.path.join with literals, format strings with literals
        self.non_raw = {}  # Method calls, self.__cI.get(), etc.

    def add_variable(self, name: str, node: ast.expr, source_lines: list[str]) -> None:
        """Add a variable and classify it."""
        value_str = self._node_to_string(node, source_lines)
        if self._is_raw(node):
            self.raw[name] = value_str
        else:
            self.non_raw[name] = value_str

    def _is_raw(self, node: ast.expr) -> bool:
        """Check if a node represents a raw (literal) value."""
        if isinstance(node, ast.Constant):
            return isinstance(node.value, str)
        if isinstance(node, ast.JoinedStr):  # f-string
            return all(
                isinstance(v, (ast.Constant, ast.FormattedValue))
                for v in node.values
            )
        if isinstance(node, ast.BinOp):
            # String concatenation or format
            if isinstance(node.op, (ast.Add, ast.Mod)):
                return self._is_raw(node.left) and self._is_raw(node.right)
        if isinstance(node, ast.Call):
            # os.path.join with literals
            if self._is_os_path_join(node):
                return all(self._is_raw(arg) for arg in node.args)
        return False

    def _is_os_path_join(self, node: ast.Call) -> bool:
        """Check if a Call node is os.path.join."""
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == "join":
                if isinstance(node.func.value, ast.Attribute):
                    if node.func.value.attr == "path":
                        if isinstance(node.func.value.value, ast.Name):
                            return node.func.value.value.id == "os"
        return False

    def _node_to_string(self, node: ast.expr, source_lines: list[str]) -> str:
        """Convert an AST node to its string representation."""
        try:
            return ast.unparse(node)
        except Exception:
            # Fallback to source extraction
            if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
                start = node.lineno - 1
                end = node.end_lineno
                lines = source_lines[start:end]
                if hasattr(node, 'col_offset'):
                    if len(lines) == 1:
                        return lines[0][node.col_offset:node.end_col_offset]
                return '\n'.join(lines)
            return "<unknown>"


class CmdBuilder:
    """Build command strings from AST nodes."""

    def __init__(self, variables: VariableTracker, source_lines: list[str]):
        self.variables = variables
        self.source_lines = source_lines
        self.local_vars = {}  # Local variable assignments within operation blocks

    def add_local_var(self, name: str, node: ast.expr) -> None:
        """Track a local variable assignment."""
        self.local_vars[name] = self._node_to_string(node)

    def _node_to_string(self, node: ast.expr) -> str:
        """Convert an AST node to string, substituting known variables."""
        try:
            return ast.unparse(node)
        except Exception:
            return "<unknown>"

    def build_cmd_from_augassign(self, node: ast.AugAssign) -> str:
        """Extract cmd addition from an augmented assignment (cmd += ...)."""
        if isinstance(node.target, ast.Name) and node.target.id == "cmd":
            return self._node_to_string(node.value)
        return ""

    def build_cmd_from_assign(self, node: ast.Assign) -> str | None:
        """Extract cmd assignment (cmd = ...)."""
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "cmd":
                return self._node_to_string(node.value)
        return None


def is_op_comparison(node: ast.Compare) -> list[str] | None:
    """
    Check if this is a comparison of the form 'op == "value"'.
    Returns list of operation names if it is, None otherwise.
    Handles both single comparisons and 'or' conditions.
    """
    ops = []

    # Check if left side is 'op'
    if isinstance(node.left, ast.Name) and node.left.id == "op":
        for comparator in node.comparators:
            if isinstance(comparator, ast.Constant) and isinstance(comparator.value, str):
                ops.append(comparator.value)

    return ops if ops else None


def extract_op_names_from_test(test_node: ast.expr) -> list[str]:
    """
    Extract operation names from an if/elif test expression.
    Handles: op == "name", (op == "a") or (op == "b"), etc.
    """
    ops = []

    if isinstance(test_node, ast.Compare):
        result = is_op_comparison(test_node)
        if result:
            ops.extend(result)

    elif isinstance(test_node, ast.BoolOp):
        if isinstance(test_node.op, ast.Or):
            for value in test_node.values:
                if isinstance(value, ast.Compare):
                    result = is_op_comparison(value)
                    if result:
                        ops.extend(result)

    return ops


def is_op_check(test_node: ast.expr) -> bool:
    """Check if this test node is checking the 'op' variable."""
    ops = extract_op_names_from_test(test_node)
    return len(ops) > 0


def extract_cmd_statements(body: list[ast.stmt], source_lines: list[str]) -> tuple[str, list[dict]]:
    """
    Extract cmd statements from a list of statements.
    Returns (cmd_string, branches) where branches contains nested if/else that don't check op.
    """
    cmd_parts = []
    branches = []
    local_vars = {}

    for stmt in body:
        if isinstance(stmt, ast.AugAssign):
            # cmd += ...
            if isinstance(stmt.target, ast.Name) and stmt.target.id == "cmd":
                cmd_str = ast.unparse(stmt.value)
                # Substitute local variables
                for _ in range(5):
                    for var_name, var_value in local_vars.items():
                        if var_name in cmd_str and not var_name.startswith("self."):
                            cmd_str = cmd_str.replace(var_name, f"({var_value})")
                cmd_parts.append(f"cmd += {cmd_str}")

        elif isinstance(stmt, ast.Assign):
            # Check for cmd = ... or local variable assignments
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    if target.id == "cmd":
                        cmd_str = ast.unparse(stmt.value)
                        cmd_parts.append(f"cmd = {cmd_str}")
                    else:
                        # Local variable assignment
                        local_vars[target.id] = ast.unparse(stmt.value)

        elif isinstance(stmt, ast.If):
            # Check if this is a nested branch (not checking op)
            if not is_op_check(stmt.test):
                branch = extract_branch(stmt, source_lines, local_vars)
                if branch:
                    branches.append(branch)
                    # Also add any cmd from the branch to the main cmd if it's unconditional
                    # Actually, branches are conditional, so we track them separately

    return "\n".join(cmd_parts), branches


def extract_branch(if_node: ast.If, source_lines: list[str], parent_vars: dict) -> dict | None:
    """Extract a nested branch (if/else inside an operation block)."""
    condition = ast.unparse(if_node.test)

    # Extract cmd from the if body
    if_cmd_parts = []
    for stmt in if_node.body:
        if isinstance(stmt, ast.AugAssign):
            if isinstance(stmt.target, ast.Name) and stmt.target.id == "cmd":
                if_cmd_parts.append(f"cmd += {ast.unparse(stmt.value)}")
        elif isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name) and target.id == "cmd":
                    if_cmd_parts.append(f"cmd = {ast.unparse(stmt.value)}")

    # Extract cmd from else body if present
    else_cmd_parts = []
    for stmt in if_node.orelse:
        if isinstance(stmt, ast.AugAssign):
            if isinstance(stmt.target, ast.Name) and stmt.target.id == "cmd":
                else_cmd_parts.append(f"cmd += {ast.unparse(stmt.value)}")
        elif isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name) and target.id == "cmd":
                    else_cmd_parts.append(f"cmd = {ast.unparse(stmt.value)}")
        elif isinstance(stmt, ast.If):
            # elif case - recursively extract
            pass  # Handle elif chains

    if if_cmd_parts or else_cmd_parts:
        branch_data = {
            "condition": condition,
            "if_cmd": "\n".join(if_cmd_parts) if if_cmd_parts else None,
        }
        if else_cmd_parts:
            branch_data["else_cmd"] = "\n".join(else_cmd_parts)
        return branch_data

    return None


def extract_preamble(body: list[ast.stmt], source_lines: list[str]) -> tuple[str, int]:
    """
    Extract preamble code (before first if op ==) and return (preamble_cmd, first_op_index).
    """
    cmd_parts = []
    first_op_idx = 0

    for i, stmt in enumerate(body):
        if isinstance(stmt, ast.If):
            if is_op_check(stmt.test):
                first_op_idx = i
                break

        if isinstance(stmt, ast.AugAssign):
            if isinstance(stmt.target, ast.Name) and stmt.target.id == "cmd":
                cmd_parts.append(f"cmd += {ast.unparse(stmt.value)}")

        elif isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name) and target.id == "cmd":
                    cmd_parts.append(f"cmd = {ast.unparse(stmt.value)}")

    return "\n".join(cmd_parts), first_op_idx


def extract_variables(body: list[ast.stmt], source_lines: list[str]) -> dict:
    """Extract variable assignments from method body."""
    raw_vars = {}
    non_raw_vars = {}

    for stmt in body:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Attribute):
                    # self.__varName = ...
                    if isinstance(target.value, ast.Name):
                        var_name = target.attr
                        value_str = ast.unparse(stmt.value)

                        # Classify as raw or non_raw
                        if is_raw_value(stmt.value):
                            raw_vars[var_name] = value_str
                        else:
                            non_raw_vars[var_name] = value_str

                elif isinstance(target, ast.Name):
                    # Local variable assignment (like iPath, oPath, etc.)
                    var_name = target.id
                    value_str = ast.unparse(stmt.value)

                    if is_raw_value(stmt.value):
                        raw_vars[var_name] = value_str
                    else:
                        non_raw_vars[var_name] = value_str

        # Check for if-else blocks that define variables (like the cmd initialization pattern)
        if isinstance(stmt, ast.If):
            # Only process if this isn't an op check
            if not is_op_check(stmt.test):
                # Look for assignments in both branches
                pass  # Could extend to track conditional variables

    return {"raw": raw_vars, "non_raw": non_raw_vars}


def is_raw_value(node: ast.expr) -> bool:
    """Check if a value is a raw literal (string, formatted string with literals)."""
    if isinstance(node, ast.Constant):
        return isinstance(node.value, str)
    if isinstance(node, ast.JoinedStr):
        return True  # f-string is considered raw
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
        # String formatting with %
        return isinstance(node.left, ast.Constant)
    return False


def get_if_body_end_line(if_node: ast.If) -> int:
    """Get the end line of just the if body, not including elif/else."""
    if if_node.body:
        last_stmt = if_node.body[-1]
        return last_stmt.end_lineno or last_stmt.lineno
    return if_node.lineno


def extract_operation(if_node: ast.If, source_lines: list[str]) -> list[dict]:
    """
    Extract operation(s) from an if/elif statement.
    Returns a list because 'or' conditions create multiple entries.
    """
    operations = []

    # Get operation names from the test
    op_names = extract_op_names_from_test(if_node.test)
    if not op_names:
        return operations

    # Get line range - just for this block, not the entire elif chain
    start_line = if_node.lineno
    end_line = get_if_body_end_line(if_node)

    # Extract cmd statements and branches from the if body
    cmd_additions, branches = extract_cmd_statements(if_node.body, source_lines)

    # Create an entry for each operation name (handles 'or' conditions)
    for op_name in op_names:
        operation = {
            "op_name": op_name,
            "line_range": [start_line, end_line],
            "cmd_additions": cmd_additions,
            "full_cmd": None,  # Will be filled in later
        }
        if branches:
            operation["branches"] = branches
        operations.append(operation)

    return operations


def extract_elif_chain(if_node: ast.If, source_lines: list[str]) -> list[dict]:
    """Extract all operations from an if/elif chain."""
    all_operations = []

    # Process the main if
    ops = extract_operation(if_node, source_lines)
    all_operations.extend(ops)

    # Process elif chain (in orelse)
    for stmt in if_node.orelse:
        if isinstance(stmt, ast.If):
            # This is an elif
            if is_op_check(stmt.test):
                ops = extract_operation(stmt, source_lines)
                all_operations.extend(ops)
                # Recurse into its orelse for more elifs
                more_ops = extract_elif_chain(stmt, source_lines)
                all_operations.extend(more_ops)

    return all_operations


def process_method(method_node: ast.FunctionDef, source_lines: list[str]) -> dict:
    """Process a single step method and extract all operations."""
    method_name = method_node.name
    body = method_node.body

    # Extract variables
    variables = extract_variables(body, source_lines)

    # Extract preamble
    preamble_cmd, first_op_idx = extract_preamble(body, source_lines)

    # Find and process all if op == chains
    operations = []
    seen_ops = set()  # Track (op_name, start_line) to avoid duplicates

    for stmt in body[first_op_idx:]:
        if isinstance(stmt, ast.If) and is_op_check(stmt.test):
            ops = extract_operation(stmt, source_lines)
            for op in ops:
                key = (op["op_name"], op["line_range"][0])
                if key not in seen_ops:
                    seen_ops.add(key)
                    operations.append(op)

            # Process elif chain
            elif_ops = extract_elif_chain(stmt, source_lines)
            for op in elif_ops:
                key = (op["op_name"], op["line_range"][0])
                if key not in seen_ops:
                    seen_ops.add(key)
                    operations.append(op)

    # Filter out operations that don't modify cmd (post-processing checks)
    operations = [
        op for op in operations
        if op["cmd_additions"].strip() or op.get("branches")
    ]

    # Build full_cmd for each operation
    for op in operations:
        if preamble_cmd and op["cmd_additions"]:
            op["full_cmd"] = preamble_cmd + "\n" + op["cmd_additions"]
        elif preamble_cmd:
            op["full_cmd"] = preamble_cmd
        else:
            op["full_cmd"] = op["cmd_additions"]

    return {
        "method": method_name,
        "line_range": [method_node.lineno, method_node.end_lineno],
        "preamble_cmd": preamble_cmd,
        "variables": variables,
        "operations": operations,
    }


def find_method(tree: ast.Module, method_name: str) -> ast.FunctionDef | None:
    """Find a method definition in the AST."""
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == method_name:
            return node
    return None


def main():
    # Read source file
    with open(SOURCE_FILE, "r") as f:
        source = f.read()

    source_lines = source.splitlines()

    # Parse AST
    tree = ast.parse(source)

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Process each method
    for method_name in STEP_METHODS:
        print(f"Processing {method_name}...")

        method_node = find_method(tree, method_name)
        if method_node is None:
            print(f"  Warning: Method {method_name} not found")
            continue

        result = process_method(method_node, source_lines)

        # Write output
        output_path = os.path.join(OUTPUT_DIR, f"{method_name}.json")
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)

        print(f"  Found {len(result['operations'])} operations")
        print(f"  Output: {output_path}")

    print("\nDone!")


if __name__ == "__main__":
    main()