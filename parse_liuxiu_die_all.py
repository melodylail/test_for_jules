#!/usr/bin/env python3
"""
Master parser script for all files under data/liuxiu/die/
Parses each file to JSON format and saves to results/data/liuxiu/die/
"""

import os
import json
import argparse
import re
from pathlib import Path


def parse_tabular_data(filepath):
    """Generic parser for tabular data files with headers and separator lines."""
    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Find the separator line (contains dashes)
    separator_index = next((i for i, line in enumerate(lines) if '---' in line), -1)
    if separator_index == -1:
        return []

    # The header is the line right before the separator
    header_line = lines[separator_index - 1].strip()
    data_lines = lines[separator_index + 1:]

    # Extract headers, splitting by 2 or more spaces
    headers = re.split(r'\s{2,}', header_line)
    # Filter out descriptive parts (containing ->) and empty strings
    headers = [h for h in headers if h and '->' not in h]

    parsed_data = []
    for line in data_lines:
        line = line.strip()
        if not line:
            continue

        # Split values by 2 or more spaces
        values = re.split(r'\s{2,}', line)

        # The first value is typically the category (DIE, SKT, SYS, etc.)
        category = values[0]
        data_values = values[1:]

        row_data = {"Category": category}

        # Pair headers with the remaining values
        for i, header in enumerate(headers):
            if i < len(data_values):
                row_data[header] = data_values[i]
            else:
                row_data[header] = ""

        parsed_data.append(row_data)

    return parsed_data


def parse_ccm_to_mem_lat(filepath):
    """Parser for ccm_to_mem_lat files (latency data)."""
    return parse_tabular_data(filepath)


def parse_df_queue(filepath):
    """
    Parser for df_queue files (hierarchical queue data).
    Outputs structured format matching CCX version for comparison.
    """
    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Queue types we're looking for
    QUEUE_TYPES = ['REQQ', 'ORIGDQ', 'PRBQ', 'RSPQ', 'RSPDQ']

    result = [{}]
    current_queue = None
    current_subsection = None

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped or line_stripped == '|':
            continue

        # Skip header lines
        if line_stripped.startswith("Level 1"):
            continue

        # Skip CCM header row
        if 'CCM0' in line_stripped and 'CCM1' in line_stripped and line_stripped.count('CCM0') > 1:
            continue

        # Parse line
        parts = re.split(r'\s{2,}', line_stripped)
        if not parts:
            continue

        # Check for queue type
        first_part = parts[0].replace('|-', '').replace('|_', '').replace('|', '').strip()

        if first_part in QUEUE_TYPES:
            current_queue = first_part
            result[0][current_queue] = {}
            current_subsection = None
            continue

        if not current_queue:
            continue

        # Check for subsection (like OCCUPANCY)
        if len(parts) >= 2:
            clean_parts = [p.replace('|-', '').replace('|_', '').replace('|', '').strip()
                          for p in parts if p.strip() and p.strip() not in ['|-', '|_', '|']]

            if len(clean_parts) == 1 and clean_parts[0] in ['OCCUPANCY']:
                current_subsection = clean_parts[0]
                result[0][current_queue][current_subsection] = {}
                continue

            # Data row - extract metric name and values
            # Find where values start (look for numeric values or percentages)
            metric_parts = []
            value_start = 0
            for i, p in enumerate(clean_parts):
                # Check if this looks like a value (number, percentage, or has K/M suffix)
                if re.match(r'^[\d.]+[%KMG]?$', p.replace(' ', '')) or re.match(r'^[\d.]+ [KMG]$', p):
                    value_start = i
                    break
                metric_parts.append(p)

            if metric_parts:
                metric_name = metric_parts[-1] if metric_parts else ''
                # Add prefix for hierarchical structure
                if len(metric_parts) > 1:
                    metric_name = '|' + metric_name

                values = clean_parts[value_start:]

                # Create value dictionary
                value_dict = {}
                for i, val in enumerate(values):
                    die_idx = i // 4
                    ccm_idx = i % 4
                    key = f"DIE{die_idx}_CCM{ccm_idx}"
                    value_dict[key] = val.strip()

                if value_dict and metric_name:
                    result[0][current_queue][metric_name] = value_dict

    return result


