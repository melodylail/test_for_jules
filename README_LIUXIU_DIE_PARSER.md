# Data Parser for data/liuxiu/die

This document describes the Python scripts for parsing data files under `data/liuxiu/die` to JSON format.

## Overview

The parser scripts convert various data files from text format to structured JSON format, making them easier to analyze programmatically.

## Files

### Main Parser
- **`parse_liuxiu_die_all.py`** - Master script that processes all files in `data/liuxiu/die`
- **`run_liuxiu_die_parser.sh`** - Shell script to run the parser easily

### Specialized Parsers
Located in the `parsers/` directory:
- **`liuxiu_ccm_to_mem_lat_parser.py`** - Parses CCM to memory latency files
- **`liuxiu_df_queue_parser.py`** - Parses DF queue data files
- **`liuxiu_df_detail_lat_parser.py`** - Parses detailed latency files
- **`liuxiu_df_data_stream_parser.py`** - Parses data stream files

## Usage

### Quick Start

Run all parsers at once:

```bash
./run_liuxiu_die_parser.sh
```

Or manually:

```bash
python3 parse_liuxiu_die_all.py --source data/liuxiu/die --output results/data/liuxiu/die
```

### Individual File Parsing

Parse a specific file using specialized parsers:

```bash
# Parse CCM to memory latency file
python3 parsers/liuxiu_ccm_to_mem_lat_parser.py data/liuxiu/die/ccm_to_mem_lat/ccm0todie2_lat_data -o output.json

# Parse queue data file
python3 parsers/liuxiu_df_queue_parser.py data/liuxiu/die/df_queue/ccm_queue_data -o output.json

# Parse detailed latency file
python3 parsers/liuxiu_df_detail_lat_parser.py data/liuxiu/die/df_detail_lat/ccm2todie2_latency_data -o output.json

# Parse data stream file
python3 parsers/liuxiu_df_data_stream_parser.py data/liuxiu/die/df_data_stream/ccm_in_data -o output.json
```

## Input Files

The parser processes the following file types:

### 1. CCM to Memory Latency (`ccm_to_mem_lat/`)
- `ccm0todie2_lat_data`
- `ccm1todie2_lat_data`
- `ccm2todie2_lat_data`
- `ccm3todie2_lat_data`

**Format**: Tabular data with headers showing latency metrics per DIE

### 2. DF Queue Data (`df_queue/`)
- `ccm_queue_data`
- `cs_queue_data`
- `iom_queue_data`

**Format**: Hierarchical data with Level 1/2/3 structure showing queue metrics

### 3. DF Detail Latency (`df_detail_lat/`)
- `ccm2todie2_latency_data`
- `cs2todie2_latency_data`
- `iom2todie2_latency_data`

**Format**: Complex hierarchical structure with TARGET_CORE_DIE sections and transaction types

### 4. DF Data Stream (`df_data_stream/`)
- `ccm_in_data`
- `ccm_out_todie2_data`
- `cs_in_data`
- `cs_out_data`
- `iom_out_todie2_data`
- `spf_in_data`
- `spf_out_data`

**Format**: Hierarchical data showing data transfer metrics

### 5. Simple Tabular Data
- `cm_data` - Core memory data
- `di_data` - Data transport between nodes/sockets
- `iom_data` - IOM (IO Module) data

**Format**: Simple tabular format with headers

## Output Structure

### Tabular Files (cm_data, di_data, iom_data, ccm_to_mem_lat)

JSON array with objects containing:
```json
[
  {
    "Category": "DIE0",
    "CS0_RDSZ": "16",
    "CS1_RDSZ": "16",
    ...
  }
]
```

### Hierarchical Files (df_queue, df_data_stream)

JSON object with sections:
```json
{
  "sections": [
    {
      "header": ["Level 1", "Level 2"],
      "die_labels": ["DIE0", "DIE1", ...],
      "entries": [
        {
          "raw_line": "...",
          "fields": [...]
        }
      ]
    }
  ]
}
```

### Complex Hierarchical Files (df_detail_lat)

JSON object with target sections:
```json
{
  "target_sections": [
    {
      "target_info": "TARGET_CORE_DIE:2",
      "level_info": ["Level 2", "Level 3"],
      "die_labels": ["DIE0", "DIE1", ...],
      "transaction_types": [
        {
          "type": "RDBLK",
          "data": [...]
        }
      ]
    }
  ]
}
```

## Output Location

All parsed JSON files are saved to: `results/data/liuxiu/die/`

The directory structure mirrors the input structure:
```
results/data/liuxiu/die/
├── ccm_to_mem_lat/
│   ├── ccm0todie2_lat_data_parsed.json
│   ├── ccm1todie2_lat_data_parsed.json
│   └── ...
├── df_queue/
│   ├── ccm_queue_data_parsed.json
│   └── ...
├── df_detail_lat/
│   └── ...
├── df_data_stream/
│   └── ...
├── cm_data_parsed.json
├── di_data_parsed.json
├── iom_data_parsed.json
└── parsing_summary.json
```

## Parsing Summary

After running the parser, check `results/data/liuxiu/die/parsing_summary.json` for:
- List of all processed files
- Success/failure status for each file
- Number of records parsed
- Error messages (if any)

## Requirements

- Python 3.6 or higher
- No external dependencies (uses only standard library)

## Examples

### Example 1: Parse all files
```bash
python3 parse_liuxiu_die_all.py
```

### Example 2: Parse to custom output directory
```bash
python3 parse_liuxiu_die_all.py --source data/liuxiu/die --output my_results/
```

### Example 3: Parse single file and print to stdout
```bash
python3 parsers/liuxiu_ccm_to_mem_lat_parser.py data/liuxiu/die/ccm_to_mem_lat/ccm0todie2_lat_data
```

## Troubleshooting

If parsing fails:
1. Check that input files exist in the expected locations
2. Verify Python 3 is installed: `python3 --version`
3. Check the parsing summary JSON for specific error messages
4. Ensure you have write permissions to the output directory

## Author

Created for parsing hardware performance data from AMD systems.
