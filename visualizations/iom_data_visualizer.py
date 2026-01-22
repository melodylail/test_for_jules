import json
import matplotlib.pyplot as plt
import numpy as np
from visualizations.visualization_utils import parse_bw_to_kb

def visualize_iom_data(json_path, output_path):
    """Generates and saves a bar chart for iom_data."""
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading or parsing {json_path}: {e}")
        return

    categories = [item['Category'] for item in data]
    min_bw = [parse_bw_to_kb(item.get('TOTAL_BW_MIN', '0')) for item in data]
    max_bw = [parse_bw_to_kb(item.get('TOTAL_BW_MAX', '0')) for item in data]

    # Separate system-level summaries (SKT, SYS) from detailed DIEs
    detail_categories = [cat for cat in categories if cat.startswith('DIE')]
    detail_min_bw = [bw for cat, bw in zip(categories, min_bw) if cat.startswith('DIE')]
    detail_max_bw = [bw for cat, bw in zip(categories, max_bw) if cat.startswith('DIE')]

    summary_categories = [cat for cat in categories if cat.startswith(('SKT', 'SYS'))]
    summary_min_bw = [bw for cat, bw in zip(categories, min_bw) if cat.startswith(('SKT', 'SYS'))]
    summary_max_bw = [bw for cat, bw in zip(categories, max_bw) if cat.startswith(('SKT', 'SYS'))]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 14))
    fig.suptitle('IOM Total Bandwidth (Min/Max) by Category', fontsize=16)

    # Plot for DIEs
    x_detail = np.arange(len(detail_categories))
    bar_width = 0.35
    ax1.bar(x_detail - bar_width/2, detail_min_bw, bar_width, label='Min BW', color='c')
    ax1.bar(x_detail + bar_width/2, detail_max_bw, bar_width, label='Max BW', color='m')
    ax1.set_ylabel('Total Bandwidth (KB/s)')
    ax1.set_title('Detailed Bandwidth per DIE')
    ax1.set_xticks(x_detail)
    ax1.set_xticklabels(detail_categories, rotation=45, ha="right")
    ax1.legend()
    ax1.grid(axis='y', linestyle='--', alpha=0.7)

    # Plot for Sockets and System
    x_summary = np.arange(len(summary_categories))
    ax2.bar(x_summary - bar_width/2, summary_min_bw, bar_width, label='Min BW', color='c')
    ax2.bar(x_summary + bar_width/2, summary_max_bw, bar_width, label='Max BW', color='m')
    ax2.set_ylabel('Total Bandwidth (KB/s)')
    ax2.set_title('Summary Bandwidth for Sockets and System')
    ax2.set_xticks(x_summary)
    ax2.set_xticklabels(summary_categories)
    ax2.legend()
    ax2.grid(axis='y', linestyle='--', alpha=0.7)

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    try:
        plt.savefig(output_path)
        print(f"Visualization saved to {output_path}")
    except Exception as e:
        print(f"Error saving visualization: {e}")

if __name__ == '__main__':
    visualize_iom_data('results/iom_data_parsed.json', 'plots/iom_data_visualization.png')
