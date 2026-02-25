#!/usr/bin/env python3
"""
Compare df_detail_lat data across CCX, DIE, and SOCKET hierarchy levels.

Handles ccm2todie2_latency, cs2todie2_latency, and iom2todie2_latency files.
For each file and transaction type, generates per-metric grouped bar charts
and dashboards comparing CCX vs DIE vs SOCKET.
"""

import json
import os
import math
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Configuration
DATA_DIR = "results/data/liuxiu"
DATASETS = ["ccx", "die", "socket"]
DATASET_COLORS = {"ccx": "#1f77b4", "die": "#ff7f0e", "socket": "#2ca02c"}
DATASET_LABELS = {"ccx": "CCX", "die": "DIE", "socket": "SOCKET"}
OUTPUT_DIR = "results/visualizations/df_detail_lat_ccx_die_socket_comparison"

LAT_FILES = [
    "ccm2todie2_latency_data",
    "cs2todie2_latency_data",
    "iom2todie2_latency_data",
]


def parse_value(value_str):
    """Parse values with K/M/G suffixes and percentages."""
    if isinstance(value_str, (int, float)):
        return float(value_str)

    value_str = str(value_str).strip()
    if not value_str or value_str == "0":
        return 0.0

    if '%' in value_str:
        try:
            return float(value_str.replace('%', '').strip())
        except ValueError:
            return 0.0

    multipliers = {'K': 1e3, 'M': 1e6, 'G': 1e9, 'T': 1e12}

    for suffix, mult in multipliers.items():
        if value_str.endswith(suffix):
            try:
                return float(value_str[:-1].strip()) * mult
            except ValueError:
                pass

    parts = value_str.split()
    if len(parts) == 2:
        try:
            number = float(parts[0])
            suffix = parts[1]
            return number * multipliers.get(suffix, 1)
        except ValueError:
            pass

    try:
        return float(value_str.replace(',', ''))
    except ValueError:
        return 0.0


def fmt(val, unit=""):
    """Format large numbers with K/M/G suffix."""
    if val == 0:
        return "0"
    elif abs(val) >= 1e9:
        return f"{val/1e9:.1f}G{unit}"
    elif abs(val) >= 1e6:
        return f"{val/1e6:.1f}M{unit}"
    elif abs(val) >= 1e3:
        return f"{val/1e3:.1f}K{unit}"
    else:
        return f"{val:.0f}{unit}"


def is_percentage(sample_values):
    """Check if values contain percentages."""
    for v in sample_values:
        if isinstance(v, str) and '%' in v:
            return True
    return False


def flatten_latency_data(data):
    """Flatten df_detail_lat sections into composite labels and metrics.

    Returns:
        composite_labels: list of str
        metrics: dict of (txn_type, metric_path) -> list of raw values
        metric_is_pct: dict of same keys -> bool
    """
    sections = data.get("sections", [])
    composite_labels = []
    metrics = {}
    metric_is_pct = {}

    for sec in sections:
        die_labels = sec["die_labels"]
        ccm_labels = sec["ccm_labels"]
        n_per_die = len(ccm_labels) // len(die_labels) if len(die_labels) > 0 else len(ccm_labels)

        # Build composite labels with section context
        target = sec.get("target_info", "")
        sec_prefix = f"{target}_" if target else ""

        for idx, ccm_label in enumerate(ccm_labels):
            die_idx = idx // n_per_die
            die_name = die_labels[die_idx]
            composite_labels.append(f"{sec_prefix}{die_name}_{ccm_label}")

        for tt in sec["transaction_types"]:
            tt_name = tt["name"]
            # Skip section-marker transaction types (e.g., SOURCE_IO_DIE:...)
            if not tt.get("level2_metrics"):
                continue

            for l2 in tt["level2_metrics"]:
                l2_name = l2["name"]

                # L2 direct values
                if l2.get("values") and any(v != "" for v in l2["values"]):
                    key = (tt_name, l2_name)
                    if key not in metrics:
                        metrics[key] = []
                        metric_is_pct[key] = is_percentage(l2["values"])
                    metrics[key].extend(l2["values"])

                # L3 metrics
                for l3 in l2.get("level3_metrics", []):
                    if l3.get("values"):
                        key = (tt_name, f"{l2_name}/{l3['name']}")
                        if key not in metrics:
                            metrics[key] = []
                            metric_is_pct[key] = is_percentage(l3["values"])
                        metrics[key].extend(l3["values"])

    return composite_labels, metrics, metric_is_pct


