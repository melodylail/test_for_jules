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

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Check for TARGET_CORE_DIE section header
        if line_stripped.startswith("TARGET_CORE_DIE:"):
            parts = re.split(r'\s{2,}', line_stripped)
            current_target_section = {
                "target_info": parts[0],
                "level_info": parts[1:3] if len(parts) > 2 else [],
                "die_labels": parts[3:] if len(parts) > 3 else [],
                "transaction_types": []
            }
            parsed_data["target_sections"].append(current_target_section)
            continue

        # Check for transaction type (RDBLK, RDSIZED, etc.)
        if line_stripped in ["RDBLK", "RDSIZED", "RDSIZEDNC", "WRSIZED", "WRSIZEDNC", "DIRTY_VICTIM", "CLEAN_VICITM", "ATOMIC"]:
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
