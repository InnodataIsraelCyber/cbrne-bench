# Environment Configuration for Task 1: Protein Engineering Pipeline

## Overview

This directory contains the Docker environment configuration, build artifacts, and runtime specifications for the 6-stage containerized protein engineering pipeline.

---

## Directory Structure

```
environment/
├── Dockerfile.stage1         # Data Preparation container
├── Dockerfile.stage2         # RFdiffusion2 Scaffold Generation
├── Dockerfile.stage3         # ProteinMPNN Sequence Design
├── Dockerfile.stage4         # DNA Chisel Codon Optimization
├── Dockerfile.stage5         # PlasmidGPT Backbone Generation
├── Dockerfile.stage6         # In Silico Cloning Simulation
├── README.md                 # This file
└── [docker-compose.yml]      # Orchestration manifest (in parent directory)
```

---

## Dockerfiles Overview

### Dockerfile.stage1 (Data Preparation & Structure Conversion)
- **Base Image:** `python:3.10-slim`
- **Size:** ~400 MB
- **Key Tools:**
  - BioPython 1.81 (CIF/PDB parsing and conversion)
  - NCBI BLAST+ (sequence alignment)
- **Input Source:** CIF files from `source_pdb_structure_inputs/` volume
- **Output:** Converted PDB structures + residue annotations
- **GPU Required:** No
- **Network Access:** Not required (offline deployment)

### Dockerfile.stage2 (RFdiffusion2 Scaffolding)
- **Base Image:** `nvidia/cuda:12.2.0-runtime-ubuntu22.04`
- **Size:** ~8 GB (with model weights)
- **Key Tools:**
  - CUDA 12.2 + cuDNN
  - Conda environment for RFdiffusion
  - PyTorch with CUDA support
- **Model Weights:** Downloaded from external source (requires internet)
- **Output:** Scaffold PDB files (10 designs)
- **GPU Required:** Yes (1x NVIDIA GPU recommended)
- **Memory:** 8-16 GB VRAM

### Dockerfile.stage3 (ProteinMPNN Design)
- **Base Image:** `pytorch/pytorch:2.0-cuda12.1-runtime-ubuntu22.04`
- **Size:** ~4 GB (pre-built PyTorch)
- **Key Tools:**
  - PyTorch 2.0 with CUDA 12.1
  - ProteinMPNN cloned from GitHub
  - BioPython, NumPy, SciPy, Pandas
- **Output:** Designed sequences (FASTA)
- **GPU Required:** Yes (1x NVIDIA GPU recommended)
- **Memory:** 6-12 GB VRAM

### Dockerfile.stage4 (DNA Chisel Optimization)
- **Base Image:** `python:3.10-slim`
- **Size:** ~500 MB
- **Key Tools:**
  - DNA Chisel 3.20.27 (codon optimization)
  - BioPython 1.81
  - Pandas 1.5.0
- **Output:** Codon-optimized DNA sequences (FASTA)
- **GPU Required:** No
- **Memory:** 2-4 GB RAM

### Dockerfile.stage5 (PlasmidGPT Backbones)
- **Base Image:** `python:3.10`
- **Size:** ~3 GB (with TensorFlow)
- **Key Tools:**
  - TensorFlow 2.13
  - Transformers 4.30
  - PyTorch 2.0
  - BioPython 1.81
- **Model Weights:** PlasmidGPT model (optional, can be pre-downloaded)
- **Output:** Plasmid backbone sequences (FASTA)
- **GPU Required:** Optional (faster with GPU)
- **Memory:** 4-8 GB RAM

### Dockerfile.stage6 (In Silico Cloning)
- **Base Image:** `python:3.10-slim`
- **Size:** ~600 MB
- **Key Tools:**
  - pydna 3.2.1 (DNA assembly simulation)
  - BioPython 1.81
  - Pandas 1.5.0
- **Output:** Assembled plasmids (GenBank format)
- **GPU Required:** No
- **Memory:** 2-4 GB RAM

---

## Build Specifications

### Build Matrix

| Stage | Base Image | Size | GPU | Build Time | Dependencies |
|-------|-----------|------|-----|-----------|--------------|
| 1 | python:3.10-slim | 400 MB | No | 2 min | BLAST, requests |
| 2 | nvidia/cuda:12.2 | 8 GB | Yes | 15 min | RFdiffusion, models |
| 3 | pytorch/pytorch:2.0 | 4 GB | Yes | 5 min | ProteinMPNN |
| 4 | python:3.10-slim | 500 MB | No | 3 min | DNA Chisel |
| 5 | python:3.10 | 3 GB | Opt | 8 min | TensorFlow, Transformers |
| 6 | python:3.10-slim | 600 MB | No | 2 min | pydna |

