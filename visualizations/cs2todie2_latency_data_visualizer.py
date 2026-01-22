import json
import matplotlib.pyplot as plt
import numpy as np
import os
from visualizations.visualization_utils import parse_value

def plot_cs2_data(data_chunk, title_prefix, output_dir):
    """Plots metrics from a chunk of the cs2todie2_latency_data."""

    transaction_types = ['RdBlk', 'WrSizedNC', 'Dirty Victims', 'Clean Victims']

    for i, (source_die_key, die_data) in enumerate(data_chunk.items()):
        fig, axes = plt.subplots(len(transaction_types), 1, figsize=(16, 8 * len(transaction_types)))
        fig.suptitle(f'{title_prefix} - {source_die_key}', fontsize=18)

        for ax, trans_type in zip(axes, transaction_types):
            if trans_type in die_data:
                sub_data = die_data[trans_type]

                sdp_data = sub_data.get('Transaction', {}).get('|SDP', {})
                fti_data = sub_data.get('Transaction', {}).get('|FTI', {})

                if not sdp_data and not fti_data:
                    # For Victims, the structure is a bit different
                    fti_data = sub_data.get('Transaction', {}).get('|FTI', {})

                labels = sorted(list(set(sdp_data.keys()) | set(fti_data.keys())))
                x = np.arange(len(labels))
                bar_width = 0.35

                sdp_values = [parse_value(sdp_data.get(label, '0')) for label in labels]
                fti_values = [parse_value(fti_data.get(label, '0')) for label in labels]

                if any(sdp_values):
                    ax.bar(x - bar_width/2, sdp_values, bar_width, label='SDP Transactions')
                if any(fti_values):
                    ax.bar(x + bar_width/2, fti_values, bar_width, label='FTI Transactions')

                ax.set_title(f'{trans_type} Transactions')
                ax.set_ylabel('Count')
                ax.set_xticks(x)
                ax.set_xticklabels(labels, rotation=45, ha='right')
                ax.legend()
                ax.grid(axis='y', linestyle='--', alpha=0.7)

        plt.tight_layout(rect=[0, 0.03, 1, 0.96])
        output_path = os.path.join(output_dir, f'{title_prefix}_part_{i+1}.png')
        try:
            plt.savefig(output_path)
            print(f"Visualization saved to {output_path}")
        except Exception as e:
            print(f"Error saving plot: {e}")
        plt.close()


def visualize_cs2todie2_latency_data(json_path, output_dir):
    """Generates and saves bar charts for cs2todie2_latency_data."""
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading or parsing {json_path}: {e}")
        return

    base_filename = os.path.splitext(os.path.basename(json_path))[0]
    for i, data_chunk in enumerate(data):
        plot_cs2_data(data_chunk, f'{base_filename}_{i}', output_dir)


if __name__ == '__main__':
    visualize_cs2todie2_latency_data('results/cs2todie2_latency_data_parsed.json', 'plots')
