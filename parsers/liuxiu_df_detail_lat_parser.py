#!/usr/bin/env python3
"""
Parser for df_detail_lat files (e.g., ccm2todie2_latency_data, cs2todie2_latency_data, iom2todie2_latency_data)
These files contain detailed latency data with TARGET_CORE_DIE sections and transaction types.
"""

import argparse
import json
import re


def parse_df_detail_lat(filepath):
    """Parse df_detail_lat data file with complex hierarchical structure."""
    with open(filepath, 'r') as f:
        lines = f.readlines()

    parsed_data = {
        "target_sections": []
    }

    current_target_section = None
    current_transaction_type = None
    expect_level_line = False  # Flag to capture Level/DIE info from next line

    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Check for TARGET_CORE_DIE or SOURCE_CORE_DIE section header
        if line_stripped.startswith("TARGET_CORE_DIE:") or line_stripped.startswith("SOURCE_CORE_DIE:"):
            parts = re.split(r'\s{2,}', line_stripped)
            current_target_section = {
                "target_info": parts[0],
                "level_info": parts[1:3] if len(parts) > 2 else [],
                "die_labels": parts[3:] if len(parts) > 3 else [],
                "transaction_types": []
            }
            parsed_data["target_sections"].append(current_target_section)
            # If header is alone on line, expect Level/DIE info on next line
            if len(parts) == 1:
                expect_level_line = True
            continue

        # Capture Level/DIE header from next line after standalone section header
        if expect_level_line and current_target_section and line_stripped.startswith("Level"):
            parts = re.split(r'\s{2,}', line_stripped)
            # Find Level entries and DIE entries
            level_parts = [p for p in parts if p.startswith("Level")]
            die_parts = [p for p in parts if p.startswith("DIE")]
            current_target_section["level_info"] = level_parts
            current_target_section["die_labels"] = die_parts
            expect_level_line = False
            continue

        expect_level_line = False  # Reset flag if we didn't match

        # Check for transaction type (RDBLK, RDSIZED, etc.) - handle both uppercase and mixed case
        transaction_types_upper = ["RDBLK", "RDSIZED", "RDSIZEDNC", "WRSIZED", "WRSIZEDNC", "DIRTY_VICTIM", "CLEAN_VICITM", "ATOMIC"]
        transaction_types_mixed = ["RdBlk", "RdSizedNC", "WrSized", "WrSizedNC", "Atomic"]
        if line_stripped in transaction_types_upper or line_stripped in transaction_types_mixed:
            current_transaction_type = {
                "type": line_stripped,
                "data": []
            }
            if current_target_section:
                current_target_section["transaction_types"].append(current_transaction_type)
            continue

        # Parse data rows
        parts = re.split(r'\s{2,}', line_stripped)

        entry = {
            "raw_line": line_stripped,
            "fields": parts
        }

        if current_transaction_type:
            current_transaction_type["data"].append(entry)
        elif current_target_section:
            # Add to target section if no transaction type yet
            if "misc_data" not in current_target_section:
                current_target_section["misc_data"] = []
            current_target_section["misc_data"].append(entry)

    return parsed_data


def main():
    parser = argparse.ArgumentParser(
        description='Parse df_detail_lat data files.'
    )
    parser.add_argument('filepath', help='Path to the data file to parse')
    parser.add_argument('--output', '-o', help='Output JSON file path')

    args = parser.parse_args()

    data = parse_df_detail_lat(args.filepath)

    output_json = json.dumps(data, indent=2)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(output_json)
        print(f"Parsed data saved to {args.output}")
    else:
        print(output_json)


if __name__ == '__main__':
    main()
