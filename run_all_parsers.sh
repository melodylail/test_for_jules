#!/bin/bash

# Create the results directory if it doesn't exist
mkdir -p results
# Create a log file for errors
rm -f error.log

# Find all files in the data directory
find data -type f | while read filepath; do
    # Determine which parser to use
    if [[ "$filepath" == *"ccm_to_mem_lat"* ]]; then
        parser="parsers/mem_lat_parser.py"
    elif [[ "$filepath" == *"df_queue"* ]]; then
        parser="parsers/df_queue_parser.py"
    elif [[ "$filepath" == *"df_data_stream"* ]]; then
        parser="parsers/df_data_stream_parser.py"
    elif [[ "$filepath" == *"df_detail_lat"* ]]; then
        parser="parsers/df_detail_lat_parser.py"
    elif [[ "$filepath" == *"cm_data"* ]]; then
        parser="parsers/cm_data_parser.py"
    elif [[ "$filepath" == *"di_data"* ]]; then
        parser="parsers/di_data_parser.py"
    elif [[ "$filepath" == *"iom_data"* ]]; then
        parser="parsers/iom_data_parser.py"
    else
        echo "No parser found for $filepath. Skipping."
        continue
    fi

    # Construct the output filename
    filename=$(basename "$filepath")
    output_filename="results/${filename%.*}_parsed.json"

    # Run the parser and save the output
    echo "Parsing $filepath with $parser..."
    if ! python3 "$parser" "$filepath" > "$output_filename" 2>>error.log; then
        echo "Failed to parse $filepath" >> error.log
        echo "---" >> error.log
    fi
done

echo "All files parsed. Results are in the 'results' directory."

if [ -s error.log ]; then
    echo
    echo "Errors occurred during parsing:"
    cat error.log
fi
