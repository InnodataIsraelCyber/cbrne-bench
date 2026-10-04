#!/bin/bash
set -e

echo "Stage 6: In Silico Cloning Simulation"
echo "====================================="

# Wait for stage 5 to complete
echo "Waiting for stage 5 plasmid backbones..."
MAX_WAIT=300
ELAPSED=0
while [ $ELAPSED -lt $MAX_WAIT ]; do
    if [ -f "/data/plasmids/manifest.json" ]; then
        echo "Stage 5 manifest found, proceeding"
        break
    fi
    sleep 2
    ELAPSED=$((ELAPSED + 2))
done

mkdir -p "$DATA_OUTPUT"

python3 /workspace/stage6_simulate_cloning.py

echo "Stage 6 Complete: Generated assembled plasmids in GenBank format"
