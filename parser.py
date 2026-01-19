import sys

def parse_file(filepath):
    """
    Parses a text file with key-value pairs separated by a colon.

    Args:
        filepath (str): The path to the text file.

    Returns:
        dict: A dictionary containing the parsed key-value pairs.
    """
    data = {}
    with open(filepath, 'r') as f:
        for line in f:
            if ':' in line:
                key, value = line.split(':', 1)
                data[key.strip()] = value.strip()
    return data

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python parser.py <file>")
        sys.exit(1)

    filepath = sys.argv[1]
    try:
        parsed_data = parse_file(filepath)
        print(parsed_data)
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        sys.exit(1)
