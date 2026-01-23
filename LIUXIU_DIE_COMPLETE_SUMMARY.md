# Complete Summary: Parsing and Visualizing data/liuxiu/die

This document provides a complete overview of all scripts, data files, and visualizations created for the `data/liuxiu/die` dataset.

## Table of Contents
1. [Overview](#overview)
2. [Parsing Scripts](#parsing-scripts)
3. [Visualization Scripts](#visualization-scripts)
4. [Quick Start Guide](#quick-start-guide)
5. [File Structure](#file-structure)
6. [Results Summary](#results-summary)

---

## Overview

This project processes hardware performance data from `data/liuxiu/die/`, converting text files to JSON format and creating visualizations for analysis.

### Pipeline
```
Raw Data Files (data/liuxiu/die/)
         ↓
   Parsing Scripts
         ↓
JSON Files (results/data/liuxiu/die/)
         ↓
Visualization Scripts
         ↓
Charts & Heatmaps (results/visualizations/)
```

---

## Parsing Scripts

### Main Parser
- **`parse_liuxiu_die_all.py`**
  - Master script that parses all 20 files automatically
  - Maintains directory structure in output
  - Creates parsing summary JSON

### Helper Script
- **`run_liuxiu_die_parser.sh`**
  - Convenient shell wrapper to run the parser

### Specialized Parsers (in `parsers/` directory)
- **`liuxiu_ccm_to_mem_lat_parser.py`** - CCM to memory latency files
- **`liuxiu_df_queue_parser.py`** - DF queue data files
- **`liuxiu_df_detail_lat_parser.py`** - Detailed latency files
- **`liuxiu_df_data_stream_parser.py`** - Data stream files

### Parsing Usage
```bash
# Run all parsers
./run_liuxiu_die_parser.sh

# Or manually
python3 parse_liuxiu_die_all.py
```

### Parsing Results
- **Files Processed:** 20
- **Success Rate:** 100% (20/20)
- **Output Location:** `results/data/liuxiu/die/`
- **Summary:** `results/data/liuxiu/die/parsing_summary.json`

#### Files Parsed
```
ccm_to_mem_lat/
  ├── ccm0todie2_lat_data_parsed.json
  ├── ccm1todie2_lat_data_parsed.json
  ├── ccm2todie2_lat_data_parsed.json
  └── ccm3todie2_lat_data_parsed.json

df_queue/
  ├── ccm_queue_data_parsed.json
  ├── cs_queue_data_parsed.json
  └── iom_queue_data_parsed.json

df_detail_lat/
  ├── ccm2todie2_latency_data_parsed.json
  ├── cs2todie2_latency_data_parsed.json
  └── iom2todie2_latency_data_parsed.json

df_data_stream/
  ├── ccm_in_data_parsed.json
  ├── ccm_out_todie2_data_parsed.json
  ├── cs_in_data_parsed.json
  ├── cs_out_data_parsed.json
  ├── iom_out_todie2_data_parsed.json
  ├── spf_in_data_parsed.json
  └── spf_out_data_parsed.json

Root files:
  ├── cm_data_parsed.json
  ├── di_data_parsed.json
  └── iom_data_parsed.json
```

---

## Visualization Scripts

### Scripts Created
1. **`visualize_liuxiu_die_ccm_to_mem_lat.py`**
   - Visualizes CCM to memory latency data
   - Creates heatmaps and bar charts
   - Output: 3 visualizations

2. **`visualize_liuxiu_die_simple_data.py`**
   - Visualizes cm_data, di_data, iom_data
   - Creates heatmaps and metric-specific bar charts
   - Output: 25 visualizations total

3. **`visualize_liuxiu_die_df_data_stream.py`**
   - Visualizes DF data stream files
   - Creates heatmaps and activity charts
   - Output: 14 visualizations (7 files × 2 each)

4. **`run_all_liuxiu_die_visualizations.sh`**
   - Runs all visualization scripts in sequence

### Visualization Usage
```bash
# Run all visualizations
./run_all_liuxiu_die_visualizations.sh

# Or run individually
python3 visualize_liuxiu_die_ccm_to_mem_lat.py
python3 visualize_liuxiu_die_simple_data.py
python3 visualize_liuxiu_die_df_data_stream.py
```

### Visualization Results
- **Total Charts Created:** 42
- **Output Location:** `results/visualizations/`

#### Chart Types
- **Heatmaps:** Show value intensity across components
- **Bar Charts:** Compare values across categories
- **Activity Charts:** Show total activity per component

---

## Quick Start Guide

### Step 1: Parse Data
```bash
./run_liuxiu_die_parser.sh
```
This creates JSON files in `results/data/liuxiu/die/`

### Step 2: Create Visualizations
```bash
./run_all_liuxiu_die_visualizations.sh
```
This creates PNG charts in `results/visualizations/`

### Step 3: View Results
```bash
# View a sample visualization
xdg-open results/visualizations/liuxiu_die_ccm_to_mem_lat/latency\(ns\)_heatmap.png

# Or browse the directory
ls -R results/visualizations/liuxiu_die*
```

---

## File Structure

### Complete Directory Layout
```
.
├── data/liuxiu/die/                    # Source data files (20 files)
│   ├── ccm_to_mem_lat/
│   ├── df_queue/
│   ├── df_detail_lat/
│   ├── df_data_stream/
│   ├── cm_data
│   ├── di_data
│   └── iom_data
│
├── parsers/                            # Specialized parser scripts
│   ├── liuxiu_ccm_to_mem_lat_parser.py
│   ├── liuxiu_df_queue_parser.py
│   ├── liuxiu_df_detail_lat_parser.py
│   └── liuxiu_df_data_stream_parser.py
│
├── parse_liuxiu_die_all.py            # Master parsing script
├── run_liuxiu_die_parser.sh           # Parser runner script
│
├── visualize_liuxiu_die_ccm_to_mem_lat.py   # Visualization scripts
├── visualize_liuxiu_die_simple_data.py
├── visualize_liuxiu_die_df_data_stream.py
├── run_all_liuxiu_die_visualizations.sh
│
├── results/
│   ├── data/liuxiu/die/               # Parsed JSON files (20 files)
│   │   ├── ccm_to_mem_lat/
│   │   ├── df_queue/
│   │   ├── df_detail_lat/
│   │   ├── df_data_stream/
│   │   └── parsing_summary.json
│   │
│   └── visualizations/                # Generated charts (42 files)
│       ├── liuxiu_die_ccm_to_mem_lat/
│       ├── liuxiu_die_simple/
│       │   ├── cm_data/
│       │   ├── di_data/
│       │   └── iom_data/
│       └── liuxiu_die_df_data_stream/
│           ├── ccm_in_data/
│           ├── ccm_out_todie2_data/
│           ├── cs_in_data/
│           ├── cs_out_data/
│           ├── iom_out_todie2_data/
│           ├── spf_in_data/
│           └── spf_out_data/
│
├── README_LIUXIU_DIE_PARSER.md        # Parsing documentation
├── README_LIUXIU_DIE_VISUALIZATIONS.md # Visualization documentation
└── LIUXIU_DIE_COMPLETE_SUMMARY.md     # This file
```

---

## Results Summary

### Parsing Statistics
| Metric | Value |
|--------|-------|
| Total Files Processed | 20 |
| Success Rate | 100% |
| Total JSON Records | ~1000+ |
| Output Format | Structured JSON |

### Visualization Statistics
| Category | Charts Created |
|----------|----------------|
| CCM to Memory Latency | 3 |
| Simple Data (cm/di/iom) | 25 |
| DF Data Stream | 14 |
| **Total** | **42** |

### File Sizes
- **Parsed JSON:** ~500 KB total
- **Visualizations:** ~15 MB total (PNG format, 300 DPI)

---

## Documentation Files

1. **`README_LIUXIU_DIE_PARSER.md`**
   - Complete guide to parsing scripts
   - Usage examples
   - Input/output format descriptions

2. **`README_LIUXIU_DIE_VISUALIZATIONS.md`**
   - Complete guide to visualization scripts
   - Chart type descriptions
   - Interpretation guidelines

3. **`LIUXIU_DIE_COMPLETE_SUMMARY.md`** (this file)
   - High-level overview
   - Quick reference guide

---

## Requirements

### Python Version
- Python 3.6 or higher

### Python Packages
```bash
pip install matplotlib pandas numpy
```

### Optional
For better plot styling:
```bash
pip install seaborn
```

---

## Troubleshooting

### Issue: No visualizations appear
**Solution:** Ensure JSON files exist in `results/data/liuxiu/die/`
```bash
# Check if JSON files exist
ls results/data/liuxiu/die/*.json

# If not, run parser first
./run_liuxiu_die_parser.sh
```

### Issue: ImportError for matplotlib
**Solution:** Install required packages
```bash
pip install matplotlib pandas numpy
```

### Issue: Visualizations are blank
**Solution:** This is normal if source data contains all zeros. Check the original data files.

---

## Next Steps

1. **Analyze Visualizations**
   - Review heatmaps for performance hotspots
   - Compare latency across different CCMs
   - Identify bandwidth bottlenecks

2. **Customize Visualizations**
   - Modify scripts to focus on specific metrics
   - Adjust color schemes
   - Add additional chart types

3. **Automate Analysis**
   - Create scripts to detect anomalies
   - Generate performance reports
   - Set up automated monitoring

---

## Summary

✅ **20 data files** successfully parsed to JSON
✅ **42 visualizations** created as PNG charts
✅ **3 main visualization scripts** ready to use
✅ **Complete documentation** provided

**All scripts are ready to use and fully documented!**

---

## Author

Created for parsing and visualizing AMD hardware performance data from the liuxiu/die dataset.

**Last Updated:** January 2026
