import re

def parse_hierarchical_section(lines, header_pattern):
    header_line1_index = next((i for i, line in enumerate(lines) if re.search(header_pattern, line)), -1)
    if header_line1_index == -1:
        return {}
    header_line2_index = header_line1_index + 1

    header_line1 = lines[header_line1_index].rstrip()
    header_line2 = lines[header_line2_index].rstrip()

    data_start_index = header_line2_index + 1
    data_lines = [line for line in lines[data_start_index:] if line.strip()]

    top_level_matches = list(re.finditer(header_pattern, header_line1))
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
            if h['start'] <= start_pos < h['end']:
                parent_header = h['name']
                break
        flat_headers.append(f"{parent_header}_{col_name}")

    parsed_data = {}
    path = []
    for line in data_lines:
        line = line.rstrip()
        if not line.strip().startswith('|') and not re.search(r'[a-zA-Z]', line[:first_col_start]):
            continue

        level = line.count('|-') + line.count('|_')
        category_name = re.sub(r'(\s*\|[-_]\s*)+', '', line[:first_col_start]).strip()

        if category_name in ('|', '_'):
            continue

        if not category_name:
             if re.search(r'[a-zA-Z]', line):
                  category_name = line[:first_col_start].strip()
                  level = 0
             else:
                  continue

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
