#!/usr/bin/env python3
"""
Compare df_queue data (ccm_queue, cs_queue, iom_queue) across CCX, DIE, and
SOCKET hierarchy levels.

For each queue file and queue type, generates:
  - Per-metric grouped bar charts comparing CCX vs DIE vs SOCKET
  - A dashboard per queue type with all its L2 metrics
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
OUTPUT_DIR = "results/visualizations/df_queue_ccx_die_socket_comparison"

QUEUE_FILES = ["ccm_queue_data", "cs_queue_data", "iom_queue_data"]


def parse_value(value_str):
    """Parse values with K/M/G suffixes and percentages."""
    if isinstance(value_str, (int, float)):
        return float(value_str)

    value_str = str(value_str).strip()
    if not value_str or value_str == "0":
        return 0.0

    # Handle percentages
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

    # Handle "N suffix" format (e.g., "765 K")
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


def is_percentage_metric(metric_name, sample_values):
    """Check if a metric contains percentage values."""
    for v in sample_values:
        if isinstance(v, str) and '%' in v:
            return True
    return False


def load_queue_data(queue_file):
    """Load a queue data file from all three datasets."""
    all_data = {}
    for ds in DATASETS:
        filepath = Path(DATA_DIR) / ds / "df_queue" / f"{queue_file}_parsed.json"
        if not filepath.exists():
            print(f"  Warning: {filepath} not found, skipping {ds}")
            continue
        with open(filepath) as f:
            all_data[ds] = json.load(f)
    return all_data


def flatten_sections(data):
    """Flatten multi-section data into a dict keyed by (queue_type, metric_name).

    Returns:
        composite_labels: list of str like "DIE0_CCM0", "DIE0_CCM1", ...
        metrics: dict of (queue_type, metric_name) -> list of values
        metric_is_pct: dict of (queue_type, metric_name) -> bool
    """
    sections = data.get("sections", [])
    composite_labels = []
    metrics = {}
    metric_is_pct = {}

    for sec in sections:
        die_labels = sec["die_labels"]
        ccm_labels = sec["ccm_labels"]
        n_per_die = len(ccm_labels) // len(die_labels)

        # Build composite labels for this section
        for idx, ccm_label in enumerate(ccm_labels):
            die_idx = idx // n_per_die
            die_name = die_labels[die_idx]
            composite_labels.append(f"{die_name}_{ccm_label}")

        # Extract metrics from queue types
        for qt in sec["queue_types"]:
            qt_name = qt["name"]
            for l2 in qt["level2_metrics"]:
                l2_name = l2["name"]

                # L2 direct values
                if l2.get("values"):
                    key = (qt_name, l2_name)
                    if key not in metrics:
                        metrics[key] = []
                        metric_is_pct[key] = is_percentage_metric(l2_name, l2["values"])
                    metrics[key].extend(l2["values"])

                # L3 metrics (OCCUPANCY buckets, Kill Rate sub-metrics, etc.)
                for l3 in l2.get("level3_metrics", []):
                    if l3.get("values"):
                        key = (qt_name, f"{l2_name}/{l3['name']}")
                        if key not in metrics:
                            metrics[key] = []
                            metric_is_pct[key] = is_percentage_metric(l3["name"], l3["values"])
                        metrics[key].extend(l3["values"])

    return composite_labels, metrics, metric_is_pct


def create_individual_chart(composite_labels, ds_values, metric_key, is_pct, output_dir, queue_file):
    """Create a grouped bar chart for a single metric."""
    qt_name, metric_name = metric_key
    n_labels = len(composite_labels)

    fig_width = max(14, n_labels * 0.6)
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

        # Add value labels only if few enough bars
        if n_labels <= 12:
            for bar, val in zip(bars, values):
                if val > 0:
                    if is_pct:
                        label = f"{val:.1f}%"
                    else:
                        label = fmt(val)
                    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                            label, ha='center', va='bottom', fontsize=6,
                            rotation=45)

    unit_label = " (%)" if is_pct else ""
    ax.set_xlabel('Component', fontsize=10)
    ax.set_ylabel(f"{metric_name}{unit_label}", fontsize=10)
    ax.set_title(f'{queue_file}: {qt_name} / {metric_name} — CCX vs DIE vs SOCKET', fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(composite_labels, rotation=90, ha='center', fontsize=6)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    safe_name = f"{metric_name}".replace(' ', '_').replace('/', '_')
    outpath = Path(output_dir) / f"{queue_file}_{qt_name}_{safe_name}_comparison.png"
    fig.savefig(outpath, dpi=150)
    plt.close(fig)
    return outpath


def create_queue_type_dashboard(composite_labels, qt_name, qt_metrics, ds_all_values,
                                metric_is_pct, output_dir, queue_file):
    """Create a dashboard for all metrics of one queue type."""
    n_metrics = len(qt_metrics)
    if n_metrics == 0:
        return None

    ncols = min(4, n_metrics)
    nrows = math.ceil(n_metrics / ncols)
    fig_width = max(20, len(composite_labels) * 0.4 * ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(fig_width, 5 * nrows))
    if nrows == 1 and ncols == 1:
        axes = np.array([[axes]])
    elif nrows == 1:
        axes = axes.reshape(1, -1)
    elif ncols == 1:
        axes = axes.reshape(-1, 1)

    x = np.arange(len(composite_labels))

    for idx, metric_name in enumerate(qt_metrics):
        row, col = idx // ncols, idx % ncols
        ax = axes[row][col]
        key = (qt_name, metric_name)
        is_pct = metric_is_pct.get(key, False)

        n_datasets = len([ds for ds in DATASETS if ds in ds_all_values and key in ds_all_values[ds]])
        bar_width = 0.8 / max(n_datasets, 1)
        offsets = np.linspace(-(n_datasets - 1) * bar_width / 2,
                              (n_datasets - 1) * bar_width / 2,
                              max(n_datasets, 1))

        ds_idx = 0
        for ds in DATASETS:
            if ds not in ds_all_values or key not in ds_all_values[ds]:
                continue
            values = ds_all_values[ds][key]
            ax.bar(x + offsets[ds_idx], values, bar_width,
                   label=DATASET_LABELS[ds],
                   color=DATASET_COLORS[ds], alpha=0.85)
            ds_idx += 1

        ax.set_title(metric_name, fontsize=9, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(composite_labels, rotation=90, ha='center', fontsize=4)
        ax.grid(axis='y', alpha=0.3)
        ax.tick_params(axis='y', labelsize=6)

        if is_pct:
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
        else:
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: fmt(v)))

    # Hide unused subplots
    for idx in range(n_metrics, nrows * ncols):
        row, col = idx // ncols, idx % ncols
        axes[row][col].set_visible(False)

    handles, labels = axes[0][0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', ncol=3,
               fontsize=11, bbox_to_anchor=(0.5, 0.99))

    fig.suptitle(f'{queue_file}: {qt_name} — CCX vs DIE vs SOCKET',
                 fontsize=14, fontweight='bold', y=1.01)
    plt.tight_layout(rect=[0, 0, 1, 0.97])

    outpath = Path(output_dir) / f"{queue_file}_{qt_name}_dashboard.png"
    fig.savefig(outpath, dpi=120, bbox_inches='tight')
    plt.close(fig)
    return outpath


def process_queue_file(queue_file):
    """Process one queue file type across all datasets."""
    print(f"\n{'='*60}")
    print(f"Processing {queue_file}...")
    print(f"{'='*60}")

    all_data = load_queue_data(queue_file)
    if not all_data:
        print(f"  No data loaded for {queue_file}")
        return

    # Flatten all datasets
    ds_composite_labels = {}
    ds_metrics = {}  # ds -> {(qt, metric_name): [values]}
    ds_metric_is_pct = {}

    for ds in DATASETS:
        if ds not in all_data:
            continue
        labels, metrics, is_pct = flatten_sections(all_data[ds])
        ds_composite_labels[ds] = labels
        ds_metrics[ds] = metrics
        ds_metric_is_pct[ds] = is_pct

    # Use the first dataset's labels as reference
    ref_ds = next(ds for ds in DATASETS if ds in ds_composite_labels)
    composite_labels = ds_composite_labels[ref_ds]
    ref_metrics = ds_metrics[ref_ds]
    ref_is_pct = ds_metric_is_pct[ref_ds]

    print(f"  Labels: {len(composite_labels)} components")
    print(f"  Datasets loaded: {[DATASET_LABELS[ds] for ds in DATASETS if ds in all_data]}")

    # Group metrics by queue type
    qt_to_metrics = {}
    for (qt_name, metric_name) in sorted(ref_metrics.keys()):
        qt_to_metrics.setdefault(qt_name, []).append(metric_name)

    # Prepare parsed values per dataset: ds -> {(qt, metric): [float_values]}
    ds_parsed = {}
    for ds in DATASETS:
        if ds not in ds_metrics:
            continue
        ds_parsed[ds] = {}
        for key, raw_values in ds_metrics[ds].items():
            ds_parsed[ds][key] = [parse_value(v) for v in raw_values]

    sub_dir = Path(OUTPUT_DIR) / queue_file
    os.makedirs(sub_dir, exist_ok=True)
    chart_count = 0

    for qt_name, metric_names in sorted(qt_to_metrics.items()):
        print(f"\n  Queue type: {qt_name} ({len(metric_names)} metrics)")

        # Individual charts
        for metric_name in metric_names:
            key = (qt_name, metric_name)
            is_pct = ref_is_pct.get(key, False)

            ds_values = {}
            for ds in DATASETS:
                if ds in ds_parsed and key in ds_parsed[ds]:
                    ds_values[ds] = ds_parsed[ds][key]

            outpath = create_individual_chart(
                composite_labels, ds_values, key, is_pct, sub_dir, queue_file)
            chart_count += 1

        # Dashboard for this queue type
        dashboard_path = create_queue_type_dashboard(
            composite_labels, qt_name, metric_names, ds_parsed,
            ref_is_pct, sub_dir, queue_file)
        if dashboard_path:
            chart_count += 1

    print(f"\n  Total charts for {queue_file}: {chart_count}")
    print(f"  Saved to: {sub_dir}/")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for queue_file in QUEUE_FILES:
        process_queue_file(queue_file)

    print(f"\n{'='*60}")
    print(f"Done! All charts saved to {OUTPUT_DIR}/")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
