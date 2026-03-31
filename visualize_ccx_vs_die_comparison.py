#!/usr/bin/env python3
"""
Comparison Visualization Script for CCX vs DIE data
Compares JSON results from results/data/liuxiu/ccx and results/data/liuxiu/die
"""

import json
import os
import glob
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path


def parse_value(value_str):
    """Parse values with suffixes like '16 G', '117 M', 'B/s', 'KB/s', etc."""
    if isinstance(value_str, (int, float)):
        return float(value_str)

    value_str = str(value_str).strip()
    if value_str == "0" or value_str == "":
        return 0.0

    # Remove units like B/s, KB/s, MB/s, GB/s
    for unit in ['GB/s', 'MB/s', 'KB/s', 'B/s']:
        if unit in value_str:
            value_str = value_str.replace(unit, '').strip()
            # Handle multipliers for bandwidth
            if unit == 'GB/s':
                mult = 1e9
            elif unit == 'MB/s':
                mult = 1e6
            elif unit == 'KB/s':
                mult = 1e3
            else:
                mult = 1
            try:
                return float(value_str) * mult
            except:
                pass

    # Handle suffixes K, M, G, T
    multipliers = {'K': 1e3, 'M': 1e6, 'G': 1e9, 'T': 1e12}

    for suffix, mult in multipliers.items():
        if value_str.endswith(suffix):
            try:
                return float(value_str[:-1].strip()) * mult
            except:
                pass

    # Handle "N suffix" format (e.g., "16 G")
    parts = value_str.split()
    if len(parts) == 2:
        try:
            number = float(parts[0])
            suffix = parts[1]
            return number * multipliers.get(suffix, 1)
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