def parse_df_detail_lat(filepath):
    """
    Parser for df_detail_lat files (detailed latency data).
    Outputs structured format matching CCX version for comparison.
    """
    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Transaction types we're looking for
    TRANSACTION_TYPES = ["RDBLK", "RDSIZED", "RDSIZEDNC", "WRSIZED", "WRSIZEDNC",
                         "DIRTY_VICTIM", "CLEAN_VICITM", "ATOMIC"]

    result = []
    current_target = None
    current_target_key = None
    current_trans_type = None
    current_metric = None
    current_sub_metric = None
    ccm_labels = []  # CCM0, CCM1, CCM2, CCM3 for each DIE

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped or line_stripped == '|':
            continue

        # Check for TARGET_CORE_DIE header line
        if line_stripped.startswith("TARGET_CORE_DIE:"):
            # Extract die number
            match = re.search(r'TARGET_CORE_DIE:(\d+)', line_stripped)
            if match:
                die_num = match.group(1)
                current_target_key = f"TARGET_CORE_DIE_{die_num}"
                current_target = {}
                result.append({current_target_key: current_target})
            continue

        # Check for CCM labels line (CCM0 CCM1 CCM2 CCM3 ...)
        if 'CCM0' in line_stripped and 'CCM1' in line_stripped:
            # This is the CCM header row, skip it - we'll generate labels
            continue

        # Check for transaction type
        if line_stripped in TRANSACTION_TYPES:
            current_trans_type = line_stripped
            if current_target is not None:
                current_target[current_trans_type] = {}
            current_metric = None
            current_sub_metric = None
            continue

        # Skip if we don't have a target or transaction type yet
        if current_target is None or current_trans_type is None:
            continue

        # Parse data rows - they start with |- or |_
        # Remove leading tree characters
        clean_line = re.sub(r'^[\|\-\s_]+', '', line_stripped)
        if not clean_line:
            continue

        # Split by multiple spaces
        parts = re.split(r'\s{2,}', clean_line)
        if not parts:
            continue

        # Check if this is a metric header (Transaction, AVG LAT(ns), SDP Latency Histogram, etc.)
        first_part = parts[0].strip()

        if first_part == "Transaction":
            current_metric = "Transaction"
            current_target[current_trans_type][current_metric] = {}
            continue
        elif first_part == "AVG LAT(ns)":
            current_metric = "AVG LAT(ns)"
            current_target[current_trans_type][current_metric] = {}
            continue
        elif first_part == "SDP Latency Histogram":
            current_metric = "SDP Latency Histogram"
            current_target[current_trans_type][current_metric] = {}
            continue
        elif first_part == "FTI Latency Histogram":
            current_metric = "FTI Latency Histogram"
            current_target[current_trans_type][current_metric] = {}
            continue

        # Check if this is a sub-metric (SDP, FTI, or time bucket)
        if current_metric is not None and len(parts) >= 2:
            sub_metric = first_part
            values = parts[1:]

            # This is a data row with values for each DIE_CCM
            if sub_metric in ['SDP', 'FTI'] or 'ns' in sub_metric:
                value_dict = {}
                # Map values to DIE_CCM labels
                for i, val in enumerate(values):
                    die_idx = i // 4
                    ccm_idx = i % 4
                    key = f"DIE{die_idx}_CCM{ccm_idx}"
                    value_dict[key] = val.strip()

                if current_metric in current_target.get(current_trans_type, {}):
                    current_target[current_trans_type][current_metric][sub_metric] = value_dict

    return result


def parse_df_data_stream(filepath):
    """
    Parser for df_data_stream files (data stream information).
    Outputs structured format matching CCX version for comparison.
    Handles both Level 1 format and TARGET_CORE_DIE format.
    """
    with open(filepath, 'r') as f:
        lines = f.readlines()

    result = [{}]
    current_section = None

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Skip header lines
        if line_stripped.startswith("Level 1") or line_stripped.startswith("TARGET_CORE_DIE"):
            continue

        # Skip CCM header row
        if 'CCM0' in line_stripped and 'CCM1' in line_stripped and line_stripped.count('CCM0') > 1:
            continue

        # Parse line
        parts = re.split(r'\s{2,}', line_stripped)
        if not parts:
            continue

        # Clean parts - remove tree characters
        clean_parts = []
        for p in parts:
            cleaned = p.replace('|-', '').replace('|_', '').replace('|', '').strip()
            if cleaned:
                clean_parts.append(cleaned)

        if not clean_parts:
            continue

        # Check if this is a section header (like "Request to DRAM", "Request to IO")
        # Section headers typically have no numeric values
        first_part = clean_parts[0]

        # Detect section headers
        if first_part.startswith("Request to") or first_part in ["Request to DRAM", "Request to IO", "Request to PIE"]:
            current_section = first_part
            result[0][current_section] = {}
            continue

        # Find where values start (look for numeric values)
        metric_parts = []
        value_start = -1
        for i, p in enumerate(clean_parts):
            # Check if this looks like a value
            if re.match(r'^[\d.]+%?$', p.replace(' ', '')) or \
               re.match(r'^[\d.]+ ?[KMG]$', p) or \
               re.match(r'^[\d]+$', p) or \
               p == '0':
                value_start = i
                break
            metric_parts.append(p)

        if value_start == -1:
            # No values found - might be a section header or subsection
            if len(clean_parts) == 1 and current_section is None:
                # Treat as top-level metric with no values yet
                continue
            continue

        # Get metric name
        metric_name = metric_parts[-1] if metric_parts else ''
        if not metric_name:
            continue

        # Get values
        values = clean_parts[value_start:]

        # Create value dictionary with DIE_CCM keys
        value_dict = {}
        for i, val in enumerate(values):
            die_idx = i // 4
            ccm_idx = i % 4
            key = f"DIE{die_idx}_CCM{ccm_idx}"
            value_dict[key] = val.strip()

        if value_dict:
            # Add to current section or top level
            if current_section and current_section in result[0]:
                # Add hierarchical prefix for sub-metrics
                if len(metric_parts) > 1:
                    metric_name = '|' + metric_name
                result[0][current_section][metric_name] = value_dict
            else:
                result[0][metric_name] = value_dict

    return result


