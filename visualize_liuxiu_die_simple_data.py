#!/usr/bin/env python3
"""
Visualization script for simple tabular data (cm_data, di_data, iom_data)
"""

import json
import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path


def parse_value(value_str):
    """Parse values with suffixes like '16 GB/s', '117 MB/s', etc."""
    if isinstance(value_str, (int, float)):
        return float(value_str)

    value_str = str(value_str).strip()
    if value_str == "0" or value_str == "":
        return 0.0

    # Remove units like B/s, KB/s, MB/s, GB/s
    value_str = value_str.replace('B/s', '').strip()

    # Handle suffixes
    multipliers = {
        'K': 1e3,
        'M': 1e6,
        'G': 1e9,
        'T': 1e12,
    }

    # Check for suffix at the end
    for suffix, mult in multipliers.items():
        if value_str.endswith(suffix):
            try:
                number = value_str[:-1].strip()
                return float(number) * mult
            except:
                pass

    # Try direct conversion
    try:
        return float(value_str.replace(',', ''))
    except:
        return 0.0


def load_json_file(filepath):
    """Load a JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def visualize_simple_data(filepath, output_dir):
    """Visualize simple tabular data files."""

    filename = Path(filepath).stem.replace('_parsed', '')
    data = load_json_file(filepath)

    if not data:
        print(f"No data in {filename}")
        return

    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Parse numeric columns
    for col in df.columns:
        if col != 'Category':
            df[f'{col}_numeric'] = df[col].apply(parse_value)

    numeric_cols = [col for col in df.columns if col.endswith('_numeric')]

    print(f"\nProcessing {filename}:")
    print(f"  Categories: {list(df['Category'])}")
    print(f"  Numeric columns: {len(numeric_cols)}")

    # Create visualizations
    os.makedirs(output_dir, exist_ok=True)

    # 1. Heatmap for all metrics
    if numeric_cols:
        fig, ax = plt.subplots(figsize=(14, 8))

        # Prepare data for heatmap
        heatmap_data = df[['Category'] + numeric_cols].set_index('Category')
        # Rename columns to remove _numeric suffix
        heatmap_data.columns = [col.replace('_numeric', '') for col in heatmap_data.columns]

        im = ax.imshow(heatmap_data.values, cmap='YlOrRd', aspect='auto')

        ax.set_xticks(np.arange(len(heatmap_data.columns)))
        ax.set_yticks(np.arange(len(heatmap_data.index)))
        ax.set_xticklabels(heatmap_data.columns, rotation=45, ha='right')
        ax.set_yticklabels(heatmap_data.index)

        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Value', rotation=270, labelpad=20)

        # Add values in cells
        for i in range(len(heatmap_data.index)):
            for j in range(len(heatmap_data.columns)):
                value = heatmap_data.values[i, j]
                if not np.isnan(value):
                    # Format based on magnitude
                    if value >= 1e9:
                        text_val = f'{value/1e9:.1f}G'
                    elif value >= 1e6:
                        text_val = f'{value/1e6:.1f}M'
                    elif value >= 1e3:
                        text_val = f'{value/1e3:.1f}K'
                    else:
                        text_val = f'{value:.0f}'

                    ax.text(j, i, text_val,
                           ha="center", va="center", color="black", fontsize=7)

        plt.title(f'{filename} - All Metrics Heatmap', fontsize=14, fontweight='bold')
        plt.xlabel('Metric', fontsize=12)
        plt.ylabel('Category', fontsize=12)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'{filename}_heatmap.png'), dpi=300, bbox_inches='tight')
        print(f"  Saved: {filename}_heatmap.png")
        plt.close()

    # 2. Bar chart for each metric
    for num_col in numeric_cols:
        original_col = num_col.replace('_numeric', '')

        fig, ax = plt.subplots(figsize=(12, 6))

        categories = df['Category']
        values = df[num_col]

        bars = ax.bar(categories, values, color='steelblue')

        ax.set_xlabel('Category', fontsize=12)
        ax.set_ylabel(original_col, fontsize=12)
        ax.set_title(f'{filename} - {original_col}', fontsize=14, fontweight='bold')
        plt.xticks(rotation=45, ha='right')
        ax.grid(axis='y', alpha=0.3)

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                if height >= 1e9:
                    label = f'{height/1e9:.1f}G'
                elif height >= 1e6:
                    label = f'{height/1e6:.1f}M'
                elif height >= 1e3:
                    label = f'{height/1e3:.1f}K'
                else:
                    label = f'{height:.0f}'

                ax.text(bar.get_x() + bar.get_width()/2., height,
                       label, ha='center', va='bottom', fontsize=8)

        plt.tight_layout()
        safe_col = original_col.replace('/', '_').replace(' ', '_')
        plt.savefig(os.path.join(output_dir, f'{filename}_{safe_col}_bar.png'), dpi=300, bbox_inches='tight')
        print(f"  Saved: {filename}_{safe_col}_bar.png")
        plt.close()


def main():
    """Main function."""
    base_dir = "results/data/liuxiu/die"
    output_base = "results/visualizations/liuxiu_die_simple"

    # Files to visualize
    files = [
        'cm_data_parsed.json',
        'di_data_parsed.json',
        'iom_data_parsed.json'
    ]

    for filename in files:
        filepath = os.path.join(base_dir, filename)

        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            continue

        output_dir = os.path.join(output_base, Path(filename).stem.replace('_parsed', ''))
        visualize_simple_data(filepath, output_dir)

    print(f"\n{'='*80}")
    print(f"All visualizations saved to: {output_base}")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
