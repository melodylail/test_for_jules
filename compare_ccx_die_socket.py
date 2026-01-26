#!/usr/bin/env python3
"""
Compare CCX, DIE, and SOCKET datasets.
Usage: python3 compare_ccx_die_socket.py
"""

import json
import os
import re
import subprocess
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data/liuxiu")
DATASETS = ["ccx", "die", "socket"]

def parse_value(val_str):
    """Convert string value like '37 M', '15 K', '90 MB/s' to numeric."""
    if not val_str or val_str == "0" or val_str == "N/A":
        return 0
    val_str = str(val_str).strip()
    val_str = re.sub(r'\s*(B/s|MB/s|GB/s|KB/s|ns|%)$', '', val_str)
    match = re.match(r'^([\d.]+)\s*([KMG])?$', val_str)
    if match:
        num = float(match.group(1))
        suffix = match.group(2)
        if suffix == 'K': return num * 1000
        elif suffix == 'M': return num * 1000000
        elif suffix == 'G': return num * 1000000000
        return num
    try:
        return float(val_str)
    except:
        return 0

def run_parser(parser_script, data_file):
    """Run parser and return JSON data."""
    try:
        result = subprocess.run(
            ["python3", os.path.join(BASE_DIR, "parsers", parser_script), data_file],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except:
        pass
    return None

def compare_cm_data():
    """Compare CM_DATA (Core-to-Memory bandwidth)."""
    print("\n" + "="*90)
    print("CM_DATA: Core-to-Memory Bandwidth Comparison")
    print("="*90)

    data = {ds: run_parser("cm_data_parser.py", f"{DATA_DIR}/{ds}/cm_data") for ds in DATASETS}

    # Build comparison table
    results = defaultdict(dict)
    for ds, rows in data.items():
        if rows:
            for row in rows:
                cat = row.get("Category", "")
                results[cat][ds] = row

    print(f"\n{'Category':<8} {'CCX':^30} {'DIE':^30} {'SOCKET':^30}")
    print(f"{'':8} {'CS_RD_Total':>12} {'BW':>14} {'CS_RD_Total':>12} {'BW':>14} {'CS_RD_Total':>12} {'BW':>14}")
    print("-"*98)

    for cat in ["DIE0", "DIE1", "DIE2", "DIE3", "DIE4", "DIE5", "DIE6", "DIE7", "SKT0", "SKT1", "SYS"]:
        row_data = []
        for ds in DATASETS:
            row = results[cat].get(ds, {})
            rd_total = sum(parse_value(row.get(f"CS{i}_RD", 0)) for i in range(4))
            bw = row.get("TOTAL_BW", "N/A")
            if rd_total >= 1e9:
                rd_str = f"{rd_total/1e9:.1f}G"
            elif rd_total >= 1e6:
                rd_str = f"{rd_total/1e6:.1f}M"
            elif rd_total >= 1e3:
                rd_str = f"{rd_total/1e3:.0f}K"
            else:
                rd_str = str(int(rd_total))
            row_data.append((rd_str, bw))

        print(f"{cat:<8} {row_data[0][0]:>12} {row_data[0][1]:>14} {row_data[1][0]:>12} {row_data[1][1]:>14} {row_data[2][0]:>12} {row_data[2][1]:>14}")

def compare_latency():
    """Compare memory latency."""
    print("\n" + "="*90)
    print("CCM_TO_MEM_LAT: Memory Access Latency Comparison (Target: DIE2)")
    print("="*90)

    print(f"\n{'Source':<22} {'DIE':^8} {'CCX (ns)':^12} {'DIE (ns)':^12} {'SOCKET (ns)':^12} {'Observation':<25}")
    print("-"*92)

    for fname in ["ccm0todie2_lat_data", "ccm1todie2_lat_data", "ccm2todie2_lat_data", "ccm3todie2_lat_data"]:
        data = {ds: run_parser("mem_lat_parser.py", f"{DATA_DIR}/{ds}/ccm_to_mem_lat/{fname}") for ds in DATASETS}

        for die in ["DIE2"]:
            latencies = {}
            requests = {}
            for ds, rows in data.items():
                if rows:
                    for row in rows:
                        if row.get("DIE") == die:
                            latencies[ds] = parse_value(row.get("avg-cacheable-latency-ns", 0))
                            requests[ds] = parse_value(row.get("total-requests", 0))

            vals = [latencies.get(ds, 0) for ds in DATASETS]
            if any(v > 0 for v in vals):
                if all(v > 0 for v in vals):
                    obs = f"SOCKET +{int(vals[2]-vals[0])}ns vs CCX"
                else:
                    obs = "Some DIEs inactive"
                print(f"{fname:<22} {die:^8} {vals[0]:^12.0f} {vals[1]:^12.0f} {vals[2]:^12.0f} {obs:<25}")

def compare_iom_data():
    """Compare IO module data."""
    print("\n" + "="*90)
    print("IOM_DATA: Non-Cache Memory (IO) Comparison")
    print("="*90)

    data = {ds: run_parser("iom_data_parser.py", f"{DATA_DIR}/{ds}/iom_data") for ds in DATASETS}

    print(f"\n{'Category':<8} {'CCX Requests':>15} {'DIE Requests':>15} {'SOCKET Requests':>18} {'Socket vs CCX':>15}")
    print("-"*75)

    for cat in ["DIE0", "DIE1", "DIE2", "DIE3", "DIE4", "DIE5", "DIE6", "DIE7", "SYS"]:
        totals = {}
        for ds, rows in data.items():
            if rows:
                for row in rows:
                    if row.get("Category") == cat:
                        total = sum(parse_value(row.get(f"CS{i}_RDSZ", 0)) +
                                   parse_value(row.get(f"CS{i}_WRSZ", 0)) for i in range(4))
                        totals[ds] = total

        vals = [totals.get(ds, 0) for ds in DATASETS]
        if vals[0] > 0:
            ratio = f"{vals[2]/vals[0]:.1f}x"
        elif vals[2] > 0:
            ratio = "inf"
        else:
            ratio = "N/A"

        print(f"{cat:<8} {vals[0]:>15.0f} {vals[1]:>15.0f} {vals[2]:>18.0f} {ratio:>15}")

def extract_metric_values_from_parsed(parsed_data, metric_name, die_index=2, section_index=0):
    """Extract metric values from parsed JSON data using new Level 1/2/3 structure.

    Args:
        parsed_data: Parsed JSON from the parser
        metric_name: Name of the metric to find
        die_index: Which DIE to extract (0-7), default 2 for DIE2
        section_index: Which section to use (for files with multiple DIE groups)

    Returns:
        Sum of values for the specified DIE
    """
    if not parsed_data or "sections" not in parsed_data:
        return 0

    sections = parsed_data.get("sections", [])
    if not sections:
        return 0

    # Try to find the metric in Level 1 categories (for Format B like ccm_in_data)
    for section in sections:
        for cat in section.get("level1_categories", []):
            # Check Level 1 name
            if cat.get("name") == metric_name:
                values = cat.get("values", [])
                return sum_die_values(values, die_index)

            # Check Level 2 metrics
            for m2 in cat.get("level2_metrics", []):
                if m2.get("name") == metric_name:
                    values = m2.get("values", [])
                    return sum_die_values(values, die_index)

                # Check Level 3 metrics
                for m3 in m2.get("level3_metrics", []):
                    if m3.get("name") == metric_name:
                        values = m3.get("values", [])
                        return sum_die_values(values, die_index)

    return 0


def sum_die_values(values, die_index, values_per_die=4):
    """Sum values for a specific DIE.

    Args:
        values: List of value strings
        die_index: Which DIE (0-7)
        values_per_die: Number of values per DIE (typically 4 for CS0-CS3)

    Returns:
        Sum of parsed values for the specified DIE
    """
    if not values:
        return 0

    start_idx = die_index * values_per_die
    end_idx = start_idx + values_per_die

    if len(values) < end_idx:
        return 0

    return sum(parse_value(v) for v in values[start_idx:end_idx])

def fmt(v):
    """Format large numbers with K/M/G suffixes."""
    if v >= 1e9:
        return f"{v/1e9:.1f}G"
    elif v >= 1e6:
        return f"{v/1e6:.1f}M"
    elif v >= 1e3:
        return f"{v/1e3:.0f}K"
    else:
        return str(int(v))

def compare_df_data_stream():
    """Compare all data flow stream metrics using new parser with Level 1/2/3 hierarchy."""
    print("\n" + "="*90)
    print("DF_DATA_STREAM: Complete Comparison (DIE2 Totals)")
    print("="*90)

    files_and_metrics = {
        "ccm_in_data": {
            "title": "CCM_IN_DATA (CCM Input Data Transfer)",
            "metrics": [
                ("Data Transfer", 1),      # Level 1 metric
                ("No Data Transfer", 1),   # Level 1 metric
                ("State/PassD", 1),        # Level 1 metric
                ("Inv_NoPassD", 2),        # Level 2 under State/PassD
                ("Inv_PassD", 2),          # Level 2 under State/PassD
                ("PrbSrc", 1),             # Level 1 metric
                ("PrbTgt", 1),             # Level 1 metric
            ]
        },
        "ccm_out_todie2_data": {
            "title": "CCM_OUT_TODIE2_DATA (CCM Output to DIE2)",
            "metrics": [
                ("RdBlkAny", 2),           # Level 2 under Request to DRAM
                ("RdBlkL", 3),             # Level 3 under RdBlkAny
                ("RdBlkC", 3),             # Level 3 under RdBlkAny
                ("SpecDramRd", 2),         # Level 2
                ("VICBLKCLN", 2),          # Level 2
                ("VICBLKFULL", 2),         # Level 2
                ("CHGTOX", 2),             # Level 2
            ]
        },
        "cs_in_data": {
            "title": "CS_IN_DATA (Requests into CS from CCM)",
            "metrics": [
                ("ChgToX", 2),             # Level 2 under Request
                ("VicBlk", 2),             # Level 2
                ("VicBlkFull", 3),         # Level 3 under VicBlk
                ("VicBlkCln", 3),          # Level 3 under VicBlk
                ("RdBlk", 2),              # Level 2
                ("RdBlkL", 3),             # Level 3 under RdBlk
                ("RdBlkX", 3),             # Level 3
                ("RdBlkC", 3),             # Level 3
                ("SrcDn", 2),              # Level 2 under Response
            ]
        },
        "cs_out_data": {
            "title": "CS_OUT_DATA (Requests from CS to UMC/Memory)",
            "metrics": [
                ("Requests to UMC", 2),    # Level 2
                ("RdBlkS", 2),             # Level 2
                ("RdSizedNC", 2),          # Level 2
                ("WrSizedNC", 2),          # Level 2
            ]
        },
        "spf_in_data": {
            "title": "SPF_IN_DATA (Requests into SPF)",
            "metrics": [
                ("RdSized", 2),            # Level 2
                ("RdBlkL", 2),             # Level 2
                ("VicBlkFull", 2),         # Level 2
                ("ChgToX", 2),             # Level 2
            ]
        },
        "spf_out_data": {
            "title": "SPF_OUT_DATA (Responses from SPF)",
            "metrics": [
                ("Target", 2),             # Level 2
                ("Miss", 2),               # Level 2
                ("Hit", 2),                # Level 2
            ]
        }
    }

    for fname, config in files_and_metrics.items():
        print(f"\n--- {config['title']} ---")
        print(f"{'Metric':<25} {'CCX':>18} {'DIE':>18} {'SOCKET':>18}")
        print("-" * 80)

        # Parse data for all datasets
        parsed = {}
        for ds in DATASETS:
            filepath = f"{DATA_DIR}/{ds}/df_data_stream/{fname}"
            parsed[ds] = run_parser("liuxiu_df_data_stream_parser.py", filepath)

        for metric_name, level in config["metrics"]:
            vals = []
            for ds in DATASETS:
                val = extract_metric_values_from_parsed(parsed[ds], metric_name, die_index=2)
                vals.append(val)
            print(f"{metric_name:<25} {fmt(vals[0]):>18} {fmt(vals[1]):>18} {fmt(vals[2]):>18}")

def extract_detail_lat_metric(parsed_data, tx_type, metric_l2, metric_l3=None, die_index=2):
    """Extract metric from df_detail_lat parsed data.

    Args:
        parsed_data: Parsed JSON from df_detail_lat parser
        tx_type: Transaction type (RDBLK, DIRTY_VICTIM, etc.)
        metric_l2: Level 2 metric name (Transaction, AVG LAT(ns), SDP Latency Histogram)
        metric_l3: Level 3 metric name (SDP, FTI, 0ns-50ns, etc.)
        die_index: Which DIE to extract (0-7)

    Returns:
        Sum of values for the specified DIE, or single value for histograms
    """
    if not parsed_data or "sections" not in parsed_data:
        return 0

    for section in parsed_data.get("sections", []):
        for tx in section.get("transaction_types", []):
            if tx.get("name") != tx_type:
                continue

            for m2 in tx.get("level2_metrics", []):
                if m2.get("name") != metric_l2:
                    continue

                if metric_l3 is None:
                    # Return Level 2 values
                    values = m2.get("values", [])
                    return sum_die_values(values, die_index)

                for m3 in m2.get("level3_metrics", []):
                    if m3.get("name") == metric_l3:
                        values = m3.get("values", [])
                        # For histogram percentages, return a single value
                        if "%" in str(values[0]) if values else False:
                            idx = die_index * 4  # CCM0 of the DIE
                            return values[idx] if len(values) > idx else "N/A"
                        return sum_die_values(values, die_index)

    return 0


def compare_df_detail_lat():
    """Compare detailed latency data using new parser with Level 1/2/3 hierarchy."""
    print("\n" + "="*90)
    print("DF_DETAIL_LAT: Detailed Latency Comparison")
    print("="*90)

    # Parse data for all datasets
    parsed = {}
    for ds in DATASETS:
        filepath = f"{DATA_DIR}/{ds}/df_detail_lat/ccm2todie2_latency_data"
        parsed[ds] = run_parser("liuxiu_df_detail_lat_parser.py", filepath)

    # Print RDBLK Transaction comparison
    print("\n--- RDBLK Transaction Counts ---")
    print(f"{'Metric':<25} {'CCX':>18} {'DIE':>18} {'SOCKET':>18}")
    print("-" * 80)

    metrics = [
        ("RDBLK", "Transaction", "SDP", 0, "RDBLK SDP DIE0"),
        ("RDBLK", "Transaction", "SDP", 1, "RDBLK SDP DIE1"),
        ("RDBLK", "Transaction", "SDP", 2, "RDBLK SDP DIE2"),
        ("RDBLK", "Transaction", "SDP", 3, "RDBLK SDP DIE3"),
        ("RDBLK", "Transaction", "FTI", 2, "RDBLK FTI DIE2"),
    ]

    for tx, l2, l3, die_idx, label in metrics:
        vals = []
        for ds in DATASETS:
            val = extract_detail_lat_metric(parsed[ds], tx, l2, l3, die_idx)
            vals.append(val if isinstance(val, (int, float)) else 0)
        print(f"{label:<25} {fmt(vals[0]):>18} {fmt(vals[1]):>18} {fmt(vals[2]):>18}")

    # Print AVG LAT
    print(f"\n{'RDBLK Avg Latency DIE2':<25}", end="")
    for ds in DATASETS:
        val = extract_detail_lat_metric(parsed[ds], "RDBLK", "AVG LAT(ns)", "SDP", 2)
        if isinstance(val, (int, float)) and val > 0:
            print(f"{val:>18.0f} ns", end="")
        else:
            print(f"{'N/A':>18}", end="")
    print()

    # Print DIRTY_VICTIM comparison
    print("\n--- DIRTY_VICTIM Transaction Counts ---")
    print(f"{'Metric':<25} {'CCX':>18} {'DIE':>18} {'SOCKET':>18}")
    print("-" * 80)

    for die_idx, label in [(2, "DIRTY_VICTIM SDP DIE2")]:
        vals = []
        for ds in DATASETS:
            val = extract_detail_lat_metric(parsed[ds], "DIRTY_VICTIM", "Transaction", "SDP", die_idx)
            vals.append(val if isinstance(val, (int, float)) else 0)
        print(f"{label:<25} {fmt(vals[0]):>18} {fmt(vals[1]):>18} {fmt(vals[2]):>18}")

    # Print latency histogram
    print("\n--- RDBLK SDP Latency Histogram (DIE2 CCM0) ---")
    print(f"{'Latency Bucket':<15} {'CCX':>18} {'DIE':>18} {'SOCKET':>18}")
    print("-" * 70)

    buckets = ["0ns-50ns", "50ns-100ns", "100ns-150ns", "150ns-200ns", "200ns-500ns", "500ns-1000ns", ">1000ns"]
    for bucket in buckets:
        vals = []
        for ds in DATASETS:
            val = extract_detail_lat_metric(parsed[ds], "RDBLK", "SDP Latency Histogram", bucket, 2)
            vals.append(val if val else "N/A")
        print(f"{bucket:<15} {str(vals[0]):>18} {str(vals[1]):>18} {str(vals[2]):>18}")


def extract_queue_metric(parsed_data, queue_type, metric_l2, metric_l3=None, section_index=0):
    """Extract metric from df_queue parsed data.

    Args:
        parsed_data: Parsed JSON from df_queue parser
        queue_type: Queue type (REQQ, PRBQ, RSPQ, ORIGDQ)
        metric_l2: Level 2 metric name (Request, Bypass Rate, Kill Rate, etc.)
        metric_l3: Level 3 metric name (optional, for sub-metrics)
        section_index: Which section to use (for files with multiple DIE groups)

    Returns:
        List of values or sum
    """
    if not parsed_data or "sections" not in parsed_data:
        return []

    sections = parsed_data.get("sections", [])
    if section_index >= len(sections):
        return []

    section = sections[section_index]

    for q in section.get("queue_types", []):
        if q.get("name") != queue_type:
            continue

        for m2 in q.get("level2_metrics", []):
            if m2.get("name") != metric_l2:
                continue

            if metric_l3 is None:
                return m2.get("values", [])

            for m3 in m2.get("level3_metrics", []):
                if m3.get("name") == metric_l3:
                    return m3.get("values", [])

    return []


def compare_df_queue():
    """Compare queue metrics using new parser with Level 1/2/3 hierarchy."""
    print("\n" + "="*90)
    print("DF_QUEUE: Queue Metrics Comparison")
    print("="*90)

    # Parse data for all datasets
    parsed = {}
    for ds in DATASETS:
        filepath = f"{DATA_DIR}/{ds}/df_queue/ccm_queue_data"
        parsed[ds] = run_parser("liuxiu_df_queue_parser.py", filepath)

    # Print CCM Queue comparison - Section 1 contains DIE2-3 (consistent with other DIE2 comparisons)
    print("\n--- CCM Queue Metrics (Section 1: DIE2-3) ---")
    print(f"{'Metric':<25} {'CCX':>18} {'DIE':>18} {'SOCKET':>18} {'Observation':<20}")
    print("-" * 100)

    metrics = [
        ("REQQ", "Request", None, "count", "REQQ Requests"),
        ("REQQ", "Bypass Rate", None, "pct", "REQQ Bypass Rate"),
        ("REQQ", "Kill Rate", None, "pct", "REQQ Kill Rate"),
        ("PRBQ", "Probe", None, "count", "PRBQ Probes"),
        ("PRBQ", "Req Bypass Rate", None, "pct", "PRBQ Bypass Rate"),
        ("RSPQ", "Response", None, "count", "RSPQ Responses"),
        ("RSPQ", "RdRsp Kill Rate", None, "pct", "RSPQ Kill Rate"),
        ("ORIGDQ", "write", None, "count", "ORIGDQ Writes"),
    ]

    for queue, l2, l3, mtype, label in metrics:
        vals_numeric = []
        vals_str = []

        for ds in DATASETS:
            values = extract_queue_metric(parsed[ds], queue, l2, l3, section_index=1)

            if mtype == "count":
                # Sum all values in section
                total = sum(parse_value(v) for v in values)
                vals_numeric.append(total)
                vals_str.append(fmt(total))
            else:
                # Average percentage values
                pct_vals = [parse_value(v.replace('%', '')) for v in values if '%' in str(v)]
                avg = sum(pct_vals) / len(pct_vals) if pct_vals else 0
                vals_numeric.append(avg)
                vals_str.append(f"{avg:.2f}%")

        # Observation
        obs = ""
        if vals_numeric[0] != 0 and vals_numeric[2] != 0:
            if mtype == "count":
                ratio = vals_numeric[2] / vals_numeric[0] if vals_numeric[0] > 0 else 0
                if ratio > 2:
                    obs = f"SOCKET {ratio:.0f}x higher"
                elif ratio < 0.5:
                    obs = f"CCX {1/ratio:.0f}x higher"
            else:
                diff = vals_numeric[2] - vals_numeric[0]
                if abs(diff) > 2:
                    obs = f"SOCKET {'+' if diff > 0 else ''}{diff:.1f}%"

        print(f"{label:<25} {vals_str[0]:>18} {vals_str[1]:>18} {vals_str[2]:>18} {obs:<20}")

def print_summary():
    """Print summary of differences."""
    print("\n" + "="*90)
    print("SUMMARY: Key Differences Between CCX, DIE, and SOCKET Datasets")
    print("="*90)

    print("""
┌─────────────────────┬──────────────────┬──────────────────┬──────────────────┐
│ Characteristic      │ CCX              │ DIE              │ SOCKET           │
├─────────────────────┼──────────────────┼──────────────────┼──────────────────┤
│ Workload Profile    │ Low utilization  │ Moderate load    │ High throughput  │
│ Per-DIE Bandwidth   │ 34-90 MB/s       │ 45-145 MB/s      │ 35 MB - 11 GB/s  │
│ System Total BW     │ ~19 GB/s         │ ~19 GB/s         │ ~17 GB/s         │
│ Memory Latency      │ 116-275 ns       │ 125-130 ns       │ 209-211 ns       │
│ IO Activity (DIE5)  │ 0 requests       │ 125 requests     │ 60K requests     │
│ CCM Data Transfer   │ 11K-41K/CCM      │ 21K-112K/CCM     │ 460K-748K/CCM    │
│ Queue Kill Rate     │ 0.54%            │ 0.73%            │ 1.26%            │
├─────────────────────┴──────────────────┴──────────────────┴──────────────────┤
│ KEY INSIGHTS:                                                                │
│ • SOCKET shows 10-100x higher per-DIE activity with higher latency          │
│ • DIE2 is the memory target (DIE:2) - latency varies by workload            │
│ • CCX has minimal IO, SOCKET concentrates IO on specific DIEs               │
│ • System-level bandwidth similar despite per-DIE differences                │
│ • Higher activity correlates with higher queue kill rates                   │
└──────────────────────────────────────────────────────────────────────────────┘
""")

if __name__ == "__main__":
    compare_cm_data()
    compare_latency()
    compare_iom_data()
    compare_df_data_stream()
    compare_df_detail_lat()
    compare_df_queue()
    print_summary()
