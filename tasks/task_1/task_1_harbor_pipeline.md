# Task 1: Protein Engineering Pipeline with Docker & Harbor

This is a containerized version of the protein engineering workflow, where each computational stage runs in its own Docker container and images are managed through Harbor container registry.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Harbor Registry                          │
│          (Central image repository & management)             │
└─────────────────────────────────────────────────────────────┘
                              ↑
        ┌─────────────────────┼─────────────────────┐
        ↓                     ↓                     ↓
   ┌─────────────┐      ┌──────────────┐      ┌──────────────┐
   │   Stage 1   │      │   Stage 2    │      │   Stage 3    │
   │  Data Prep  │ →    │ RFdiffusion2 │ →    │ ProteinMPNN  │
   └─────────────┘      └──────────────┘      └──────────────┘
        ↓                     ↓                     ↓
   ┌─────────────┐      ┌──────────────┐      ┌──────────────┐
   │   Stage 4   │      │   Stage 5    │      │   Stage 6    │
   │DNA Chisel   │ ←    │ PlasmidGPT   │ ←    │  Purification│
   └─────────────┘      └──────────────┘      └──────────────┘
        ↓                     ↓                     ↓
   Docker Volume Mounts ← Shared Data Directory ← Output Files
```

---

## Setup: Harbor Registry Configuration

### 1. Harbor Installation & Configuration

```bash
# 1.1 Pull Harbor installer
wget https://github.com/goharbor/harbor/releases/download/v2.8.0/harbor-online-installer-v2.8.0.tgz
tar xzvf harbor-online-installer-v2.8.0.tgz
cd harbor

# 1.2 Configure harbor.yml
# Edit the following in harbor.yml:
# - hostname: harbor.innodata.local  (or your registry domain)
# - http.port: 80
# - https.port: 443
# - harbor_admin_password: <secure-password>

# 1.3 Install Harbor
sudo ./install.sh --with-trivy --with-notary

# 1.4 Verify Harbor is running
docker-compose ps
```

### 2. Harbor Projects & Authentication

```bash
# 2.1 Create a new project for protein engineering
# Via Harbor UI or CLI:
curl -u admin:<password> -X POST \
  "https://harbor.innodata.local/api/v2.0/projects" \
  -H "Content-Type: application/json" \
  -d '{"project_name":"protein-engineering","public":false}'

# 2.2 Create robot account for automated pushes
curl -u admin:<password> -X POST \
  "https://harbor.innodata.local/api/v2.0/robotaccounts" \
  -H "Content-Type: application/json" \
  -d '{
    "name":"build-bot",
    "description":"Automated build account",
    "access":[{
      "resource":"/project/1/repository",
      "action":["pull","push"]
    }]
  }'

# 2.3 Login locally and verify
docker login harbor.innodata.local
# Username: robot$protein-engineering+build-bot
# Password: <generated-token>

docker pull harbor.innodata.local/protein-engineering/base:latest
```

---

## Stage 1: Data Preparation & Structure Download

### Dockerfile: `Dockerfile.stage1`

```dockerfile
FROM python:3.10-slim

WORKDIR /workspace

# Install BLAST and bioinformatics tools
RUN apt-get update && apt-get install -y \
    ncbi-blast+ \
    wget \
    curl \
    git \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    biopython==1.81 \
    pydantic==2.0 \
    requests==2.31.0

# Copy PDB downloader script
COPY scripts/download_pdb.py /workspace/
COPY scripts/extract_residues.py /workspace/

# Set environment variables
ENV PDB_IDS="1IFS 1UQ4 2P8N"
ENV OUTPUT_DIR="/data/structures"

# Create output directory with proper permissions
RUN mkdir -p $OUTPUT_DIR

# Entrypoint script
COPY scripts/stage1_entrypoint.sh /workspace/
RUN chmod +x /workspace/stage1_entrypoint.sh

ENTRYPOINT ["/workspace/stage1_entrypoint.sh"]
```

### Script: `scripts/stage1_entrypoint.sh`

```bash
#!/bin/bash
set -e

echo "=== Stage 1: Data Preparation & Structure Download ==="
echo "Downloading PDB structures: $PDB_IDS"

# Step 1.1: Download PDB files
for pdb_id in $PDB_IDS; do
  echo "Fetching $pdb_id..."
  python /workspace/download_pdb.py \
    --pdb_id $pdb_id \
    --output_dir $OUTPUT_DIR
done

# Step 1.2: Extract catalytic residues
echo "Extracting residue annotations..."
python /workspace/extract_residues.py \
  --input_dir $OUTPUT_DIR \
  --output_file $OUTPUT_DIR/residues.csv

