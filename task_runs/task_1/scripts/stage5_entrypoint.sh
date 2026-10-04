#!/bin/bash
set -e

echo "Stage 5: PlasmidGPT Backbone Generation"
echo "========================================"

mkdir -p "$DATA_OUTPUT"

python3 /workspace/stage5_plasmid_generate.py

echo "Stage 5 Complete: Generated plasmid backbones"
