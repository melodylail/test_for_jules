#!/bin/bash

export PYTHONPATH=$PYTHONPATH:.

echo "Running all visualization scripts..."

python3 visualizations/cm_data_visualizer.py
python3 visualizations/di_data_visualizer.py
python3 visualizations/iom_data_visualizer.py
python3 visualizations/ccm_queue_data_visualizer.py
python3 visualizations/cs2todie2_latency_data_visualizer.py
python3 visualizations/iom2todie2_latency_data_visualizer.py
python3 visualizations/data_stream_visualizer.py results/spf_in_data_parsed.json plots
python3 visualizations/data_stream_visualizer.py results/spf_out_data_parsed.json plots
python3 visualizations/data_stream_visualizer.py results/cs_in_data_parsed.json plots
python3 visualizations/data_stream_visualizer.py results/ccm_in_data_parsed.json plots
python3 visualizations/data_stream_visualizer.py results/ccm_out_todie2_data_parsed.json plots
python3 visualizations/data_stream_visualizer.py results/iom_out_todie2_data_parsed.json plots
python3 visualizations/data_stream_visualizer.py results/cs_out_data_parsed.json plots

echo "All visualizations generated. Results are in the 'plots' directory."