### Total Build Time: ~35 minutes (sequential)

### Build Requirements
- Docker 20.10+
- Docker Compose 2.0+
- 30 GB free disk space (for all images)
- NVIDIA Docker runtime (for GPU stages)
- NVIDIA CUDA 12.2+ (for GPU stages)

---

## Published Fixtures & Offline Dependencies

### Pre-Built Docker Image Locations

#### In Harbor Registry
All images are pushed to: `https://harbor.innodata.local/protein-engineering/`

| Stage | Registry Tag | Size | Scan Status |
|-------|-------------|------|------------|
| stage1 | `stage1:latest` | 400 MB | Enabled |
| stage2 | `stage2:latest` | 8 GB | Enabled |
| stage3 | `stage3:latest` | 4 GB | Enabled |
| stage4 | `stage4:latest` | 500 MB | Enabled |
| stage5 | `stage5:latest` | 3 GB | Enabled |
| stage6 | `stage6:latest` | 600 MB | Enabled |

#### Offline Dependency Management

**For Air-Gapped Deployment:**

1. **Pre-download Model Weights**
   - RFdiffusion: Download from external source and mount at `/workspace/models/`
   - PlasmidGPT: Pre-build and include in Docker image

2. **Offline Python Packages**
   ```bash
   docker run --rm python:3.10-slim pip download \
     biopython==1.81 pydantic==2.0 requests==2.31.0 \
     -d ./offline-packages/
   
   # In Dockerfile, use: --no-index --find-links ./offline-packages/
   ```

3. **Pre-Seed PDB Files**
   ```bash
   # Copy PDB files to shared volume before pipeline execution
   docker volume create pipeline-data
   docker run --rm -v pipeline-data:/data busybox \
     sh -c "echo 'pre-seeded' > /data/pdb_ready.txt"
   ```

---

## Tool Interfaces & APIs

### labctl Command Interface

All pipeline operations use standard Docker and Docker Compose CLI:

```bash
# Build stage image
docker build -f environment/Dockerfile.stage1 \
  -t harbor.innodata.local/protein-engineering/stage1:latest .

# Login to Harbor
docker login harbor.innodata.local -u admin

# Push image
docker push harbor.innodata.local/protein-engineering/stage1:latest

# Orchestrate entire pipeline
docker-compose -f docker-compose.yml up --build

# Monitor logs
docker-compose logs -f stage2-rfdiffusion
```

### Harbor Gateway API

**Base URL:** `https://harbor.innodata.local/api/v2.0/`

**Key Endpoints:**

```bash
# Create project
curl -u admin:PASSWORD -X POST \
  https://harbor.innodata.local/api/v2.0/projects \
  -H "Content-Type: application/json" \
  -d '{"project_name":"protein-engineering","public":false}'

# List repositories
curl -u admin:PASSWORD \
  https://harbor.innodata.local/api/v2.0/projects/protein-engineering/repositories

# Get image details
curl -u admin:PASSWORD \
  https://harbor.innodata.local/api/v2.0/projects/protein-engineering/repositories/stage1/artifacts

# Trigger vulnerability scan
curl -u admin:PASSWORD -X POST \
  https://harbor.innodata.local/api/v2.0/projects/protein-engineering/repositories/stage1/artifacts/{digest}/scan
```

### Docker Compose Service Configuration

**docker-compose.yml** defines:
- 6 stage services (stage1-preparation, stage2-rfdiffusion, ..., stage6-cloning)
- 1 data volume (pipeline-data)
- 1 overlay network (pipeline-network)
- Resource limits and GPU allocation (for stages 2-3)
- Logging configuration (JSON file driver, 10MB max size)
- Health checks and service dependencies

---

## Environment Variables

### Global Configuration
```bash
HARBOR_URL=harbor.innodata.local
PROJECT=protein-engineering
DOCKER_BUILDKIT=1  # Enable BuildKit for faster builds
DOCKER_COMPOSE_INTERACTIVE_NO_CLI=true  # Suppress interactive prompts
```

