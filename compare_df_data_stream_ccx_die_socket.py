#!/usr/bin/env python3
"""
Compare df_data_stream data across CCX, DIE, and SOCKET hierarchy levels.

Handles all 7 stream files (ccm_in, ccm_out_todie2, cs_in, cs_out,
iom_out_todie2, spf_in, spf_out).  For each file, flattens sections into
composite labels and compares every metric across the three datasets.
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
OUTPUT_DIR = "results/visualizations/df_data_stream_ccx_die_socket_comparison"

STREAM_FILES = [
    "ccm_in_data",
    "ccm_out_todie2_data",
    "cs_in_data",
    "cs_out_data",
    "iom_out_todie2_data",
    "spf_in_data",
    "spf_out_data",
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


def flatten_stream_data(data):
    """Flatten df_data_stream sections into composite labels and metrics.

    Returns:
        composite_labels: list of str like "DIE0_CCM0"
        metrics: dict of (l1_name, metric_path) -> list of raw values
            metric_path is "" for L1 direct values, or "L2_name" / "L2_name/L3_name"
        metric_is_pct: dict of same keys -> bool
    """
    sections = data.get("sections", [])
    composite_labels = []
    metrics = {}
    metric_is_pct = {}

    for sec in sections:
        die_labels = sec["die_labels"]
        cs_labels = sec["cs_labels"]
        n_per_die = len(cs_labels) // len(die_labels) if len(die_labels) > 0 else len(cs_labels)

        for idx, cs_label in enumerate(cs_labels):
            die_idx = idx // n_per_die
            die_name = die_labels[die_idx]
            composite_labels.append(f"{die_name}_{cs_label}")

        for l1 in sec["level1_categories"]:
            l1_name = l1["name"]

            # L1 direct values
            if l1.get("values"):
                key = (l1_name, "")
                if key not in metrics:
                    metrics[key] = []
                    metric_is_pct[key] = is_percentage(l1["values"])
                metrics[key].extend(l1["values"])

            # L2 metrics
            for l2 in l1.get("level2_metrics", []):
                if l2.get("values"):
                    key = (l1_name, l2["name"])
                    if key not in metrics:
                        metrics[key] = []
                        metric_is_pct[key] = is_percentage(l2["values"])
                    metrics[key].extend(l2["values"])

                # L3 metrics
                for l3 in l2.get("level3_metrics", []):
                    if l3.get("values"):
                        key = (l1_name, f"{l2['name']}/{l3['name']}")
                        if key not in metrics:
                            metrics[key] = []
                            metric_is_pct[key] = is_percentage(l3["values"])
                        metrics[key].extend(l3["values"])

    return composite_labels, metrics, metric_is_pct


def load_stream_data(stream_file):
    """Load a stream data file from all three datasets."""
    all_data = {}
    for ds in DATASETS:
        filepath = Path(DATA_DIR) / ds / "df_data_stream" / f"{stream_file}_parsed.json"
        if not filepath.exists():
            print(f"  Warning: {filepath} not found, skipping {ds}")
            continue
        with open(filepath) as f:
            all_data[ds] = json.load(f)
    return all_data


def create_individual_chart(composite_labels, ds_values, l1_name, metric_path,
                            is_pct, output_dir, stream_file):
    """Create a grouped bar chart for a single metric."""
    n_labels = len(composite_labels)
    fig_width = max(14, n_labels * 0.55)
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

        if n_labels <= 12:
            for bar, val in zip(bars, values):
                if val > 0:
                    label = f"{val:.1f}%" if is_pct else fmt(val)
                    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                            label, ha='center', va='bottom', fontsize=6, rotation=45)

    display_name = f"{l1_name} / {metric_path}" if metric_path else l1_name
    unit_label = " (%)" if is_pct else ""
    ax.set_xlabel('Component', fontsize=10)
    ax.set_ylabel(f"{display_name}{unit_label}", fontsize=9)
    ax.set_title(f'{stream_file}: {display_name} — CCX vs DIE vs SOCKET', fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels(composite_labels, rotation=90, ha='center', fontsize=6)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    safe_name = f"{l1_name}_{metric_path}".replace(' ', '_').replace('/', '_').replace(':', '_')
    safe_name = safe_name.rstrip('_')
    outpath = Path(output_dir) / f"{stream_file}_{safe_name}_comparison.png"
    fig.savefig(outpath, dpi=150)
    plt.close(fig)
    return outpath


def create_l1_dashboard(composite_labels, l1_name, l1_metric_keys, ds_parsed,
                        metric_is_pct, output_dir, stream_file):
    """Create a dashboard for all metrics under one L1 category."""
    n_metrics = len(l1_metric_keys)
    if n_metrics == 0:
        return None

    ncols = min(4, n_metrics)
    nrows = math.ceil(n_metrics / ncols)
    fig_width = max(20, len(composite_labels) * 0.35 * ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(fig_width, 5 * nrows))
    if nrows == 1 and ncols == 1:
        axes = np.array([[axes]])
    elif nrows == 1:
        axes = axes.reshape(1, -1)
    elif ncols == 1:
        axes = axes.reshape(-1, 1)

    x = np.arange(len(composite_labels))

    for idx, key in enumerate(l1_metric_keys):
        row, col = idx // ncols, idx % ncols
        ax = axes[row][col]
        is_pct = metric_is_pct.get(key, False)
        _, metric_path = key
        title = metric_path if metric_path else l1_name

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

        ax.set_title(title, fontsize=8, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(composite_labels, rotation=90, ha='center', fontsize=4)
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

    fig.suptitle(f'{stream_file}: {l1_name} — CCX vs DIE vs SOCKET',
                 fontsize=13, fontweight='bold', y=1.01)
    plt.tight_layout(rect=[0, 0, 1, 0.97])

    safe_l1 = l1_name.replace(' ', '_').replace('/', '_').replace(':', '_')
    outpath = Path(output_dir) / f"{stream_file}_{safe_l1}_dashboard.png"
    fig.savefig(outpath, dpi=120, bbox_inches='tight')
    plt.close(fig)
    return outpath


def process_stream_file(stream_file):
    """Process one stream file across all datasets."""
    print(f"\n{'='*60}")
    print(f"Processing {stream_file}...")
    print(f"{'='*60}")

    all_data = load_stream_data(stream_file)
    if not all_data:
        print(f"  No data loaded for {stream_file}")
        return

    # Flatten all datasets
    ds_composite_labels = {}
    ds_metrics = {}
    ds_metric_is_pct = {}

    for ds in DATASETS:
        if ds not in all_data:
            continue
        labels, metrics, is_pct = flatten_stream_data(all_data[ds])
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

    # Parse values for all datasets
    ds_parsed = {}
    for ds in DATASETS:
        if ds not in ds_metrics:
            continue
        ds_parsed[ds] = {}
        for key, raw_values in ds_metrics[ds].items():
            ds_parsed[ds][key] = [parse_value(v) for v in raw_values]

    sub_dir = Path(OUTPUT_DIR) / stream_file
    os.makedirs(sub_dir, exist_ok=True)
    chart_count = 0

    # Group metrics by L1 name
    l1_to_keys = {}
    for key in sorted(ref_metrics.keys()):
        l1_name, _ = key
        l1_to_keys.setdefault(l1_name, []).append(key)

    for l1_name, keys in sorted(l1_to_keys.items()):
        print(f"  L1: {l1_name} ({len(keys)} metrics)")

        # Individual charts
        for key in keys:
            l1_n, metric_path = key
            is_pct = ref_is_pct.get(key, False)

            ds_values = {}
            for ds in DATASETS:
                if ds in ds_parsed and key in ds_parsed[ds]:
                    ds_values[ds] = ds_parsed[ds][key]

            create_individual_chart(composite_labels, ds_values, l1_n, metric_path,
                                    is_pct, sub_dir, stream_file)
            chart_count += 1

        # Dashboard for this L1 category
        if len(keys) > 1:
            create_l1_dashboard(composite_labels, l1_name, keys, ds_parsed,
                                ref_is_pct, sub_dir, stream_file)
            chart_count += 1

    print(f"\n  Total charts for {stream_file}: {chart_count}")
    print(f"  Saved to: {sub_dir}/")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for stream_file in STREAM_FILES:
        process_stream_file(stream_file)

    print(f"\n{'='*60}")
    print(f"Done! All charts saved to {OUTPUT_DIR}/")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
