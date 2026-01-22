import re

def parse_value(value_str):
    if not isinstance(value_str, str):
        return 0
    value_str = value_str.strip().upper()
    multiplier = 1
    if 'K' in value_str:
        multiplier = 1e3
    elif 'M' in value_str:
        multiplier = 1e6
    elif 'B' in value_str:
        multiplier = 1e9

    num_part = re.search(r'[\d.]+', value_str)
    if num_part:
        return float(num_part.group()) * multiplier
    return 0

def parse_bw_to_kb(value):
    """Converts bandwidth string (e.g., '4371 B/s', '11 KB/s') to KB/s."""
    value = value.strip()
    num_part = re.search(r'[\d.]+', value)
    if not num_part:
        return 0
    num = float(num_part.group())

    if 'GB/s' in value:
        return num * 1024 * 1024
    if 'MB/s' in value:
        return num * 1024
    elif 'KB/s' in value:
        return num
    elif 'B/s' in value:
        return num / 1024
    return num

def parse_bw(value):
    """Converts bandwidth string (e.g., '145 MB/s', '18 GB/s') to MB/s."""
    value = value.strip()
    num_part = re.search(r'[\d.]+', value)
    if not num_part:
        return 0
    num = float(num_part.group())

    if 'GB/s' in value:
        return num * 1024
    elif 'MB/s' in value:
        return num
    elif 'KB/s' in value:
        return num / 1024
    elif 'B/s' in value:
        return num / (1024 * 1024)
    return num
