#!/bin/bash
#
# Run all simple data visualization and cross-level comparisons:
#   1. Per-folder simple visualizations (ccx/die/socket) for cm_data, di_data, iom_data
#   2. Cross-level comparisons (CCX vs DIE vs SOCKET) for cm_data, di_data, iom_data
#   3. Cross-level comparisons for ccm0-3todie2_lat_data (ccm_to_mem_lat)
#   4. Cross-level comparisons for df_queue (ccm_queue, cs_queue, iom_queue)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Running simple visualizations (per folder) ==="
python3 visualize_liuxiu_die_simple_data.py

echo ""
echo "=== Running cm_data CCX vs DIE vs SOCKET comparison ==="
python3 compare_cm_data_ccx_die_socket.py

echo ""
echo "=== Running di_data CCX vs DIE vs SOCKET comparison ==="
python3 compare_di_data_ccx_die_socket.py

echo ""
echo "=== Running iom_data CCX vs DIE vs SOCKET comparison ==="
python3 compare_iom_data_ccx_die_socket.py

echo ""
echo "=== Running ccm_to_mem_lat CCX vs DIE vs SOCKET comparison ==="
python3 compare_ccm_to_mem_lat_ccx_die_socket.py

echo ""
echo "=== Running df_queue CCX vs DIE vs SOCKET comparison ==="
python3 compare_df_queue_ccx_die_socket.py

echo ""
echo "=== Done ==="
echo "Results:"
echo "  Per-folder:  results/visualizations/liuxiu_{ccx,die,socket}_simple/"
echo "  Comparison:  results/visualizations/cm_data_ccx_die_socket_comparison/"
echo "  Comparison:  results/visualizations/di_data_ccx_die_socket_comparison/"
echo "  Comparison:  results/visualizations/iom_data_ccx_die_socket_comparison/"
echo "  Comparison:  results/visualizations/ccm_to_mem_lat_ccx_die_socket_comparison/"
echo "  Comparison:  results/visualizations/df_queue_ccx_die_socket_comparison/"
