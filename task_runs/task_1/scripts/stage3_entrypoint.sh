#!/bin/bash
set -e

echo "Stage 3: ProteinMPNN Sequence Design"
echo "====================================="

mkdir -p "$DATA_OUTPUT"

python3 /workspace/stage3_design.py

echo "Stage 3 Complete: Generated 160+ designed sequences"
