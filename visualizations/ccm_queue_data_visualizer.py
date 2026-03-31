import json
import matplotlib.pyplot as plt
import numpy as np
import os
from visualizations.visualization_utils import parse_value

def plot_metrics(data_chunk, output_filename):
    """Plots a set of metrics from a chunk of the CCM queue data."""
    metrics_to_plot = ['Request', 'write', 'PrbRsp', 'Probe', 'Response']

    # Check which metrics are available in this chunk
    available_metrics = []
    first_queue = next(iter(data_chunk.values()), {})
    for metric in metrics_to_plot:
        if metric in first_queue:
            available_metrics.append(metric)

    if not available_metrics:
        print(f"No plottable metrics found in data for {output_filename}")
        return

    num_metrics = len(available_metrics)
    fig, axes = plt.subplots(num_metrics, 1, figsize=(15, 5 * num_metrics))
    if num_metrics == 1:
        axes = [axes] # Make it iterable

    fig.suptitle('CCM Queue Metrics', fontsize=16)

    for ax, metric in zip(axes, available_metrics):
        all_dies = set()
        queue_data = {}

        for queue_type, details in data_chunk.items():
            if metric in details:
                metric_values = details[metric]
                queue_data[queue_type] = {die: parse_value(val) for die, val in metric_values.items()}
                all_dies.update(metric_values.keys())

        sorted_dies = sorted(list(all_dies))
        x = np.arange(len(sorted_dies))

        num_queues = len(queue_data)
        bar_width = 0.8 / num_queues

        for i, (queue_type, values) in enumerate(queue_data.items()):
            y_values = [values.get(die, 0) for die in sorted_dies]
            offset = (i - num_queues / 2 + 0.5) * bar_width
            ax.bar(x + offset, y_values, bar_width, label=queue_type)

        ax.set_ylabel('Count (Log Scale)')
        ax.set_title(f'{metric} Counts')
        ax.set_xticks(x)
        ax.set_xticklabels(sorted_dies, rotation=45, ha="right")
        ax.set_yscale('log')
        ax.legend()
        ax.grid(axis='y', linestyle='--', alpha=0.7)

    plt.tight_layout(rect=[0, 0.03, 1, 0.96])

    try:
        plt.savefig(output_filename)
        print(f"Visualization saved to {output_filename}")
    except Exception as e:
        print(f"Error saving visualization: {e}")
    plt.close()


def visualize_ccm_queue_data(json_path, output_dir):
    """Generates and saves bar charts for ccm_queue_data."""
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading or parsing {json_path}: {e}")
        return

    for i, data_chunk in enumerate(data):
        output_path = os.path.join(output_dir, f'ccm_queue_data_part_{i+1}.png')
        plot_metrics(data_chunk, output_path)


if __name__ == '__main__':
    visualize_ccm_queue_data('results/ccm_queue_data_parsed.json', 'plots')
