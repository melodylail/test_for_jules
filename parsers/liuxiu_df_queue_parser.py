#!/usr/bin/env python3
"""
Parser for df_queue files (e.g., ccm_queue_data, iom_queue_data, cs_queue_data)
These files contain hierarchical queue data with Level 1/2/3 structure.

Structure:
- Queue types (Level 1): REQQ, ORIGDQ, PRBQ, RSPQ
- Level 2 metrics: OCCUPANCY, Request, Bypass Rate, Pick Rate, Kill Rate, etc.
- Level 3 metrics: 0%-25%, 25%-50%, Command Token Unavail, etc.
"""

import argparse
import json
import re


def parse_df_queue(filepath):
    """Parse df_queue data file with proper Level 1/2/3 hierarchy."""
    with open(filepath, 'r') as f:
        lines = f.readlines()

    parsed_data = {
        "sections": []
    }

    current_section = None
    current_level1 = None  # Queue type (REQQ, etc.)
    current_level2 = None  # Metric (OCCUPANCY, Request, etc.)

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Check if this is a header line with Level information
        if "Level 1" in line_stripped:
            parts = re.split(r'\s{2,}', line_stripped)
            level_parts = [p for p in parts if p.startswith("Level")]
            die_parts = [p for p in parts if p.startswith("DIE") or p.startswith("SKT")]

            current_section = {
                "level_headers": level_parts,
                "die_labels": die_parts,
                "ccm_labels": [],
                "queue_types": []
            }
            parsed_data["sections"].append(current_section)
            current_level1 = None
            current_level2 = None
            continue

        # Check if this is the CCM/CS/IOM label row
        if current_section and re.match(r'^(CCM|CS|IOM)\d', line_stripped):
            parts = re.split(r'\s{2,}', line_stripped)
            current_section["ccm_labels"] = parts
            continue

        # Parse the hierarchical structure
        parts = re.split(r'\s{2,}', line_stripped)

        if not parts:
            continue

        first_part = parts[0]

        # Skip empty pipe lines
        if first_part == '|' and len(parts) == 1:
            continue

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

            # Check if next part is also a pipe (nested Level 2 header like "|-  |_  MetricName")
            # This is actually a Level 3 metric under the current Level 2
            if metric_name in ['|-', '|_'] and len(parts) > 2:
                actual_metric_name = parts[2]
                values = extract_values(parts[3:]) if len(parts) > 3 else []
                if actual_metric_name and current_level2:
                    current_level2["level3_metrics"].append({
                        "name": actual_metric_name,
                        "values": values,
                        "raw_line": line_stripped
                    })
                continue

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

        # Check for Level 1 (queue type like REQQ, ORIGDQ, PRBQ, RSPQ)
        # These are standalone words at the start of a line without |- prefix
        if not first_part.startswith('|') and current_section:
            values = extract_values(parts[1:]) if len(parts) > 1 else []

            # Queue types typically have no values on the same line
            if len(values) == 0:
                current_level1 = {
                    "name": first_part,
                    "level2_metrics": [],
                    "raw_line": line_stripped
                }
                current_section["queue_types"].append(current_level1)
                current_level2 = None
            continue

    return parsed_data


def extract_values(parts):
    """Extract numeric values from parts."""
    values = []
    for p in parts:
        p_clean = p.strip()
        # Match numeric values with optional K/M/G suffix or percentage
        if p_clean and re.match(r'^[\d.]+\s*[KMG]?%?$', p_clean):
            values.append(p_clean)
    return values


def main():
    parser = argparse.ArgumentParser(
        description='Parse df_queue data files with Level 1/2/3 hierarchy.'
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
