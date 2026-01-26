#!/usr/bin/env python3
"""
Comprehensive Visualization for CCX vs DIE vs SOCKET comparison.
Matches the comparison logic in compare_ccx_die_socket.py with Level 3 metrics.
"""

import json
import os
import subprocess
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Configuration
DATA_DIR = "data/liuxiu"
DATASETS = ["ccx", "die", "socket"]
DATASET_COLORS = {"ccx": "#1f77b4", "die": "#ff7f0e", "socket": "#2ca02c"}
DATASET_LABELS = {"ccx": "CCX", "die": "DIE", "socket": "SOCKET"}
OUTPUT_DIR = "results/visualizations/ccx_die_socket_comparison"
PARSERS_DIR = "parsers"


def parse_value(value_str):
    """Parse values with K/M/G suffixes."""
    if isinstance(value_str, (int, float)):
        return float(value_str)

    value_str = str(value_str).strip()
    if not value_str or value_str == "0":
        return 0.0

    # Handle percentages
    if '%' in value_str:
        try:
            return float(value_str.replace('%', '').strip())
        except:
            return 0.0

    # Handle K, M, G suffixes
    multipliers = {'K': 1e3, 'M': 1e6, 'G': 1e9, 'T': 1e12}

    for suffix, mult in multipliers.items():
        if value_str.endswith(suffix):
            try:
                return float(value_str[:-1].strip()) * mult
            except:
                pass

    # Handle "N suffix" format (e.g., "1.5 M")
    parts = value_str.split()
    if len(parts) == 2:
        try:
            number = float(parts[0])
            suffix = parts[1]
            return number * multipliers.get(suffix, 1)
        except:
            pass

    try:
        return float(value_str.replace(',', ''))
    except:
        return 0.0


