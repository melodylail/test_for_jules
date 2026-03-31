# Visualization Scripts for data/liuxiu/die

This document describes the visualization scripts that process the parsed JSON files from `results/data/liuxiu/die` and create charts and heatmaps.

## Overview

The visualization scripts read the JSON files created by the parsing scripts and generate various charts, heatmaps, and graphs to help analyze the hardware performance data.

## Visualization Scripts

### 1. CCM to Memory Latency Visualization
**Script:** `visualize_liuxiu_die_ccm_to_mem_lat.py`

**Data Source:** `results/data/liuxiu/die/ccm_to_mem_lat/`

**Outputs:**
- Heatmaps showing latency values across different CCMs and DIEs
- Bar charts comparing latency cycles and latency (ns) across paths
- All visualizations saved to `results/visualizations/liuxiu_die_ccm_to_mem_lat/`

**Visualizations Created:**
- `latency(cycles)_heatmap.png` - Heatmap of latency cycles
- `latency(ns)_heatmap.png` - Heatmap of latency in nanoseconds
- `latency(cycles)_bar.png` - Bar chart of latency cycles

### 2. Simple Data Visualization
**Script:** `visualize_liuxiu_die_simple_data.py`

**Data Sources:**
- `results/data/liuxiu/die/cm_data_parsed.json`
- `results/data/liuxiu/die/di_data_parsed.json`
- `results/data/liuxiu/die/iom_data_parsed.json`

**Outputs:**
For each file (cm_data, di_data, iom_data):
- Comprehensive heatmap showing all metrics
- Individual bar charts for each metric
- All visualizations saved to `results/visualizations/liuxiu_die_simple/<filename>/`

**Example Visualizations:**
- `cm_data_heatmap.png` - All metrics in one view
- `cm_data_CS0_RD_bar.png` - CS0 Read metric
- `iom_data_TOTAL_BW_MIN_bar.png` - Total bandwidth minimum
- And more...

### 3. DF Data Stream Visualization
**Script:** `visualize_liuxiu_die_df_data_stream.py`

**Data Source:** `results/data/liuxiu/die/df_data_stream/`

**Outputs:**
For each data stream file:
- Heatmap showing metric values across all components
- Bar chart showing total activity per component
- All visualizations saved to `results/visualizations/liuxiu_die_df_data_stream/<filename>/`

**Files Processed:**
- ccm_in_data
- ccm_out_todie2_data
- cs_in_data
- cs_out_data
- iom_out_todie2_data
- spf_in_data
- spf_out_data

**Example Visualizations:**
- `ccm_in_data_heatmap.png` - Heatmap of all metrics
- `ccm_in_data_total_activity_bar.png` - Total activity by component

## Usage

### Run All Visualizations

```bash
./run_all_liuxiu_die_visualizations.sh
```

### Run Individual Visualization Scripts

```bash
# CCM to memory latency
python3 visualize_liuxiu_die_ccm_to_mem_lat.py

# Simple data (cm_data, di_data, iom_data)
python3 visualize_liuxiu_die_simple_data.py

# DF data stream
python3 visualize_liuxiu_die_df_data_stream.py
```

## Output Location

All visualizations are saved to: `results/visualizations/`

```
results/visualizations/
├── liuxiu_die_ccm_to_mem_lat/
│   ├── latency(cycles)_heatmap.png
│   ├── latency(ns)_heatmap.png
│   └── latency(cycles)_bar.png
├── liuxiu_die_simple/
│   ├── cm_data/
│   │   ├── cm_data_heatmap.png
│   │   ├── cm_data_CS0_RD_bar.png
│   │   └── ... (9 more charts)
│   ├── di_data/
│   │   ├── di_data_heatmap.png
│   │   └── ... (3 more charts)
│   └── iom_data/
│       ├── iom_data_heatmap.png
│       └── ... (10 more charts)
└── liuxiu_die_df_data_stream/
    ├── ccm_in_data/
    │   ├── ccm_in_data_heatmap.png
    │   └── ccm_in_data_total_activity_bar.png
    ├── ccm_out_todie2_data/
    └── ... (5 more directories)
```

## Visualization Types

### Heatmaps
- **Purpose:** Show value intensity across multiple dimensions
- **Color Scheme:**
  - Yellow to Red (YlOrRd) for latency and general metrics
  - Values displayed in cells for easy reading
  - Automatic scaling with K, M, G suffixes for large numbers

### Bar Charts
- **Purpose:** Compare values across categories
- **Features:**
  - Color-coded by source (CCM, component, etc.)
  - Value labels on top of bars
  - Grid lines for easier reading
  - Automatic formatting of large numbers (K, M, G)

## Data Processing

The scripts automatically:
- Parse values with suffixes (K=thousands, M=millions, G=billions)
- Handle bandwidth units (B/s, KB/s, MB/s, GB/s)
- Filter out zero-value entries for clearer visualizations
- Format numbers appropriately for display

## Requirements

### Python Packages
```bash
pip install matplotlib pandas numpy
```

Or if you have a virtual environment:
```bash
source venv/bin/activate
pip install matplotlib pandas numpy
```

## Statistics Summary

Total visualizations created: **42 charts**

### Breakdown:
- **CCM to Memory Latency:** 3 charts
- **Simple Data (cm_data, di_data, iom_data):** 25 charts
- **DF Data Stream (7 files × 2 charts each):** 14 charts

## Interpretation Guide

### Latency Heatmaps
- **Darker colors** = Higher latency (potentially problematic)
- **Lighter colors** = Lower latency (better performance)
- **Zeros** indicate no traffic on that path

### Activity/Bandwidth Charts
- **Taller bars** = More activity/higher bandwidth
- Compare across DIEs to identify hotspots
- Check for imbalances that might indicate performance issues

### Queue Data
- **Occupancy ranges** show how full queues are
- High occupancy in upper ranges (75%-100%) may indicate congestion
- Kill/drop rates indicate resource contention

## Troubleshooting

### No visualizations created
- Ensure JSON files exist in `results/data/liuxiu/die/`
- Run the parsing scripts first if needed
- Check that matplotlib is installed

### Import errors
```bash
pip install matplotlib pandas numpy seaborn
```

### Empty or all-zero charts
- This is normal if the source data contains all zeros
- The scripts filter out all-zero rows for clearer visualization

## Next Steps

After generating visualizations:
1. Review heatmaps to identify performance hotspots
2. Compare latency across different CCMs
3. Analyze bandwidth distribution across DIEs
4. Look for patterns or anomalies in the data
5. Use insights to optimize system configuration

## Examples

### Viewing a Visualization
```bash
# On Linux
xdg-open results/visualizations/liuxiu_die_ccm_to_mem_lat/latency\(ns\)_heatmap.png

# On Mac
open results/visualizations/liuxiu_die_ccm_to_mem_lat/latency\(ns\)_heatmap.png

# On Windows
start results/visualizations/liuxiu_die_ccm_to_mem_lat/latency(ns)_heatmap.png
```

## Author

Created for visualizing AMD hardware performance data from the liuxiu/die dataset.
