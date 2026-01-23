#!/usr/bin/env python3
"""
Full Comparison Visualization Script for CCX vs DIE data
Compares all JSON results including df_data_stream, df_queue, df_detail_lat
"""

import json
import os
import glob
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path


def parse_value(value_str):
    """Parse values with suffixes."""
    if isinstance(value_str, (int, float)):
        return float(value_str)

    value_str = str(value_str).strip()
    if value_str == "0" or value_str == "":
        return 0.0

    # Remove units
    for unit in ['GB/s', 'MB/s', 'KB/s', 'B/s']:
        if unit in value_str:
            value_str = value_str.replace(unit, '').strip()
            if unit == 'GB/s':
                mult_unit = 1e9
            elif unit == 'MB/s':
                mult_unit = 1e6
            elif unit == 'KB/s':
                mult_unit = 1e3
            else:
                mult_unit = 1
            try:
                return float(value_str) * mult_unit
            except:
                pass

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

    # Handle "N suffix" format
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


def load_json_file(filepath):
    """Load a JSON file."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            json_start = min(
                content.find('[') if content.find('[') >= 0 else len(content),
                content.find('{') if content.find('{') >= 0 else len(content)
            )
            if json_start < len(content):
                content = content[json_start:]
            return json.loads(content)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None


def extract_ccx_df_data_stream(data):
    """Extract data from CCX df_data_stream format (structured dict)."""
    if not data or not isinstance(data, list) or len(data) == 0:
        return {}

    result = {}
    for item in data:
        if isinstance(item, dict):
            for metric_name, values in item.items():
                if isinstance(values, dict):
                    result[metric_name] = {k: parse_value(v) for k, v in values.items()}
    return result


def extract_die_df_data_stream(data):
    """Extract data from DIE df_data_stream format (now same as CCX)."""
    # DIE format now matches CCX format after parser fix
    return extract_ccx_df_data_stream(data)


def extract_ccx_df_queue(data):
    """Extract data from CCX df_queue format."""
    if not data or not isinstance(data, list) or len(data) == 0:
        return {}

    result = {}
    for item in data:
        if isinstance(item, dict):
            for queue_name, queue_data in item.items():
                if isinstance(queue_data, dict):
                    for metric_name, values in queue_data.items():
                        if isinstance(values, dict) and values:
                            key = f"{queue_name}_{metric_name}"
                            result[key] = {k: parse_value(v) for k, v in values.items()}
    return result


def extract_die_df_queue(data):
    """Extract data from DIE df_queue format (now same as CCX)."""
    # DIE format now matches CCX format after parser fix
    return extract_ccx_df_queue(data)


def compare_hierarchical_data(ccx_data, die_data, title, output_dir, filename):
    """Compare hierarchical data between CCX and DIE."""

    os.makedirs(output_dir, exist_ok=True)

    # Find common metrics
    ccx_keys = set(ccx_data.keys())
    die_keys = set(die_data.keys())
    common_keys = ccx_keys & die_keys

    if not common_keys:
        print(f"    No common metrics found for {filename}")
        # Try partial matching
        for ccx_key in ccx_keys:
            for die_key in die_keys:
                if ccx_key.lower() in die_key.lower() or die_key.lower() in ccx_key.lower():
                    common_keys.add((ccx_key, die_key))

    print(f"    Found {len(common_keys)} common metrics")

    # Create comparison for top metrics
    metrics_to_compare = list(common_keys)[:10]  # Limit to 10 metrics

    for metric in metrics_to_compare:
        if isinstance(metric, tuple):
            ccx_metric, die_metric = metric
        else:
            ccx_metric = die_metric = metric

        ccx_vals = ccx_data.get(ccx_metric, {})
        die_vals = die_data.get(die_metric, {})

        if not ccx_vals or not die_vals:
            continue

        # Find common components
        common_components = sorted(set(ccx_vals.keys()) & set(die_vals.keys()))

        if len(common_components) < 2:
            continue

        # Limit components for visualization
        components = common_components[:16]

        ccx_values = [ccx_vals.get(c, 0) for c in components]
        die_values = [die_vals.get(c, 0) for c in components]

        # Skip if all zeros
        if sum(ccx_values) == 0 and sum(die_values) == 0:
            continue

        fig, ax = plt.subplots(figsize=(14, 7))

        x = np.arange(len(components))
        width = 0.35

        bars1 = ax.bar(x - width/2, ccx_values, width, label='CCX', color='steelblue', alpha=0.8)
        bars2 = ax.bar(x + width/2, die_values, width, label='DIE', color='coral', alpha=0.8)

        ax.set_xlabel('Component', fontsize=12)
        ax.set_ylabel('Value', fontsize=12)

        safe_metric = str(ccx_metric)[:40]
        ax.set_title(f'{filename} - {safe_metric}\nCCX vs DIE', fontsize=12, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(components, rotation=45, ha='right', fontsize=8)
        ax.legend()
        ax.grid(axis='y', alpha=0.3)

        plt.tight_layout()
        safe_name = str(ccx_metric).replace('/', '_').replace(' ', '_').replace('|', '')[:30]
        plt.savefig(os.path.join(output_dir, f'{filename}_{safe_name}_comparison.png'),
                   dpi=300, bbox_inches='tight')
        plt.close()
        print(f"      Saved: {filename}_{safe_name}_comparison.png")


def extract_ccx_df_detail_lat(data):
    """Extract data from CCX df_detail_lat format (nested dict structure)."""
    if not data or not isinstance(data, list) or len(data) == 0:
        return {}

    result = {}
    for item in data:
        if isinstance(item, dict):
            for target_die, operations in item.items():
                if not isinstance(operations, dict):
                    continue
                for op_name, metrics in operations.items():
                    if not isinstance(metrics, dict):
                        continue
                    for metric_name, channels in metrics.items():
                        if not isinstance(channels, dict):
                            continue
                        for channel_name, values in channels.items():
                            if isinstance(values, dict):
                                key = f"{op_name}_{metric_name}_{channel_name}"
                                result[key] = {k: parse_value(v) for k, v in values.items()}
    return result


def extract_die_df_detail_lat(data):
    """Extract data from DIE df_detail_lat format (now same structure as CCX)."""
    if not data or not isinstance(data, list) or len(data) == 0:
        return {}

    # DIE data now has same structure as CCX after parser fix:
    # TARGET_CORE_DIE_X -> op_name -> metric_name -> channel_name -> values
    result = {}
    for item in data:
        if isinstance(item, dict):
            for target_die, operations in item.items():
                if not isinstance(operations, dict):
                    continue
                for op_name, metrics in operations.items():
                    if not isinstance(metrics, dict):
                        continue
                    for metric_name, channels in metrics.items():
                        if not isinstance(channels, dict):
                            continue
                        for channel_name, values in channels.items():
                            if isinstance(values, dict):
                                key = f"{op_name}_{metric_name}_{channel_name}"
                                result[key] = {k: parse_value(v) for k, v in values.items()}
    return result


def compare_df_detail_lat(ccx_dir, die_dir, output_dir):
    """Compare df_detail_lat files."""

    os.makedirs(output_dir, exist_ok=True)

    ccx_files = glob.glob(os.path.join(ccx_dir, "*_parsed.json"))
    die_files = glob.glob(os.path.join(die_dir, "*_parsed.json"))

    ccx_names = {Path(f).stem.replace('_parsed', ''): f for f in ccx_files}
    die_names = {Path(f).stem.replace('_parsed', ''): f for f in die_files}

    common_files = set(ccx_names.keys()) & set(die_names.keys())

    print(f"  Found {len(common_files)} common df_detail_lat files")

    files_with_data = 0
    for filename in sorted(common_files):
        print(f"    Processing {filename}...")

        ccx_data = load_json_file(ccx_names[filename])
        die_data = load_json_file(die_names[filename])

        if not ccx_data and not die_data:
            print(f"      Both files are empty, skipping")
            continue

        ccx_extracted = extract_ccx_df_detail_lat(ccx_data) if ccx_data else {}
        die_extracted = extract_die_df_detail_lat(die_data) if die_data else {}

        if not ccx_extracted and not die_extracted:
            print(f"      No data extracted from either file")
            continue

        if ccx_extracted and not die_extracted:
            # Create CCX-only visualizations
            files_with_data += 1
            print(f"      DIE data is empty - creating CCX-only visualization")
            create_ccx_only_visualization(ccx_extracted, filename, output_dir)
        elif ccx_extracted and die_extracted:
            files_with_data += 1
            compare_hierarchical_data(ccx_extracted, die_extracted,
                                     f"df_detail_lat - {filename}",
                                     os.path.join(output_dir, filename),
                                     filename)

    if files_with_data == 0:
        print("      No files with comparable data found")


def create_ccx_only_visualization(ccx_data, filename, output_dir):
    """Create visualization for CCX data only when DIE data is not available."""
    os.makedirs(output_dir, exist_ok=True)

    # Get key metrics (Transaction and AVG LAT)
    key_metrics = [k for k in ccx_data.keys() if 'Transaction' in k or 'AVG LAT' in k][:5]

    for metric in key_metrics:
        values = ccx_data.get(metric, {})
        if not values:
            continue

        # Get non-zero values
        components = sorted([k for k, v in values.items() if v > 0])
        if len(components) < 2:
            continue

        vals = [values.get(c, 0) for c in components]

        fig, ax = plt.subplots(figsize=(12, 6))

        x = np.arange(len(components))
        ax.bar(x, vals, color='steelblue', alpha=0.8)

        ax.set_xlabel('Component', fontsize=12)
        ax.set_ylabel('Value', fontsize=12)

        safe_metric = str(metric)[:50]
        ax.set_title(f'{filename} - {safe_metric}\n(CCX data only - DIE data not available)', fontsize=11, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(components, rotation=45, ha='right', fontsize=8)
        ax.grid(axis='y', alpha=0.3)

        plt.tight_layout()
        safe_name = str(metric).replace('/', '_').replace(' ', '_').replace('|', '')[:30]
        plt.savefig(os.path.join(output_dir, f'{filename}_{safe_name}_ccx_only.png'),
                   dpi=300, bbox_inches='tight')
        plt.close()
        print(f"      Saved: {filename}_{safe_name}_ccx_only.png")


def compare_df_data_stream(ccx_dir, die_dir, output_dir):
    """Compare df_data_stream files."""

    os.makedirs(output_dir, exist_ok=True)

    ccx_files = glob.glob(os.path.join(ccx_dir, "*_parsed.json"))
    die_files = glob.glob(os.path.join(die_dir, "*_parsed.json"))

    # Match files by name
    ccx_names = {Path(f).stem.replace('_parsed', ''): f for f in ccx_files}
    die_names = {Path(f).stem.replace('_parsed', ''): f for f in die_files}

    common_files = set(ccx_names.keys()) & set(die_names.keys())

    print(f"  Found {len(common_files)} common df_data_stream files")

    for filename in sorted(common_files):
        print(f"    Processing {filename}...")

        ccx_data = load_json_file(ccx_names[filename])
        die_data = load_json_file(die_names[filename])

        if not ccx_data or not die_data:
            continue

        # Extract data based on format
        ccx_extracted = extract_ccx_df_data_stream(ccx_data)
        die_extracted = extract_die_df_data_stream(die_data)

        if ccx_extracted and die_extracted:
            compare_hierarchical_data(ccx_extracted, die_extracted,
                                     f"df_data_stream - {filename}",
                                     os.path.join(output_dir, filename),
                                     filename)


def compare_df_queue(ccx_dir, die_dir, output_dir):
    """Compare df_queue files."""

    os.makedirs(output_dir, exist_ok=True)

    ccx_files = glob.glob(os.path.join(ccx_dir, "*_parsed.json"))
    die_files = glob.glob(os.path.join(die_dir, "*_parsed.json"))

    ccx_names = {Path(f).stem.replace('_parsed', ''): f for f in ccx_files}
    die_names = {Path(f).stem.replace('_parsed', ''): f for f in die_files}

    common_files = set(ccx_names.keys()) & set(die_names.keys())

    print(f"  Found {len(common_files)} common df_queue files")

    for filename in sorted(common_files):
        print(f"    Processing {filename}...")

        ccx_data = load_json_file(ccx_names[filename])
        die_data = load_json_file(die_names[filename])

        if not ccx_data or not die_data:
            continue

        ccx_extracted = extract_ccx_df_queue(ccx_data)
        die_extracted = extract_die_df_queue(die_data)

        if ccx_extracted and die_extracted:
            compare_hierarchical_data(ccx_extracted, die_extracted,
                                     f"df_queue - {filename}",
                                     os.path.join(output_dir, filename),
                                     filename)


def create_summary_dashboard(ccx_base, die_base, output_dir):
    """Create a summary dashboard comparing all data types."""

    os.makedirs(output_dir, exist_ok=True)

    fig = plt.figure(figsize=(20, 16))
    fig.suptitle('CCX vs DIE - Complete Data Comparison Summary', fontsize=18, fontweight='bold', y=0.98)

    # Load simple data
    ccx_cm = load_json_file(os.path.join(ccx_base, 'cm_data_parsed.json'))
    die_cm = load_json_file(os.path.join(die_base, 'cm_data_parsed.json'))

    ccx_iom = load_json_file(os.path.join(ccx_base, 'iom_data_parsed.json'))
    die_iom = load_json_file(os.path.join(die_base, 'iom_data_parsed.json'))

    # Subplot 1: CM Data Total Bandwidth
    ax1 = fig.add_subplot(2, 3, 1)
    if ccx_cm and die_cm:
        categories = [e['Category'] for e in ccx_cm if not e['Category'].startswith('S')][:8]
        ccx_bw = [parse_value(next((e['TOTAL_BW'] for e in ccx_cm if e['Category'] == c), '0')) for c in categories]
        die_bw = [parse_value(next((e['TOTAL_BW'] for e in die_cm if e['Category'] == c), '0')) for c in categories]

        x = np.arange(len(categories))
        width = 0.35
        ax1.bar(x - width/2, np.array(ccx_bw)/1e6, width, label='CCX', color='steelblue')
        ax1.bar(x + width/2, np.array(die_bw)/1e6, width, label='DIE', color='coral')
        ax1.set_xlabel('DIE')
        ax1.set_ylabel('Bandwidth (MB/s)')
        ax1.set_title('Core Memory - Total BW')
        ax1.set_xticks(x)
        ax1.set_xticklabels(categories, rotation=45)
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3)

    # Subplot 2: IOM Data
    ax2 = fig.add_subplot(2, 3, 2)
    if ccx_iom and die_iom:
        categories = [e['Category'] for e in ccx_iom if not e['Category'].startswith('S')][:8]
        ccx_vals = [parse_value(next((e.get('TOTAL_BW_MIN', '0') for e in ccx_iom if e['Category'] == c), '0')) for c in categories]
        die_vals = [parse_value(next((e.get('TOTAL_BW_MIN', '0') for e in die_iom if e['Category'] == c), '0')) for c in categories]

        x = np.arange(len(categories))
        ax2.bar(x - width/2, ccx_vals, width, label='CCX', color='steelblue')
        ax2.bar(x + width/2, die_vals, width, label='DIE', color='coral')
        ax2.set_xlabel('DIE')
        ax2.set_ylabel('Bandwidth (B/s)')
        ax2.set_title('IOM - Min Bandwidth')
        ax2.set_xticks(x)
        ax2.set_xticklabels(categories, rotation=45)
        ax2.legend()
        ax2.grid(axis='y', alpha=0.3)

    # Subplot 3: CCM to Mem Lat comparison
    ax3 = fig.add_subplot(2, 3, 3)
    ccx_lat_files = glob.glob(os.path.join(ccx_base, 'ccm_to_mem_lat', '*_parsed.json'))
    die_lat_files = glob.glob(os.path.join(die_base, 'ccm_to_mem_lat', '*_parsed.json'))

    if ccx_lat_files and die_lat_files:
        ccx_latencies = []
        die_latencies = []
        labels = []

        for ccx_file in sorted(ccx_lat_files):
            ccm_name = Path(ccx_file).stem.replace('_parsed', '')
            die_file = os.path.join(die_base, 'ccm_to_mem_lat', f'{ccm_name}_parsed.json')

            if os.path.exists(die_file):
                ccx_data = load_json_file(ccx_file)
                die_data = load_json_file(die_file)

                if ccx_data and die_data:
                    # Get non-zero latency
                    for entry in ccx_data:
                        cat = entry.get('DIE', entry.get('Category', ''))
                        lat_col = 'avg-cacheable-latency-ns'
                        if lat_col in entry:
                            lat = parse_value(entry[lat_col])
                            if lat > 0:
                                ccx_latencies.append(lat)
                                labels.append(f"{ccm_name[:6]}\n{cat}")

                                # Find corresponding die entry
                                for de in die_data:
                                    de_cat = de.get('Category', de.get('DIE', ''))
                                    if de_cat == cat:
                                        # Check for latency column with different possible names
                                        for col in de.keys():
                                            if 'latency' in col.lower() and 'ns' in col.lower():
                                                die_latencies.append(parse_value(de[col]))
                                                break
                                        else:
                                            die_latencies.append(0)
                                        break

        if ccx_latencies and die_latencies and len(ccx_latencies) == len(die_latencies):
            x = np.arange(len(labels))
            ax3.bar(x - width/2, ccx_latencies, width, label='CCX', color='steelblue')
            ax3.bar(x + width/2, die_latencies, width, label='DIE', color='coral')
            ax3.set_xlabel('CCM to DIE Path')
            ax3.set_ylabel('Latency (ns)')
            ax3.set_title('CCM to Memory Latency')
            ax3.set_xticks(x)
            ax3.set_xticklabels(labels, fontsize=7, rotation=45)
            ax3.legend()
            ax3.grid(axis='y', alpha=0.3)

    # Subplot 4: df_data_stream summary
    ax4 = fig.add_subplot(2, 3, 4)
    ccx_stream_files = glob.glob(os.path.join(ccx_base, 'df_data_stream', '*_parsed.json'))
    die_stream_files = glob.glob(os.path.join(die_base, 'df_data_stream', '*_parsed.json'))

    if ccx_stream_files and die_stream_files:
        stream_names = []
        ccx_totals = []
        die_totals = []

        for ccx_file in sorted(ccx_stream_files)[:7]:
            name = Path(ccx_file).stem.replace('_parsed', '').replace('_data', '')
            die_file = os.path.join(die_base, 'df_data_stream', f'{Path(ccx_file).stem}.json')

            ccx_data = load_json_file(ccx_file)
            die_file_match = [f for f in die_stream_files if Path(f).stem.replace('_parsed', '') == Path(ccx_file).stem.replace('_parsed', '')]

            if die_file_match:
                die_data = load_json_file(die_file_match[0])

                ccx_ext = extract_ccx_df_data_stream(ccx_data)
                die_ext = extract_die_df_data_stream(die_data)

                # Sum all values
                ccx_total = sum(sum(v.values()) for v in ccx_ext.values() if isinstance(v, dict))
                die_total = sum(sum(v.values()) for v in die_ext.values() if isinstance(v, dict))

                stream_names.append(name[:10])
                ccx_totals.append(ccx_total)
                die_totals.append(die_total)

        if stream_names:
            x = np.arange(len(stream_names))
            ax4.bar(x - width/2, np.array(ccx_totals)/1e6, width, label='CCX', color='steelblue')
            ax4.bar(x + width/2, np.array(die_totals)/1e6, width, label='DIE', color='coral')
            ax4.set_xlabel('Data Stream')
            ax4.set_ylabel('Total (Millions)')
            ax4.set_title('DF Data Stream - Totals')
            ax4.set_xticks(x)
            ax4.set_xticklabels(stream_names, rotation=45)
            ax4.legend()
            ax4.grid(axis='y', alpha=0.3)

    # Subplot 5: df_queue summary
    ax5 = fig.add_subplot(2, 3, 5)
    ccx_queue_files = glob.glob(os.path.join(ccx_base, 'df_queue', '*_parsed.json'))
    die_queue_files = glob.glob(os.path.join(die_base, 'df_queue', '*_parsed.json'))

    if ccx_queue_files and die_queue_files:
        queue_names = []
        ccx_requests = []
        die_requests = []

        for ccx_file in sorted(ccx_queue_files):
            name = Path(ccx_file).stem.replace('_parsed', '').replace('_queue_data', '')
            die_file_match = [f for f in die_queue_files if Path(f).stem.replace('_parsed', '') == Path(ccx_file).stem.replace('_parsed', '')]

            if die_file_match:
                ccx_data = load_json_file(ccx_file)
                die_data = load_json_file(die_file_match[0])

                ccx_ext = extract_ccx_df_queue(ccx_data)
                die_ext = extract_die_df_queue(die_data)

                # Sum Request values
                ccx_req = sum(sum(v.values()) for k, v in ccx_ext.items() if 'Request' in k and isinstance(v, dict))
                die_req = sum(sum(v.values()) for k, v in die_ext.items() if 'Request' in k and isinstance(v, dict))

                queue_names.append(name)
                ccx_requests.append(ccx_req)
                die_requests.append(die_req)

        if queue_names:
            x = np.arange(len(queue_names))
            ax5.bar(x - width/2, np.array(ccx_requests)/1e6, width, label='CCX', color='steelblue')
            ax5.bar(x + width/2, np.array(die_requests)/1e6, width, label='DIE', color='coral')
            ax5.set_xlabel('Queue Type')
            ax5.set_ylabel('Requests (Millions)')
            ax5.set_title('DF Queue - Total Requests')
            ax5.set_xticks(x)
            ax5.set_xticklabels(queue_names, rotation=45)
            ax5.legend()
            ax5.grid(axis='y', alpha=0.3)

    # Subplot 6: Summary text
    ax6 = fig.add_subplot(2, 3, 6)
    ax6.axis('off')

    summary_text = "COMPARISON SUMMARY\n" + "="*35 + "\n\n"
    summary_text += "Data Sources:\n"
    summary_text += f"  CCX: results/data/liuxiu/ccx/\n"
    summary_text += f"  DIE: results/data/liuxiu/die/\n\n"
    summary_text += "Files Compared:\n"
    summary_text += f"  • cm_data, di_data, iom_data\n"
    summary_text += f"  • ccm_to_mem_lat (4 files)\n"
    summary_text += f"  • df_data_stream (7 files)\n"
    summary_text += f"  • df_queue (3 files)\n"
    summary_text += f"  • df_detail_lat (3 files)\n\n"
    summary_text += "Legend:\n"
    summary_text += "  Blue = CCX data\n"
    summary_text += "  Orange = DIE data\n"

    ax6.text(0.1, 0.9, summary_text, transform=ax6.transAxes,
             fontsize=11, verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'full_comparison_dashboard.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: full_comparison_dashboard.png")


def main():
    """Main function."""

    ccx_base = "results/data/liuxiu/ccx"
    die_base = "results/data/liuxiu/die"
    output_base = "results/visualizations/ccx_vs_die_comparison"

    print("="*70)
    print("CCX vs DIE Full Data Comparison")
    print("="*70)

    # 1. Compare df_data_stream
    print("\n1. Comparing df_data_stream files...")
    compare_df_data_stream(
        os.path.join(ccx_base, 'df_data_stream'),
        os.path.join(die_base, 'df_data_stream'),
        os.path.join(output_base, 'df_data_stream')
    )

    # 2. Compare df_queue
    print("\n2. Comparing df_queue files...")
    compare_df_queue(
        os.path.join(ccx_base, 'df_queue'),
        os.path.join(die_base, 'df_queue'),
        os.path.join(output_base, 'df_queue')
    )

    # 3. Compare df_detail_lat
    print("\n3. Comparing df_detail_lat files...")
    compare_df_detail_lat(
        os.path.join(ccx_base, 'df_detail_lat'),
        os.path.join(die_base, 'df_detail_lat'),
        os.path.join(output_base, 'df_detail_lat')
    )

    # 4. Create summary dashboard
    print("\n4. Creating full comparison dashboard...")
    create_summary_dashboard(ccx_base, die_base, output_base)

    print("\n" + "="*70)
    print(f"All comparisons saved to: {output_base}")
    print("="*70)


if __name__ == "__main__":
    main()
