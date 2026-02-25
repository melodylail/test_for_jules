#!/usr/bin/env python3
"""
Compare ccm0-3todie2_lat_data across CCX, DIE, and SOCKET hierarchy levels.
For each of the 4 CCM sources (ccm0-ccm3), generates per-column grouped bar
charts and a summary dashboard.
"""

import json
import os
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Configuration
DATA_DIR = "results/data/liuxiu"
DATASETS = ["ccx", "die", "socket"]
DATASET_COLORS = {"ccx": "#1f77b4", "die": "#ff7f0e", "socket": "#2ca02c"}
DATASET_LABELS = {"ccx": "CCX", "die": "DIE", "socket": "SOCKET"}
OUTPUT_DIR = "results/visualizations/ccm_to_mem_lat_ccx_die_socket_comparison"
CCM_SOURCES = ["ccm0", "ccm1", "ccm2", "ccm3"]
DATA_COLUMNS = ["total-latency-cycles", "total-requests", "avg-cacheable-latency-ns"]


def parse_value(value_str):
    """Parse values with K/M/G suffixes."""
    if isinstance(value_str, (int, float)):
        return float(value_str)

    value_str = str(value_str).strip()
    if not value_str or value_str == "0":
        return 0.0

    multipliers = {'K': 1e3, 'M': 1e6, 'G': 1e9, 'T': 1e12}

    for suffix, mult in multipliers.items():
        if value_str.endswith(suffix):
            try:
                return float(value_str[:-1].strip()) * mult
            except ValueError:
                pass

    # Handle "N suffix" format (e.g., "16 G")
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
    elif val >= 1e9:
        return f"{val/1e9:.1f}G{unit}"
    elif val >= 1e6:
        return f"{val/1e6:.1f}M{unit}"
    elif val >= 1e3:
        return f"{val/1e3:.1f}K{unit}"
    else:
        return f"{val:.0f}{unit}"


def load_data(ccm_source):
    """Load ccmNtodie2_lat_data_parsed.json for each dataset."""
    data = {}
    filename = f"{ccm_source}todie2_lat_data_parsed.json"
    for ds in DATASETS:
        filepath = Path(DATA_DIR) / ds / "ccm_to_mem_lat" / filename
        if not filepath.exists():
            print(f"Warning: {filepath} not found, skipping {ds}")
            continue
        with open(filepath) as f:
            rows = json.load(f)
        data[ds] = {row["DIE"]: row for row in rows}
    return data


def get_categories(data, ccm_source):
    """Get the ordered list of DIE categories from the first available dataset."""
    filename = f"{ccm_source}todie2_lat_data_parsed.json"
    for ds in DATASETS:
        if ds in data:
            filepath = Path(DATA_DIR) / ds / "ccm_to_mem_lat" / filename
            with open(filepath) as f:
                rows = json.load(f)
            return [row["DIE"] for row in rows]
    return []


