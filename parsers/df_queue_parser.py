import argparse
import json
import re

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
        parsed_section = parse_section(section_lines)
        if parsed_section:
            all_parsed_data.append(parsed_section)

    return all_parsed_data

def parse_section(lines):
    header_line1_index = next((i for i, line in enumerate(lines) if re.search(r'[A-Z]+\d+', line) and 'Level' in line), -1)
    if header_line1_index == -1: header_line1_index = next((i for i, line in enumerate(lines) if re.search(r'[A-Z]+\d+', line)), 0)
    header_line2_index = header_line1_index + 1

    header_line1 = lines[header_line1_index].rstrip()
    header_line2 = lines[header_line2_index].rstrip()

    data_start_index = header_line2_index + 1
    data_lines = [line for line in lines[data_start_index:] if line.strip()]

    top_level_matches = list(re.finditer(r'[A-Z]+\d+(_[A-Z]+\d+)*', header_line1))
    top_level_headers = []
    max_header_len = max(len(header_line1), len(header_line2))
    for i, match in enumerate(top_level_matches):
        start = match.start()
        end = top_level_matches[i+1].start() if i + 1 < len(top_level_matches) else max_header_len
        top_level_headers.append({'name': match.group(), 'start': start, 'end': end})

    col_starts = [match.start() for match in re.finditer(r'\S+', header_line2)]
    col_names = re.findall(r'\S+', header_line2)
    first_col_start = col_starts[0] if col_starts else 0

    flat_headers = []
    for i, start_pos in enumerate(col_starts):
        col_name = col_names[i]
        parent_header = "Unknown"
        for h in top_level_headers:
            if h['start'] <= start_pos < h['end']: parent_header = h['name']; break
        flat_headers.append(f"{parent_header}_{col_name}")

    parsed_data = {}
    path = []
    for line in data_lines:
        line = line.rstrip()
        if not line.strip().startswith('|') and not re.search(r'[a-zA-Z]', line[:first_col_start]): continue

        level = line.count('|-') + line.count('|_')
        category_name = re.sub(r'(\s*\|[-_]\s*)+', '', line[:first_col_start]).strip()

        if category_name in ('|', '_'):
            continue

        if not category_name:
             if re.search(r'[a-zA-Z]', line):
                  category_name = line[:first_col_start].strip()
                  level = 0
             else: continue

        path = path[:level]

        current_level_dict = parsed_data
        for key in path:
            current_level_dict = current_level_dict.setdefault(key, {})

        values_part = line[first_col_start:].strip()
        if values_part:
            row_data = {}
            for i, header in enumerate(flat_headers):
                start = col_starts[i]
                end = col_starts[i+1] if i + 1 < len(col_starts) else len(line)
                value = line[start:end].strip()
                row_data[header] = value

            if category_name not in current_level_dict:
                current_level_dict[category_name] = {}
            current_level_dict[category_name].update(row_data)
        else:
            current_level_dict.setdefault(category_name, {})

        path.append(category_name)

    return parsed_data

def main():
    parser = argparse.ArgumentParser(description='Parse df_queue files.')
    parser.add_argument('filepath', help='The path to the file to parse.')
    args = parser.parse_args()
    data = parse_df_queue(args.filepath)
    print(json.dumps(data, indent=2))

if __name__ == '__main__':
    main()
