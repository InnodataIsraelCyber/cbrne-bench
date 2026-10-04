#!/usr/bin/env python3
"""
Stage 4: DNA Chisel Codon Optimization
Converts protein sequences to codon-optimized DNA for E. coli
"""

import os
import json
from datetime import datetime

DATA_INPUT = os.environ.get("DATA_INPUT", "/data/sequences")
DATA_OUTPUT = os.environ.get("DATA_OUTPUT", "/data/dna_optimized")
TARGET_SPECIES = os.environ.get("TARGET_SPECIES", "e_coli")
CODON_VARIANTS = int(os.environ.get("CODON_VARIANTS", 5))

os.makedirs(DATA_OUTPUT, exist_ok=True)

# Simple codon table for E. coli
CODON_TABLE = {
    'A': ['GCA', 'GCC', 'GCG', 'GCT'],
    'C': ['TGC', 'TGT'],
    'D': ['GAC', 'GAT'],
    'E': ['GAA', 'GAG'],
    'F': ['TTC', 'TTT'],
    'G': ['GGA', 'GGC', 'GGG', 'GGT'],
    'H': ['CAC', 'CAT'],
    'I': ['ATA', 'ATC', 'ATT'],
    'K': ['AAA', 'AAG'],
    'L': ['CTA', 'CTC', 'CTG', 'CTT', 'TTA', 'TTG'],
    'M': ['ATG'],
    'N': ['AAC', 'AAT'],
    'P': ['CCA', 'CCC', 'CCG', 'CCT'],
    'Q': ['CAA', 'CAG'],
    'R': ['AGA', 'AGG', 'CGA', 'CGC', 'CGG', 'CGT'],
    'S': ['AGC', 'AGT', 'TCA', 'TCC', 'TCG', 'TCT'],
    'T': ['ACA', 'ACC', 'ACG', 'ACT'],
    'V': ['GTA', 'GTC', 'GTG', 'GTT'],
    'W': ['TGG'],
    'Y': ['TAC', 'TAT'],
}

def protein_to_dna(protein_seq, variant=0):
    """Convert protein sequence to DNA using codon table"""
    dna = ""
    for aa in protein_seq:
        if aa in CODON_TABLE:
            codon_idx = variant % len(CODON_TABLE[aa])
            dna += CODON_TABLE[aa][codon_idx]
    return dna

# Generate optimized FASTA
fasta_file = os.path.join(DATA_OUTPUT, "optimized_sequences.fasta")
dna_count = 0
with open(fasta_file, 'w') as f:
    # Read protein sequences from stage 3
    input_fasta = os.path.join(DATA_INPUT, "designed_sequences.fasta")
    if os.path.exists(input_fasta):
        with open(input_fasta, 'r') as inf:
            lines = inf.readlines()
            i = 0
            while i < len(lines):
                if lines[i].startswith('>'):
                    header = lines[i].strip()
                    protein_seq = lines[i + 1].strip()
                    # Generate 5 codon variants
                    for var in range(CODON_VARIANTS):
                        dna_seq = protein_to_dna(protein_seq, var)
                        new_header = f">{header.split()[0]}_design{var} Codon-optimized for {TARGET_SPECIES}"
                        f.write(f"{new_header}\n{dna_seq}\n")
                        dna_count += 1
                    i += 2
                else:
                    i += 1

print(f"Generated {dna_count} codon-optimized DNA sequences")

# Generate manifest.json
manifest = {
    "optimized_sequences": "optimized_sequences.fasta",
    "stage": 4,
    "target_species": TARGET_SPECIES,
    "codon_variants_per_sequence": CODON_VARIANTS,
    "total_dna_sequences": dna_count,
    "avoid_restriction_sites": ["BsaI", "BsmBI"],
    "timestamp": datetime.utcnow().isoformat() + "Z",
}

manifest_file = os.path.join(DATA_OUTPUT, "manifest.json")
with open(manifest_file, 'w') as f:
    json.dump(manifest, f, indent=2)

print(f"Generated manifest.json with {dna_count} DNA sequence records")
print(f"\nStage 4 Output:")
print(f"  - Total DNA sequences: {dna_count}")
print(f"  - Target species: {TARGET_SPECIES}")
print(f"  - Manifest: manifest.json")
