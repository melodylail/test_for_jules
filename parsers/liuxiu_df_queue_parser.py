#!/usr/bin/env python3
"""
Parser for df_queue files (e.g., ccm_queue_data, iom_queue_data, cs_queue_data)
These files contain hierarchical queue data with Level 1/2/3 structure.
"""

import argparse
import json
import re


def parse_df_queue(filepath):
    """Parse df_queue data file with hierarchical structure."""
    with open(filepath, 'r') as f:
        lines = f.readlines()

    parsed_data = {
        "sections": []
    }

    current_die_group = None
    current_section = None

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Check if this is a header line with DIE information
        if line_stripped.startswith("Level 1"):
            parts = re.split(r'\s{2,}', line_stripped)
            if len(parts) > 2:
                # Extract DIE labels
                die_labels = parts[2:]
                current_die_group = {
                    "header": parts[:2],
                    "die_labels": die_labels,
                    "entries": []
                }
                parsed_data["sections"].append(current_die_group)
            continue

        # Parse data rows
        parts = re.split(r'\s{2,}', line_stripped)

        if current_die_group is not None:
            entry = {
                "raw_line": line_stripped,
                "fields": parts
            }
            current_die_group["entries"].append(entry)
        else:
            # Create a standalone entry
            entry = {
                "raw_line": line_stripped,
                "fields": parts
            }
            if "sections" not in parsed_data or len(parsed_data["sections"]) == 0:
                parsed_data["sections"].append({"entries": []})
            if "entries" in parsed_data["sections"][-1]:
                parsed_data["sections"][-1]["entries"].append(entry)

    return parsed_data


def main():
    parser = argparse.ArgumentParser(
        description='Parse df_queue data files.'
    )
    parser.add_argument('filepath', help='Path to the data file to parse')
    parser.add_argument('--output', '-o', help='Output JSON file path')

    args = parser.parse_args()

    data = parse_df_queue(args.filepath)

    output_json = json.dumps(data, indent=2)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(output_json)
        print(f"Parsed data saved to {args.output}")
    else:
        print(output_json)


if __name__ == '__main__':
    main()
