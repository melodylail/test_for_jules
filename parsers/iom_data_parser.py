import argparse
import json
import re

def parse_iom_data(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Find the separator line
    separator_index = next((i for i, line in enumerate(lines) if '---' in line), -1)
    if separator_index == -1:
        return []

    # The header is on the line just before the separator
    header_line = lines[separator_index - 1].strip()
    data_lines = lines[separator_index + 1:]

    # Extract headers
    headers = re.split(r'\s{2,}', header_line)
    headers = [h for h in headers if h.strip() and '->' not in h]

    parsed_data = []
    for line in data_lines:
        line = line.strip()
        if not line:
            continue

        # Split the line into the category and the rest of the values
        parts = re.split(r'\s{2,}', line, 1)
        category = parts[0]
        values_str = parts[1] if len(parts) > 1 else ""

        # Use regex to find all data points, including those with units
        values = re.findall(r'(\d+\s*[KMGT]?B/s|\d+)', values_str)

        row_data = {"Category": category}

        for i, header in enumerate(headers):
            if i < len(values):
                row_data[header] = values[i]
            else:
                row_data[header] = ""

        parsed_data.append(row_data)

    return parsed_data

def main():
    parser = argparse.ArgumentParser(description='Parse the iom_data file.')
    parser.add_argument('filepath', help='The path to the iom_data file to parse.')
    args = parser.parse_args()

    data = parse_iom_data(args.filepath)
    print(json.dumps(data, indent=2))

if __name__ == '__main__':
    main()
