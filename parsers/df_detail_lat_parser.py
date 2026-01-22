import argparse
import json
import re
from parsers.hierarchical_parser_utils import parse_hierarchical_section

def parse_df_detail_lat(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    section_starts = [i for i, line in enumerate(lines) if 'TARGET_CORE_DIE' in line or 'SOURCE_CORE_DIE' in line]
    if not section_starts:
        section_starts = [0]

    all_parsed_data = []
    for i in range(len(section_starts)):
        start = section_starts[i]
        end = section_starts[i+1] if i + 1 < len(section_starts) else len(lines)
        section_lines = lines[start:end]

        parsed_section = parse_hierarchical_section(section_lines, r'DIE\d+')

        # Add TARGET_CORE_DIE or SOURCE_CORE_DIE info
        for line in section_lines:
            match = re.search(r'(TARGET_CORE_DIE|SOURCE_CORE_DIE):(\d+)', line)
            if match:
                parsed_section = {f"{match.group(1)}_{match.group(2)}": parsed_section}
                break

        if parsed_section:
            all_parsed_data.append(parsed_section)

    return all_parsed_data

def main():
    parser = argparse.ArgumentParser(description='Parse df_detail_lat files.')
    parser.add_argument('filepath', help='The path to the file to parse.')
    args = parser.parse_args()
    data = parse_df_detail_lat(args.filepath)
    print(json.dumps(data, indent=2))

if __name__ == '__main__':
    main()
