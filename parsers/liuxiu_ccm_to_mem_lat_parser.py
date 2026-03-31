#!/usr/bin/env python3
"""
Parser for ccm_to_mem_lat files (e.g., ccm0todie2_lat_data, ccm1todie2_lat_data, etc.)
These files contain latency data for accessing memory by each node's CPUs.
"""

import argparse
import json
import re


def parse_ccm_to_mem_lat(filepath):
    """Parse ccm_to_mem_lat data file."""
    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Find the separator line
    separator_index = next((i for i, line in enumerate(lines) if '---' in line), -1)
    if separator_index == -1:
        return []

    # The header is the line right before the separator
    header_line = lines[separator_index - 1].strip()
    data_lines = lines[separator_index + 1:]

    # Extract headers
    headers = re.split(r'\s{2,}', header_line)
    headers = [h for h in headers if h.strip() and '->' not in h]

    parsed_data = []
    for line in data_lines:
        line = line.strip()
        if not line:
            continue

        # Split values by 2 or more spaces
        values = re.split(r'\s{2,}', line)

        # The first value is the category (DIE0, DIE1, etc.)
        category = values[0]
        data_values = values[1:]

        row_data = {"Category": category}

        # Pair headers with values
        for i, header in enumerate(headers):
            if i < len(data_values):
                row_data[header] = data_values[i]
            else:
                row_data[header] = ""

        parsed_data.append(row_data)

    return parsed_data


def main():
    parser = argparse.ArgumentParser(
        description='Parse ccm_to_mem_lat data files.'
    )
    parser.add_argument('filepath', help='Path to the data file to parse')
    parser.add_argument('--output', '-o', help='Output JSON file path')

    args = parser.parse_args()

    data = parse_ccm_to_mem_lat(args.filepath)

    output_json = json.dumps(data, indent=2)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(output_json)
        print(f"Parsed data saved to {args.output}")
    else:
        print(output_json)


if __name__ == '__main__':
    main()
