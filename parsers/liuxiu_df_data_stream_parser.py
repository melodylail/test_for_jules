#!/usr/bin/env python3
"""
Parser for df_data_stream files (e.g., ccm_in_data, ccm_out_todie2_data, cs_in_data, etc.)
These files contain data stream information with hierarchical Level 1/2 structure.
"""

import argparse
import json
import re


def parse_df_data_stream(filepath):
    """Parse df_data_stream data file."""
    with open(filepath, 'r') as f:
        lines = f.readlines()

    parsed_data = {
        "sections": []
    }

    current_section = None

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Check if this is a header line with Level information
        if line_stripped.startswith("Level 1"):
            parts = re.split(r'\s{2,}', line_stripped)
            current_section = {
                "header": parts[:2],
                "die_labels": parts[2:] if len(parts) > 2 else [],
                "entries": []
            }
            parsed_data["sections"].append(current_section)
            continue

        # Parse data rows
        parts = re.split(r'\s{2,}', line_stripped)

        entry = {
            "raw_line": line_stripped,
            "fields": parts
        }

        if current_section is not None:
            current_section["entries"].append(entry)
        else:
            # Create a default section if none exists
            if not parsed_data["sections"]:
                parsed_data["sections"].append({"entries": []})
            parsed_data["sections"][-1]["entries"].append(entry)

    return parsed_data


def main():
    parser = argparse.ArgumentParser(
        description='Parse df_data_stream data files.'
    )
    parser.add_argument('filepath', help='Path to the data file to parse')
    parser.add_argument('--output', '-o', help='Output JSON file path')

    args = parser.parse_args()

    data = parse_df_data_stream(args.filepath)

    output_json = json.dumps(data, indent=2)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(output_json)
        print(f"Parsed data saved to {args.output}")
    else:
        print(output_json)


if __name__ == '__main__':
    main()
