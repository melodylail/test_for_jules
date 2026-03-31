#!/bin/bash
#
# Parse all raw data files under data/liuxiu/{ccx,die,socket}/
# and save parsed JSON to results/data/liuxiu/{ccx,die,socket}/
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

export PYTHONPATH="$PYTHONPATH:."

DATA_ROOT="data/liuxiu"
RESULTS_ROOT="results/data/liuxiu"
ERROR_LOG="error.log"

rm -f "$ERROR_LOG"
touch "$ERROR_LOG"

for level in ccx die socket; do
    echo "=============================="
    echo "Parsing $level data..."
    echo "=============================="

    SRC="$DATA_ROOT/$level"
    DST="$RESULTS_ROOT/$level"

    if [ ! -d "$SRC" ]; then
        echo "  Warning: $SRC not found, skipping"
        continue
    fi

    # --- Simple file parsers (cm_data, di_data, iom_data) ---
    for data_name in cm_data di_data iom_data; do
        if [ -f "$SRC/$data_name" ]; then
            mkdir -p "$DST"
            echo "  Parsing $SRC/$data_name..."
            python3 "parsers/${data_name}_parser.py" "$SRC/$data_name" > "$DST/${data_name}_parsed.json" 2>> "$ERROR_LOG"
        fi
    done

    # --- ccm_to_mem_lat (4 files) ---
    if [ -d "$SRC/ccm_to_mem_lat" ]; then
        mkdir -p "$DST/ccm_to_mem_lat"
        for data_file in "$SRC/ccm_to_mem_lat"/*; do
            if [ -f "$data_file" ]; then
                filename=$(basename "$data_file")
                echo "  Parsing $data_file..."
                python3 parsers/mem_lat_parser.py "$data_file" > "$DST/ccm_to_mem_lat/${filename}_parsed.json" 2>> "$ERROR_LOG"
            fi
        done
    fi

    # --- df_queue (ccm_queue_data, cs_queue_data, iom_queue_data) ---
    if [ -d "$SRC/df_queue" ]; then
        mkdir -p "$DST/df_queue"
        for data_file in "$SRC/df_queue"/*; do
            if [ -f "$data_file" ]; then
                filename=$(basename "$data_file")
                echo "  Parsing $data_file..."
                python3 parsers/liuxiu_df_queue_parser.py "$data_file" > "$DST/df_queue/${filename}_parsed.json" 2>> "$ERROR_LOG"
            fi
        done
    fi

    # --- df_data_stream (7 files) ---
    if [ -d "$SRC/df_data_stream" ]; then
        mkdir -p "$DST/df_data_stream"
        for data_file in "$SRC/df_data_stream"/*; do
            if [ -f "$data_file" ]; then
                filename=$(basename "$data_file")
                echo "  Parsing $data_file..."
                python3 parsers/liuxiu_df_data_stream_parser.py "$data_file" > "$DST/df_data_stream/${filename}_parsed.json" 2>> "$ERROR_LOG"
            fi
        done
    fi

    # --- df_detail_lat (3 files) ---
    if [ -d "$SRC/df_detail_lat" ]; then
        mkdir -p "$DST/df_detail_lat"
        for data_file in "$SRC/df_detail_lat"/*; do
            if [ -f "$data_file" ]; then
                filename=$(basename "$data_file")
                echo "  Parsing $data_file..."
                python3 parsers/liuxiu_df_detail_lat_parser.py "$data_file" > "$DST/df_detail_lat/${filename}_parsed.json" 2>> "$ERROR_LOG"
            fi
        done
    fi

    echo ""
done

echo "All files parsed. Results in $RESULTS_ROOT/"

if [ -s "$ERROR_LOG" ]; then
    echo ""
    echo "Errors occurred during parsing:"
    cat "$ERROR_LOG"
fi
