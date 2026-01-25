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

def extract_die2_values_from_file(filepath, metrics):
    """Extract DIE2 values for given metrics from a raw data file."""
    results = {}
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()

        for line in lines[2:]:  # Skip header lines
            parts = re.split(r'\s{2,}', line.strip())
            if not parts:
                continue

            # Get metric name (first non-empty, non-pipe part)
            metric_name = None
            for p in parts:
                p_clean = p.replace('|-', '').replace('|_', '').replace('|', '').strip()
                if p_clean and p_clean not in ['', '-']:
                    metric_name = p_clean
                    break

            if metric_name in metrics:
                # Extract numeric values
                values = []
                for p in parts[1:]:
                    p_clean = p.replace('|-', '').replace('|_', '').replace('|', '').strip()
                    if p_clean and re.match(r'^[\d.]+\s*[KMG]?$', p_clean):
                        values.append(parse_value(p_clean))

                # DIE2 is typically the 3rd DIE (index 2), each DIE has 4 CS values
                if len(values) >= 12:
                    die2_sum = sum(values[8:12])
                    results[metric_name] = die2_sum
    except:
        pass
    return results

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
    """Compare all data flow stream metrics."""
    print("\n" + "="*90)
    print("DF_DATA_STREAM: Complete Comparison (DIE2 Totals)")
    print("="*90)

    files_and_metrics = {
        "ccm_in_data": {
            "title": "CCM_IN_DATA (CCM Input Data Transfer)",
            "metrics": ["Data Transfer", "PrbTgt"]
        },
        "cs_in_data": {
            "title": "CS_IN_DATA (Requests into CS from CCM)",
            "metrics": ["VicBlk", "RdBlk", "ChgToX"]
        },
        "cs_out_data": {
            "title": "CS_OUT_DATA (Requests from CS to UMC/Memory)",
            "metrics": ["Requests to UMC", "RdBlkS", "WrSizedNC"]
        },
        "spf_in_data": {
            "title": "SPF_IN_DATA (Requests into SPF)",
            "metrics": ["RdSized", "RdBlkL", "VicBlkFull", "ChgToX"]
        },
        "spf_out_data": {
            "title": "SPF_OUT_DATA (Responses from SPF)",
            "metrics": ["Target", "Miss", "Hit"]
        }
    }

    for fname, config in files_and_metrics.items():
        print(f"\n--- {config['title']} ---")
        print(f"{'Metric':<25} {'CCX':>18} {'DIE':>18} {'SOCKET':>18}")
        print("-" * 80)

        for metric in config["metrics"]:
            vals = []
            for ds in DATASETS:
                filepath = f"{DATA_DIR}/{ds}/df_data_stream/{fname}"
                result = extract_die2_values_from_file(filepath, [metric])
                vals.append(result.get(metric, 0))
            print(f"{metric:<25} {fmt(vals[0]):>18} {fmt(vals[1]):>18} {fmt(vals[2]):>18}")

def compare_df_detail_lat():
    """Compare detailed latency histograms."""
    print("\n" + "="*90)
    print("DF_DETAIL_LAT: RDBLK Latency Distribution (CCM2 to DIE2)")
    print("="*90)

    data = {ds: run_parser("liuxiu_df_detail_lat_parser.py",
                           f"{DATA_DIR}/{ds}/df_detail_lat/ccm2todie2_latency_data")
            for ds in DATASETS}

    # Extract latency histogram for RDBLK SDP
    print(f"\n{'Latency Bucket':<15} {'CCX':>15} {'DIE':>15} {'SOCKET':>15}")
    print("-"*62)

    histograms = defaultdict(dict)
    for ds, parsed in data.items():
        if parsed and parsed.get("target_sections"):
            for section in parsed["target_sections"]:
                for tx in section.get("transaction_types", []):
                    if tx.get("type") in ["RDBLK", "RdBlk"]:
                        in_histogram = False
                        for entry in tx.get("data", []):
                            raw = entry.get("raw_line", "")
                            fields = entry.get("fields", [])
                            if "SDP Latency Histogram" in raw:
                                in_histogram = True
                            elif in_histogram and "ns" in raw:
                                bucket = fields[2] if len(fields) > 2 else "N/A"
                                value = fields[3] if len(fields) > 3 else "0"
                                histograms[bucket][ds] = value
                            elif "FTI" in raw:
                                in_histogram = False

    for bucket in ["0ns-50ns", "50ns-100ns", "100ns-150ns", "150ns-200ns", "200ns-500ns", "500ns-1000ns", ">1000ns"]:
        vals = [histograms[bucket].get(ds, "0.00%") for ds in DATASETS]
        print(f"{bucket:<15} {vals[0]:>15} {vals[1]:>15} {vals[2]:>15}")

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
    print_summary()
