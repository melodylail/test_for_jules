import json
import matplotlib.pyplot as plt
import numpy as np
from visualizations.visualization_utils import parse_bw

def visualize_cm_data(json_path, output_path):
    """Generates and saves a bar chart for cm_data."""
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading or parsing {json_path}: {e}")
        return

    categories = [item['Category'] for item in data]
    total_bw = [parse_bw(item.get('TOTAL_BW', '0')) for item in data]

    # Separate system-level summaries (SKT, SYS) for a clearer plot
    detail_categories = [cat for cat in categories if not cat.startswith(('SKT', 'SYS'))]
    detail_bw = [bw for cat, bw in zip(categories, total_bw) if not cat.startswith(('SKT', 'SYS'))]

    summary_categories = [cat for cat in categories if cat.startswith(('SKT', 'SYS'))]
    summary_bw = [bw for cat, bw in zip(categories, total_bw) if cat.startswith(('SKT', 'SYS'))]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12), sharex=False)
    fig.suptitle('Total Bandwidth by Category', fontsize=16)

    # Plot for DIEs (linear scale)
    ax1.bar(detail_categories, detail_bw, color='skyblue')
    ax1.set_ylabel('Total Bandwidth (MB/s)')
    ax1.set_title('Detailed Bandwidth per DIE')
    ax1.set_xticklabels(detail_categories, rotation=45, ha="right")
    ax1.grid(axis='y', linestyle='--', alpha=0.7)

    # Plot for Sockets and System (log scale is better due to large differences)
    ax2.bar(summary_categories, summary_bw, color='lightgreen')
    ax2.set_ylabel('Total Bandwidth (MB/s) - Log Scale')
    ax2.set_title('Summary Bandwidth for Sockets and System')
    ax2.set_yscale('log') # Use log scale for vastly different values
    ax2.set_xticklabels(summary_categories, rotation=0)
    ax2.grid(axis='y', linestyle='--', alpha=0.7)

    # Add labels on top of bars for summary plot
    for i, v in enumerate(summary_bw):
        ax2.text(i, v * 1.1, f"{v:,.0f}", ha='center', va='bottom')


    plt.tight_layout(rect=[0, 0, 1, 0.96])

    try:
        plt.savefig(output_path)
        print(f"Visualization saved to {output_path}")
    except Exception as e:
        print(f"Error saving visualization: {e}")

if __name__ == '__main__':
    visualize_cm_data('results/cm_data_parsed.json', 'plots/cm_data_visualization.png')
