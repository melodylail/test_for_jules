#!/usr/bin/env python3
"""
Visualization script for df_data_stream JSON files
"""

import json
import os
import glob
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path


def parse_value(value_str):
    """Parse numeric values with suffixes."""
    if isinstance(value_str, (int, float)):
        return float(value_str)

    value_str = str(value_str).strip()
    if value_str == "0" or value_str == "":
        return 0.0

    # Handle K, M, G suffixes
    multipliers = {'K': 1e3, 'M': 1e6, 'G': 1e9, 'T': 1e12}

    for suffix, mult in multipliers.items():
        if value_str.endswith(suffix):
            try:
                return float(value_str[:-1].strip()) * mult
            except:
                pass

    # Handle percentages
    if '%' in value_str:
        try:
            return float(value_str.replace('%', '').strip())
        except:
            return 0.0

    try:
        return float(value_str.replace(',', ''))
    except:
        return 0.0


def extract_data_from_sections(json_data):
    """Extract structured data from the sections format."""
    if not json_data or 'sections' not in json_data:
        return []

    all_rows = []

    for section in json_data['sections']:
        if 'entries' not in section:
            continue

        die_labels = section.get('die_labels', [])

        for entry in section['entries']:
            fields = entry.get('fields', [])

            if len(fields) > 1:
                # First field is usually the metric name
                metric = fields[0]

                # Check if this looks like a data row (not a header)
                if metric and not metric.startswith('Level') and not metric.startswith('CCM'):
                    row = {'Metric': metric}

                    # Map remaining fields to DIE columns
                    for i, value in enumerate(fields[1:]):
                        if i < len(die_labels):
                            col_name = die_labels[i]
                        else:
                            col_name = f'DIE{i}'

                        row[col_name] = parse_value(value)

                    all_rows.append(row)

    return all_rows


def visualize_data_stream(filepath, output_dir):
    """Visualize a single data stream file."""

    filename = Path(filepath).stem.replace('_parsed', '')

    with open(filepath, 'r') as f:
        json_data = json.load(f)

    rows = extract_data_from_sections(json_data)

    if not rows:
        print(f"No data extracted from {filename}")
        return

    df = pd.DataFrame(rows)

    print(f"\nProcessing {filename}:")
    print(f"  Rows extracted: {len(df)}")
    print(f"  Columns: {list(df.columns)}")

    os.makedirs(output_dir, exist_ok=True)

    # Get numeric columns (all except Metric)
    numeric_cols = [col for col in df.columns if col != 'Metric']

    if not numeric_cols:
        print(f"  No numeric columns found")
        return

    # 1. Create heatmap for all metrics
    fig, ax = plt.subplots(figsize=(14, 10))

    heatmap_data = df.set_index('Metric')[numeric_cols]

    # Filter out rows where all values are 0
    row_sums = heatmap_data.sum(axis=1)
    heatmap_data = heatmap_data[row_sums > 0]

    if len(heatmap_data) == 0:
        print(f"  No non-zero data to visualize")
        plt.close()
        return

    im = ax.imshow(heatmap_data.values, cmap='YlOrRd', aspect='auto')

    ax.set_xticks(np.arange(len(heatmap_data.columns)))
    ax.set_yticks(np.arange(len(heatmap_data.index)))
    ax.set_xticklabels(heatmap_data.columns, rotation=45, ha='right')
    ax.set_yticklabels(heatmap_data.index, fontsize=8)

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Value', rotation=270, labelpad=20)

    # Add values in cells for non-zero values
    for i in range(len(heatmap_data.index)):
        for j in range(len(heatmap_data.columns)):
            value = heatmap_data.values[i, j]
            if not np.isnan(value) and value > 0:
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
                       ha="center", va="center", color="black", fontsize=6)

    plt.title(f'{filename} - Data Stream Heatmap', fontsize=14, fontweight='bold')
    plt.xlabel('Component', fontsize=12)
    plt.ylabel('Metric', fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'{filename}_heatmap.png'), dpi=300, bbox_inches='tight')
    print(f"  Saved: {filename}_heatmap.png")
    plt.close()

    # 2. Bar chart showing total activity per component
    fig, ax = plt.subplots(figsize=(12, 6))

    totals = heatmap_data.sum(axis=0)
    components = totals.index
    values = totals.values

    bars = ax.bar(components, values, color='steelblue')

    ax.set_xlabel('Component', fontsize=12)
    ax.set_ylabel('Total Activity', fontsize=12)
    ax.set_title(f'{filename} - Total Activity by Component', fontsize=14, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    ax.grid(axis='y', alpha=0.3)

    # Add value labels
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
    plt.savefig(os.path.join(output_dir, f'{filename}_total_activity_bar.png'), dpi=300, bbox_inches='tight')
    print(f"  Saved: {filename}_total_activity_bar.png")
    plt.close()


def main():
    """Main function."""
    data_dir = "results/data/liuxiu/die/df_data_stream"
    output_base = "results/visualizations/liuxiu_die_df_data_stream"

    if not os.path.exists(data_dir):
        print(f"Directory not found: {data_dir}")
        return

    json_files = glob.glob(os.path.join(data_dir, "*_parsed.json"))

    if not json_files:
        print(f"No JSON files found in {data_dir}")
        return

    print(f"Found {len(json_files)} files to visualize")

    for filepath in sorted(json_files):
        filename = Path(filepath).stem.replace('_parsed', '')
        output_dir = os.path.join(output_base, filename)
        visualize_data_stream(filepath, output_dir)

    print(f"\n{'='*80}")
    print(f"All visualizations saved to: {output_base}")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
