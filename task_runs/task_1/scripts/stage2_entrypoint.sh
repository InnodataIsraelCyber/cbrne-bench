#!/bin/bash
set -e

echo "Stage 2: RFdiffusion2 Scaffold Generation"
echo "=========================================="

mkdir -p "$DATA_OUTPUT"

python3 /workspace/stage2_scaffolding.py

echo "Stage 2 Complete: Generated 10 protein scaffolds"
