import argparse
import json
import re

def parse_mem_lat(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    separator_idx = next((i for i, line in enumerate(lines) if '---' in line), -1)
    if separator_idx == -1:
        return []

    data_lines = [l for l in lines[separator_idx + 1:] if l.strip()]
    if not data_lines:
        return []

    # Headers are hardcoded due to the multi-line and complex nature of the original header.
    # This approach is simpler than trying to parse the two-line header.
    headers = [
        "DIE",
        "total-latency-cycles",
        "total-requests",
        "avg-cacheable-latency-ns"
    ]

    parsed_data = []
    for line in data_lines:
        # Split line by multiple spaces
        values = re.split(r'\s{2,}', line.strip())

        row_data = {}
        for i, header in enumerate(headers):
            if i < len(values):
                row_data[header] = values[i]
            else:
                row_data[header] = ""

        parsed_data.append(row_data)

    return parsed_data

def main():
    parser = argparse.ArgumentParser(description='Parse a memory latency file.')
    parser.add_argument('filepath', help='The path to the file to parse.')
    args = parser.parse_args()

    data = parse_mem_lat(args.filepath)
    print(json.dumps(data, indent=2))

if __name__ == '__main__':
    main()
