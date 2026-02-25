#!/bin/bash
#
# Run all simple data visualization and cross-level comparisons:
#   1. Per-folder simple visualizations (ccx/die/socket) for cm_data, di_data, iom_data
#   2. Cross-level comparisons (CCX vs DIE vs SOCKET) for cm_data, di_data, iom_data
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
echo "=== Done ==="
echo "Results:"
echo "  Per-folder:  results/visualizations/liuxiu_{ccx,die,socket}_simple/"
echo "  Comparison:  results/visualizations/cm_data_ccx_die_socket_comparison/"
echo "  Comparison:  results/visualizations/di_data_ccx_die_socket_comparison/"
echo "  Comparison:  results/visualizations/iom_data_ccx_die_socket_comparison/"
