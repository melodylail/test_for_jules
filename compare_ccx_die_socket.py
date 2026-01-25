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
    """Compare detailed latency data."""
    print("\n" + "="*90)
    print("DF_DETAIL_LAT: Detailed Latency Comparison")
    print("="*90)

    # Extract transaction counts and latency from raw files
    all_data = {}
    for ds in DATASETS:
        filepath = f"{DATA_DIR}/{ds}/df_detail_lat/ccm2todie2_latency_data"
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()
        except:
            continue

        data = {}
        for i, line in enumerate(lines):
            # Extract RDBLK SDP transaction values (line ~5)
            if 'SDP' in line and 'Transaction' not in line and 'Histogram' not in line and i < 10:
                parts = re.split(r'\s{2,}', line.strip())
                vals = [parse_value(p) for p in parts if re.match(r'^[\d.]+\s*[KMG]?$', p.strip())]
                if vals and len(vals) >= 16:
                    data["RDBLK_SDP_DIE0"] = sum(vals[:4])
                    data["RDBLK_SDP_DIE1"] = sum(vals[4:8])
                    data["RDBLK_SDP_DIE2"] = sum(vals[8:12])
                    data["RDBLK_SDP_DIE3"] = sum(vals[12:16])
                    data["RDBLK_SDP_Total"] = sum(vals)
                break

        # Extract FTI values
        for i, line in enumerate(lines):
            if 'FTI' in line and 'Transaction' not in line and 'Histogram' not in line and i < 10:
                parts = re.split(r'\s{2,}', line.strip())
                vals = [parse_value(p) for p in parts if re.match(r'^[\d.]+\s*[KMG]?$', p.strip())]
                if vals and len(vals) >= 12:
                    data["RDBLK_FTI_DIE2"] = sum(vals[8:12])
                    data["RDBLK_FTI_Total"] = sum(vals)
                break

        # Extract AVG LAT values
        for i, line in enumerate(lines):
            if 'AVG LAT' in line:
                for j in range(i+1, min(i+3, len(lines))):
                    if 'SDP' in lines[j]:
                        parts = re.split(r'\s{2,}', lines[j].strip())
                        vals = [parse_value(p) for p in parts if re.match(r'^[\d.]+$', p.strip())]
                        if vals and len(vals) >= 12:
                            nonzero = [v for v in vals[8:12] if v > 0]
                            data["RDBLK_AvgLat_DIE2"] = sum(nonzero) / len(nonzero) if nonzero else 0
                        break
                break

        # Extract DIRTY_VICTIM SDP values
        in_dirty_victim = False
        for i, line in enumerate(lines):
            if 'DIRTY_VICTIM' in line:
                in_dirty_victim = True
                continue
            if in_dirty_victim and 'SDP' in line and 'Transaction' not in line and 'Histogram' not in line:
                parts = re.split(r'\s{2,}', line.strip())
                vals = [parse_value(p) for p in parts if re.match(r'^[\d.]+\s*[KMG]?$', p.strip())]
                if vals and len(vals) >= 12:
                    data["DirtyVictim_SDP_DIE2"] = sum(vals[8:12])
                    data["DirtyVictim_SDP_Total"] = sum(vals)
                break

        # Extract latency histogram
        in_sdp_histogram = False
        buckets = ["0ns-50ns", "50ns-100ns", "100ns-150ns", "150ns-200ns", "200ns-500ns", "500ns-1000ns", ">1000ns"]
        for line in lines:
            if 'SDP Latency Histogram' in line:
                in_sdp_histogram = True
                continue
            if in_sdp_histogram and 'FTI' in line:
                break
            if in_sdp_histogram:
                for bucket in buckets:
                    if bucket in line:
                        parts = re.split(r'\s{2,}', line.strip())
                        pct_vals = [p for p in parts if '%' in p]
                        if len(pct_vals) >= 9:
                            data[f"Histogram_{bucket}"] = pct_vals[8]  # DIE2 CCM0
                        break

        all_data[ds] = data

    # Print RDBLK Transaction comparison
    print("\n--- RDBLK Transaction Counts ---")
    print(f"{'Metric':<25} {'CCX':>18} {'DIE':>18} {'SOCKET':>18}")
    print("-" * 80)

    metrics = [
        ("RDBLK_SDP_DIE0", "RDBLK SDP DIE0"),
        ("RDBLK_SDP_DIE1", "RDBLK SDP DIE1"),
        ("RDBLK_SDP_DIE2", "RDBLK SDP DIE2"),
        ("RDBLK_SDP_DIE3", "RDBLK SDP DIE3"),
        ("RDBLK_SDP_Total", "RDBLK SDP Total"),
        ("RDBLK_FTI_DIE2", "RDBLK FTI DIE2"),
        ("RDBLK_FTI_Total", "RDBLK FTI Total"),
    ]
    for key, label in metrics:
        vals = [all_data.get(ds, {}).get(key, 0) for ds in DATASETS]
        print(f"{label:<25} {fmt(vals[0]):>18} {fmt(vals[1]):>18} {fmt(vals[2]):>18}")

    # Print latency
    print(f"\n{'RDBLK Avg Latency DIE2':<25}", end="")
    for ds in DATASETS:
        lat = all_data.get(ds, {}).get("RDBLK_AvgLat_DIE2", 0)
        print(f"{lat:>18.0f} ns" if lat > 0 else f"{'N/A':>18}", end="")
    print()

    # Print DIRTY_VICTIM comparison
    print("\n--- DIRTY_VICTIM Transaction Counts ---")
    print(f"{'Metric':<25} {'CCX':>18} {'DIE':>18} {'SOCKET':>18}")
    print("-" * 80)
    for key, label in [("DirtyVictim_SDP_DIE2", "DIRTY_VICTIM SDP DIE2"), ("DirtyVictim_SDP_Total", "DIRTY_VICTIM SDP Total")]:
        vals = [all_data.get(ds, {}).get(key, 0) for ds in DATASETS]
        print(f"{label:<25} {fmt(vals[0]):>18} {fmt(vals[1]):>18} {fmt(vals[2]):>18}")

    # Print latency histogram
    print("\n--- RDBLK SDP Latency Histogram (DIE2 CCM0) ---")
    print(f"{'Latency Bucket':<15} {'CCX':>18} {'DIE':>18} {'SOCKET':>18}")
    print("-" * 70)
    buckets = ["0ns-50ns", "50ns-100ns", "100ns-150ns", "150ns-200ns", "200ns-500ns", "500ns-1000ns", ">1000ns"]
    for bucket in buckets:
        vals = [all_data.get(ds, {}).get(f"Histogram_{bucket}", "N/A") for ds in DATASETS]
        print(f"{bucket:<15} {vals[0]:>18} {vals[1]:>18} {vals[2]:>18}")


