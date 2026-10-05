#!/bin/bash
set -e

echo "Stage 2: RFdiffusion2 Scaffold Generation"
echo "=========================================="

# Wait for stage 1 to complete
echo "Waiting for stage 1 structures..."
MAX_WAIT=300
ELAPSED=0
while [ $ELAPSED -lt $MAX_WAIT ]; do
    if [ -f "$DATA_INPUT/manifest.json" ]; then
        echo "Stage 1 manifest found, proceeding"
        break
    fi
    sleep 2
    ELAPSED=$((ELAPSED + 2))
done

mkdir -p "$DATA_OUTPUT"

python3 /workspace/stage2_scaffolding.py

echo "Stage 2 Complete: Generated 10 protein scaffolds"
