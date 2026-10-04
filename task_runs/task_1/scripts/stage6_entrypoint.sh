#!/bin/bash
set -e

echo "Stage 6: In Silico Cloning Simulation"
echo "====================================="

mkdir -p "$DATA_OUTPUT"

python3 /workspace/stage6_simulate_cloning.py

echo "Stage 6 Complete: Generated assembled plasmids in GenBank format"
