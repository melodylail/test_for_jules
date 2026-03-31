import argparse
import json
import re

def parse_cm_data(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Find the separator line
    separator_index = next((i for i, line in enumerate(lines) if '---' in line), -1)
    if separator_index == -1:
        return []

    # The header is the line right before the separator
    header_line = lines[separator_index - 1].strip()
    data_lines = lines[separator_index + 1:]

    # Extract headers, splitting by 2 or more spaces
    headers = re.split(r'\s{2,}', header_line)
    # Filter out descriptive parts and empty strings
    headers = [h for h in headers if h and '->' not in h]

    parsed_data = []
    for line in data_lines:
        line = line.strip()
        if not line:
            continue

        # Split values by 2 or more spaces
        values = re.split(r'\s{2,}', line)

        # The first value is the category
        category = values[0]
        data_values = values[1:]

        row_data = {"Category": category}

        # Pair headers with the remaining values
        for i, header in enumerate(headers):
            if i < len(data_values):
                row_data[header] = data_values[i]
            else:
                row_data[header] = ""

        parsed_data.append(row_data)

    return parsed_data

def main():
    parser = argparse.ArgumentParser(description='Parse the cm_data file.')
    parser.add_argument('filepath', help='The path to the cm_data file to parse.')
    args = parser.parse_args()

    data = parse_cm_data(args.filepath)
    print(json.dumps(data, indent=2))

if __name__ == '__main__':
    main()
