#!/usr/bin/env python3
"""
Visualization script for CCM to Memory Latency JSON data from data/liuxiu/die
"""

import json
import os
import glob
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path


def parse_value(value_str):
    """
    Parse values with suffixes like '16 G', '117 M', etc.
    Returns the numeric value.
    """
    if isinstance(value_str, (int, float)):
        return float(value_str)

    value_str = str(value_str).strip()
    if value_str == "0" or value_str == "":
        return 0.0

    # Handle suffixes
    multipliers = {
        'K': 1e3,
        'M': 1e6,
        'G': 1e9,
        'T': 1e12,
    }

    parts = value_str.split()
    if len(parts) == 2:
        number, suffix = parts
        return float(number) * multipliers.get(suffix, 1)
    else:
        try:
            return float(value_str)
        except:
            return 0.0


def load_json_files(directory_path):
    """
    Load all JSON files from the specified directory.
    """
    json_files = glob.glob(os.path.join(directory_path, "*_parsed.json"))

    all_data = []
    for json_file in sorted(json_files):
        ccm_name = Path(json_file).stem.replace("_parsed", "")

        with open(json_file, 'r') as f:
            data = json.load(f)

        for entry in data:
            entry['CCM'] = ccm_name
            # Parse the numeric fields based on actual column names
            keys_to_parse = [key for key in entry.keys() if key not in ['Category', 'CCM']]
            for key in keys_to_parse:
                value = entry[key]
                entry[f'{key}_numeric'] = parse_value(value)
            all_data.append(entry)

    return pd.DataFrame(all_data)


def create_visualizations(df, output_dir="results/visualizations/liuxiu_die_ccm_to_mem_lat"):
    """
    Create various visualizations for the latency data.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Set up the plotting style
    plt.style.use('seaborn-v0_8-darkgrid')

    # Find the numeric columns
    numeric_cols = [col for col in df.columns if col.endswith('_numeric')]

    if len(numeric_cols) == 0:
        print("No numeric columns found in data")
        return

    # Filter out entries with zero values for clearer visualization
    df_nonzero = df.copy()

    # Get unique categories (DIE0, DIE1, etc.)
    categories = df['Category'].unique()
    ccms = df['CCM'].unique()

    print(f"Found {len(categories)} categories and {len(ccms)} CCMs")
    print(f"Categories: {categories}")
    print(f"CCMs: {ccms}")

    # 1. Create heatmap for average latency (if exists)
    latency_cols = [col for col in df.columns if 'latency' in col.lower() and 'numeric' in col]

    if latency_cols:
        for lat_col in latency_cols:
            original_col = lat_col.replace('_numeric', '')

            fig, ax = plt.subplots(figsize=(12, 8))

            # Create pivot table
            try:
                pivot_data = df.pivot(index='Category', columns='CCM', values=lat_col)

                im = ax.imshow(pivot_data.values, cmap='YlOrRd', aspect='auto')

                ax.set_xticks(np.arange(len(pivot_data.columns)))
                ax.set_yticks(np.arange(len(pivot_data.index)))
                ax.set_xticklabels(pivot_data.columns, rotation=45, ha='right')
                ax.set_yticklabels(pivot_data.index)

                # Add colorbar
                cbar = plt.colorbar(im, ax=ax)
                cbar.set_label(original_col, rotation=270, labelpad=20)

                # Add values in cells
                for i in range(len(pivot_data.index)):
                    for j in range(len(pivot_data.columns)):
                        value = pivot_data.values[i, j]
                        if not np.isnan(value) and value > 0:
                            text = ax.text(j, i, f'{value:.0f}',
                                         ha="center", va="center", color="black", fontsize=8)

                plt.title(f'{original_col} - CCM to DIE Heatmap', fontsize=14, fontweight='bold')
                plt.xlabel('CCM Source', fontsize=12)
                plt.ylabel('Destination DIE', fontsize=12)
                plt.tight_layout()

                safe_name = original_col.replace('/', '_').replace(' ', '_')
                plt.savefig(os.path.join(output_dir, f'{safe_name}_heatmap.png'), dpi=300, bbox_inches='tight')
                print(f"Saved: {os.path.join(output_dir, f'{safe_name}_heatmap.png')}")
                plt.close()
            except Exception as e:
                print(f"Could not create pivot for {lat_col}: {e}")

    # 2. Bar charts for request/cycle counts
    request_cols = [col for col in numeric_cols if 'request' in col.lower() or 'cycle' in col.lower()]

    for req_col in request_cols:
        original_col = req_col.replace('_numeric', '')

        # Filter non-zero data
        df_filtered = df[df[req_col] > 0]

        if len(df_filtered) > 0:
            fig, ax = plt.subplots(figsize=(12, 6))

            # Group by CCM and Category
            df_grouped = df_filtered.groupby(['CCM', 'Category'])[req_col].sum().reset_index()

            x = np.arange(len(df_grouped))
            colors = plt.cm.Set3(np.linspace(0, 1, len(ccms)))

            bars = ax.bar(x, df_grouped[req_col],
                         color=[colors[list(ccms).index(ccm)] for ccm in df_grouped['CCM']])

            ax.set_xlabel('CCM to DIE Path', fontsize=12)
            ax.set_ylabel(original_col, fontsize=12)
            ax.set_title(f'{original_col} by CCM to DIE Path', fontsize=14, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels([f"{row['CCM']}\n→{row['Category']}" for _, row in df_grouped.iterrows()],
                              rotation=45, ha='right', fontsize=9)
            ax.grid(axis='y', alpha=0.3)

            # Add legend
            handles = [plt.Rectangle((0,0),1,1, color=colors[i]) for i in range(len(ccms))]
            ax.legend(handles, ccms, title='CCM', loc='upper right')

            plt.tight_layout()
            safe_name = original_col.replace('/', '_').replace(' ', '_')
            plt.savefig(os.path.join(output_dir, f'{safe_name}_bar.png'), dpi=300, bbox_inches='tight')
            print(f"Saved: {os.path.join(output_dir, f'{safe_name}_bar.png')}")
            plt.close()

    # 3. Summary Statistics Table
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    print("\nAll Data:")
    print(df.to_string())

    print("\n" + "="*80)
    print(f"Total visualizations saved to: {output_dir}")
    print("="*80)


def main():
    """
    Main function to run the visualization.
    """
    data_dir = "results/data/liuxiu/die/ccm_to_mem_lat"

    if not os.path.exists(data_dir):
        print(f"Error: Directory {data_dir} does not exist")
        return

    print(f"Loading JSON files from: {data_dir}")
    df = load_json_files(data_dir)

    if len(df) == 0:
        print("No data loaded!")
        return

    print(f"Loaded {len(df)} data entries from {len(df['CCM'].unique())} CCM files")

    print("\nCreating visualizations...")
    create_visualizations(df)

    print("\nVisualization complete!")


if __name__ == "__main__":
    main()