def create_individual_chart(data, categories, column, ccm_source, output_dir):
    """Create a grouped bar chart for a single data column."""
    fig, ax = plt.subplots(figsize=(12, 7))

    x = np.arange(len(categories))
    n_datasets = len([ds for ds in DATASETS if ds in data])
    bar_width = 0.25
    offsets = np.linspace(-(n_datasets - 1) * bar_width / 2,
                          (n_datasets - 1) * bar_width / 2,
                          n_datasets)

    for i, ds in enumerate(DATASETS):
        if ds not in data:
            continue
        values = []
        for cat in categories:
            row = data[ds].get(cat, {})
            raw = row.get(column, "0")
            values.append(parse_value(raw))

        bars = ax.bar(x + offsets[i], values, bar_width,
                      label=DATASET_LABELS[ds],
                      color=DATASET_COLORS[ds], alpha=0.85)

        for bar, val in zip(bars, values):
            if val > 0:
                label = fmt(val)
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                        label, ha='center', va='bottom', fontsize=8,
                        rotation=45)

    col_safe = column.replace('-', '_')
    ax.set_xlabel('DIE', fontsize=12)
    ax.set_ylabel(column, fontsize=12)
    ax.set_title(f'{ccm_source}todie2_lat: {column} — CCX vs DIE vs SOCKET', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, rotation=45, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    outpath = Path(output_dir) / f"{ccm_source}todie2_lat_{col_safe}_comparison.png"
    fig.savefig(outpath, dpi=150)
    plt.close(fig)
    print(f"  Saved {outpath}")


def create_dashboard(data, categories, ccm_source, output_dir):
    """Create a 1x3 dashboard with all 3 columns for one CCM source."""
    fig, axes = plt.subplots(1, 3, figsize=(22, 7))

    x = np.arange(len(categories))
    n_datasets = len([ds for ds in DATASETS if ds in data])
    bar_width = 0.25
    offsets = np.linspace(-(n_datasets - 1) * bar_width / 2,
                          (n_datasets - 1) * bar_width / 2,
                          n_datasets)

    for col_idx, column in enumerate(DATA_COLUMNS):
        ax = axes[col_idx]

        for i, ds in enumerate(DATASETS):
            if ds not in data:
                continue
            values = []
            for cat in categories:
                row = data[ds].get(cat, {})
                raw = row.get(column, "0")
                values.append(parse_value(raw))

            ax.bar(x + offsets[i], values, bar_width,
                   label=DATASET_LABELS[ds],
                   color=DATASET_COLORS[ds], alpha=0.85)

        ax.set_title(column, fontsize=10, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(categories, rotation=45, ha='right', fontsize=8)
        ax.grid(axis='y', alpha=0.3)
        ax.tick_params(axis='y', labelsize=8)

        ax.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda v, _: fmt(v))
        )

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', ncol=3,
               fontsize=12, bbox_to_anchor=(0.5, 0.98))

    fig.suptitle(f'{ccm_source}todie2_lat Comparison: CCX vs DIE vs SOCKET',
                 fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout(rect=[0, 0, 1, 0.93])

    outpath = Path(output_dir) / f"{ccm_source}todie2_lat_comparison_dashboard.png"
    fig.savefig(outpath, dpi=150)
    plt.close(fig)
    print(f"  Saved {outpath}")


def create_combined_dashboard(all_data, all_categories, output_dir):
    """Create a 4x3 combined dashboard with all CCM sources and all columns."""
    fig, axes = plt.subplots(4, 3, figsize=(24, 22))

    for row_idx, ccm_source in enumerate(CCM_SOURCES):
        data = all_data[ccm_source]
        categories = all_categories[ccm_source]

        x = np.arange(len(categories))
        n_datasets = len([ds for ds in DATASETS if ds in data])
        bar_width = 0.25
        offsets = np.linspace(-(n_datasets - 1) * bar_width / 2,
                              (n_datasets - 1) * bar_width / 2,
                              n_datasets)

        for col_idx, column in enumerate(DATA_COLUMNS):
            ax = axes[row_idx][col_idx]

            for i, ds in enumerate(DATASETS):
                if ds not in data:
                    continue
                values = []
                for cat in categories:
                    row = data[ds].get(cat, {})
                    raw = row.get(column, "0")
                    values.append(parse_value(raw))

                ax.bar(x + offsets[i], values, bar_width,
                       label=DATASET_LABELS[ds],
                       color=DATASET_COLORS[ds], alpha=0.85)

            title = f"{ccm_source}: {column}" if col_idx == 0 or row_idx == 0 else column
            if row_idx == 0:
                ax.set_title(column, fontsize=10, fontweight='bold')
            if col_idx == 0:
                ax.set_ylabel(ccm_source.upper(), fontsize=11, fontweight='bold')

            ax.set_xticks(x)
            ax.set_xticklabels(categories, rotation=45, ha='right', fontsize=6)
            ax.grid(axis='y', alpha=0.3)
            ax.tick_params(axis='y', labelsize=6)

            ax.yaxis.set_major_formatter(
                plt.FuncFormatter(lambda v, _: fmt(v))
            )

    handles, labels = axes[0][0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', ncol=3,
               fontsize=12, bbox_to_anchor=(0.5, 0.98))

    fig.suptitle('CCM-to-Memory Latency Comparison: CCX vs DIE vs SOCKET',
                 fontsize=16, fontweight='bold', y=1.0)
    plt.tight_layout(rect=[0, 0, 1, 0.96])

    outpath = Path(output_dir) / "ccm_to_mem_lat_combined_dashboard.png"
    fig.savefig(outpath, dpi=150)
    plt.close(fig)
    print(f"  Saved {outpath}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_data = {}
    all_categories = {}

    for ccm_source in CCM_SOURCES:
        print(f"\nProcessing {ccm_source}todie2_lat_data...")
        data = load_data(ccm_source)
        if not data:
            print(f"  Error: No data loaded for {ccm_source}.")
            continue

        categories = get_categories(data, ccm_source)
        print(f"  Categories: {categories}")
        print(f"  Datasets loaded: {[DATASET_LABELS[ds] for ds in DATASETS if ds in data]}")

        all_data[ccm_source] = data
        all_categories[ccm_source] = categories

        print("  Generating per-column charts...")
        for column in DATA_COLUMNS:
            create_individual_chart(data, categories, column, ccm_source, OUTPUT_DIR)

        print("  Generating per-source dashboard...")
        create_dashboard(data, categories, ccm_source, OUTPUT_DIR)

    if all_data:
        print("\nGenerating combined 4x3 dashboard...")
        create_combined_dashboard(all_data, all_categories, OUTPUT_DIR)

    print(f"\nDone! All charts saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