### Stage-Specific Variables
| Stage | Variable | Value | Notes |
|-------|----------|-------|-------|
| 1 | PDB_IDS | "1IFS 1UQ4 2P8N" | Space-separated PDB codes |
| 1 | OUTPUT_DIR | /data/structures | |
| 2 | DATA_INPUT | /data/structures | |
| 2 | DATA_OUTPUT | /data/scaffolds | |
| 3 | FIXED_POSITIONS | "80 123 177 180 209" | Space-separated residue numbers |
| 3 | SAMPLING_TEMP | 0.1 | Range: 0.01-1.0 |
| 3 | NUM_SEQUENCES | 16 | Sequences per scaffold |
| 4 | TARGET_SPECIES | e_coli | Options: e_coli, yeast, mammalian, plant |
| 5 | DATA_INPUT | /data/dna_optimized | |
| 5 | DATA_OUTPUT | /data/plasmids | |
| 6 | DATA_INPUT_GENE | /data/dna_optimized | |
| 6 | DATA_INPUT_BACKBONE | /data/plasmids | |
| 6 | DATA_OUTPUT | /data/assembled_plasmids | |

---

## Input Data Source

**Source PDB Inputs:** Mount `source_pdb_structure_inputs/` folder containing CIF files:
```bash
# In docker-compose.yml, stage1 service:
volumes:
  - ./source_pdb_structure_inputs:/workspace/input_structures:ro
  - pipeline-data:/data
```

**CIF Files (mmCIF format):**
- `1IFS.cif` - 243 KB
- `1UQ4.cif` - 296 KB  
- `2P8N.cif` - 262 KB

---

## Shared Data Directory

### Mount Point
All containers mount the `pipeline-data` volume at `/data`

### Directory Structure
```
/data/
├── structures/               # Stage 1 output
│   ├── 1IFS.pdb
│   ├── 1UQ4.pdb
│   ├── 2P8N.pdb
│   ├── residues.csv
│   └── manifest.json
├── scaffolds/                # Stage 2 output
│   ├── scaffolds_1.pdb
│   ├── ...
│   └── manifest.json
├── sequences/                # Stage 3 output
│   ├── designed_sequences.fasta
│   └── manifest.json
├── dna_optimized/            # Stage 4 output
│   ├── optimized_sequences.fasta
│   └── manifest.json
├── plasmids/                 # Stage 5 output
│   ├── backbones_generated.fasta
│   └── manifest.json
└── assembled_plasmids/       # Stage 6 output
    ├── assembled_plasmids.gb
    └── manifest.json
```

### Volume Persistence
- Type: `local` driver
- Data persists on host at: `docker volume inspect pipeline-data`
- Backup: `docker run --rm -v pipeline-data:/backup -v $(pwd):/save busybox tar czf /save/backup.tar.gz -C /backup .`

---

## Network Configuration

### Docker Compose Network
- **Name:** `pipeline-network`
- **Driver:** `bridge`
- **Scope:** Local to Docker host
- **DNS:** Enabled (containers resolve by service name)

### Service Communication
```
stage1 → stage2 → stage3 → stage4 → stage5 → stage6
        (via docker-compose depends_on)
```

### Port Exposure
- Harbor Registry: `:443` (HTTPS), `:80` (HTTP)
- All pipeline containers: No ports exposed (internal communication only)

---

## Performance & Resource Limits

### Memory Allocation
```yaml
stage1:
  memory: 2g
  memswap: 2g
stage2:  # RFdiffusion (GPU)
  memory: 16g
  memswap: 16g
stage3:  # ProteinMPNN (GPU)
  memory: 12g
  memswap: 12g
stage4:
  memory: 4g
  memswap: 4g
stage5:
  memory: 8g
  memswap: 8g
stage6:
  memory: 4g
  memswap: 4g
```

### GPU Allocation
```yaml
stage2:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
stage3:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

---

## Deployment Checklist

- [ ] Harbor instance running at `harbor.innodata.local`
- [ ] Docker daemon with compose support installed
- [ ] NVIDIA Docker runtime installed (if using GPU)
- [ ] Build all Dockerfiles: `docker-compose build`
- [ ] Test Harbor authentication: `docker login harbor.innodata.local`
- [ ] Push images: `for stage in 1 2 3 4 5 6; do docker push harbor.innodata.local/protein-engineering/stage${stage}:latest; done`
- [ ] Create docker-compose.yml with correct image references
- [ ] Execute pipeline: `docker-compose up`
- [ ] Validate outputs in `/data/assembled_plasmids/manifest.json`
