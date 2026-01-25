#!/usr/bin/env python3
"""
Parser for df_detail_lat files (e.g., ccm2todie2_latency_data, cs2todie2_latency_data, iom2todie2_latency_data)
These files contain detailed latency data with TARGET_CORE_DIE sections and transaction types.

Structure:
- Target header: TARGET_CORE_DIE:2 or SOURCE_CORE_DIE:X
- Transaction types (Level 1): RDBLK, RDSIZED, DIRTY_VICTIM, etc.
- Level 2 metrics: Transaction, AVG LAT(ns), SDP Latency Histogram, FTI Latency Histogram
- Level 3 metrics: SDP, FTI, 0ns-50ns, 50ns-100ns, etc.
"""

import argparse
import json
import re


def parse_df_detail_lat(filepath):
    """Parse df_detail_lat data file with proper Level 1/2/3 hierarchy."""
    with open(filepath, 'r') as f:
        lines = f.readlines()

    parsed_data = {
        "sections": []
    }

    current_section = None
    current_level1 = None  # Transaction type (RDBLK, etc.)
    current_level2 = None  # Metric category (Transaction, AVG LAT, etc.)
    pending_target_info = None

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Check for TARGET_CORE_DIE or SOURCE_CORE_DIE section header
        if line_stripped.startswith("TARGET_CORE_DIE:") or line_stripped.startswith("SOURCE_CORE_DIE:"):
            parts = re.split(r'\s{2,}', line_stripped)
            pending_target_info = parts[0]

            # Check if Level info is on the same line
            level_parts = [p for p in parts if p.startswith("Level")]
            die_parts = [p for p in parts if p.startswith("DIE") or p.startswith("SKT")]

            if level_parts:
                current_section = {
                    "target_info": pending_target_info,
                    "level_headers": level_parts,
                    "die_labels": die_parts,
                    "ccm_labels": [],
                    "transaction_types": []
                }
                parsed_data["sections"].append(current_section)
                pending_target_info = None
                current_level1 = None
                current_level2 = None
            continue

        # Check if this is a Level header line
        if "Level 1" in line_stripped or "Level 2" in line_stripped:
            parts = re.split(r'\s{2,}', line_stripped)
            level_parts = [p for p in parts if p.startswith("Level")]
            die_parts = [p for p in parts if p.startswith("DIE") or p.startswith("SKT")]

            current_section = {
                "level_headers": level_parts,
                "die_labels": die_parts,
                "ccm_labels": [],
                "transaction_types": []
            }
            if pending_target_info:
                current_section["target_info"] = pending_target_info
                pending_target_info = None
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
            # Check if next part is also a pipe (nested Level 2 header like "|-  |-  SDP")
            if metric_name in ['|-', '|_'] and len(parts) > 2:
                # This is actually a Level 3 metric
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

        # Check for Level 1 (transaction type like RDBLK, RDSIZED, etc.)
        # These are standalone words at the start of a line without |- prefix
        if not first_part.startswith('|') and current_section:
            # Check if this looks like a transaction type (uppercase or mixed case)
            values = extract_values(parts[1:]) if len(parts) > 1 else []

            # Transaction types typically have no values on the same line
            if len(values) == 0:
                current_level1 = {
                    "name": first_part,
                    "level2_metrics": [],
                    "raw_line": line_stripped
                }
                current_section["transaction_types"].append(current_level1)
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
        description='Parse df_detail_lat data files with Level 1/2/3 hierarchy.'
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
