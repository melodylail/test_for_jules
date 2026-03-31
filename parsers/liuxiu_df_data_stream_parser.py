#!/usr/bin/env python3
"""
Parser for df_data_stream files (e.g., ccm_in_data, ccm_out_todie2_data, cs_in_data, etc.)
These files contain data stream information with hierarchical Level 1/2/3 structure.

Two formats are supported:

Format A (cs_in_data, ccm_out_todie2_data):
- Level 1: Categories without values (e.g., "Request", "Request to DRAM")
- Level 2: Metrics with "|-" prefix and values
- Level 3: Sub-metrics with "|  |-" or "|  |_" prefix

Format B (ccm_in_data):
- Level 1: Metrics with values directly (no category wrapper)
- Level 2: Sub-metrics with "|-" prefix
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
    header_line_count = 0
    pending_target_info = None  # Store target info until next section is created

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Check for TARGET_CORE_DIE or SOURCE_CORE_DIE header
        if line_stripped.startswith("TARGET_CORE_DIE:") or line_stripped.startswith("SOURCE_CORE_DIE:"):
            # Store this to add to the next section
            pending_target_info = line_stripped
            continue

        # Check if this is a header line with Level information
        if "Level 1" in line_stripped:
            parts = re.split(r'\s{2,}', line_stripped)
            level_headers = [p for p in parts if p.startswith("Level")]
            die_labels = [p for p in parts if p.startswith("DIE") or p.startswith("SKT")]

            # Always create a new section for each Level header
            current_section = {
                "level_headers": level_headers,
                "die_labels": die_labels,
                "cs_labels": [],
                "level1_categories": []
            }
            # Add pending target info if any
            if pending_target_info:
                current_section["target_info"] = pending_target_info
                pending_target_info = None
            parsed_data["sections"].append(current_section)
            current_level1 = None
            current_level2 = None

            header_line_count = 1
            continue

        # Check if this is the CS/CCM/IOM label row (comes after Level header)
        if header_line_count == 1 and re.match(r'^(CS|CCM|IOM)\d', line_stripped):
            parts = re.split(r'\s{2,}', line_stripped)
            if current_section:
                current_section["cs_labels"] = parts
            header_line_count = 0
            continue

        header_line_count = 0

        # Parse the hierarchical structure
        parts = re.split(r'\s{2,}', line_stripped)

        if not parts:
            continue

        first_part = parts[0]

        # Check for Level 3 (sub-metric under Level 2)
        # Pattern: "|  |-  MetricName  values..." or "|  |_  MetricName  values..."
        if first_part == '|' and len(parts) > 1 and parts[1] in ['|-', '|_']:
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
        # Pattern: "|-  MetricName  values..." or "|_  MetricName  values..."
        if first_part in ['|-', '|_']:
            metric_name = parts[1] if len(parts) > 1 else None
            values = extract_values(parts[2:]) if len(parts) > 2 else []

            if metric_name:
                current_level2 = {
                    "name": metric_name,
                    "values": values,
                    "level3_metrics": [],
                    "raw_line": line_stripped
                }
                if current_level1:
                    current_level1["level2_metrics"].append(current_level2)
                elif current_section:
                    # Format B: Level 2 directly under section (no Level 1 category)
                    if "level2_metrics" not in current_section:
                        current_section["level2_metrics"] = []
                    current_section["level2_metrics"].append(current_level2)
            continue

        # Check for Level 1
        # Could be a category (no values) or a metric with values
        if not first_part.startswith('|') and current_section:
            # Extract values from the rest of the parts
            values = extract_values(parts[1:]) if len(parts) > 1 else []

            # Determine if this is a category (no values) or a metric (has values)
            has_values = len(values) > 0

            if has_values:
                # Format B: Level 1 metric with values
                current_level1 = {
                    "name": first_part,
                    "values": values,
                    "level2_metrics": [],
                    "raw_line": line_stripped
                }
                current_section["level1_categories"].append(current_level1)
                current_level2 = None
            else:
                # Format A: Level 1 category without values
                current_level1 = {
                    "name": first_part,
                    "level2_metrics": [],
                    "raw_line": line_stripped
                }
                current_section["level1_categories"].append(current_level1)
                current_level2 = None
            continue

    return parsed_data


def extract_values(parts):
    """Extract numeric values from parts."""
    values = []
    for p in parts:
        p_clean = p.strip()
        # Match numeric values with optional K/M/G suffix
        if p_clean and re.match(r'^[\d.]+\s*[KMG]?$', p_clean):
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
