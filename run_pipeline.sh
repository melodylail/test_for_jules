#!/bin/bash
#
# Full pipeline: parse all raw data then generate all visualizations.
#
# Step 1: Parse raw data from data/liuxiu/{ccx,die,socket}/ into JSON
# Step 2: Generate per-folder simple visualizations
# Step 3: Generate cross-level (CCX vs DIE vs SOCKET) comparison charts
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================================"
echo "  Step 1: Parsing raw data"
echo "========================================================"
./run_all_parsers.sh

echo ""
echo "========================================================"
echo "  Step 2: Generating visualizations"
echo "========================================================"
./run_cm_data_visualizations.sh

echo ""
echo "========================================================"
echo "  Pipeline complete!"
echo "========================================================"
echo ""
echo "Parsed data:     results/data/liuxiu/{ccx,die,socket}/"
echo "Visualizations:  results/visualizations/"
