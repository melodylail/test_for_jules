#!/bin/bash
#
# Run cm_data visualization scripts:
#   1. Per-folder simple visualizations (ccx/die/socket)
#   2. Cross-level comparison (CCX vs DIE vs SOCKET)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Running cm_data simple visualizations (per folder) ==="
python3 visualize_liuxiu_die_simple_data.py

echo ""
echo "=== Running cm_data CCX vs DIE vs SOCKET comparison ==="
python3 compare_cm_data_ccx_die_socket.py

echo ""
echo "=== Done ==="
echo "Results:"
echo "  Per-folder:  results/visualizations/liuxiu_{ccx,die,socket}_simple/"
echo "  Comparison:  results/visualizations/cm_data_ccx_die_socket_comparison/"
