import argparse
import json
import re
from parsers.hierarchical_parser_utils import parse_hierarchical_section

def parse_df_queue(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    section_starts = [i for i, line in enumerate(lines) if 'Level 1' in line]
    if not section_starts:
        section_starts = [0]

    all_parsed_data = []
    for i in range(len(section_starts)):
        start = section_starts[i]
        end = section_starts[i+1] if i + 1 < len(section_starts) else len(lines)
        section_lines = lines[start:end]
        parsed_section = parse_hierarchical_section(section_lines, r'[A-Z]+\d+(_[A-Z]+\d+)*')
        if parsed_section:
            all_parsed_data.append(parsed_section)

    return all_parsed_data

def main():
    parser = argparse.ArgumentParser(description='Parse df_queue files.')
    parser.add_argument('filepath', help='The path to the file to parse.')
    args = parser.parse_args()
    data = parse_df_queue(args.filepath)
    print(json.dumps(data, indent=2))

if __name__ == '__main__':
    main()
