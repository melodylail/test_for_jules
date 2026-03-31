#!/usr/bin/env python3
"""
Compare cm_data across CCX, DIE, and SOCKET hierarchy levels.
Generates per-column grouped bar charts and a summary dashboard.
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
OUTPUT_DIR = "results/visualizations/cm_data_ccx_die_socket_comparison"
DATA_COLUMNS = ["CS0_RD", "CS1_RD", "CS2_RD", "CS3_RD",
                "CS0_WR", "CS1_WR", "CS2_WR", "CS3_WR",
                "TOTAL_BW"]


def parse_value(value_str):
    """Parse values with K/M/G suffixes and units like MB/s, GB/s."""
    if isinstance(value_str, (int, float)):
        return float(value_str)

    value_str = str(value_str).strip()
    if not value_str or value_str == "0":
        return 0.0

    # Remove units like B/s, KB/s, MB/s, GB/s
    value_str = value_str.replace('B/s', '').strip()

    multipliers = {'K': 1e3, 'M': 1e6, 'G': 1e9, 'T': 1e12}

    for suffix, mult in multipliers.items():
        if value_str.endswith(suffix):
            try:
                return float(value_str[:-1].strip()) * mult
            except ValueError:
                pass

    # Handle "N suffix" format (e.g., "1.5 M")
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


def load_data():
    """Load cm_data_parsed.json for each dataset."""
    data = {}
    for ds in DATASETS:
        filepath = Path(DATA_DIR) / ds / "cm_data_parsed.json"
        if not filepath.exists():
            print(f"Warning: {filepath} not found, skipping {ds}")
            continue
        with open(filepath) as f:
            rows = json.load(f)
        data[ds] = {row["Category"]: row for row in rows}
    return data


def get_categories(data):
    """Get the ordered list of categories from the first available dataset."""
    for ds in DATASETS:
        if ds in data:
            filepath = Path(DATA_DIR) / ds / "cm_data_parsed.json"
            with open(filepath) as f:
                rows = json.load(f)
            return [row["Category"] for row in rows]
    return []


def create_individual_chart(data, categories, column, output_dir):
    """Create a grouped bar chart for a single data column."""
    fig, ax = plt.subplots(figsize=(14, 7))

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
                        label, ha='center', va='bottom', fontsize=7,
                        rotation=45)

    ax.set_xlabel('Category', fontsize=12)
    ax.set_ylabel(column, fontsize=12)
    ax.set_title(f'cm_data: {column} — CCX vs DIE vs SOCKET', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, rotation=45, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    outpath = Path(output_dir) / f"cm_data_{column}_comparison.png"
    fig.savefig(outpath, dpi=150)
    plt.close(fig)
    print(f"  Saved {outpath}")


def create_dashboard(data, categories, output_dir):
    """Create a 3x3 dashboard with all 9 columns."""
    fig, axes = plt.subplots(3, 3, figsize=(22, 16))
    axes = axes.flatten()

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

        ax.set_title(column, fontsize=11, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(categories, rotation=45, ha='right', fontsize=7)
        ax.grid(axis='y', alpha=0.3)
        ax.tick_params(axis='y', labelsize=7)

        # Format y-axis with K/M/G
        ax.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda v, _: fmt(v))
        )

    # Add shared legend
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', ncol=3,
               fontsize=12, bbox_to_anchor=(0.5, 0.98))

    fig.suptitle('cm_data Comparison: CCX vs DIE vs SOCKET',
                 fontsize=16, fontweight='bold', y=1.0)
    plt.tight_layout(rect=[0, 0, 1, 0.96])

    outpath = Path(output_dir) / "cm_data_comparison_dashboard.png"
    fig.savefig(outpath, dpi=150)
    plt.close(fig)
    print(f"  Saved {outpath}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Loading cm_data from CCX, DIE, and SOCKET...")
    data = load_data()
    if not data:
        print("Error: No data loaded.")
        return

    categories = get_categories(data)
    print(f"  Categories: {categories}")
    print(f"  Datasets loaded: {[DATASET_LABELS[ds] for ds in DATASETS if ds in data]}")

    print("\nGenerating per-column charts...")
    for column in DATA_COLUMNS:
        create_individual_chart(data, categories, column, OUTPUT_DIR)

    print("\nGenerating summary dashboard...")
    create_dashboard(data, categories, OUTPUT_DIR)

    print(f"\nDone! All charts saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
