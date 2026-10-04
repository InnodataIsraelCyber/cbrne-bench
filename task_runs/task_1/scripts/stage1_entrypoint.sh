#!/bin/bash
set -e

echo "Stage 1: Data Preparation & Structure Conversion"
echo "=================================================="

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Copy PDB files from input
if [ -d "/workspace/input_structures" ]; then
    cp /workspace/input_structures/*.cif "$OUTPUT_DIR/" 2>/dev/null || true
fi

# Run Python script to convert and process
python3 /workspace/stage1_processing.py

echo "Stage 1 Complete: Generated manifest.json and residue annotations"