def compare_df_queue():
    """Compare queue metrics."""
    print("\n" + "="*90)
    print("DF_QUEUE: Queue Metrics Comparison")
    print("="*90)

    all_data = {}
    for ds in DATASETS:
        filepath = f"{DATA_DIR}/{ds}/df_queue/ccm_queue_data"
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()
        except:
            continue

        data = {}
        current_queue = None

        for line in lines:
            line_stripped = line.strip()

            # Detect queue type
            if line_stripped in ["REQQ", "RSPQ", "PRBQ", "ORIGDQ"]:
                current_queue = line_stripped
                continue

            parts = re.split(r'\s{2,}', line_stripped)

            if current_queue == "REQQ":
                if "Request" in line_stripped and "Kill" not in line_stripped:
                    vals = [parse_value(p) for p in parts if re.match(r'^[\d.]+\s*[KMG]?$', p.strip())]
                    data["REQQ_Request_DIE0"] = sum(vals[:4]) if len(vals) >= 4 else 0
                    data["REQQ_Request_DIE1"] = sum(vals[4:8]) if len(vals) >= 8 else 0
                elif "Bypass Rate" in line_stripped and "|" not in line_stripped[:5]:
                    vals = [parse_value(p.replace('%', '')) for p in parts if '%' in p]
                    data["REQQ_Bypass_DIE0"] = sum(vals[:4])/4 if len(vals) >= 4 else 0
                elif "Kill Rate" in line_stripped and "|_" in line_stripped:
                    vals = [parse_value(p.replace('%', '')) for p in parts if '%' in p]
                    data["REQQ_Kill_DIE0"] = sum(vals[:4])/4 if len(vals) >= 4 else 0

            elif current_queue == "PRBQ":
                if "Probe" in line_stripped and "Bypass" not in line_stripped:
                    vals = [parse_value(p) for p in parts if re.match(r'^[\d.]+\s*[KMG]?$', p.strip())]
                    data["PRBQ_Probe_DIE0"] = sum(vals[:4]) if len(vals) >= 4 else 0
                elif "Req Bypass Rate" in line_stripped:
                    vals = [parse_value(p.replace('%', '')) for p in parts if '%' in p]
                    data["PRBQ_Bypass_DIE0"] = sum(vals[:4])/4 if len(vals) >= 4 else 0

            elif current_queue == "RSPQ":
                if "Response" in line_stripped:
                    vals = [parse_value(p) for p in parts if re.match(r'^[\d.]+\s*[KMG]?$', p.strip())]
                    data["RSPQ_Response_DIE0"] = sum(vals[:4]) if len(vals) >= 4 else 0
                elif "RdRsp Kill Rate" in line_stripped:
                    vals = [parse_value(p.replace('%', '')) for p in parts if '%' in p]
                    data["RSPQ_Kill_DIE0"] = sum(vals[:4])/4 if len(vals) >= 4 else 0

            elif current_queue == "ORIGDQ":
                if "write" in line_stripped and "Pick" not in line_stripped:
                    vals = [parse_value(p) for p in parts if re.match(r'^[\d.]+\s*[KMG]?$', p.strip())]
                    data["ORIGDQ_Write_DIE0"] = sum(vals[:4]) if len(vals) >= 4 else 0

        all_data[ds] = data

    # Print CCM Queue comparison
    print("\n--- CCM Queue Metrics (DIE0) ---")
    print(f"{'Metric':<25} {'CCX':>18} {'DIE':>18} {'SOCKET':>18} {'Observation':<20}")
    print("-" * 100)

    metrics = [
        ("REQQ_Request_DIE0", "REQQ Requests", "count"),
        ("REQQ_Request_DIE1", "REQQ Requests DIE1", "count"),
        ("REQQ_Bypass_DIE0", "REQQ Bypass Rate", "pct"),
        ("REQQ_Kill_DIE0", "REQQ Kill Rate", "pct"),
        ("PRBQ_Probe_DIE0", "PRBQ Probes", "count"),
        ("PRBQ_Bypass_DIE0", "PRBQ Bypass Rate", "pct"),
        ("RSPQ_Response_DIE0", "RSPQ Responses", "count"),
        ("RSPQ_Kill_DIE0", "RSPQ Kill Rate", "pct"),
        ("ORIGDQ_Write_DIE0", "ORIGDQ Writes", "count"),
    ]

    for key, label, mtype in metrics:
        vals = [all_data.get(ds, {}).get(key, 0) for ds in DATASETS]

        if mtype == "count":
            strs = [fmt(v) for v in vals]
        else:
            strs = [f"{v:.2f}%" for v in vals]

        # Observation
        obs = ""
        if vals[0] != 0 and vals[2] != 0:
            if mtype == "count":
                ratio = vals[2] / vals[0] if vals[0] > 0 else 0
                if ratio > 2:
                    obs = f"SOCKET {ratio:.0f}x higher"
                elif ratio < 0.5:
                    obs = f"CCX {1/ratio:.0f}x higher"
            else:
                diff = vals[2] - vals[0]
                if abs(diff) > 2:
                    obs = f"SOCKET {'+' if diff > 0 else ''}{diff:.1f}%"

        print(f"{label:<25} {strs[0]:>18} {strs[1]:>18} {strs[2]:>18} {obs:<20}")

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
