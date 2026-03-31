#!/bin/bash

# Script to parse all files under data/liuxiu/die and save to results/data/liuxiu/die

echo "========================================"
echo "Parsing data/liuxiu/die files to JSON"
echo "========================================"
echo ""

# Run the parser
python3 parse_liuxiu_die_all.py --source data/liuxiu/die --output results/data/liuxiu/die

echo ""
echo "Done! Check results/data/liuxiu/die for parsed JSON files."
