#!/bin/bash
set -e

echo "Stage 4: DNA Chisel Codon Optimization"
echo "======================================="

# Wait for stage 3 to complete
echo "Waiting for stage 3 sequences..."
MAX_WAIT=300
ELAPSED=0
while [ $ELAPSED -lt $MAX_WAIT ]; do
    if [ -f "$DATA_INPUT/manifest.json" ]; then
        echo "Stage 3 manifest found, proceeding"
        break
    fi
    sleep 2
    ELAPSED=$((ELAPSED + 2))
done

mkdir -p "$DATA_OUTPUT"

python3 /workspace/stage4_codon_optimize.py

echo "Stage 4 Complete: Generated codon-optimized DNA sequences"
