#!/bin/bash

# Create the results directory if it doesn't exist
mkdir -p results

# Find all files in the data directory
find data -type f | while read filepath; do
    # Determine which parser to use
    if [[ "$filepath" == *"ccm_to_mem_lat"* ]]; then
        parser="parsers/mem_lat_parser.py"
    elif [[ "$filepath" == *"df_"* ]]; then
        parser="parsers/hierarchical_parser.py"
    else
        parser="parsers/simple_tabular_parser.py"
    fi

    # Construct the output filename
    filename=$(basename "$filepath")
    output_filename="results/${filename%.*}_parsed.json"

    # Run the parser and save the output
    echo "Parsing $filepath with $parser..."
    python3 "$parser" "$filepath" > "$output_filename"
done

echo "All files parsed. Results are in the 'results' directory."