def load_latency_data(lat_file):
    """Load a latency data file from all three datasets."""
    all_data = {}
    for ds in DATASETS:
        filepath = Path(DATA_DIR) / ds / "df_detail_lat" / f"{lat_file}_parsed.json"
        if not filepath.exists():
            print(f"  Warning: {filepath} not found, skipping {ds}")
            continue
        with open(filepath) as f:
            all_data[ds] = json.load(f)
    return all_data


def create_individual_chart(composite_labels, ds_values, tt_name, metric_path,
                            is_pct, output_dir, lat_file):
    """Create a grouped bar chart for a single metric."""
    n_labels = len(composite_labels)
    fig_width = max(14, n_labels * 0.5)
    fig, ax = plt.subplots(figsize=(fig_width, 7))

    x = np.arange(n_labels)
    n_datasets = len(ds_values)
    bar_width = 0.8 / max(n_datasets, 1)
    offsets = np.linspace(-(n_datasets - 1) * bar_width / 2,
                          (n_datasets - 1) * bar_width / 2,
                          n_datasets)

    for i, ds in enumerate(DATASETS):
        if ds not in ds_values:
            continue
        values = ds_values[ds]
        bars = ax.bar(x + offsets[i], values, bar_width,
                      label=DATASET_LABELS[ds],
                      color=DATASET_COLORS[ds], alpha=0.85)

        if n_labels <= 16:
            for bar, val in zip(bars, values):
                if val > 0:
                    label = f"{val:.1f}%" if is_pct else fmt(val)
                    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                            label, ha='center', va='bottom', fontsize=5, rotation=45)

    display_name = f"{tt_name} / {metric_path}"
    unit_label = " (%)" if is_pct else ""
    ax.set_xlabel('Component', fontsize=10)
    ax.set_ylabel(f"{metric_path}{unit_label}", fontsize=9)
    ax.set_title(f'{lat_file}: {display_name} — CCX vs DIE vs SOCKET', fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels(composite_labels, rotation=90, ha='center', fontsize=5)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    safe_name = f"{tt_name}_{metric_path}".replace(' ', '_').replace('/', '_').replace(':', '_').replace('(', '').replace(')', '')
    outpath = Path(output_dir) / f"{lat_file}_{safe_name}_comparison.png"
    fig.savefig(outpath, dpi=150)
    plt.close(fig)
    return outpath


def create_txn_dashboard(composite_labels, tt_name, tt_metric_keys, ds_parsed,
                         metric_is_pct, output_dir, lat_file):
    """Create a dashboard for all metrics of one transaction type."""
    n_metrics = len(tt_metric_keys)
    if n_metrics == 0:
        return None

    ncols = min(4, n_metrics)
    nrows = math.ceil(n_metrics / ncols)
    fig_width = max(20, len(composite_labels) * 0.3 * ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(fig_width, 5 * nrows))
    if nrows == 1 and ncols == 1:
        axes = np.array([[axes]])
    elif nrows == 1:
        axes = axes.reshape(1, -1)
    elif ncols == 1:
        axes = axes.reshape(-1, 1)

    x = np.arange(len(composite_labels))

    for idx, key in enumerate(tt_metric_keys):
        row, col = idx // ncols, idx % ncols
        ax = axes[row][col]
        is_pct = metric_is_pct.get(key, False)
        _, metric_path = key

        n_ds = len([ds for ds in DATASETS if ds in ds_parsed and key in ds_parsed[ds]])
        bar_width = 0.8 / max(n_ds, 1)
        offsets = np.linspace(-(n_ds - 1) * bar_width / 2,
                              (n_ds - 1) * bar_width / 2,
                              max(n_ds, 1))

        ds_idx = 0
        for ds in DATASETS:
            if ds not in ds_parsed or key not in ds_parsed[ds]:
                continue
            ax.bar(x + offsets[ds_idx], ds_parsed[ds][key], bar_width,
                   label=DATASET_LABELS[ds],
                   color=DATASET_COLORS[ds], alpha=0.85)
            ds_idx += 1

        ax.set_title(metric_path, fontsize=8, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(composite_labels, rotation=90, ha='center', fontsize=3)
        ax.grid(axis='y', alpha=0.3)
        ax.tick_params(axis='y', labelsize=6)

        if is_pct:
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
        else:
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: fmt(v)))

    for idx in range(n_metrics, nrows * ncols):
        row, col = idx // ncols, idx % ncols
        axes[row][col].set_visible(False)

    handles, labels = axes[0][0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', ncol=3,
               fontsize=11, bbox_to_anchor=(0.5, 0.99))

    fig.suptitle(f'{lat_file}: {tt_name} — CCX vs DIE vs SOCKET',
                 fontsize=13, fontweight='bold', y=1.01)
    plt.tight_layout(rect=[0, 0, 1, 0.97])

    safe_tt = tt_name.replace(' ', '_').replace('/', '_').replace(':', '_')
    outpath = Path(output_dir) / f"{lat_file}_{safe_tt}_dashboard.png"
    fig.savefig(outpath, dpi=120, bbox_inches='tight')
    plt.close(fig)
    return outpath


