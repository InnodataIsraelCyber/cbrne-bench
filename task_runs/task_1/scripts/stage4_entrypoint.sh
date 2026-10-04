#!/bin/bash
set -e

echo "Stage 4: DNA Chisel Codon Optimization"
echo "======================================="

mkdir -p "$DATA_OUTPUT"

python3 /workspace/stage4_codon_optimize.py

echo "Stage 4 Complete: Generated codon-optimized DNA sequences"
