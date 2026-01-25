#!/usr/bin/env python3
"""
Parser for df_data_stream files (e.g., ccm_in_data, ccm_out_todie2_data, cs_in_data, etc.)
These files contain data stream information with hierarchical Level 1/2/3 structure.

Structure:
- Level 1: Top-level categories (e.g., "Request", "Response", "Request to DRAM")
- Level 2: Metrics with "|-" prefix (e.g., "ChgToX", "VicBlk", "RdBlk")
- Level 3: Sub-metrics with "|  |-" or "|  |_" prefix (e.g., "VicBlkFull", "RdBlkL")
"""

import argparse
import json
import re


def parse_df_data_stream(filepath):
    """Parse df_data_stream data file with proper Level 1/2/3 hierarchy."""
    with open(filepath, 'r') as f:
        lines = f.readlines()

    parsed_data = {
        "sections": []
    }

    current_section = None
    current_level1 = None
    current_level2 = None
    die_labels = []
    cs_labels = []

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Check if this is a header line with Level information
        if line_stripped.startswith("Level 1"):
            parts = re.split(r'\s{2,}', line_stripped)
            # Extract Level headers and DIE labels
            level_headers = [p for p in parts if p.startswith("Level")]
            die_labels = [p for p in parts if p.startswith("DIE") or p.startswith("SKT")]
            current_section = {
                "level_headers": level_headers,
                "die_labels": die_labels,
                "cs_labels": [],
                "level1_categories": []
            }
            parsed_data["sections"].append(current_section)
            continue

        # Check if this is the CS/CCM/IOM label row
        if current_section and re.match(r'^(CS|CCM|IOM)\d', line_stripped):
            parts = re.split(r'\s{2,}', line_stripped)
            current_section["cs_labels"] = parts
            continue

        # Parse the hierarchical structure
        parts = re.split(r'\s{2,}', line_stripped)

        # Determine the level based on prefix pattern
        # Level 1: No prefix, just a category name (e.g., "Request", "Response")
        # Level 2: Starts with "|-" (e.g., "|-  ChgToX")
        # Level 3: Starts with "|  |-" or "|  |_" (e.g., "|  |_  VicBlkFull")

        if not parts:
            continue

        first_part = parts[0]

        # Check for Level 3 (sub-metric under Level 2)
        if first_part == '|' and len(parts) > 1 and parts[1] in ['|-', '|_']:
            # Level 3 metric
            metric_name = parts[2] if len(parts) > 2 else None
            values = extract_values(parts[3:]) if len(parts) > 3 else []

            if metric_name and current_level2:
                current_level2["level3_metrics"].append({
                    "name": metric_name,
                    "values": values,
                    "raw_line": line_stripped
                })
            continue

        # Check for Level 2 (metric with |- or |_ prefix)
        if first_part in ['|-', '|_']:
            metric_name = parts[1] if len(parts) > 1 else None
            values = extract_values(parts[2:]) if len(parts) > 2 else []

            if metric_name and current_level1:
                current_level2 = {
                    "name": metric_name,
                    "values": values,
                    "level3_metrics": [],
                    "raw_line": line_stripped
                }
                current_level1["level2_metrics"].append(current_level2)
            continue

        # Check for Level 1 category (no prefix, single word or phrase)
        # These are lines like "Request", "Response", "Request to DRAM", etc.
        if not first_part.startswith('|') and not re.match(r'^[\d.]+\s*[KMG]?$', first_part):
            # Check if this looks like a category (not a data line)
            # Categories typically have few parts and no numeric values in the first few fields
            is_category = True
            for p in parts[:3]:
                if re.match(r'^[\d.]+\s*[KMG]?$', p):
                    is_category = False
                    break

            if is_category and current_section:
                current_level1 = {
                    "name": first_part,
                    "level2_metrics": [],
                    "raw_line": line_stripped
                }
                current_section["level1_categories"].append(current_level1)
                current_level2 = None
                continue

        # If we get here, it's a data line that doesn't fit the hierarchy
        # Store it as raw data
        if current_section:
            if "misc_entries" not in current_section:
                current_section["misc_entries"] = []
            current_section["misc_entries"].append({
                "raw_line": line_stripped,
                "fields": parts
            })

    return parsed_data


def extract_values(parts):
    """Extract numeric values from parts."""
    values = []
    for p in parts:
        p_clean = p.strip()
        if p_clean and re.match(r'^[\d.]+\s*[KMG]?$', p_clean):
            values.append(p_clean)
        elif p_clean and p_clean not in ['|-', '|_', '|', '']:
            # Non-numeric, non-pipe value
            values.append(p_clean)
    return values


def main():
    parser = argparse.ArgumentParser(
        description='Parse df_data_stream data files with Level 1/2/3 hierarchy.'
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
