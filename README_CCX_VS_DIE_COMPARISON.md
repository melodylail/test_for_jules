# CCX vs DIE Data Comparison Visualization

This document describes the comparison visualization script that compares JSON data between `results/data/liuxiu/ccx` and `results/data/liuxiu/die` folders.

## Overview

The comparison script loads corresponding JSON files from both CCX and DIE datasets and creates side-by-side visualizations to identify differences between the two data sources.

## Script

**Main Script:** `visualize_ccx_vs_die_comparison.py`
**Runner Script:** `run_ccx_vs_die_comparison.sh`

## Usage

### Quick Start
```bash
./run_ccx_vs_die_comparison.sh
```

### Manual Run
```bash
python3 visualize_ccx_vs_die_comparison.py
```

## Output Location

All comparison visualizations are saved to:
```
results/visualizations/ccx_vs_die_comparison/
```

## Comparisons Performed

### 1. Simple Data Files
**Files Compared:**
- `cm_data_parsed.json` - Core Memory data
- `di_data_parsed.json` - Data Transport between sockets
- `iom_data_parsed.json` - IO Module data

**Visualizations Created:**
- Side-by-side bar charts for each metric
- 3-panel heatmap comparison (CCX, DIE, % Difference)

### 2. CCM to Memory Latency
**Files Compared:**
- `ccm0todie2_lat_data_parsed.json`
- `ccm1todie2_lat_data_parsed.json`
- `ccm2todie2_lat_data_parsed.json`
- `ccm3todie2_lat_data_parsed.json`

**Visualizations Created:**
- Summary heatmap comparing average latency across all CCMs

### 3. Overall Summary
**Visualizations Created:**
- `cm_data_bandwidth_summary.png` - Total bandwidth comparison
- `overall_summary_comparison.png` - Multi-panel summary with statistics

## Visualization Types

### Side-by-Side Bar Charts
- **Blue bars (steelblue):** CCX data
- **Orange bars (coral):** DIE data
- Labels show exact values on each bar
- Easy comparison of same metric between datasets

### 3-Panel Heatmap Comparison
1. **Left panel (Blues):** CCX data heatmap
2. **Center panel (Oranges):** DIE data heatmap
3. **Right panel (RdBu_r):** Percentage difference
   - Red = DIE > CCX
   - Blue = CCX > DIE
   - White = Equal

### Summary Dashboard
Multi-panel figure showing:
- Core Memory bandwidth by DIE
- IOM bandwidth by DIE
- DI data comparison
- Summary statistics text

## Files Created (26 total)

### Overall Summaries (3)
```
ccx_vs_die_comparison/
├── cm_data_bandwidth_summary.png
├── overall_summary_comparison.png
└── ccm_to_mem_lat/
    └── ccm_to_mem_lat_summary_comparison.png
```

### Simple Data Comparisons (23)
```
ccx_vs_die_comparison/simple_data/
├── cm_data_CS0_RD_comparison.png
├── cm_data_CS0_WR_comparison.png
├── cm_data_CS1_RD_comparison.png
├── cm_data_CS1_WR_comparison.png
├── cm_data_CS2_RD_comparison.png
├── cm_data_CS2_WR_comparison.png
├── cm_data_CS3_RD_comparison.png
├── cm_data_CS3_WR_comparison.png
├── cm_data_TOTAL_BW_comparison.png
├── cm_data_heatmap_comparison.png
├── di_data_IO_DIE2_comparison.png
├── di_data_heatmap_comparison.png
├── iom_data_CS0_RDSZ_comparison.png
├── iom_data_CS0_WRSZ_comparison.png
├── iom_data_CS1_RDSZ_comparison.png
├── iom_data_CS1_WRSZ_comparison.png
├── iom_data_CS2_RDSZ_comparison.png
├── iom_data_CS2_WRSZ_comparison.png
├── iom_data_CS3_RDSZ_comparison.png
├── iom_data_CS3_WRSZ_comparison.png
├── iom_data_TOTAL_BW_MAX_comparison.png
├── iom_data_TOTAL_BW_MIN_comparison.png
└── iom_data_heatmap_comparison.png
```

## Interpreting Results

### Color Coding
| Color | Meaning |
|-------|---------|
| Blue bars | CCX data |
| Orange/Coral bars | DIE data |
| Red in diff heatmap | DIE > CCX |
| Blue in diff heatmap | CCX > DIE |

### Key Metrics to Compare

1. **Total Bandwidth (TOTAL_BW)**
   - Higher bandwidth indicates more memory traffic
   - Large differences may indicate different workload characteristics

2. **Read/Write Sizes (RDSZ/WRSZ)**
   - Compare I/O patterns between datasets

3. **Latency (avg-cacheable-latency-ns)**
   - Lower values indicate faster memory access
   - Differences may indicate different memory configurations

### What to Look For

1. **Consistent Differences**
   - If one dataset consistently shows higher values, it may indicate:
     - Different workload running
     - Different system configuration
     - Different measurement time

2. **DIE-Specific Variations**
   - Some DIEs may show larger differences than others
   - Could indicate NUMA effects or workload placement

3. **Metric Patterns**
   - Similar patterns across metrics suggest consistent behavior
   - Divergent patterns may need investigation

## Example Analysis

```python
# Quick analysis of the comparison data
import json

# Load parsed JSON files
with open('results/data/liuxiu/ccx/cm_data_parsed.json') as f:
    ccx_data = json.load(f)

with open('results/data/liuxiu/die/cm_data_parsed.json') as f:
    die_data = json.load(f)

# Compare SYS total bandwidth
ccx_sys = next(d for d in ccx_data if d['Category'] == 'SYS')
die_sys = next(d for d in die_data if d['Category'] == 'SYS')

print(f"CCX SYS TOTAL_BW: {ccx_sys['TOTAL_BW']}")
print(f"DIE SYS TOTAL_BW: {die_sys['TOTAL_BW']}")
```

## Requirements

### Python Packages
```bash
pip install matplotlib pandas numpy
```

## Extending the Comparison

To add more comparison types:

1. Add a new comparison function in `visualize_ccx_vs_die_comparison.py`
2. Call it from the `main()` function
3. Follow the existing pattern for loading and comparing data

Example:
```python
def compare_new_data(ccx_dir, die_dir, output_dir):
    """Compare a new data type."""
    # Load data
    ccx_data = load_json_file(os.path.join(ccx_dir, 'new_data_parsed.json'))
    die_data = load_json_file(os.path.join(die_dir, 'new_data_parsed.json'))

    # Create comparison visualization
    # ...
```

## Troubleshooting

### No visualizations created
- Ensure both CCX and DIE JSON files exist
- Check that file names match between directories

### Import errors
```bash
pip install matplotlib pandas numpy
```

### Empty charts
- Both datasets may have zero values for that metric
- Check the raw JSON files for data

## Summary

| Statistic | Value |
|-----------|-------|
| Total Comparison Charts | 26 |
| Data Types Compared | 3 (cm_data, di_data, iom_data) |
| CCM Latency Files Compared | 4 |
| Output Format | PNG (300 DPI) |

---

**Script:** `visualize_ccx_vs_die_comparison.py`
**Output:** `results/visualizations/ccx_vs_die_comparison/`