# Step 1.3: Validate structures
echo "Validating PDB structures..."
for pdb_file in $OUTPUT_DIR/*.pdb; do
  python -c "
from Bio.PDB import PDBParser
parser = PDBParser(QUIET=True)
structure = parser.get_structure('test', '$pdb_file')
print(f'✓ {pdb_file} is valid')
"
done

# Step 1.4: Create manifest for next stage
cat > $OUTPUT_DIR/manifest.json << EOF
{
  "pdb_files": ["1IFS.pdb", "1UQ4.pdb", "2P8N.pdb"],
  "residues": "residues.csv",
  "stage": 1,
  "timestamp": "$(date -Iseconds)"
}
EOF

echo "=== Stage 1 Complete ==="
echo "Output: $OUTPUT_DIR"
ls -la $OUTPUT_DIR
```

### Script: `scripts/download_pdb.py`

```python
#!/usr/bin/env python3
import os
import sys
import requests
from pathlib import Path

def download_pdb(pdb_id, output_dir):
    """Download PDB structure from RCSB."""
    url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
    output_path = Path(output_dir) / f"{pdb_id}.pdb"
    
    print(f"Downloading {pdb_id} from {url}...")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with open(output_path, 'w') as f:
            f.write(response.text)
        
        print(f"✓ Saved to {output_path}")
        return True
    except Exception as e:
        print(f"✗ Failed to download {pdb_id}: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdb_id", required=True)
    parser.add_argument("--output_dir", required=True)
    args = parser.parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)
    success = download_pdb(args.pdb_id, args.output_dir)
    sys.exit(0 if success else 1)
```

### Script: `scripts/extract_residues.py`

```python
#!/usr/bin/env python3
import csv
import os
from pathlib import Path
from Bio.PDB import PDBParser

RESIDUES_OF_INTEREST = {
    "Glu177": {"name": "GLU", "number": 177, "role": "Key catalytic residue; stabilizes oxycarbonium ion"},
    "Arg180": {"name": "ARG", "number": 180, "role": "Protonates adenine at N3; transition state stabilization"},
    "Tyr80": {"name": "TYR", "number": 80, "role": "Stacks on substrate adenine ring"},
    "Tyr123": {"name": "TYR", "number": 123, "role": "Stacks on opposite side of adenine"},
    "Asn209": {"name": "ASN", "number": 209, "role": "Substrate binding"},
}

def extract_residues(input_dir, output_file):
    """Extract catalytic residue information from PDB files."""
    parser = PDBParser(QUIET=True)
    results = []
    
    for pdb_file in Path(input_dir).glob("*.pdb"):
        print(f"Processing {pdb_file.name}...")
        try:
            structure = parser.get_structure("protein", str(pdb_file))
            model = structure[0]
            chain = model["A"]
            
            for res_label, res_info in RESIDUES_OF_INTEREST.items():
                res_num = res_info["number"]
                try:
                    residue = chain[res_num]
                    results.append({
                        "PDB": pdb_file.stem.upper(),
                        "Residue": res_label,
                        "Type": res_info["name"],
                        "Position": res_num,
                        "Role": res_info["role"],
                        "Present": "Yes"
                    })
                except KeyError:
                    results.append({
                        "PDB": pdb_file.stem.upper(),
                        "Residue": res_label,
                        "Type": res_info["name"],
                        "Position": res_num,
                        "Role": res_info["role"],
                        "Present": "No"
                    })
        except Exception as e:
            print(f"Warning: Could not parse {pdb_file}: {e}")
    
    # Write CSV
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys() if results else [])
        writer.writeheader()
        writer.writerows(results)
    
    print(f"✓ Extracted residue data to {output_file}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", required=True)
    parser.add_argument("--output_file", required=True)
    args = parser.parse_args()
    
    extract_residues(args.input_dir, args.output_file)
```

---

## Stage 2: RFdiffusion2 Scaffold Generation

### Dockerfile: `Dockerfile.stage2`

```dockerfile
FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    conda \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Clone RFdiffusion repository
RUN git clone https://github.com/jwolynes/RFdiffusion.git /workspace/RFdiffusion

WORKDIR /workspace/RFdiffusion

# Install conda environment
COPY environment_rfdiffusion.yml /workspace/
RUN conda env create -f /workspace/environment_rfdiffusion.yml

# Activate environment for subsequent RUN commands
SHELL ["conda", "run", "-n", "diffusion", "/bin/bash", "-c"]

# Download model weights
RUN mkdir -p /workspace/models && \
    cd /workspace/models && \
    wget https://example.com/RFdiffusion_model.tar.gz && \
    tar xzf RFdiffusion_model.tar.gz

# Copy configuration and scripts
COPY scripts/stage2_entrypoint.sh /workspace/
COPY scripts/run_rfdiffusion.py /workspace/

RUN chmod +x /workspace/stage2_entrypoint.sh

# Set environment
ENV PYTHONPATH=/workspace/RFdiffusion:$PYTHONPATH
ENV DATA_INPUT=/data/structures
ENV DATA_OUTPUT=/data/scaffolds

ENTRYPOINT ["/workspace/stage2_entrypoint.sh"]
```

### Script: `scripts/stage2_entrypoint.sh`

```bash
#!/bin/bash
set -e

echo "=== Stage 2: RFdiffusion2 Scaffold Generation ==="

# Activate conda environment
source /opt/conda/etc/profile.d/conda.sh
conda activate diffusion

# Define catalytic residues and motif parameters
CATALYTIC_RESIDUES="A177 A180 A80 A123 A209"
CONTIG_SPEC="A177-177/0 50-150"
INPUT_PDB="$DATA_INPUT/1IFS.pdb"
OUTPUT_DIR="$DATA_OUTPUT"

mkdir -p "$OUTPUT_DIR"

echo "Running RFdiffusion with parameters:"
echo "  Input PDB: $INPUT_PDB"
echo "  Contig spec: $CONTIG_SPEC"
echo "  Hotspot residues: $CATALYTIC_RESIDUES"

# Run RFdiffusion
python /workspace/run_rfdiffusion.py \
  --input_pdb "$INPUT_PDB" \
  --contig "$CONTIG_SPEC" \
  --hotspot_res $CATALYTIC_RESIDUES \
  --num_designs 10 \
  --model_weights /workspace/models \
  --output_dir "$OUTPUT_DIR"

# Create manifest for next stage
cat > "$OUTPUT_DIR/manifest.json" << EOF
{
  "scaffolds": "scaffolds_*.pdb",
  "stage": 2,
  "num_designs": 10,
  "catalytic_residues": "$CATALYTIC_RESIDUES",
  "contig_spec": "$CONTIG_SPEC",
  "timestamp": "$(date -Iseconds)"
}
EOF

echo "=== Stage 2 Complete ==="
ls -la "$OUTPUT_DIR"
```

### Script: `scripts/run_rfdiffusion.py`

```python
#!/usr/bin/env python3
import os
import sys
import subprocess
import json
from pathlib import Path

def run_rfdiffusion(input_pdb, contig, hotspot_res, num_designs, model_weights, output_dir):
    """Execute RFdiffusion sampling."""
    
    print(f"Initializing RFdiffusion with input: {input_pdb}")
    
    # Construct command
    cmd = [
        "python", "-m", "rfdiffusion.run_diffusion",
        f"--input_pdb={input_pdb}",
        f"--contig={contig}",
        f"--hotspot_res={hotspot_res}",
        f"--num_designs={num_designs}",
        f"--model_weights_dir={model_weights}",
        f"--output_dir={output_dir}",
        "--inference_steps=50",
        "--inference_noise_level=1.0",
    ]
    
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        print("✓ RFdiffusion sampling completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ RFdiffusion failed: {e.stderr}", file=sys.stderr)
        return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_pdb", required=True)
    parser.add_argument("--contig", required=True)
    parser.add_argument("--hotspot_res", nargs="+", required=True)
    parser.add_argument("--num_designs", type=int, default=10)
    parser.add_argument("--model_weights", required=True)
    parser.add_argument("--output_dir", required=True)
    
    args = parser.parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)
    success = run_rfdiffusion(
        args.input_pdb,
        args.contig,
        " ".join(args.hotspot_res),
        args.num_designs,
        args.model_weights,
        args.output_dir
    )
    sys.exit(0 if success else 1)
```

---

## Stage 3: ProteinMPNN Sequence Design

### Dockerfile: `Dockerfile.stage3`

```dockerfile
FROM pytorch/pytorch:2.0-cuda12.1-runtime-ubuntu22.04

WORKDIR /workspace

RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    biopython==1.81 \
    numpy==1.24.0 \
    scipy==1.10.0 \
    pandas==1.5.0

# Clone ProteinMPNN
RUN git clone https://github.com/dauparas/ProteinMPNN /workspace/ProteinMPNN

WORKDIR /workspace/ProteinMPNN

# Copy scripts
COPY scripts/stage3_entrypoint.sh /workspace/
COPY scripts/stage3_design.py /workspace/

RUN chmod +x /workspace/stage3_entrypoint.sh

ENV FIXED_POSITIONS="80 123 177 180 209"
ENV DATA_INPUT=/data/scaffolds
ENV DATA_OUTPUT=/data/sequences
ENV SAMPLING_TEMP=0.1
ENV NUM_SEQUENCES=16

ENTRYPOINT ["/workspace/stage3_entrypoint.sh"]
```

### Script: `scripts/stage3_entrypoint.sh`

```bash
#!/bin/bash
set -e

echo "=== Stage 3: ProteinMPNN Sequence Design ==="

INPUT_DIR="$DATA_INPUT"
OUTPUT_DIR="$DATA_OUTPUT"
FIXED_POS="$FIXED_POSITIONS"

mkdir -p "$OUTPUT_DIR"

# Step 3.1: Parse scaffolds into JSONL format
echo "Parsing scaffolds..."
for scaffold in "$INPUT_DIR"/scaffolds_*.pdb; do
    if [ -f "$scaffold" ]; then
        echo "Processing $(basename $scaffold)..."
        python /workspace/ProteinMPNN/helper_scripts/parse_multiple_chains.py \
            --input_path "$scaffold" \
            --output_path "${OUTPUT_DIR}/$(basename $scaffold .pdb).jsonl"
    fi
done

# Step 3.2: Create fixed positions file
echo "Creating fixed positions constraints..."
python /workspace/scripts/stage3_design.py \
    --input_dir "$OUTPUT_DIR" \
    --output_dir "$OUTPUT_DIR" \
    --fixed_positions $FIXED_POS \
    --chain "A"

# Step 3.3: Run ProteinMPNN for sequence design
echo "Running ProteinMPNN design..."
for jsonl_file in "$OUTPUT_DIR"/*.jsonl; do
    if [ -f "$jsonl_file" ] && [[ ! "$jsonl_file" == *fixed* ]]; then
        basename="${jsonl_file%.jsonl}"
        echo "Designing for $(basename $jsonl_file)..."
        
        python /workspace/ProteinMPNN/protein_mpnn_run.py \
            --jsonl_path "$jsonl_file" \
            --fixed_positions_jsonl "${basename}_fixed.jsonl" \
            --out_folder "${OUTPUT_DIR}/$(basename $basename)_output" \
            --num_seq_per_target $NUM_SEQUENCES \
            --sampling_temp "$SAMPLING_TEMP" \
            --use_soluble_model
    fi
done

# Step 3.4: Aggregate results
echo "Aggregating sequences..."
python /workspace/scripts/aggregate_fasta.py \
    --input_dir "$OUTPUT_DIR" \
    --output_file "$OUTPUT_DIR/designed_sequences.fasta"

# Create manifest
cat > "$OUTPUT_DIR/manifest.json" << EOF
{
  "sequences_fasta": "designed_sequences.fasta",
  "stage": 3,
  "sampling_temperature": "$SAMPLING_TEMP",
  "fixed_positions": "$FIXED_POS",
  "num_sequences": "$NUM_SEQUENCES",
  "timestamp": "$(date -Iseconds)"
}
EOF

echo "=== Stage 3 Complete ==="
ls -la "$OUTPUT_DIR"
```

### Script: `scripts/stage3_design.py`

```python
#!/usr/bin/env python3
import json
import os
from pathlib import Path

def create_fixed_positions(input_dir, output_dir, fixed_positions, chain):
    """Create fixed positions constraint files for ProteinMPNN."""
    
    fixed_pos_list = list(map(int, fixed_positions.split()))
    
    for jsonl_file in Path(input_dir).glob("*.jsonl"):
        if "fixed" in jsonl_file.name:
            continue
        
        print(f"Creating fixed positions for {jsonl_file.name}...")
        
        with open(jsonl_file, 'r') as f:
            data = json.load(f)
        
        # Create fixed positions mapping
        fixed_dict = {
            "fixed_positions": [
                [f"{chain}{pos}"] for pos in fixed_pos_list
            ]
        }
        
        output_file = jsonl_file.parent / f"{jsonl_file.stem}_fixed.jsonl"
        with open(output_file, 'w') as f:
            json.dump(fixed_dict, f)
        
        print(f"✓ Saved to {output_file}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", required=True)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--fixed_positions", required=True)
    parser.add_argument("--chain", default="A")
    
    args = parser.parse_args()
    create_fixed_positions(args.input_dir, args.output_dir, args.fixed_positions, args.chain)
```

---

## Stage 4: DNA Chisel Codon Optimization

### Dockerfile: `Dockerfile.stage4`

```dockerfile
FROM python:3.10-slim

WORKDIR /workspace

RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    dnachisel[reports]==3.20.27 \
    biopython==1.81 \
    pandas==1.5.0

COPY scripts/stage4_entrypoint.sh /workspace/
COPY scripts/stage4_codon_optimize.py /workspace/

RUN chmod +x /workspace/stage4_entrypoint.sh

ENV TARGET_SPECIES=e_coli
ENV DATA_INPUT=/data/sequences
ENV DATA_OUTPUT=/data/dna_optimized

ENTRYPOINT ["/workspace/stage4_entrypoint.sh"]
```

### Script: `scripts/stage4_entrypoint.sh`

```bash
#!/bin/bash
set -e

echo "=== Stage 4: DNA Codon Optimization with DNA Chisel ==="

INPUT_FILE="$DATA_INPUT/designed_sequences.fasta"
OUTPUT_DIR="$DATA_OUTPUT"
SPECIES="$TARGET_SPECIES"

mkdir -p "$OUTPUT_DIR"

if [ ! -f "$INPUT_FILE" ]; then
    echo "✗ Input FASTA file not found: $INPUT_FILE"
    exit 1
fi

echo "Input: $INPUT_FILE"
echo "Target species: $SPECIES"
echo "Output: $OUTPUT_DIR"

# Run codon optimization
python /workspace/scripts/stage4_codon_optimize.py \
    --input_fasta "$INPUT_FILE" \
    --output_dir "$OUTPUT_DIR" \
    --target_species "$SPECIES" \
    --num_designs 5

# Create manifest
cat > "$OUTPUT_DIR/manifest.json" << EOF
{
  "optimized_sequences": "optimized_sequences.fasta",
  "stage": 4,
  "target_species": "$SPECIES",
  "timestamp": "$(date -Iseconds)"
}
EOF

echo "=== Stage 4 Complete ==="
ls -la "$OUTPUT_DIR"
```

### Script: `scripts/stage4_codon_optimize.py`

```python
#!/usr/bin/env python3
import os
import sys
import random
from pathlib import Path
from Bio import SeqIO
from Bio.SeqUtils.CodonUsageFrequencies import ShortGenomeCodonUsage
from dnachisel import (
    DnaOptimizationProblem,
    EnforceTranslation,
    CodonOptimize,
    AvoidPattern,
)

def optimize_sequence(protein_seq, target_species, seed=42):
    """Optimize a protein sequence to DNA using DNA Chisel."""
    
    random.seed(seed)
    
    # Generate initial DNA sequence
    starting_dna = "".join([random.choice("ATCG") for _ in range(len(protein_seq) * 3)])
    
    # Define constraints
    constraint = EnforceTranslation(
        translation=protein_seq,
        genetic_table="Standard",
        start_codon="keep"
    )
    
    # Define objectives
    objectives = [
        CodonOptimize(species=target_species),
        AvoidPattern("BsaI_site"),
        AvoidPattern("BsmBI_site"),
    ]
    
    # Build optimization problem
    problem = DnaOptimizationProblem(
        sequence=starting_dna,
        constraints=[constraint],
        objectives=objectives
    )
    
    # Solve
    problem.resolve_constraints()
    problem.optimize()
    
    if problem.success:
        return str(problem.sequence)
    else:
        print(f"Warning: Optimization failed for sequence (length {len(protein_seq)})")
        return None

def process_fasta(input_fasta, output_dir, target_species, num_designs=5):
    """Process all sequences in a FASTA file."""
    
    success_count = 0
    fail_count = 0
    results = []
    
    for record in SeqIO.parse(input_fasta, "fasta"):
        print(f"Optimizing {record.id}...")
        
        protein_seq = str(record.seq).replace("*", "")  # Remove stop codon
        
        for i in range(num_designs):
            optimized_dna = optimize_sequence(protein_seq, target_species, seed=42 + i)
            
            if optimized_dna:
                results.append({
                    "id": f"{record.id}_design{i+1}",
                    "description": f"Codon-optimized for {target_species}",
                    "seq": optimized_dna
                })
                success_count += 1
            else:
                fail_count += 1
    
    # Write output FASTA
    output_file = Path(output_dir) / "optimized_sequences.fasta"
    with open(output_file, 'w') as f:
        for result in results:
            f.write(f">{result['id']} {result['description']}\n")
            # Wrap at 60 chars
            seq = result['seq']
            for i in range(0, len(seq), 60):
                f.write(seq[i:i+60] + "\n")
    
    print(f"\n✓ Optimization complete:")
    print(f"  Successes: {success_count}")
    print(f"  Failures: {fail_count}")
    print(f"  Output: {output_file}")
    
    return success_count, fail_count

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_fasta", required=True)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--target_species", default="e_coli")
    parser.add_argument("--num_designs", type=int, default=5)
    
    args = parser.parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)
    success, fail = process_fasta(
        args.input_fasta,
        args.output_dir,
        args.target_species,
        args.num_designs
    )
    sys.exit(0 if fail == 0 else 1)
```

---

## Stage 5: PlasmidGPT Backbone Generation

### Dockerfile: `Dockerfile.stage5`

```dockerfile
FROM python:3.10

WORKDIR /workspace

RUN pip install --no-cache-dir \
    tensorflow==2.13.0 \
    transformers==4.30.0 \
    biopython==1.81 \
    torch==2.0.0

# Clone or copy PlasmidGPT
RUN git clone https://github.com/lingxusb/PlasmidGPT /workspace/PlasmidGPT

WORKDIR /workspace/PlasmidGPT

# Download model weights (if needed)
# Model size may be large, consider using a volume mount instead

COPY scripts/stage5_entrypoint.sh /workspace/
COPY scripts/stage5_plasmid_generate.py /workspace/

RUN chmod +x /workspace/stage5_entrypoint.sh

ENV DATA_INPUT=/data/dna_optimized
ENV DATA_OUTPUT=/data/plasmids

ENTRYPOINT ["/workspace/stage5_entrypoint.sh"]
```

### Script: `scripts/stage5_entrypoint.sh`

```bash
#!/bin/bash
set -e

echo "=== Stage 5: PlasmidGPT Backbone Generation ==="

INPUT_FILE="$DATA_INPUT/optimized_sequences.fasta"
OUTPUT_DIR="$DATA_OUTPUT"

mkdir -p "$OUTPUT_DIR"

if [ ! -f "$INPUT_FILE" ]; then
    echo "✗ Input file not found: $INPUT_FILE"
    exit 1
fi

echo "Generating plasmid backbones..."

python /workspace/scripts/stage5_plasmid_generate.py \
    --input_fasta "$INPUT_FILE" \
    --output_dir "$OUTPUT_DIR" \
    --num_backbones 3

# Create manifest
cat > "$OUTPUT_DIR/manifest.json" << EOF
{
  "plasmid_backbones": "backbones_*.fasta",
  "stage": 5,
  "timestamp": "$(date -Iseconds)"
}
EOF

echo "=== Stage 5 Complete ==="
ls -la "$OUTPUT_DIR"
```

### Script: `scripts/stage5_plasmid_generate.py`

```python
#!/usr/bin/env python3
import os
from pathlib import Path
from Bio import SeqIO
from Bio.Seq import Seq

def generate_plasmid_backbone(seed_sequence, num_backbones=3):
    """Generate plasmid backbones using simulated PlasmidGPT."""
    
    # Simplified: in production, use actual PlasmidGPT model
    backbones = []
    
    base_components = {
        "ori": "TTTTGTAATACGACTCACTATAGGG",  # T7 promoter
        "amp_r": "GGTGCGCGGCAGCGACCCCCCCACGCGCCGGGCTGGCGCCCGGGCACCGGCGCGGCG",
        "terminator": "TTAAGAGACCGGCAGATCTGGAGGTGGCTATAAAGAGTCAGGAGTCTCCTTCC",
        "rbs": "AGGAGGTGAGGTGAGGGATCA",  # RBS
    }
    
    for i in range(num_backbones):
        # Assemble backbone
        backbone_seq = (
            base_components["ori"] +
            base_components["rbs"] +
            seed_sequence +
            base_components["terminator"] +
            base_components["amp_r"]
        )
        backbones.append({
            "id": f"plasmid_backbone_{i+1}",
            "seq": backbone_seq
        })
    
    return backbones

def process_sequences(input_fasta, output_dir, num_backbones=3):
    """Generate plasmids for all input sequences."""
    
    results = []
    
    for record in SeqIO.parse(input_fasta, "fasta"):
        print(f"Generating backbones for {record.id}...")
        
        seed_seq = str(record.seq)
        backbones = generate_plasmid_backbone(seed_seq, num_backbones)
        
        for backbone in backbones:
            results.append({
                "id": f"{record.id}_{backbone['id']}",
                "seq": backbone['seq']
            })
    
    # Write output
    output_file = Path(output_dir) / "backbones_generated.fasta"
    with open(output_file, 'w') as f:
        for result in results:
            f.write(f">{result['id']}\n")
            seq = result['seq']
            for i in range(0, len(seq), 60):
                f.write(seq[i:i+60] + "\n")
    
    print(f"✓ Generated {len(results)} plasmid backbones")
    print(f"  Output: {output_file}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_fasta", required=True)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--num_backbones", type=int, default=3)
    
    args = parser.parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)
    process_sequences(args.input_fasta, args.output_dir, args.num_backbones)
```

---

## Stage 6: In Silico Cloning Simulation

### Dockerfile: `Dockerfile.stage6`

```dockerfile
FROM python:3.10-slim

WORKDIR /workspace

RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    pydna==3.2.1 \
    biopython==1.81 \
    pandas==1.5.0

COPY scripts/stage6_entrypoint.sh /workspace/
COPY scripts/stage6_simulate_cloning.py /workspace/

RUN chmod +x /workspace/stage6_entrypoint.sh

ENV DATA_INPUT_GENE=/data/dna_optimized
ENV DATA_INPUT_BACKBONE=/data/plasmids
ENV DATA_OUTPUT=/data/assembled_plasmids

ENTRYPOINT ["/workspace/stage6_entrypoint.sh"]
```

### Script: `scripts/stage6_entrypoint.sh`

```bash
#!/bin/bash
set -e

echo "=== Stage 6: In Silico Cloning Simulation ==="

GENE_FILE="$DATA_INPUT_GENE/optimized_sequences.fasta"
BACKBONE_FILE="$DATA_INPUT_BACKBONE/backbones_generated.fasta"
OUTPUT_DIR="$DATA_OUTPUT"

mkdir -p "$OUTPUT_DIR"

if [ ! -f "$GENE_FILE" ] || [ ! -f "$BACKBONE_FILE" ]; then
    echo "✗ Input files not found"
    exit 1
fi

echo "Simulating in silico cloning..."
echo "  Genes: $GENE_FILE"
echo "  Backbones: $BACKBONE_FILE"

python /workspace/scripts/stage6_simulate_cloning.py \
    --gene_fasta "$GENE_FILE" \
    --backbone_fasta "$BACKBONE_FILE" \
    --output_dir "$OUTPUT_DIR" \
    --assembly_method "Gibson"

# Create manifest
cat > "$OUTPUT_DIR/manifest.json" << EOF
{
  "final_plasmids": "assembled_plasmids.gb",
  "stage": 6,
  "assembly_method": "Gibson",
  "timestamp": "$(date -Iseconds)"
}
EOF

echo "=== Stage 6 Complete ==="
ls -la "$OUTPUT_DIR"
```

### Script: `scripts/stage6_simulate_cloning.py`

```python
#!/usr/bin/env python3
import os
from pathlib import Path
from Bio import SeqIO
from pydna.dseqrecord import Dseqrecord
from pydna.assembly import assembly

def simulate_gibson_assembly(backbone_seq, insert_seq, name):
    """Simulate Gibson assembly using pydna."""
    
    # Convert to Dseqrecord objects
    backbone_record = Dseqrecord(backbone_seq, circular=True, name=name)
    insert_record = Dseqrecord(insert_seq, name=f"{name}_insert")
    
    # Simulate assembly (simplified)
    try:
        assembled = assembly([backbone_record, insert_record])
        if assembled:
            return assembled[0]
    except Exception as e:
        print(f"Warning: Assembly failed for {name}: {e}")
    
    return None

def process_cloning(gene_fasta, backbone_fasta, output_dir, assembly_method):
    """Simulate cloning of genes into backbones."""
    
    genes = {record.id: str(record.seq) for record in SeqIO.parse(gene_fasta, "fasta")}
    backbones = {record.id: str(record.seq) for record in SeqIO.parse(backbone_fasta, "fasta")}
    
    results = []
    
    for backbone_id, backbone_seq in backbones.items():
        for gene_id, gene_seq in genes.items():
            print(f"Cloning {gene_id} into {backbone_id}...")
            
            # Simulate assembly
            final_plasmid = simulate_gibson_assembly(backbone_seq, gene_seq, f"{gene_id}_{backbone_id}")
            
            if final_plasmid:
                results.append(final_plasmid)
    
    # Write GenBank output
    output_file = Path(output_dir) / "assembled_plasmids.gb"
    SeqIO.write(results, str(output_file), "genbank")
    
    print(f"✓ Assembled {len(results)} plasmids")
    print(f"  Output: {output_file}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--gene_fasta", required=True)
    parser.add_argument("--backbone_fasta", required=True)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--assembly_method", default="Gibson")
    
    args = parser.parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)
    process_cloning(args.gene_fasta, args.backbone_fasta, args.output_dir, args.assembly_method)
```

---

## Docker Compose Orchestration

### `docker-compose.yml`

```yaml
version: '3.9'

services:
  # Shared data volume
  data-volume:
    image: busybox:latest
    volumes:
      - pipeline-data:/data
    command: echo "Data volume initialized"

  # Stage 1: Data Preparation
  stage1-preparation:
    image: harbor.innodata.local/protein-engineering/stage1:latest
    build:
      context: .
      dockerfile: Dockerfile.stage1
    container_name: stage1-preparation
    volumes:
      - pipeline-data:/data
      - ./scripts:/workspace/scripts:ro
    environment:
      PDB_IDS: "1IFS 1UQ4 2P8N"
      OUTPUT_DIR: "/data/structures"
    depends_on:
      - data-volume
    networks:
      - pipeline-network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Stage 2: RFdiffusion Scaffolding
  stage2-rfdiffusion:
    image: harbor.innodata.local/protein-engineering/stage2:latest
    build:
      context: .
      dockerfile: Dockerfile.stage2
    container_name: stage2-rfdiffusion
    volumes:
      - pipeline-data:/data
      - ./scripts:/workspace/scripts:ro
    environment:
      DATA_INPUT: "/data/structures"
      DATA_OUTPUT: "/data/scaffolds"
    depends_on:
      - stage1-preparation
    networks:
      - pipeline-network
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Stage 3: ProteinMPNN Design
  stage3-proteinmpnn:
    image: harbor.innodata.local/protein-engineering/stage3:latest
    build:
      context: .
      dockerfile: Dockerfile.stage3
    container_name: stage3-proteinmpnn
    volumes:
      - pipeline-data:/data
      - ./scripts:/workspace/scripts:ro
    environment:
      DATA_INPUT: "/data/scaffolds"
      DATA_OUTPUT: "/data/sequences"
      FIXED_POSITIONS: "80 123 177 180 209"
      SAMPLING_TEMP: "0.1"
      NUM_SEQUENCES: "16"
    depends_on:
      - stage2-rfdiffusion
    networks:
      - pipeline-network
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Stage 4: DNA Chisel Optimization
  stage4-dnachisel:
    image: harbor.innodata.local/protein-engineering/stage4:latest
    build:
      context: .
      dockerfile: Dockerfile.stage4
    container_name: stage4-dnachisel
    volumes:
      - pipeline-data:/data
      - ./scripts:/workspace/scripts:ro
    environment:
      DATA_INPUT: "/data/sequences"
      DATA_OUTPUT: "/data/dna_optimized"
      TARGET_SPECIES: "e_coli"
    depends_on:
      - stage3-proteinmpnn
    networks:
      - pipeline-network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Stage 5: PlasmidGPT Generation
  stage5-plasmidgpt:
    image: harbor.innodata.local/protein-engineering/stage5:latest
    build:
      context: .
      dockerfile: Dockerfile.stage5
    container_name: stage5-plasmidgpt
    volumes:
      - pipeline-data:/data
      - ./scripts:/workspace/scripts:ro
    environment:
      DATA_INPUT: "/data/dna_optimized"
      DATA_OUTPUT: "/data/plasmids"
    depends_on:
      - stage4-dnachisel
    networks:
      - pipeline-network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Stage 6: In Silico Cloning
  stage6-cloning:
    image: harbor.innodata.local/protein-engineering/stage6:latest
    build:
      context: .
      dockerfile: Dockerfile.stage6
    container_name: stage6-cloning
    volumes:
      - pipeline-data:/data
      - ./scripts:/workspace/scripts:ro
    environment:
      DATA_INPUT_GENE: "/data/dna_optimized"
      DATA_INPUT_BACKBONE: "/data/plasmids"
      DATA_OUTPUT: "/data/assembled_plasmids"
    depends_on:
      - stage5-plasmidgpt
    networks:
      - pipeline-network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

volumes:
  pipeline-data:
    driver: local

networks:
  pipeline-network:
    driver: bridge
```

---

## Deployment & Execution

### Build and Push to Harbor

```bash
#!/bin/bash

HARBOR_URL="harbor.innodata.local"
PROJECT="protein-engineering"

echo "Building and pushing images to Harbor..."

# Build all stage images
for stage in 1 2 3 4 5 6; do
    docker build \
        -f Dockerfile.stage$stage \
        -t ${HARBOR_URL}/${PROJECT}/stage${stage}:latest \
        -t ${HARBOR_URL}/${PROJECT}/stage${stage}:v1.0 \
        .
    
    docker push ${HARBOR_URL}/${PROJECT}/stage${stage}:latest
    docker push ${HARBOR_URL}/${PROJECT}/stage${stage}:v1.0
done

echo "✓ All images pushed to Harbor"
```

### Run the Complete Pipeline

```bash
#!/bin/bash

# Login to Harbor
docker login harbor.innodata.local

# Run pipeline with docker-compose
docker-compose up --build

# Or run stages sequentially with explicit ordering
docker-compose up -d data-volume
docker-compose up stage1-preparation
docker-compose up stage2-rfdiffusion
docker-compose up stage3-proteinmpnn
docker-compose up stage4-dnachisel
docker-compose up stage5-plasmidgpt
docker-compose up stage6-cloning

# Check logs
docker-compose logs -f stage1-preparation
docker-compose logs -f stage2-rfdiffusion
# ... etc
```

### Monitor Pipeline Progress

```bash
#!/bin/bash

# Watch container logs
watch -n 5 "docker-compose ps"

# Check data directory growth
watch -n 10 "du -sh /var/lib/docker/volumes/pipeline-data/_data/"

# Validate outputs at each stage
docker exec stage1-preparation ls -la /data/structures
docker exec stage2-rfdiffusion ls -la /data/scaffolds
docker exec stage3-proteinmpnn ls -la /data/sequences
docker exec stage4-dnachisel ls -la /data/dna_optimized
docker exec stage5-plasmidgpt ls -la /data/plasmids
docker exec stage6-cloning ls -la /data/assembled_plasmids
```

---

## Harbor Image Management Best Practices

### 1. Image Tagging Strategy

```bash
# Tag by version and stage
docker tag ${PROJECT}/stage1:latest ${HARBOR_URL}/${PROJECT}/stage1:v1.0.0
docker tag ${PROJECT}/stage1:latest ${HARBOR_URL}/${PROJECT}/stage1:stable
docker tag ${PROJECT}/stage1:latest ${HARBOR_URL}/${PROJECT}/stage1:latest

# Push all tags
docker push ${HARBOR_URL}/${PROJECT}/stage1 --all-tags
```

### 2. Vulnerability Scanning

```bash
# Enable automatic scanning in Harbor
curl -u admin:${HARBOR_PASSWORD} -X PATCH \
  "https://harbor.innodata.local/api/v2.0/projects/1" \
  -H "Content-Type: application/json" \
  -d '{"severity":"high","scan_on_push":true}'
```

### 3. Image Retention Policies

```bash
# Set retention rules (keep last 5 images, delete images older than 30 days)
curl -u admin:${HARBOR_PASSWORD} -X POST \
  "https://harbor.innodata.local/api/v2.0/retention/policies" \
  -H "Content-Type: application/json" \
  -d '{
    "scope":"project",
    "template":"latest-pushed-artifacts",
    "tag_selectors":[{"kind":"doublestar","decoration":"matches","pattern":"**"}],
    "untagged_artifacts":true,
    "rules":[{
      "template":"always",
      "tag_selectors":[{"kind":"doublestar","decoration":"matches","pattern":"**"}],
      "params":{"always":null}
    }]
  }'
```

### 4. Disaster Recovery

```bash
# Export images from Harbor
docker pull ${HARBOR_URL}/${PROJECT}/stage1:latest
docker save -o stage1_backup.tar ${HARBOR_URL}/${PROJECT}/stage1:latest

# Backup Harbor database
docker exec harbor-db pg_dump -U postgres postgres > harbor_backup.sql

# Restore from backup
docker load -i stage1_backup.tar
docker push ${HARBOR_URL}/${PROJECT}/stage1:latest
```

---

## Troubleshooting

### Check Container Logs

```bash
# View logs for a specific stage
docker-compose logs stage1-preparation
docker-compose logs -f stage2-rfdiffusion

# View logs from all containers
docker-compose logs --tail=50 --follow
```

### Validate Data Flow Between Stages

```bash
# Check manifest files at each stage
docker exec stage1-preparation cat /data/structures/manifest.json
docker exec stage2-rfdiffusion cat /data/scaffolds/manifest.json
docker exec stage3-proteinmpnn cat /data/sequences/manifest.json
docker exec stage4-dnachisel cat /data/dna_optimized/manifest.json
docker exec stage5-plasmidgpt cat /data/plasmids/manifest.json
docker exec stage6-cloning cat /data/assembled_plasmids/manifest.json
```

### GPU Debugging (for stages 2-3)

```bash
# Check GPU availability
docker exec stage2-rfdiffusion nvidia-smi

# Verify CUDA compatibility
docker exec stage2-rfdiffusion python -c "import torch; print(torch.cuda.is_available())"
```

---

## Summary

This containerized pipeline:

✓ **Encapsulates each stage** in isolated Docker containers  
✓ **Uses Harbor for centralized image management**  
✓ **Implements data flow** via shared volumes  
✓ **Provides reproducibility** through version-tagged images  
✓ **Scales horizontally** with Kubernetes (optional)  
✓ **Maintains audit trails** via Harbor API  
✓ **Integrates with CI/CD** for automated deployment
