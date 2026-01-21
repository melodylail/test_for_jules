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

    headers = [
        "DIE",
        "total-latency-cycles",
        "total-requests",
        "avg-cacheable-latency-ns"
    ]

    parsed_data = []
    for line in data_lines:
        # Split the line into parts based on whitespace
        parts = re.split(r'\s{2,}', line.strip())

        row = {}
        # Assign parts to headers
        for i, header in enumerate(headers):
            if i < len(parts):
                row[header] = parts[i]
            else:
                row[header] = "" # Assign empty string if no more parts

        parsed_data.append(row)

    return parsed_data

def main():
    parser = argparse.ArgumentParser(description='Parse a memory latency file.')
    parser.add_argument('filepath', help='The path to the file to parse.')
    args = parser.parse_args()

    try:
        data = parse_mem_lat(args.filepath)
        if data:
            print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"Error parsing file: {e}", file=sys.stderr)

if __name__ == '__main__':
    main()
