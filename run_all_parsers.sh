#!/bin/bash

export PYTHONPATH=$PYTHONPATH:.

echo "Running all parser scripts..."

# Define parser-to-data mapping
declare -A parser_map
parser_map["parsers/df_queue_parser.py"]="data/df_queue"
parser_map["parsers/mem_lat_parser.py"]="data/ccm_to_mem_lat"
parser_map["parsers/df_data_stream_parser.py"]="data/df_data_stream"
parser_map["parsers/df_detail_lat_parser.py"]="data/df_detail_lat"

# Map specific parsers to files without extensions
declare -A file_parser_map
file_parser_map["data/di_data"]="parsers/di_data_parser.py"
file_parser_map["data/iom_data"]="parsers/iom_data_parser.py"
file_parser_map["data/cm_data"]="parsers/cm_data_parser.py"

# Clear previous results and error log
rm -f results/*.json
rm -f error.log
touch error.log

# Function to run a parser on all files in a directory
run_parser() {
    local parser_script=$1
    local data_dir=$2

    for data_file in "$data_dir"/*; do
        if [ -f "$data_file" ]; then
            local filename=$(basename "$data_file")
            local filename_no_ext="${filename%.*}"
            local output_file="results/${filename_no_ext}_parsed.json"
            echo "Parsing $data_file with $parser_script..."
            python3 "$parser_script" "$data_file" > "$output_file" 2>> error.log
            if [ $? -ne 0 ]; then
                echo "Failed to parse $data_file" >> error.log
                echo "---" >> error.log
            fi
        fi
    done
}

# Iterate over the directory map and run parsers
for parser in "${!parser_map[@]}"; do
    run_parser "$parser" "${parser_map[$parser]}"
done

# Iterate over the file map and run parsers
for data_file in "${!file_parser_map[@]}"; do
    parser_script="${file_parser_map[$data_file]}"
    filename=$(basename "$data_file")
    output_file="results/${filename}_parsed.json"
    echo "Parsing $data_file with $parser_script..."
    python3 "$parser_script" "$data_file" > "$output_file" 2>> error.log
    if [ $? -ne 0 ]; then
        echo "Failed to parse $data_file" >> error.log
        echo "---" >> error.log
    fi
done

echo "All files parsed. Results are in the 'results' directory."

# Report errors if any
if [ -s error.log ]; then
    echo ""
    echo "Errors occurred during parsing:"
    cat error.log
fi
