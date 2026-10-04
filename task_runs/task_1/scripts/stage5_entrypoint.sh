#!/bin/bash
set -e

echo "Stage 5: PlasmidGPT Backbone Generation"
echo "========================================"

# Wait for stage 4 to complete
echo "Waiting for stage 4 codon-optimized sequences..."
MAX_WAIT=300
ELAPSED=0
while [ $ELAPSED -lt $MAX_WAIT ]; do
    if [ -f "$DATA_INPUT/manifest.json" ]; then
        echo "Stage 4 manifest found, proceeding"
        break
    fi
    sleep 2
    ELAPSED=$((ELAPSED + 2))
done

mkdir -p "$DATA_OUTPUT"

python3 /workspace/stage5_plasmid_generate.py

echo "Stage 5 Complete: Generated plasmid backbones"
