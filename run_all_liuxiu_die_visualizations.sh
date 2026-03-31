#!/bin/bash

# Script to run all visualization scripts for liuxiu/die data

echo "========================================"
echo "Creating Visualizations for liuxiu/die Data"
echo "========================================"
echo ""

echo "1. Visualizing CCM to Memory Latency data..."
python3 visualize_liuxiu_die_ccm_to_mem_lat.py

echo ""
echo "2. Visualizing Simple Data (cm_data, di_data, iom_data)..."
python3 visualize_liuxiu_die_simple_data.py

echo ""
echo "3. Visualizing DF Data Stream data..."
python3 visualize_liuxiu_die_df_data_stream.py

echo ""
echo "========================================"
echo "All visualizations complete!"
echo "Check results/visualizations/ for outputs"
echo "========================================"
