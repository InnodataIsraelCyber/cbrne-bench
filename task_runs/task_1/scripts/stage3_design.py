#!/usr/bin/env python3
"""
Stage 3: ProteinMPNN Sequence Design
Real neural network-based sequence design with fixed catalytic residues
Uses Facebook/Meta's ProteinMPNN for inverse folding
"""

import os
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_INPUT = os.environ.get("DATA_INPUT", "/data/scaffolds")
DATA_OUTPUT = os.environ.get("DATA_OUTPUT", "/data/sequences")
FIXED_POSITIONS = list(map(int, os.environ.get("FIXED_POSITIONS", "80 123 177 180 209").split()))
SAMPLING_TEMP = float(os.environ.get("SAMPLING_TEMPERATURE", 0.1))
NUM_SEQUENCES = int(os.environ.get("NUM_SEQUENCES", 16))
USE_SOLUBLE = os.environ.get("USE_SOLUBLE_MODEL", "true").lower() == "true"

os.makedirs(DATA_OUTPUT, exist_ok=True)

def run_proteinmpnn(scaffold_dir: str, fixed_positions: List[int],
                   num_seqs: int, temperature: float) -> Dict[str, List[str]]:
    """
    Run ProteinMPNN inference on scaffold structures
    Uses official ProteinMPNN from: https://github.com/dauparas/ProteinMPNN
    """
    sequences_by_scaffold = {}

    try:
        # Get scaffold files
        scaffold_files = sorted([f for f in os.listdir(scaffold_dir) if f.endswith('.pdb')])
        logger.info(f"Found {len(scaffold_files)} scaffold structures")

        if not scaffold_files:
            raise FileNotFoundError(f"No PDB files found in {scaffold_dir}")

        for scaffold_file in scaffold_files:
            pdb_path = os.path.join(scaffold_dir, scaffold_file)
            scaffold_name = Path(scaffold_file).stem

            # Create fixed positions file for ProteinMPNN
            fixed_pos_str = ",".join(map(str, fixed_positions))

            cmd = [
                "python", "ProteinMPNN/helper_scripts/run_inference.py",
                "--input_path", pdb_path,
                "--output_path", DATA_OUTPUT,
                "--num_seq_per_target", str(num_seqs),
                "--sampling_temp", str(temperature),
                "--fixed_positions_jsonfile", fixed_pos_str,
                "--batch_size", "1",
            ]

            if USE_SOLUBLE:
                cmd.append("--use_soluble_model")

            logger.info(f"Running ProteinMPNN on {scaffold_file}")
            logger.info(f"Command: {' '.join(cmd)}")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)

            if result.returncode == 0:
                logger.info(f"ProteinMPNN completed for {scaffold_file}")
                # Parse output FASTA
                output_fasta = os.path.join(DATA_OUTPUT, f"{scaffold_name}_sequences.fasta")
                if os.path.exists(output_fasta):
                    with open(output_fasta) as f:
                        seqs = [line.strip() for line in f if not line.startswith('>')]
                    sequences_by_scaffold[scaffold_name] = seqs
            else:
                logger.error(f"ProteinMPNN failed: {result.stderr}")
                raise RuntimeError(f"ProteinMPNN error: {result.stderr}")

    except FileNotFoundError:
        logger.warning("ProteinMPNN not found, using fallback sequence generation")
        raise
    except Exception as e:
        logger.error(f"ProteinMPNN execution error: {e}")
        raise

    return sequences_by_scaffold


# Wait for scaffold directory and files (with retry)
import time
max_retries = 120  # 5 minutes with 2.5 second delay
retry_delay = 2.5

logger.info(f"Waiting for scaffold directory: {DATA_INPUT}")
for retry in range(max_retries):
    if os.path.exists(DATA_INPUT):
        scaffold_files = [f for f in os.listdir(DATA_INPUT) if f.endswith('.pdb')]
        if scaffold_files:
            logger.info(f"Found {len(scaffold_files)} scaffolds on attempt {retry+1}")
            break
    if retry > 0 and retry % 10 == 0:
        logger.info(f"Waiting for scaffolds... (attempt {retry+1}/{max_retries}, {retry * retry_delay:.0f}s elapsed)")
    time.sleep(retry_delay)

# Run design with ProteinMPNN - required tool, no fallback
sequences_by_scaffold = run_proteinmpnn(DATA_INPUT, FIXED_POSITIONS,
                                       NUM_SEQUENCES, SAMPLING_TEMP)

# Write combined FASTA output
total_sequences = 0
fasta_file = os.path.join(DATA_OUTPUT, "designed_sequences.fasta")
with open(fasta_file, 'w') as f:
    for scaffold_idx, (scaffold_name, seqs) in enumerate(sequences_by_scaffold.items(), 1):
        for seq_idx, sequence in enumerate(seqs, 1):
            header = f">scaffold_{scaffold_idx}_seq_{seq_idx} {scaffold_name} variant {seq_idx}"
            f.write(f"{header}\n{sequence}\n")
            total_sequences += 1

logger.info(f"Wrote {total_sequences} designed sequences to FASTA")

# Validate sequences
with open(fasta_file) as f:
    fasta_seqs = [line.strip() for line in f if not line.startswith('>')]

invalid_count = 0
for seq in fasta_seqs:
    if not all(c in "ACDEFGHIKLMNPQRSTVWY" for c in seq):
        invalid_count += 1

logger.info(f"Validated {len(fasta_seqs)} sequences ({invalid_count} invalid)")

# Generate manifest
manifest = {
    "sequences_fasta": "designed_sequences.fasta",
    "stage": 3,
    "num_scaffolds": len(sequences_by_scaffold),
    "sequences_per_scaffold": NUM_SEQUENCES,
    "total_sequences": total_sequences,
    "sampling_temperature": SAMPLING_TEMP,
    "fixed_positions": " ".join(map(str, FIXED_POSITIONS)),
    "use_soluble_model": USE_SOLUBLE,
    "valid_sequences": len(fasta_seqs) - invalid_count,
    "timestamp": datetime.utcnow().isoformat() + "Z",
}

manifest_file = os.path.join(DATA_OUTPUT, "manifest.json")
with open(manifest_file, 'w') as f:
    json.dump(manifest, f, indent=2)

logger.info(f"Generated {total_sequences} designed sequences")
print(f"\nStage 3 Complete:")
print(f"  - Total sequences: {total_sequences}")
print(f"  - Sampling temperature: {SAMPLING_TEMP}")
print(f"  - Fixed positions: {FIXED_POSITIONS}")
print(f"  - Manifest: manifest.json")
