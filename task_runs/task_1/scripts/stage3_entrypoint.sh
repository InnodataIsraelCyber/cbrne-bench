#!/bin/bash
set -e

echo "Stage 3: ProteinMPNN Sequence Design"
echo "====================================="

# Wait for stage 2 to complete
echo "Waiting for stage 2 scaffolds..."
MAX_WAIT=300
ELAPSED=0
while [ $ELAPSED -lt $MAX_WAIT ]; do
    if [ -f "$DATA_INPUT/manifest.json" ]; then
        echo "Stage 2 manifest found, proceeding"
        break
    fi
    sleep 2
    ELAPSED=$((ELAPSED + 2))
    if [ $((ELAPSED % 20)) -eq 0 ]; then
        echo "Still waiting... ($ELAPSED/$MAX_WAIT seconds)"
    fi
done

mkdir -p "$DATA_OUTPUT"

python3 /workspace/stage3_design.py

echo "Stage 3 Complete: Generated 160+ designed sequences"
