import argparse
import json
import re

def parse_simple_tabular(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    separator_index = next((i for i, line in enumerate(lines) if '---' in line), -1)

    if separator_index != -1:
        header_line_index = separator_index - 1
        while not lines[header_line_index].strip():
            header_line_index -= 1
        header_line = lines[header_line_index].strip()
        data_lines = lines[separator_index + 1:]
    else:
        header_line = lines[0].strip()
        data_lines = lines[1:]

    headers = re.split(r'\s{2,}', header_line)
    headers = [h for h in headers if h.strip() and '->' not in h]

    parsed_data = []
    for line in data_lines:
        line = line.strip()
        if not line: continue

        # This regex will match numbers with optional units (K, M, MB/s, etc.) as a single token
        values = re.findall(r'(\d+\s*(?:[KMG]B/s|[KMG])|\d+)', line)

        # The first word of the line is always the category, even if it's not matched by the regex
        category = re.split(r'\s{2,}', line)[0]

        row_data = {"Category": category}

        for i, header in enumerate(headers):
             if i < len(values):
                row_data[header] = values[i]

        parsed_data.append(row_data)

    return parsed_data

def main():
    parser = argparse.ArgumentParser(description='Parse a simple tabular file.')
    parser.add_argument('filepath', help='The path to the file to parse.')
    args = parser.parse_args()

    data = parse_simple_tabular(args.filepath)
    print(json.dumps(data, indent=2))

if __name__ == '__main__':
    main()
