#!/usr/bin/env python3
"""
Script to enrich operations_final.json with additional data.

To add new enrichment functions:
1. Define a function that takes op_name (str) and returns dict or None
2. Add the function to ENRICHMENT_FUNCTIONS list

Example:
    def get_category(op_name: str) -> dict | None:
        if op_name.startswith("annot-"):
            return {"category": "annotation"}
        return None

    ENRICHMENT_FUNCTIONS = [get_category]
"""

import json
from pathlib import Path
from typing import Callable

# Type alias for enrichment functions
EnrichmentFunc = Callable[[str], dict | None]

# =============================================================================
# ENRICHMENT FUNCTIONS - Add your functions here
# =============================================================================


def example_function(op_name: str) -> dict | None:
    """
    Example enrichment function.

    Args:
        op_name: The operation name (e.g., "annot-merge")

    Returns:
        A dict with fields to add to the operation, or None to skip.

    Example:
        return {"category": "annotation", "priority": 1}
    """
    # TODO: Implement your logic here
    # Example:
    # if op_name.startswith("annot-"):
    #     return {"category": "annotation"}
    return None


# =============================================================================
# REGISTER FUNCTIONS HERE - Add/remove functions from this list
# =============================================================================

ENRICHMENT_FUNCTIONS: list[EnrichmentFunc] = [
    # example_function,  # Uncomment or add your functions here
]


# =============================================================================
# CORE LOGIC - No need to modify below this line
# =============================================================================

def load_operations(filepath: Path) -> dict:
    """Load operations JSON file."""
    with open(filepath, "r") as f:
        return json.load(f)


def save_operations(data: dict, filepath: Path) -> None:
    """Save operations JSON file with pretty formatting."""
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


def enrich_operations(
    data: dict,
    functions: list[EnrichmentFunc],
    verbose: bool = True
) -> dict:
    """
    Apply all enrichment functions to each operation.

    Args:
        data: The full JSON data with 'operations' key
        functions: List of enrichment functions to apply
        verbose: Print progress information

    Returns:
        The enriched data dict
    """
    operations = data.get("operations", [])

    if not functions:
        print("Warning: No enrichment functions registered.")
        return data

    stats = {func.__name__: 0 for func in functions}

    for op in operations:
        op_name = op.get("op_name")
        if not op_name:
            continue

        for func in functions:
            try:
                result = func(op_name)
                if result and isinstance(result, dict):
                    op.update(result)
                    stats[func.__name__] += 1
            except Exception as e:
                print(f"Error in {func.__name__} for '{op_name}': {e}")

    if verbose:
        print(f"\nProcessed {len(operations)} operations")
        print("Enrichments applied per function:")
        for name, count in stats.items():
            print(f"  - {name}: {count}")

    return data


def main():
    """Main entry point."""
    script_dir = Path(__file__).parent
    input_file = script_dir / "operations_final.json"
    output_file = script_dir / "operations_final.json"  # Overwrite in place

    # To save to a different file, uncomment:
    # output_file = script_dir / "operations_enriched.json"

    print(f"Loading: {input_file}")
    data = load_operations(input_file)

    print(f"Running {len(ENRICHMENT_FUNCTIONS)} enrichment function(s)...")
    enriched_data = enrich_operations(data, ENRICHMENT_FUNCTIONS)

    print(f"Saving: {output_file}")
    save_operations(enriched_data, output_file)

    print("Done!")


if __name__ == "__main__":
    main()