def process_lat_file(lat_file):
    """Process one latency file across all datasets."""
    print(f"\n{'='*60}")
    print(f"Processing {lat_file}...")
    print(f"{'='*60}")

    all_data = load_latency_data(lat_file)
    if not all_data:
        print(f"  No data loaded for {lat_file}")
        return

    ds_composite_labels = {}
    ds_metrics = {}
    ds_metric_is_pct = {}

    for ds in DATASETS:
        if ds not in all_data:
            continue
        labels, metrics, is_pct = flatten_latency_data(all_data[ds])
        ds_composite_labels[ds] = labels
        ds_metrics[ds] = metrics
        ds_metric_is_pct[ds] = is_pct

    ref_ds = next(ds for ds in DATASETS if ds in ds_composite_labels)
    composite_labels = ds_composite_labels[ref_ds]
    ref_metrics = ds_metrics[ref_ds]
    ref_is_pct = ds_metric_is_pct[ref_ds]

    print(f"  Labels: {len(composite_labels)} components")
    print(f"  Metrics: {len(ref_metrics)} total")
    print(f"  Datasets loaded: {[DATASET_LABELS[ds] for ds in DATASETS if ds in all_data]}")

    # Parse values
    ds_parsed = {}
    for ds in DATASETS:
        if ds not in ds_metrics:
            continue
        ds_parsed[ds] = {}
        for key, raw_values in ds_metrics[ds].items():
            ds_parsed[ds][key] = [parse_value(v) for v in raw_values]

    sub_dir = Path(OUTPUT_DIR) / lat_file
    os.makedirs(sub_dir, exist_ok=True)
    chart_count = 0

    # Group by transaction type
    tt_to_keys = {}
    for key in sorted(ref_metrics.keys()):
        tt_name, _ = key
        tt_to_keys.setdefault(tt_name, []).append(key)

    for tt_name, keys in sorted(tt_to_keys.items()):
        print(f"  Txn: {tt_name} ({len(keys)} metrics)")

        for key in keys:
            tt_n, metric_path = key
            is_pct = ref_is_pct.get(key, False)

            ds_values = {}
            for ds in DATASETS:
                if ds in ds_parsed and key in ds_parsed[ds]:
                    ds_values[ds] = ds_parsed[ds][key]

            create_individual_chart(composite_labels, ds_values, tt_n, metric_path,
                                    is_pct, sub_dir, lat_file)
            chart_count += 1

        # Dashboard per transaction type
        if len(keys) > 1:
            create_txn_dashboard(composite_labels, tt_name, keys, ds_parsed,
                                 ref_is_pct, sub_dir, lat_file)
            chart_count += 1

    print(f"\n  Total charts for {lat_file}: {chart_count}")
    print(f"  Saved to: {sub_dir}/")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for lat_file in LAT_FILES:
        process_lat_file(lat_file)

    print(f"\n{'='*60}")
    print(f"Done! All charts saved to {OUTPUT_DIR}/")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