def parse_generic_file(filepath):
    """
    Generic parser that tries to identify the file type and parse accordingly.
    """
    filename = os.path.basename(filepath)

    # Determine parser based on filename patterns
    # NOTE: Order matters! More specific patterns must come before general ones

    # Check for detailed latency files first (before general latency_data)
    if 'todie2_latency_data' in filename:
        # Detailed latency files (df_detail_lat)
        return parse_df_detail_lat(filepath)
    elif 'queue_data' in filename:
        # Queue files
        return parse_df_queue(filepath)
    elif any(x in filename for x in ['_in_data', '_out_data', 'out_todie2_data']):
        # Data stream files
        return parse_df_data_stream(filepath)
    elif 'lat_data' in filename or 'latency_data' in filename:
        # Simple latency files (ccm_to_mem_lat)
        return parse_tabular_data(filepath)
    elif filename in ['iom_data', 'cm_data', 'di_data']:
        # Simple tabular files
        return parse_tabular_data(filepath)
    else:
        # Default to tabular parser
        return parse_tabular_data(filepath)


def process_all_files(source_dir, output_dir):
    """
    Process all files in source_dir and save parsed JSON to output_dir.
    Maintains the directory structure.
    """
    source_path = Path(source_dir)
    output_path = Path(output_dir)

    # Find all files (not directories)
    all_files = [f for f in source_path.rglob('*') if f.is_file()]

    print(f"Found {len(all_files)} files to process")

    results_summary = []

    for file_path in all_files:
        # Get relative path from source directory
        rel_path = file_path.relative_to(source_path)

        # Create corresponding output path
        output_file_path = output_path / rel_path.parent / f"{rel_path.name}_parsed.json"

        # Create output directory if it doesn't exist
        output_file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            print(f"Processing: {rel_path}")

            # Parse the file
            parsed_data = parse_generic_file(str(file_path))

            # Save to JSON
            with open(output_file_path, 'w') as f:
                json.dump(parsed_data, f, indent=2)

            results_summary.append({
                "source": str(rel_path),
                "output": str(output_file_path.relative_to(output_path)),
                "status": "success",
                "records": len(parsed_data)
            })

            print(f"  ✓ Saved to: {output_file_path.relative_to(output_path)} ({len(parsed_data)} records)")

        except Exception as e:
            print(f"  ✗ Error: {e}")
            results_summary.append({
                "source": str(rel_path),
                "output": str(output_file_path.relative_to(output_path)),
                "status": "error",
                "error": str(e)
            })

    # Save summary
    summary_path = output_path / "parsing_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(results_summary, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Processing complete!")
    print(f"Total files processed: {len(all_files)}")
    print(f"Successful: {sum(1 for r in results_summary if r['status'] == 'success')}")
    print(f"Failed: {sum(1 for r in results_summary if r['status'] == 'error')}")
    print(f"Summary saved to: {summary_path}")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description='Parse all files under data/liuxiu/die to JSON format'
    )
    parser.add_argument(
        '--source',
        default='data/liuxiu/die',
        help='Source directory containing data files (default: data/liuxiu/die)'
    )
    parser.add_argument(
        '--output',
        default='results/data/liuxiu/die',
        help='Output directory for parsed JSON files (default: results/data/liuxiu/die)'
    )

    args = parser.parse_args()

    process_all_files(args.source, args.output)


if __name__ == '__main__':
    main()
