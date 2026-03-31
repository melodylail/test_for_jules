import json
import matplotlib.pyplot as plt
from visualizations.visualization_utils import parse_bw

def visualize_di_data(json_path, output_path):
    """Generates and saves a bar chart for di_data."""
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading or parsing {json_path}: {e}")
        return

    sockets = [item['Category'] for item in data]
    io_dies = [key for key in data[0] if key != 'Category']

    fig, ax = plt.subplots(figsize=(10, 6))

    bar_width = 0.25
    index = range(len(sockets))

    for i, die in enumerate(io_dies):
        bw_values = [parse_bw(item.get(die, '0')) for item in data]
        bar_positions = [pos + i * bar_width for pos in index]
        ax.bar(bar_positions, bw_values, bar_width, label=die)

    ax.set_xlabel('Socket')
    ax.set_ylabel('Bandwidth (MB/s)')
    ax.set_title('IO DIE Bandwidth per Socket')
    ax.set_xticks([pos + bar_width for pos in index])
    ax.set_xticklabels(sockets)
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    plt.tight_layout()

    try:
        plt.savefig(output_path)
        print(f"Visualization saved to {output_path}")
    except Exception as e:
        print(f"Error saving visualization: {e}")

if __name__ == '__main__':
    visualize_di_data('results/di_data_parsed.json', 'plots/di_data_visualization.png')
