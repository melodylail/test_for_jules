import argparse
import re
import json

class Node:
    def __init__(self, name, level, values=None):
        self.name = name
        self.level = level
        self.values = values or {}
        self.children = []

    def to_dict(self):
        result = {
            'name': self.name,
        }
        if self.values:
            result['values'] = self.values
        if self.children:
            result['children'] = [child.to_dict() for child in self.children]
        return result

def parse_simple_tabular(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    header_line = ''
    header_positions = []
    header = []
    data = []
    data_starts = False

    # Filter out lines that are not part of the table data.
    clean_lines = [line for line in lines if line.strip() and not line.strip().startswith('Note:') and not ':' in line]

    for i, line in enumerate(clean_lines):

        if '------' in line:
            header_line = clean_lines[i-1]
            # Split header into columns and find their starting positions
            header = re.split(r'\s{2,}', header_line.strip())
            start = 0
            for h in header:
                # Find the position of each header, starting search from the end of the last one
                pos = header_line.find(h, start)
                header_positions.append(pos)
                start = pos + len(h)

            data_starts = True
            continue

        if data_starts:
            row = {}
            for j, h in enumerate(header):
                start = header_positions[j]
                # The end of the column is the start of the next one
                end = header_positions[j+1] if j+1 < len(header_positions) else len(line)
                value = line[start:end].strip()
                row[h] = value
            data.append(row)

    return data

def get_level_and_name(line):
    # This function determines the indentation level of a line in a hierarchical file.
    match = re.match(r'([|`\s-]*)(.*?)\s{2,}', line)
    if match:
        prefix = match.group(1)
        name = match.group(2).strip()
        # Level is determined by the raw length of the prefix, adjusted for connectors
        level = len(prefix.replace('|-', '  ').replace('|_', '  '))
        return level, name
    # Fallback for lines without special prefixes
    return 0, line.strip().split('  ')[0]


def parse_hierarchical(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    header_lines = []
    data_lines = []
    is_header = True

    # Separate header and data lines. Header ends when first real data line starts.
    for line in lines:
        stripped = line.strip()
        if is_header and ('Level' in line or 'DIE' in line or 'CS' in line or 'CCM' in line) and not re.search(r'\d%', stripped):
            header_lines.append(line)
        else:
            # First line that seems like data ends the header
            if is_header:
                is_header = False
            # Skip repeated headers in the body of the file
            if 'Level 1' in line or 'TARGET_CORE' in line:
                continue
            data_lines.append(line)

    columns = []
    if header_lines:
        l1_line = ""
        for hline in header_lines:
            if "DIE" in hline or "SKT" in hline or "SYS" in hline:
                l1_line = hline
                break

        l1_headers_with_pos = [(m.group(0), m.start()) for m in re.finditer(r'DIE\d+|SKT\d+|SYS', l1_line)]

        l2_line = ""
        for hline in header_lines:
            if "CS" in hline or "CCM" in hline:
                l2_line = hline
                break

        if l2_line:
            l2_headers_with_pos = [(m.group(0), m.start()) for m in re.finditer(r'CS\d+|CCM\d+', l2_line)]

            for l2_header, l2_pos in l2_headers_with_pos:
                current_l1 = ''
                for l1_header, l1_pos in l1_headers_with_pos:
                    if l2_pos >= l1_pos:
                        current_l1 = l1_header
                columns.append(f"{current_l1}_{l2_header}")


    root = Node('root', -1)
    stack = [root]

    for line in data_lines:
        if not line.strip(): continue

        level, name = get_level_and_name(line)
        if not name: continue

        # Extract values
        values_str_match = re.search(r'\s{2,}([-0-9].*)', line)
        values = {}
        if values_str_match and columns:
            values_str = values_str_match.group(1)
            values_list = re.split(r'\s+', values_str.strip())
            # Handle cases where value is missing for some columns
            values = dict(zip(columns[:len(values_list)], values_list))

        node = Node(name, level, values)

        while stack and stack[-1].level >= level:
            stack.pop()

        if stack:
            stack[-1].children.append(node)
        stack.append(node)

    return root.to_dict().get('children', [])


def main():
    parser = argparse.ArgumentParser(description='Parse a file.')
    parser.add_argument('filepath', help='The path to the file to parse.')
    args = parser.parse_args()

    print(f"Parsing file: {args.filepath}")

    is_hierarchical = False
    with open(args.filepath, 'r') as f:
        # Heuristic to detect file type.
        # Hierarchical files have tree-like structures with '|-' or '|_'
        # or have 'Level 1' in their headers.
        content = f.read()
        if '|- ' in content or '|_ ' in content or 'Level 1' in content:
            is_hierarchical = True

    if is_hierarchical:
        data = parse_hierarchical(args.filepath)
    else:
        data = parse_simple_tabular(args.filepath)

    if data:
        print(json.dumps(data, indent=2))

if __name__ == '__main__':
    main()
