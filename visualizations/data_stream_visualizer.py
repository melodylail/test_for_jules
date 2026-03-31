import json
import matplotlib.pyplot as plt
import numpy as np
import os
import argparse
from visualizations.visualization_utils import parse_value

def plot_data_stream_data(data_chunk, title_prefix, output_dir):
    transaction_types = list(data_chunk.keys())

    fig, axes = plt.subplots(len(transaction_types), 1, figsize=(18, 10 * len(transaction_types)))
    if len(transaction_types) == 1:
        axes = [axes]
    fig.suptitle(f'{title_prefix}', fontsize=18)

    for ax, trans_type in zip(axes, transaction_types):
        sub_data = data_chunk[trans_type]
        labels = sorted(list(sub_data.keys()))
        x = np.arange(len(labels))

        values = [parse_value(sub_data.get(label, '0')) for label in labels]

        ax.bar(x, values, label=trans_type)
        ax.set_title(f'{trans_type} Transactions')
        ax.set_ylabel('Count')
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=90, ha='center')
        ax.legend()
        ax.grid(axis='y', linestyle='--', alpha=0.7)

    plt.tight_layout(rect=[0, 0.03, 1, 0.96])
    output_path = os.path.join(output_dir, f'{title_prefix}.png')
    try:
        plt.savefig(output_path)
        print(f"Visualization saved to {output_path}")
    except Exception as e:
        print(f"Error saving plot: {e}")
    plt.close()

def visualize_data_stream_data(json_path, output_dir):
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading or parsing {json_path}: {e}")
        return

    base_filename = os.path.splitext(os.path.basename(json_path))[0]
    for i, data_chunk in enumerate(data):
        plot_data_stream_data(data_chunk, f'{base_filename}_{i}', output_dir)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Visualize data stream files.')
    parser.add_argument('json_path', help='The path to the JSON file to parse.')
    parser.add_argument('output_dir', help='The directory to save the plots.')
    args = parser.parse_args()

    visualize_data_stream_data(args.json_path, args.output_dir)