def run_parser(parser_name, filepath):
    """Run a parser and return parsed JSON data."""
    parser_path = os.path.join(PARSERS_DIR, parser_name)
    if not os.path.exists(filepath):
        return None

    try:
        result = subprocess.run(
            ["python3", parser_path, filepath],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception as e:
        print(f"Error running parser: {e}")
    return None


def fmt(val, unit=""):
    """Format large numbers with K/M/G suffix."""
    if val == 0:
        return "0"
    elif val >= 1e9:
        return f"{val/1e9:.1f}G{unit}"
    elif val >= 1e6:
        return f"{val/1e6:.1f}M{unit}"
    elif val >= 1e3:
        return f"{val/1e3:.1f}K{unit}"
    else:
        return f"{val:.0f}{unit}"


def extract_metric_values(parsed_data, metric_name, die_index=2):
    """Extract metric values from df_data_stream parsed data."""
    if not parsed_data or "sections" not in parsed_data:
        return 0

    sections = parsed_data.get("sections", [])
    if not sections:
        return 0

    num_sections = len(sections)
    if num_sections == 1:
        target_section_idx = 0
        local_die_index = die_index
    else:
        target_section_idx = None
        local_die_index = die_index
        for i, section in enumerate(sections):
            die_labels = section.get("die_labels", [])
            die_name = f"DIE{die_index}"
            if die_name in die_labels:
                target_section_idx = i
                local_die_index = die_labels.index(die_name)
                break
        if target_section_idx is None:
            return 0

    section = sections[target_section_idx]

    # Search in level1_categories
    for cat in section.get("level1_categories", []):
        if cat.get("name") == metric_name:
            values = cat.get("values", [])
            if values and local_die_index * 4 < len(values):
                total = sum(parse_value(values[local_die_index * 4 + i]) for i in range(min(4, len(values) - local_die_index * 4)))
                return total

        # Search in level2_metrics
        for l2 in cat.get("level2_metrics", []):
            if l2.get("name") == metric_name:
                values = l2.get("values", [])
                if values and local_die_index * 4 < len(values):
                    total = sum(parse_value(values[local_die_index * 4 + i]) for i in range(min(4, len(values) - local_die_index * 4)))
                    return total

            # Search in level3_metrics
            for l3 in l2.get("level3_metrics", []):
                if l3.get("name") == metric_name:
                    values = l3.get("values", [])
                    if values and local_die_index * 4 < len(values):
                        total = sum(parse_value(values[local_die_index * 4 + i]) for i in range(min(4, len(values) - local_die_index * 4)))
                        return total

    return 0


def extract_detail_lat_metric(parsed_data, tx_type, metric_l2, metric_l3=None, die_index=2):
    """Extract metric from df_detail_lat parsed data."""
    if not parsed_data or "sections" not in parsed_data:
        return 0

    sections = parsed_data.get("sections", [])
    section_index = die_index // 4
    local_die_index = die_index % 4

    if section_index >= len(sections):
        return 0

    section = sections[section_index]

    for tx in section.get("transaction_types", []):
        if tx.get("name") == tx_type:
            for l2 in tx.get("level2_metrics", []):
                if l2.get("name") == metric_l2:
                    if metric_l3:
                        for l3 in l2.get("level3_metrics", []):
                            if l3.get("name") == metric_l3:
                                values = l3.get("values", [])
                                if values and local_die_index * 4 < len(values):
                                    total = sum(parse_value(values[local_die_index * 4 + i]) for i in range(min(4, len(values) - local_die_index * 4)))
                                    return total
                    else:
                        values = l2.get("values", [])
                        if values and local_die_index * 4 < len(values):
                            total = sum(parse_value(values[local_die_index * 4 + i]) for i in range(min(4, len(values) - local_die_index * 4)))
                            return total
    return 0


def extract_queue_metric(parsed_data, queue_type, metric_l2, metric_l3=None, section_index=0):
    """Extract metric from df_queue parsed data."""
    if not parsed_data or "sections" not in parsed_data:
        return []

    sections = parsed_data.get("sections", [])
    if section_index >= len(sections):
        return []

    section = sections[section_index]

    for qt in section.get("queue_types", []):
        if qt.get("name") == queue_type:
            for l2 in qt.get("level2_metrics", []):
                if l2.get("name") == metric_l2:
                    if metric_l3:
                        for l3 in l2.get("level3_metrics", []):
                            if l3.get("name") == metric_l3:
                                return l3.get("values", [])
                    else:
                        return l2.get("values", [])
    return []


def visualize_cm_data():
    """Visualize Core-to-Memory Bandwidth comparison for all DIEs."""
    print("  Creating CM_DATA visualization...")

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('Core-to-Memory Bandwidth Comparison (All DIEs)', fontsize=14, fontweight='bold')

    # Load data using correct parser
    data = {}
    for ds in DATASETS:
        filepath = f"{DATA_DIR}/{ds}/cm_data"
        if os.path.exists(filepath):
            parsed = run_parser("cm_data_parser.py", filepath)
            data[ds] = parsed

    dies = [f"DIE{i}" for i in range(8)]
    x = np.arange(len(dies))
    width = 0.25

    # Chart 1: CS Read Total (sum of CS0_RD through CS3_RD)
    ax = axes[0]
    for i, ds in enumerate(DATASETS):
        if ds not in data or not data[ds]:
            continue

        values = []
        for die in dies:
            val = 0
            for entry in data[ds]:
                if entry.get("Category") == die:
                    # Sum all CS read columns
                    val = sum(parse_value(entry.get(f"CS{j}_RD", 0)) for j in range(4))
                    break
            values.append(val)

        ax.bar(x + (i - 1) * width, np.array(values) / 1e6, width,
               label=DATASET_LABELS[ds], color=DATASET_COLORS[ds], alpha=0.8)

    ax.set_xlabel('DIE', fontsize=11)
    ax.set_ylabel('Value (Millions)', fontsize=11)
    ax.set_title('CS Read Total (CS0-CS3)', fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(dies)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    # Chart 2: Total Bandwidth
    ax = axes[1]
    for i, ds in enumerate(DATASETS):
        if ds not in data or not data[ds]:
            continue

        values = []
        for die in dies:
            val = 0
            for entry in data[ds]:
                if entry.get("Category") == die:
                    bw_str = entry.get("TOTAL_BW", "0")
                    # Parse bandwidth (e.g., "90 MB/s", "19 GB/s")
                    if "GB/s" in str(bw_str):
                        val = parse_value(bw_str.replace("GB/s", "").strip()) * 1e9
                    elif "MB/s" in str(bw_str):
                        val = parse_value(bw_str.replace("MB/s", "").strip()) * 1e6
                    else:
                        val = parse_value(bw_str)
                    break
            values.append(val)

        ax.bar(x + (i - 1) * width, np.array(values) / 1e6, width,
               label=DATASET_LABELS[ds], color=DATASET_COLORS[ds], alpha=0.8)

    ax.set_xlabel('DIE', fontsize=11)
    ax.set_ylabel('Bandwidth (MB/s)', fontsize=11)
    ax.set_title('Total Bandwidth', fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(dies)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'cm_data_all_dies.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print("    Saved: cm_data_all_dies.png")


def visualize_df_data_stream():
    """Visualize DF_DATA_STREAM with Level 3 metrics."""
    print("  Creating DF_DATA_STREAM visualizations...")

    output_subdir = os.path.join(OUTPUT_DIR, 'df_data_stream')
    os.makedirs(output_subdir, exist_ok=True)

    # Parse data for each dataset
    files_metrics = {
        "ccm_in_data": ["Data Transfer", "No Data Transfer", "State/PassD", "Inv_NoPassD", "Inv_PassD", "Shr_NoPassD", "Shr_PassD", "PrbSrc", "PrbTgt"],
        "cs_in_data": ["ChgToX", "VicBlk", "VicBlkFull", "VicBlkCln", "RdBlk", "RdBlkL", "RdBlkX", "RdBlkC"],
    }

    for fname, metrics in files_metrics.items():
        parsed = {}
        for ds in DATASETS:
            filepath = f"{DATA_DIR}/{ds}/df_data_stream/{fname}"
            parsed[ds] = run_parser("liuxiu_df_data_stream_parser.py", filepath)

        # Create multi-row figure for this file
        n_metrics = len(metrics)
        n_cols = 3
        n_rows = (n_metrics + n_cols - 1) // n_cols

        fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, 5 * n_rows))
        fig.suptitle(f'{fname.upper()} - All DIEs Comparison (Including Level 3)', fontsize=14, fontweight='bold')
        axes = axes.flatten() if n_rows > 1 else [axes] if n_cols == 1 else axes.flatten()

        dies = [f"DIE{i}" for i in range(8)]
        x = np.arange(len(dies))
        width = 0.25

        for idx, metric in enumerate(metrics):
            if idx >= len(axes):
                break
            ax = axes[idx]

            for i, ds in enumerate(DATASETS):
                if ds not in parsed or not parsed[ds]:
                    continue

                values = [extract_metric_values(parsed[ds], metric, die_idx) for die_idx in range(8)]
                ax.bar(x + (i - 1) * width, np.array(values) / 1e6, width,
                       label=DATASET_LABELS[ds], color=DATASET_COLORS[ds], alpha=0.8)

            ax.set_xlabel('DIE', fontsize=10)
            ax.set_ylabel('Value (Millions)', fontsize=10)
            ax.set_title(metric, fontsize=11)
            ax.set_xticks(x)
            ax.set_xticklabels(dies, fontsize=8)
            ax.legend(fontsize=8)
            ax.grid(axis='y', alpha=0.3)

        # Hide empty subplots
        for idx in range(len(metrics), len(axes)):
            axes[idx].set_visible(False)

        plt.tight_layout()
        plt.savefig(os.path.join(output_subdir, f'{fname}_all_dies.png'), dpi=300, bbox_inches='tight')
        plt.close()
        print(f"    Saved: {fname}_all_dies.png")


def visualize_df_detail_lat():
    """Visualize DF_DETAIL_LAT with Level 3 latency histograms."""
    print("  Creating DF_DETAIL_LAT visualizations...")

    output_subdir = os.path.join(OUTPUT_DIR, 'df_detail_lat')
    os.makedirs(output_subdir, exist_ok=True)

    # Parse data
    parsed = {}
    for ds in DATASETS:
        filepath = f"{DATA_DIR}/{ds}/df_detail_lat/ccm2todie2_latency_data"
        parsed[ds] = run_parser("liuxiu_df_detail_lat_parser.py", filepath)

    # 1. Transaction counts comparison (all DIEs)
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('RDBLK Transaction Counts - All DIEs Comparison', fontsize=14, fontweight='bold')

    dies = [f"DIE{i}" for i in range(8)]
    x = np.arange(len(dies))
    width = 0.25

    metrics = [
        ("RDBLK", "Transaction", "SDP", "RDBLK SDP Transactions"),
        ("RDBLK", "Transaction", "FTI", "RDBLK FTI Transactions"),
        ("RDBLK", "AVG LAT(ns)", "SDP", "RDBLK SDP Avg Latency (ns)"),
        ("DIRTY_VICTIM", "Transaction", "SDP", "DIRTY_VICTIM SDP Transactions"),
    ]

    for idx, (tx, l2, l3, title) in enumerate(metrics):
        ax = axes[idx // 2, idx % 2]

        for i, ds in enumerate(DATASETS):
            if ds not in parsed or not parsed[ds]:
                continue

            values = [extract_detail_lat_metric(parsed[ds], tx, l2, l3, die_idx) for die_idx in range(8)]
            ax.bar(x + (i - 1) * width, values, width,
                   label=DATASET_LABELS[ds], color=DATASET_COLORS[ds], alpha=0.8)

        ax.set_xlabel('DIE', fontsize=11)
        ax.set_ylabel('Count' if 'Transaction' in title else 'Latency (ns)', fontsize=11)
        ax.set_title(title, fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels(dies)
        ax.legend()
        ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_subdir, 'rdblk_transactions_all_dies.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print("    Saved: rdblk_transactions_all_dies.png")

    # 2. Level 3: Latency Histogram comparison (DIE2)
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('RDBLK Latency Histogram (Level 3) - DIE2 Comparison', fontsize=14, fontweight='bold')

    latency_buckets = ["0ns-50ns", "50ns-100ns", "100ns-150ns", "150ns-200ns", "200ns-500ns", "500ns-1000ns", ">1000ns"]
    x = np.arange(len(latency_buckets))

    for ax_idx, (histogram_type, title) in enumerate([("SDP Latency Histogram", "SDP"), ("FTI Latency Histogram", "FTI")]):
        ax = axes[ax_idx]

        for i, ds in enumerate(DATASETS):
            if ds not in parsed or not parsed[ds]:
                continue

            values = []
            for bucket in latency_buckets:
                val = extract_detail_lat_metric(parsed[ds], "RDBLK", histogram_type, bucket, die_index=2)
                values.append(val)

            ax.bar(x + (i - 1) * width, values, width,
                   label=DATASET_LABELS[ds], color=DATASET_COLORS[ds], alpha=0.8)

        ax.set_xlabel('Latency Bucket', fontsize=11)
        ax.set_ylabel('Percentage (%)', fontsize=11)
        ax.set_title(f'{title} Latency Histogram', fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels(latency_buckets, rotation=45, ha='right', fontsize=9)
        ax.legend()
        ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_subdir, 'latency_histogram_level3_die2.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print("    Saved: latency_histogram_level3_die2.png")


def visualize_df_queue():
    """Visualize DF_QUEUE with Level 3 metrics."""
    print("  Creating DF_QUEUE visualizations...")

    output_subdir = os.path.join(OUTPUT_DIR, 'df_queue')
    os.makedirs(output_subdir, exist_ok=True)

    # Parse data
    parsed = {}
    for ds in DATASETS:
        filepath = f"{DATA_DIR}/{ds}/df_queue/ccm_queue_data"
        parsed[ds] = run_parser("liuxiu_df_queue_parser.py", filepath)

    # 1. Queue metrics by section (DIE pairs)
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle('Queue Metrics - All DIE Sections Comparison', fontsize=14, fontweight='bold')

    section_labels = ["DIE0-1", "DIE2-3", "DIE4-5", "DIE6-7"]
    x = np.arange(len(section_labels))
    width = 0.25

    queue_metrics = [
        ("REQQ", "Request", None, "REQQ Request"),
        ("REQQ", "Kill Rate", None, "REQQ Kill Rate (%)"),
        ("PRBQ", "Probe", None, "PRBQ Probe"),
        ("RSPQ", "Response", None, "RSPQ Response"),
        ("ORIGDQ", "write", None, "ORIGDQ Write"),
    ]

    for idx, (queue, l2, l3, title) in enumerate(queue_metrics):
        if idx >= 6:
            break
        ax = axes[idx // 3, idx % 3]

        for i, ds in enumerate(DATASETS):
            if ds not in parsed or not parsed[ds]:
                continue

            values = []
            for section_idx in range(4):
                vals = extract_queue_metric(parsed[ds], queue, l2, l3, section_index=section_idx)
                if "Rate" in title:
                    pct_vals = [parse_value(v.replace('%', '')) for v in vals if '%' in str(v)]
                    avg = sum(pct_vals) / len(pct_vals) if pct_vals else 0
                    values.append(avg)
                else:
                    total = sum(parse_value(v) for v in vals)
                    values.append(total)

            if "Rate" in title:
                ax.bar(x + (i - 1) * width, values, width,
                       label=DATASET_LABELS[ds], color=DATASET_COLORS[ds], alpha=0.8)
            else:
                ax.bar(x + (i - 1) * width, np.array(values) / 1e6, width,
                       label=DATASET_LABELS[ds], color=DATASET_COLORS[ds], alpha=0.8)

        ax.set_xlabel('DIE Section', fontsize=11)
        ax.set_ylabel('Percentage (%)' if "Rate" in title else 'Count (Millions)', fontsize=11)
        ax.set_title(title, fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels(section_labels)
        ax.legend()
        ax.grid(axis='y', alpha=0.3)

    # Hide unused subplot
    axes[1, 2].set_visible(False)

    plt.tight_layout()
    plt.savefig(os.path.join(output_subdir, 'queue_metrics_all_sections.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print("    Saved: queue_metrics_all_sections.png")

    # 2. Level 3: OCCUPANCY buckets
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle('Queue OCCUPANCY Level 3 - DIE2-3 Section', fontsize=14, fontweight='bold')

    occupancy_buckets = ["0%-25%", "25%-50%", "50%-75%", "75%-100%"]
    x = np.arange(len(occupancy_buckets))

    queue_types = ["REQQ", "PRBQ", "RSPQ"]

    for ax_idx, queue in enumerate(queue_types):
        ax = axes[ax_idx]

        for i, ds in enumerate(DATASETS):
            if ds not in parsed or not parsed[ds]:
                continue

            values = []
            for bucket in occupancy_buckets:
                vals = extract_queue_metric(parsed[ds], queue, "OCCUPANCY", bucket, section_index=1)
                pct_vals = [parse_value(v.replace('%', '')) for v in vals if '%' in str(v)]
                avg = sum(pct_vals) / len(pct_vals) if pct_vals else 0
                values.append(avg)

            ax.bar(x + (i - 1) * width, values, width,
                   label=DATASET_LABELS[ds], color=DATASET_COLORS[ds], alpha=0.8)

        ax.set_xlabel('Occupancy Bucket', fontsize=11)
        ax.set_ylabel('Percentage (%)', fontsize=11)
        ax.set_title(f'{queue} OCCUPANCY', fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels(occupancy_buckets)
        ax.legend()
        ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_subdir, 'occupancy_level3_die2_3.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print("    Saved: occupancy_level3_die2_3.png")


def create_summary_dashboard():
    """Create a comprehensive summary dashboard."""
    print("  Creating summary dashboard...")

    fig = plt.figure(figsize=(24, 18))
    fig.suptitle('CCX vs DIE vs SOCKET - Complete Comparison Summary', fontsize=18, fontweight='bold', y=0.98)

    # Create grid
    gs = fig.add_gridspec(3, 4, hspace=0.3, wspace=0.3)

    # 1. CM_DATA Bandwidth
    ax1 = fig.add_subplot(gs[0, 0])
    data = {}
    for ds in DATASETS:
        filepath = f"{DATA_DIR}/{ds}/cm_data"
        if os.path.exists(filepath):
            data[ds] = run_parser("cm_data_parser.py", filepath)

    dies = [f"DIE{i}" for i in range(8)]
    x = np.arange(len(dies))
    width = 0.25

    for i, ds in enumerate(DATASETS):
        if ds not in data or not data[ds]:
            continue
        values = []
        for die in dies:
            val = 0
            for entry in data[ds]:
                if entry.get("Category") == die:
                    # Sum all CS read columns
                    val = sum(parse_value(entry.get(f"CS{j}_RD", 0)) for j in range(4))
                    break
            values.append(val)
        ax1.bar(x + (i - 1) * width, np.array(values) / 1e6, width,
               label=DATASET_LABELS[ds], color=DATASET_COLORS[ds], alpha=0.8)

    ax1.set_title('CM_DATA: CS Read Total', fontsize=11)
    ax1.set_xlabel('DIE')
    ax1.set_ylabel('Millions')
    ax1.set_xticks(x)
    ax1.set_xticklabels(dies, fontsize=8)
    ax1.legend(fontsize=8)
    ax1.grid(axis='y', alpha=0.3)

    # 2. IOM_DATA (Non-Cache Memory Requests)
    ax2 = fig.add_subplot(gs[0, 1])
    iom_data = {}
    for ds in DATASETS:
        filepath = f"{DATA_DIR}/{ds}/iom_data"
        if os.path.exists(filepath):
            iom_data[ds] = run_parser("iom_data_parser.py", filepath)

    for i, ds in enumerate(DATASETS):
        if ds not in iom_data or not iom_data[ds]:
            continue
        values = []
        for die in dies:
            val = 0
            for entry in iom_data[ds]:
                if entry.get("Category") == die:
                    # Sum all read size columns for total requests
                    val = sum(parse_value(entry.get(f"CS{j}_RDSZ", 0)) for j in range(4))
                    break
            values.append(val)
        ax2.bar(x + (i - 1) * width, values, width,
               label=DATASET_LABELS[ds], color=DATASET_COLORS[ds], alpha=0.8)

    ax2.set_title('IOM_DATA: Total Read Requests', fontsize=11)
    ax2.set_xlabel('DIE')
    ax2.set_ylabel('Count')
    ax2.set_xticks(x)
    ax2.set_xticklabels(dies, fontsize=8)
    ax2.legend(fontsize=8)
    ax2.grid(axis='y', alpha=0.3)

    # 3. CCM_IN Data Transfer
    ax3 = fig.add_subplot(gs[0, 2])
    ccm_in = {}
    for ds in DATASETS:
        filepath = f"{DATA_DIR}/{ds}/df_data_stream/ccm_in_data"
        ccm_in[ds] = run_parser("liuxiu_df_data_stream_parser.py", filepath)

    for i, ds in enumerate(DATASETS):
        if ds not in ccm_in or not ccm_in[ds]:
            continue
        values = [extract_metric_values(ccm_in[ds], "Data Transfer", die_idx) for die_idx in range(8)]
        ax3.bar(x + (i - 1) * width, np.array(values) / 1e6, width,
               label=DATASET_LABELS[ds], color=DATASET_COLORS[ds], alpha=0.8)

    ax3.set_title('CCM_IN: Data Transfer', fontsize=11)
    ax3.set_xlabel('DIE')
    ax3.set_ylabel('Millions')
    ax3.set_xticks(x)
    ax3.set_xticklabels(dies, fontsize=8)
    ax3.legend(fontsize=8)
    ax3.grid(axis='y', alpha=0.3)

    # 4. CCM_IN Level 3: Inv_PassD
    ax4 = fig.add_subplot(gs[0, 3])
    for i, ds in enumerate(DATASETS):
        if ds not in ccm_in or not ccm_in[ds]:
            continue
        values = [extract_metric_values(ccm_in[ds], "Inv_PassD", die_idx) for die_idx in range(8)]
        ax4.bar(x + (i - 1) * width, np.array(values) / 1e3, width,
               label=DATASET_LABELS[ds], color=DATASET_COLORS[ds], alpha=0.8)

    ax4.set_title('CCM_IN Level 3: Inv_PassD', fontsize=11)
    ax4.set_xlabel('DIE')
    ax4.set_ylabel('Thousands')
    ax4.set_xticks(x)
    ax4.set_xticklabels(dies, fontsize=8)
    ax4.legend(fontsize=8)
    ax4.grid(axis='y', alpha=0.3)

    # 5. CS_IN VicBlk
    ax5 = fig.add_subplot(gs[1, 0])
    cs_in = {}
    for ds in DATASETS:
        filepath = f"{DATA_DIR}/{ds}/df_data_stream/cs_in_data"
        cs_in[ds] = run_parser("liuxiu_df_data_stream_parser.py", filepath)

    for i, ds in enumerate(DATASETS):
        if ds not in cs_in or not cs_in[ds]:
            continue
        values = [extract_metric_values(cs_in[ds], "VicBlk", die_idx) for die_idx in range(8)]
        ax5.bar(x + (i - 1) * width, np.array(values) / 1e6, width,
               label=DATASET_LABELS[ds], color=DATASET_COLORS[ds], alpha=0.8)

    ax5.set_title('CS_IN: VicBlk', fontsize=11)
    ax5.set_xlabel('DIE')
    ax5.set_ylabel('Millions')
    ax5.set_xticks(x)
    ax5.set_xticklabels(dies, fontsize=8)
    ax5.legend(fontsize=8)
    ax5.grid(axis='y', alpha=0.3)

    # 6. CS_IN Level 3: VicBlkFull
    ax6 = fig.add_subplot(gs[1, 1])
    for i, ds in enumerate(DATASETS):
        if ds not in cs_in or not cs_in[ds]:
            continue
        values = [extract_metric_values(cs_in[ds], "VicBlkFull", die_idx) for die_idx in range(8)]
        ax6.bar(x + (i - 1) * width, np.array(values) / 1e6, width,
               label=DATASET_LABELS[ds], color=DATASET_COLORS[ds], alpha=0.8)

    ax6.set_title('CS_IN Level 3: VicBlkFull', fontsize=11)
    ax6.set_xlabel('DIE')
    ax6.set_ylabel('Millions')
    ax6.set_xticks(x)
    ax6.set_xticklabels(dies, fontsize=8)
    ax6.legend(fontsize=8)
    ax6.grid(axis='y', alpha=0.3)

    # 7. DF_DETAIL_LAT RDBLK SDP
    ax7 = fig.add_subplot(gs[1, 2])
    detail_lat = {}
    for ds in DATASETS:
        filepath = f"{DATA_DIR}/{ds}/df_detail_lat/ccm2todie2_latency_data"
        detail_lat[ds] = run_parser("liuxiu_df_detail_lat_parser.py", filepath)

    for i, ds in enumerate(DATASETS):
        if ds not in detail_lat or not detail_lat[ds]:
            continue
        values = [extract_detail_lat_metric(detail_lat[ds], "RDBLK", "Transaction", "SDP", die_idx) for die_idx in range(8)]
        ax7.bar(x + (i - 1) * width, np.array(values) / 1e6, width,
               label=DATASET_LABELS[ds], color=DATASET_COLORS[ds], alpha=0.8)

    ax7.set_title('DF_DETAIL_LAT: RDBLK SDP', fontsize=11)
    ax7.set_xlabel('DIE')
    ax7.set_ylabel('Millions')
    ax7.set_xticks(x)
    ax7.set_xticklabels(dies, fontsize=8)
    ax7.legend(fontsize=8)
    ax7.grid(axis='y', alpha=0.3)

    # 8. Level 3: SDP Latency Histogram (DIE2)
    ax8 = fig.add_subplot(gs[1, 3])
    latency_buckets = ["0ns-50ns", "50ns-100ns", "100ns-150ns", "150ns-200ns", "200ns-500ns", "500ns-1000ns", ">1000ns"]
    x_lat = np.arange(len(latency_buckets))

    for i, ds in enumerate(DATASETS):
        if ds not in detail_lat or not detail_lat[ds]:
            continue
        values = [extract_detail_lat_metric(detail_lat[ds], "RDBLK", "SDP Latency Histogram", bucket, die_index=2) for bucket in latency_buckets]
        ax8.bar(x_lat + (i - 1) * width, values, width,
               label=DATASET_LABELS[ds], color=DATASET_COLORS[ds], alpha=0.8)

    ax8.set_title('Level 3: SDP Latency Histogram (DIE2)', fontsize=11)
    ax8.set_xlabel('Bucket')
    ax8.set_ylabel('Percentage (%)')
    ax8.set_xticks(x_lat)
    ax8.set_xticklabels([b[:7] for b in latency_buckets], rotation=45, ha='right', fontsize=7)
    ax8.legend(fontsize=8)
    ax8.grid(axis='y', alpha=0.3)

    # 9. DF_QUEUE REQQ Request
    ax9 = fig.add_subplot(gs[2, 0])
    queue_data = {}
    for ds in DATASETS:
        filepath = f"{DATA_DIR}/{ds}/df_queue/ccm_queue_data"
        queue_data[ds] = run_parser("liuxiu_df_queue_parser.py", filepath)

    section_labels = ["DIE0-1", "DIE2-3", "DIE4-5", "DIE6-7"]
    x_sec = np.arange(len(section_labels))

    for i, ds in enumerate(DATASETS):
        if ds not in queue_data or not queue_data[ds]:
            continue
        values = []
        for section_idx in range(4):
            vals = extract_queue_metric(queue_data[ds], "REQQ", "Request", None, section_index=section_idx)
            total = sum(parse_value(v) for v in vals)
            values.append(total)
        ax9.bar(x_sec + (i - 1) * width, np.array(values) / 1e6, width,
               label=DATASET_LABELS[ds], color=DATASET_COLORS[ds], alpha=0.8)

    ax9.set_title('DF_QUEUE: REQQ Request', fontsize=11)
    ax9.set_xlabel('Section')
    ax9.set_ylabel('Millions')
    ax9.set_xticks(x_sec)
    ax9.set_xticklabels(section_labels)
    ax9.legend(fontsize=8)
    ax9.grid(axis='y', alpha=0.3)

    # 10. Level 3: REQQ OCCUPANCY
    ax10 = fig.add_subplot(gs[2, 1])
    occupancy_buckets = ["0%-25%", "25%-50%", "50%-75%", "75%-100%"]
    x_occ = np.arange(len(occupancy_buckets))

    for i, ds in enumerate(DATASETS):
        if ds not in queue_data or not queue_data[ds]:
            continue
        values = []
        for bucket in occupancy_buckets:
            vals = extract_queue_metric(queue_data[ds], "REQQ", "OCCUPANCY", bucket, section_index=1)
            pct_vals = [parse_value(v.replace('%', '')) for v in vals if '%' in str(v)]
            avg = sum(pct_vals) / len(pct_vals) if pct_vals else 0
            values.append(avg)
        ax10.bar(x_occ + (i - 1) * width, values, width,
                label=DATASET_LABELS[ds], color=DATASET_COLORS[ds], alpha=0.8)

    ax10.set_title('Level 3: REQQ OCCUPANCY (DIE2-3)', fontsize=11)
    ax10.set_xlabel('Bucket')
    ax10.set_ylabel('Percentage (%)')
    ax10.set_xticks(x_occ)
    ax10.set_xticklabels(occupancy_buckets)
    ax10.legend(fontsize=8)
    ax10.grid(axis='y', alpha=0.3)

    # 11. Level 3: RSPQ OCCUPANCY
    ax11 = fig.add_subplot(gs[2, 2])
    for i, ds in enumerate(DATASETS):
        if ds not in queue_data or not queue_data[ds]:
            continue
        values = []
        for bucket in occupancy_buckets:
            vals = extract_queue_metric(queue_data[ds], "RSPQ", "OCCUPANCY", bucket, section_index=1)
            pct_vals = [parse_value(v.replace('%', '')) for v in vals if '%' in str(v)]
            avg = sum(pct_vals) / len(pct_vals) if pct_vals else 0
            values.append(avg)
        ax11.bar(x_occ + (i - 1) * width, values, width,
                label=DATASET_LABELS[ds], color=DATASET_COLORS[ds], alpha=0.8)

    ax11.set_title('Level 3: RSPQ OCCUPANCY (DIE2-3)', fontsize=11)
    ax11.set_xlabel('Bucket')
    ax11.set_ylabel('Percentage (%)')
    ax11.set_xticks(x_occ)
    ax11.set_xticklabels(occupancy_buckets)
    ax11.legend(fontsize=8)
    ax11.grid(axis='y', alpha=0.3)

    # 12. Summary text
    ax12 = fig.add_subplot(gs[2, 3])
    ax12.axis('off')

    summary_text = """COMPARISON SUMMARY
=====================================

Data Sources:
  CCX:    data/liuxiu/ccx/
  DIE:    data/liuxiu/die/
  SOCKET: data/liuxiu/socket/

Metrics Compared:
  Level 1/2: Basic metrics
  Level 3:   Sub-metrics

Key Visualizations:
  - CM_DATA: Bandwidth per DIE
  - IOM_DATA: IO Requests per DIE
  - DF_DATA_STREAM: Data flow metrics
    + Level 3: Inv_PassD, VicBlkFull
  - DF_DETAIL_LAT: Latency data
    + Level 3: Latency histograms
  - DF_QUEUE: Queue metrics
    + Level 3: OCCUPANCY buckets

Legend:
  Blue   = CCX
  Orange = DIE
  Green  = SOCKET
"""

    ax12.text(0.05, 0.95, summary_text, transform=ax12.transAxes,
             fontsize=10, verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))

    plt.savefig(os.path.join(OUTPUT_DIR, 'complete_comparison_dashboard.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print("    Saved: complete_comparison_dashboard.png")


def main():
    """Main function."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 70)
    print("CCX vs DIE vs SOCKET Visualization")
    print("=" * 70)

    print("\n1. Visualizing CM_DATA...")
    visualize_cm_data()

    print("\n2. Visualizing DF_DATA_STREAM with Level 3...")
    visualize_df_data_stream()

    print("\n3. Visualizing DF_DETAIL_LAT with Level 3...")
    visualize_df_detail_lat()

    print("\n4. Visualizing DF_QUEUE with Level 3...")
    visualize_df_queue()

    print("\n5. Creating summary dashboard...")
    create_summary_dashboard()

    print("\n" + "=" * 70)
    print(f"All visualizations saved to: {OUTPUT_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()