def load_json_file(filepath):
    """Load a JSON file and return its contents."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            # Handle files that might have extra text before JSON
            # Find the first '[' or '{'
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


def compare_simple_data(ccx_file, die_file, output_dir, filename):
    """Compare simple tabular data files (cm_data, di_data, iom_data)."""

    ccx_data = load_json_file(ccx_file)
    die_data = load_json_file(die_file)

    if not ccx_data or not die_data:
        print(f"  Could not load data for {filename}")
        return

    ccx_df = pd.DataFrame(ccx_data)
    die_df = pd.DataFrame(die_data)

    # Find common columns (excluding Category)
    ccx_cols = set(ccx_df.columns) - {'Category'}
    die_cols = set(die_df.columns) - {'Category'}
    common_cols = ccx_cols & die_cols

    if not common_cols:
        print(f"  No common columns found for {filename}")
        return

    os.makedirs(output_dir, exist_ok=True)

    # Parse numeric values
    for col in common_cols:
        ccx_df[f'{col}_numeric'] = ccx_df[col].apply(parse_value)
        die_df[f'{col}_numeric'] = die_df[col].apply(parse_value)

    # Find common categories
    common_categories = set(ccx_df['Category']) & set(die_df['Category'])
    ccx_df_filtered = ccx_df[ccx_df['Category'].isin(common_categories)].copy()
    die_df_filtered = die_df[die_df['Category'].isin(common_categories)].copy()

    # Sort by category for consistent ordering
    ccx_df_filtered = ccx_df_filtered.sort_values('Category').reset_index(drop=True)
    die_df_filtered = die_df_filtered.sort_values('Category').reset_index(drop=True)

    categories = ccx_df_filtered['Category'].tolist()

    # Create comparison bar charts for each numeric column
    for col in sorted(common_cols):
        numeric_col = f'{col}_numeric'

        ccx_values = ccx_df_filtered[numeric_col].values
        die_values = die_df_filtered[numeric_col].values

        # Skip if all zeros
        if np.sum(ccx_values) == 0 and np.sum(die_values) == 0:
            continue

        fig, ax = plt.subplots(figsize=(14, 7))

        x = np.arange(len(categories))
        width = 0.35

        bars1 = ax.bar(x - width/2, ccx_values, width, label='CCX', color='steelblue', alpha=0.8)
        bars2 = ax.bar(x + width/2, die_values, width, label='DIE', color='coral', alpha=0.8)

        ax.set_xlabel('Category', fontsize=12)
        ax.set_ylabel(col, fontsize=12)
        ax.set_title(f'{filename} - {col}\nCCX vs DIE Comparison', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(categories, rotation=45, ha='right')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)

        # Add value labels on bars
        def format_value(v):
            if v >= 1e9:
                return f'{v/1e9:.1f}G'
            elif v >= 1e6:
                return f'{v/1e6:.1f}M'
            elif v >= 1e3:
                return f'{v/1e3:.1f}K'
            else:
                return f'{v:.0f}'

        for bar in bars1:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       format_value(height), ha='center', va='bottom', fontsize=7, color='steelblue')

        for bar in bars2:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       format_value(height), ha='center', va='bottom', fontsize=7, color='coral')

        plt.tight_layout()
        safe_col = col.replace('/', '_').replace(' ', '_')
        plt.savefig(os.path.join(output_dir, f'{filename}_{safe_col}_comparison.png'), dpi=300, bbox_inches='tight')
        plt.close()
        print(f"    Saved: {filename}_{safe_col}_comparison.png")

    # Create difference heatmap
    fig, axes = plt.subplots(1, 3, figsize=(18, 8))

    # Prepare data for heatmaps
    numeric_cols = [f'{col}_numeric' for col in common_cols]

    ccx_heatmap = ccx_df_filtered[['Category'] + list(numeric_cols)].set_index('Category')
    die_heatmap = die_df_filtered[['Category'] + list(numeric_cols)].set_index('Category')

    # Rename columns
    ccx_heatmap.columns = [col.replace('_numeric', '') for col in ccx_heatmap.columns]
    die_heatmap.columns = [col.replace('_numeric', '') for col in die_heatmap.columns]

    # Calculate difference (die - ccx)
    diff_heatmap = die_heatmap - ccx_heatmap

    # Calculate percentage difference where ccx > 0
    pct_diff = ((die_heatmap - ccx_heatmap) / ccx_heatmap.replace(0, np.nan) * 100).fillna(0)

    # Plot CCX heatmap
    im1 = axes[0].imshow(ccx_heatmap.values, cmap='Blues', aspect='auto')
    axes[0].set_xticks(np.arange(len(ccx_heatmap.columns)))
    axes[0].set_yticks(np.arange(len(ccx_heatmap.index)))
    axes[0].set_xticklabels(ccx_heatmap.columns, rotation=45, ha='right', fontsize=8)
    axes[0].set_yticklabels(ccx_heatmap.index)
    axes[0].set_title('CCX Data', fontsize=12, fontweight='bold')
    plt.colorbar(im1, ax=axes[0], shrink=0.8)

    # Plot DIE heatmap
    im2 = axes[1].imshow(die_heatmap.values, cmap='Oranges', aspect='auto')
    axes[1].set_xticks(np.arange(len(die_heatmap.columns)))
    axes[1].set_yticks(np.arange(len(die_heatmap.index)))
    axes[1].set_xticklabels(die_heatmap.columns, rotation=45, ha='right', fontsize=8)
    axes[1].set_yticklabels(die_heatmap.index)
    axes[1].set_title('DIE Data', fontsize=12, fontweight='bold')
    plt.colorbar(im2, ax=axes[1], shrink=0.8)

    # Plot difference heatmap
    vmax = np.abs(pct_diff.values).max()
    im3 = axes[2].imshow(pct_diff.values, cmap='RdBu_r', aspect='auto', vmin=-vmax, vmax=vmax)
    axes[2].set_xticks(np.arange(len(pct_diff.columns)))
    axes[2].set_yticks(np.arange(len(pct_diff.index)))
    axes[2].set_xticklabels(pct_diff.columns, rotation=45, ha='right', fontsize=8)
    axes[2].set_yticklabels(pct_diff.index)
    axes[2].set_title('% Difference (DIE - CCX)', fontsize=12, fontweight='bold')
    cbar = plt.colorbar(im3, ax=axes[2], shrink=0.8)
    cbar.set_label('% Change', rotation=270, labelpad=15)

    plt.suptitle(f'{filename} - CCX vs DIE Comparison', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'{filename}_heatmap_comparison.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"    Saved: {filename}_heatmap_comparison.png")


def compare_ccm_to_mem_lat(ccx_dir, die_dir, output_dir):
    """Compare CCM to memory latency data between CCX and DIE."""

    os.makedirs(output_dir, exist_ok=True)

    ccx_files = sorted(glob.glob(os.path.join(ccx_dir, "*_parsed.json")))
    die_files = sorted(glob.glob(os.path.join(die_dir, "*_parsed.json")))

    # Load all data
    ccx_all_data = []
    die_all_data = []

    for ccx_file in ccx_files:
        ccm_name = Path(ccx_file).stem.replace("_parsed", "")
        data = load_json_file(ccx_file)
        if data:
            for entry in data:
                entry['CCM'] = ccm_name
                entry['Source'] = 'CCX'
                # Check for different key names (DIE vs Category)
                if 'DIE' in entry:
                    entry['Category'] = entry['DIE']
                ccx_all_data.append(entry)

    for die_file in die_files:
        ccm_name = Path(die_file).stem.replace("_parsed", "")
        data = load_json_file(die_file)
        if data:
            for entry in data:
                entry['CCM'] = ccm_name
                entry['Source'] = 'DIE'
                if 'DIE' in entry:
                    entry['Category'] = entry['DIE']
                die_all_data.append(entry)

    if not ccx_all_data or not die_all_data:
        print("  No CCM to mem lat data found")
        return

    ccx_df = pd.DataFrame(ccx_all_data)
    die_df = pd.DataFrame(die_all_data)

    # Parse numeric values for latency columns
    latency_cols = []
    for col in ccx_df.columns:
        if 'latency' in col.lower() or 'request' in col.lower() or 'cycle' in col.lower():
            latency_cols.append(col)
            ccx_df[f'{col}_numeric'] = ccx_df[col].apply(parse_value)

    for col in die_df.columns:
        if 'latency' in col.lower() or 'request' in col.lower() or 'cycle' in col.lower():
            if col in latency_cols:
                die_df[f'{col}_numeric'] = die_df[col].apply(parse_value)

    # Find common CCMs
    common_ccms = set(ccx_df['CCM'].unique()) & set(die_df['CCM'].unique())

    print(f"  Found {len(common_ccms)} common CCM files to compare")

    # Create comparison visualizations for each CCM
    for ccm in sorted(common_ccms):
        ccx_ccm = ccx_df[ccx_df['CCM'] == ccm].copy()
        die_ccm = die_df[die_df['CCM'] == ccm].copy()

        # Find common categories/DIEs
        common_cats = set(ccx_ccm['Category']) & set(die_ccm['Category'])

        ccx_ccm = ccx_ccm[ccx_ccm['Category'].isin(common_cats)].sort_values('Category')
        die_ccm = die_ccm[die_ccm['Category'].isin(common_cats)].sort_values('Category')

        categories = ccx_ccm['Category'].tolist()

        # Create comparison for latency columns
        for col in latency_cols:
            numeric_col = f'{col}_numeric'

            if numeric_col not in ccx_ccm.columns or numeric_col not in die_ccm.columns:
                continue

            ccx_values = ccx_ccm[numeric_col].values
            die_values = die_ccm[numeric_col].values

            # Skip if all zeros
            if np.sum(ccx_values) == 0 and np.sum(die_values) == 0:
                continue

            fig, ax = plt.subplots(figsize=(12, 6))

            x = np.arange(len(categories))
            width = 0.35

            bars1 = ax.bar(x - width/2, ccx_values, width, label='CCX', color='steelblue', alpha=0.8)
            bars2 = ax.bar(x + width/2, die_values, width, label='DIE', color='coral', alpha=0.8)

            ax.set_xlabel('Target DIE', fontsize=12)
            ax.set_ylabel(col, fontsize=12)
            ax.set_title(f'{ccm} - {col}\nCCX vs DIE Comparison', fontsize=14, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels(categories, rotation=45, ha='right')
            ax.legend()
            ax.grid(axis='y', alpha=0.3)

            plt.tight_layout()
            safe_col = col.replace('/', '_').replace(' ', '_').replace('-', '_')
            safe_ccm = ccm.replace('/', '_')
            plt.savefig(os.path.join(output_dir, f'{safe_ccm}_{safe_col}_comparison.png'), dpi=300, bbox_inches='tight')
            plt.close()
            print(f"    Saved: {safe_ccm}_{safe_col}_comparison.png")

    # Create summary heatmap comparing avg latency across all CCMs
    fig, axes = plt.subplots(1, 2, figsize=(14, 8))

    # Get avg-cacheable-latency-ns or similar column for CCX
    ccx_lat_col = None
    for col in ccx_df.columns:
        if 'avg' in col.lower() and 'latency' in col.lower():
            ccx_lat_col = col
            break

    # Get corresponding column for DIE (may have different name)
    die_lat_col = None
    for col in die_df.columns:
        if 'avg' in col.lower() and 'latency' in col.lower():
            die_lat_col = col
            break
        elif 'latency' in col.lower() and 'ns' in col.lower():
            die_lat_col = col
            break

    # Parse die latency column if found
    if die_lat_col and f'{die_lat_col}_numeric' not in die_df.columns:
        die_df[f'{die_lat_col}_numeric'] = die_df[die_lat_col].apply(parse_value)

    if ccx_lat_col and f'{ccx_lat_col}_numeric' in ccx_df.columns and die_lat_col and f'{die_lat_col}_numeric' in die_df.columns:
        # Create pivot tables
        ccx_pivot = ccx_df.pivot_table(
            index='Category',
            columns='CCM',
            values=f'{ccx_lat_col}_numeric',
            aggfunc='mean'
        )
        die_pivot = die_df.pivot_table(
            index='Category',
            columns='CCM',
            values=f'{die_lat_col}_numeric',
            aggfunc='mean'
        )

        # Plot side by side
        vmax = max(ccx_pivot.values.max(), die_pivot.values.max())

        im1 = axes[0].imshow(ccx_pivot.values, cmap='YlOrRd', aspect='auto', vmin=0, vmax=vmax)
        axes[0].set_xticks(np.arange(len(ccx_pivot.columns)))
        axes[0].set_yticks(np.arange(len(ccx_pivot.index)))
        axes[0].set_xticklabels(ccx_pivot.columns, rotation=45, ha='right', fontsize=8)
        axes[0].set_yticklabels(ccx_pivot.index)
        axes[0].set_title('CCX - Avg Latency (ns)', fontsize=12, fontweight='bold')
        plt.colorbar(im1, ax=axes[0], shrink=0.8)

        # Add values
        for i in range(len(ccx_pivot.index)):
            for j in range(len(ccx_pivot.columns)):
                val = ccx_pivot.values[i, j]
                if not np.isnan(val) and val > 0:
                    axes[0].text(j, i, f'{val:.0f}', ha='center', va='center', fontsize=7)

        im2 = axes[1].imshow(die_pivot.values, cmap='YlOrRd', aspect='auto', vmin=0, vmax=vmax)
        axes[1].set_xticks(np.arange(len(die_pivot.columns)))
        axes[1].set_yticks(np.arange(len(die_pivot.index)))
        axes[1].set_xticklabels(die_pivot.columns, rotation=45, ha='right', fontsize=8)
        axes[1].set_yticklabels(die_pivot.index)
        axes[1].set_title('DIE - Avg Latency (ns)', fontsize=12, fontweight='bold')
        plt.colorbar(im2, ax=axes[1], shrink=0.8)

        # Add values
        for i in range(len(die_pivot.index)):
            for j in range(len(die_pivot.columns)):
                val = die_pivot.values[i, j]
                if not np.isnan(val) and val > 0:
                    axes[1].text(j, i, f'{val:.0f}', ha='center', va='center', fontsize=7)

        plt.suptitle('CCM to Memory Latency - CCX vs DIE Comparison', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'ccm_to_mem_lat_summary_comparison.png'), dpi=300, bbox_inches='tight')
        plt.close()
        print(f"    Saved: ccm_to_mem_lat_summary_comparison.png")


def create_overall_summary(ccx_base, die_base, output_dir):
    """Create an overall summary comparing CCX and DIE data."""

    os.makedirs(output_dir, exist_ok=True)

    # Collect total bandwidth data from cm_data
    ccx_cm = load_json_file(os.path.join(ccx_base, 'cm_data_parsed.json'))
    die_cm = load_json_file(os.path.join(die_base, 'cm_data_parsed.json'))

    if ccx_cm and die_cm:
        # Extract total bandwidth for each category
        ccx_bw = {entry['Category']: parse_value(entry.get('TOTAL_BW', '0')) for entry in ccx_cm}
        die_bw = {entry['Category']: parse_value(entry.get('TOTAL_BW', '0')) for entry in die_cm}

        common_cats = sorted(set(ccx_bw.keys()) & set(die_bw.keys()))

        fig, ax = plt.subplots(figsize=(14, 7))

        x = np.arange(len(common_cats))
        width = 0.35

        ccx_vals = [ccx_bw[cat] for cat in common_cats]
        die_vals = [die_bw[cat] for cat in common_cats]

        bars1 = ax.bar(x - width/2, np.array(ccx_vals) / 1e6, width, label='CCX', color='steelblue', alpha=0.8)
        bars2 = ax.bar(x + width/2, np.array(die_vals) / 1e6, width, label='DIE', color='coral', alpha=0.8)

        ax.set_xlabel('Category', fontsize=12)
        ax.set_ylabel('Total Bandwidth (MB/s)', fontsize=12)
        ax.set_title('Core Memory Bandwidth - CCX vs DIE Comparison', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(common_cats, rotation=45, ha='right')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)

        # Add value labels
        for bar in bars1:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.0f}', ha='center', va='bottom', fontsize=8)

        for bar in bars2:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.0f}', ha='center', va='bottom', fontsize=8)

        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'cm_data_bandwidth_summary.png'), dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  Saved: cm_data_bandwidth_summary.png")

    # Create multi-panel comparison figure
    fig = plt.figure(figsize=(16, 12))

    # Add title
    fig.suptitle('CCX vs DIE Data Comparison Summary', fontsize=16, fontweight='bold', y=0.98)

    # Subplot 1: CM Data comparison
    ax1 = fig.add_subplot(2, 2, 1)
    if ccx_cm and die_cm:
        categories = common_cats[:8]  # First 8 categories (DIEs)
        ccx_vals = [ccx_bw.get(cat, 0) / 1e6 for cat in categories]
        die_vals = [die_bw.get(cat, 0) / 1e6 for cat in categories]

        x = np.arange(len(categories))
        width = 0.35

        ax1.bar(x - width/2, ccx_vals, width, label='CCX', color='steelblue', alpha=0.8)
        ax1.bar(x + width/2, die_vals, width, label='DIE', color='coral', alpha=0.8)
        ax1.set_xlabel('DIE')
        ax1.set_ylabel('Bandwidth (MB/s)')
        ax1.set_title('Core Memory - Total Bandwidth by DIE')
        ax1.set_xticks(x)
        ax1.set_xticklabels(categories, rotation=45, ha='right')
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3)

    # Subplot 2: IOM Data comparison
    ccx_iom = load_json_file(os.path.join(ccx_base, 'iom_data_parsed.json'))
    die_iom = load_json_file(os.path.join(die_base, 'iom_data_parsed.json'))

    ax2 = fig.add_subplot(2, 2, 2)
    if ccx_iom and die_iom:
        ccx_iom_bw = {entry['Category']: parse_value(entry.get('TOTAL_BW_MIN', '0')) for entry in ccx_iom}
        die_iom_bw = {entry['Category']: parse_value(entry.get('TOTAL_BW_MIN', '0')) for entry in die_iom}

        common_iom_cats = sorted(set(ccx_iom_bw.keys()) & set(die_iom_bw.keys()))[:8]

        x = np.arange(len(common_iom_cats))
        width = 0.35

        ccx_vals = [ccx_iom_bw.get(cat, 0) for cat in common_iom_cats]
        die_vals = [die_iom_bw.get(cat, 0) for cat in common_iom_cats]

        ax2.bar(x - width/2, ccx_vals, width, label='CCX', color='steelblue', alpha=0.8)
        ax2.bar(x + width/2, die_vals, width, label='DIE', color='coral', alpha=0.8)
        ax2.set_xlabel('DIE')
        ax2.set_ylabel('Bandwidth (B/s)')
        ax2.set_title('IOM - Min Bandwidth by DIE')
        ax2.set_xticks(x)
        ax2.set_xticklabels(common_iom_cats, rotation=45, ha='right')
        ax2.legend()
        ax2.grid(axis='y', alpha=0.3)

    # Subplot 3: DI Data comparison
    ccx_di = load_json_file(os.path.join(ccx_base, 'di_data_parsed.json'))
    die_di = load_json_file(os.path.join(die_base, 'di_data_parsed.json'))

    ax3 = fig.add_subplot(2, 2, 3)
    if ccx_di and die_di:
        # Get IO DIE columns
        io_cols = [col for col in ccx_di[0].keys() if 'IO' in col or 'DIE' in col and col != 'Category']

        if io_cols:
            categories = [entry['Category'] for entry in ccx_di]

            for i, entry in enumerate(ccx_di):
                for col in io_cols:
                    ccx_val = parse_value(entry.get(col, '0'))
                    die_val = parse_value(die_di[i].get(col, '0') if i < len(die_di) else '0')

            # Simple bar for first IO column
            col = io_cols[0]
            ccx_vals = [parse_value(entry.get(col, '0')) / 1e6 for entry in ccx_di]
            die_vals = [parse_value(entry.get(col, '0')) / 1e6 for entry in die_di]

            x = np.arange(len(categories))
            width = 0.35

            ax3.bar(x - width/2, ccx_vals, width, label='CCX', color='steelblue', alpha=0.8)
            ax3.bar(x + width/2, die_vals, width, label='DIE', color='coral', alpha=0.8)
            ax3.set_xlabel('Socket')
            ax3.set_ylabel(f'{col} (MB/s)')
            ax3.set_title(f'DI Data - {col}')
            ax3.set_xticks(x)
            ax3.set_xticklabels(categories)
            ax3.legend()
            ax3.grid(axis='y', alpha=0.3)

    # Subplot 4: Summary statistics
    ax4 = fig.add_subplot(2, 2, 4)
    ax4.axis('off')

    # Calculate summary stats
    summary_text = "SUMMARY STATISTICS\n" + "="*40 + "\n\n"

    if ccx_cm and die_cm:
        ccx_total_bw = sum(parse_value(e.get('TOTAL_BW', '0')) for e in ccx_cm if e['Category'] == 'SYS')
        die_total_bw = sum(parse_value(e.get('TOTAL_BW', '0')) for e in die_cm if e['Category'] == 'SYS')
        diff_bw = ((die_total_bw - ccx_total_bw) / ccx_total_bw * 100) if ccx_total_bw > 0 else 0

        summary_text += f"Core Memory (SYS):\n"
        summary_text += f"  CCX Total BW: {ccx_total_bw/1e9:.2f} GB/s\n"
        summary_text += f"  DIE Total BW: {die_total_bw/1e9:.2f} GB/s\n"
        summary_text += f"  Difference: {diff_bw:+.1f}%\n\n"

    summary_text += "Data Sources:\n"
    summary_text += f"  CCX: results/data/liuxiu/ccx/\n"
    summary_text += f"  DIE: results/data/liuxiu/die/\n"

    ax4.text(0.1, 0.9, summary_text, transform=ax4.transAxes,
             fontsize=11, verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'overall_summary_comparison.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: overall_summary_comparison.png")


def main():
    """Main function to run all comparisons."""

    ccx_base = "results/data/liuxiu/ccx"
    die_base = "results/data/liuxiu/die"
    output_base = "results/visualizations/ccx_vs_die_comparison"

    print("="*60)
    print("CCX vs DIE Data Comparison")
    print("="*60)

    # 1. Compare simple data files
    simple_files = ['cm_data', 'di_data', 'iom_data']

    print("\n1. Comparing simple data files...")
    for filename in simple_files:
        print(f"\n  Processing {filename}...")
        ccx_file = os.path.join(ccx_base, f'{filename}_parsed.json')
        die_file = os.path.join(die_base, f'{filename}_parsed.json')

        if os.path.exists(ccx_file) and os.path.exists(die_file):
            compare_simple_data(ccx_file, die_file,
                              os.path.join(output_base, 'simple_data'),
                              filename)
        else:
            print(f"    Skipping {filename} - file not found")

    # 2. Compare CCM to memory latency
    print("\n2. Comparing CCM to memory latency data...")
    ccx_lat_dir = os.path.join(ccx_base, 'ccm_to_mem_lat')
    die_lat_dir = os.path.join(die_base, 'ccm_to_mem_lat')

    if os.path.exists(ccx_lat_dir) and os.path.exists(die_lat_dir):
        compare_ccm_to_mem_lat(ccx_lat_dir, die_lat_dir,
                              os.path.join(output_base, 'ccm_to_mem_lat'))
    else:
        print("  CCM to mem lat directories not found")

    # 3. Create overall summary
    print("\n3. Creating overall summary...")
    create_overall_summary(ccx_base, die_base, output_base)

    print("\n" + "="*60)
    print(f"All comparisons saved to: {output_base}")
    print("="*60)


if __name__ == "__main__":
    main()
