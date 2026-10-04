# Task 1: Protein Engineering Pipeline with Docker & Harbor

## Quick Summary

This directory contains **complete documentation** for deploying and executing a containerized protein engineering pipeline with 6 computational stages, managed through Harbor container registry.

### What's Included

1. **[instruction.md](instruction.md)** - Complete task specification
   - Objectives, inputs, outputs, schemas
   - Scored constraints and evaluation rubric
   - Tolerances and execution checklist

2. **[tool-manifest.json](tool-manifest.json)** - Tool definitions
   - Docker CLI commands (build, login, push, compose)
   - Harbor API endpoints
   - labctl command interface definitions

3. **schemas/** - Output validation schemas
   - `stage_manifest.schema.json` - Manifest files (one per stage)
   - `residue_annotation.schema.json` - Stage 1 residue CSV
   - `sequence_fasta.schema.json` - Stages 3-5 sequence files
   - `plasmid_genbank.schema.json` - Stage 6 final output

4. **environment/** - Docker configuration
   - `Dockerfile.stage1` through `Dockerfile.stage6`
   - `README.md` - Environment setup guide

---

## Quick Start

### Prerequisites
```bash
# Check requirements
docker --version          # Docker 20.10+
docker-compose --version  # Docker Compose 2.0+
nvidia-docker --version   # For GPU stages
```

### Build & Deploy
```bash
# 1. Configure Harbor (one-time)
cd environment/
docker login harbor.innodata.local -u admin -p <password>

# 2. Build all stage images
docker build -f Dockerfile.stage1 -t harbor.innodata.local/protein-engineering/stage1:latest .
docker build -f Dockerfile.stage2 -t harbor.innodata.local/protein-engineering/stage2:latest .
docker build -f Dockerfile.stage3 -t harbor.innodata.local/protein-engineering/stage3:latest .
docker build -f Dockerfile.stage4 -t harbor.innodata.local/protein-engineering/stage4:latest .
docker build -f Dockerfile.stage5 -t harbor.innodata.local/protein-engineering/stage5:latest .
docker build -f Dockerfile.stage6 -t harbor.innodata.local/protein-engineering/stage6:latest .

# 3. Push to Harbor
for stage in 1 2 3 4 5 6; do
  docker push harbor.innodata.local/protein-engineering/stage${stage}:latest
done

# 4. Execute pipeline (from parent directory with docker-compose.yml)
docker-compose up --build
```

### Monitor Progress
```bash
# View logs
docker-compose logs -f stage1-preparation
docker-compose logs -f stage2-rfdiffusion
# ... etc

# Check data flow
docker exec stage1-preparation cat /data/structures/manifest.json
docker exec stage2-rfdiffusion cat /data/scaffolds/manifest.json
# ... etc
```

---

## File Structure

```
task_1/
├── README.md                          # This file
├── instruction.md                     # Complete task specification
├── INPUTS.md                          # Input data specification
├── tool-manifest.json                 # Tool interface definitions
├── source_pdb_structure_inputs/       # Pre-seeded CIF input files
│   ├── 1IFS.cif (243 KB)
│   ├── 1UQ4.cif (296 KB)
│   └── 2P8N.cif (262 KB)
├── outputs/                           # Required output structure
│   └── OUTPUTS_SPEC.md                # Output file specifications
├── schemas/                           # Output validation schemas
│   ├── stage_manifest.schema.json
│   ├── residue_annotation.schema.json
│   ├── sequence_fasta.schema.json
│   └── plasmid_genbank.schema.json
├── environment/                       # Docker configuration
│   ├── README.md                      # Environment setup guide
│   ├── Dockerfile.stage1              # Data Preparation
│   ├── Dockerfile.stage2              # RFdiffusion2 Scaffolding
│   ├── Dockerfile.stage3              # ProteinMPNN Design
│   ├── Dockerfile.stage4              # DNA Chisel Optimization
│   ├── Dockerfile.stage5              # PlasmidGPT Backbones
│   ├── Dockerfile.stage6              # In Silico Cloning
│   └── [scripts/]                     # (Referenced in Dockerfiles)
└── [docker-compose.yml]               # Orchestration manifest (parent dir)
```

---

## Stage Overview

### Stage 1: Data Preparation & Structure Conversion
- **Input:** CIF files from `source_pdb_structure_inputs/` (1IFS.cif, 1UQ4.cif, 2P8N.cif)
- **Process:** Convert CIF → PDB format, extract catalytic residue annotations
- **Output:** PDB files + residues.csv + manifest.json
- **Image:** `stage1:latest` (400 MB)
- **Time:** ~1-2 minutes
- **Network:** Not required (offline/air-gapped)

### Stage 2: RFdiffusion2 Scaffold Generation
- **Input:** PDB structures from Stage 1
- **Process:** Generate 10 protein scaffolds with catalytic residues constrained
- **Output:** scaffolds_*.pdb (10 files) + manifest.json
- **Image:** `stage2:latest` (8 GB, GPU)
- **Time:** ~5-15 minutes (with GPU)

### Stage 3: ProteinMPNN Sequence Design
- **Input:** Scaffolds from Stage 2
- **Process:** Design 16 sequences per scaffold, keeping catalytic residues fixed
- **Output:** designed_sequences.fasta + manifest.json
- **Image:** `stage3:latest` (4 GB, GPU)
- **Time:** ~5-10 minutes (with GPU)

### Stage 4: DNA Chisel Codon Optimization
- **Input:** Protein sequences from Stage 3
- **Process:** Convert to DNA with optimal codon usage for *E. coli*, avoid restriction sites
- **Output:** optimized_sequences.fasta + manifest.json
- **Image:** `stage4:latest` (500 MB)
- **Time:** ~3-5 minutes

### Stage 5: PlasmidGPT Backbone Generation
- **Input:** Optimized DNA sequences from Stage 4
- **Process:** Generate 3 plasmid backbones per sequence with promoter, RBS, terminator, amp_r
- **Output:** backbones_generated.fasta + manifest.json
- **Image:** `stage5:latest` (3 GB)
- **Time:** ~2-5 minutes

### Stage 6: In Silico Cloning Simulation
- **Input:** DNA sequences (Stage 4) + Plasmid backbones (Stage 5)
- **Process:** Simulate Gibson assembly of genes into backbones
- **Output:** assembled_plasmids.gb (GenBank format) + manifest.json
- **Image:** `stage6:latest` (600 MB)
- **Time:** ~2-3 minutes

---

## Success Criteria (30 + 35 + 20 + 15 = 100 points)

### Build & Registry (30 points)
- All 6 Dockerfiles build successfully
- All images push to Harbor
- Vulnerability scanning enabled
- Robot account configured

### Pipeline Execution (35 points)
- Stage 1 downloads 3 PDB files + residue annotations
- Stage 2 generates 10 scaffolds with preserved catalytic residues
- Stage 3 produces 160+ designed sequences (16 × 10 scaffolds)
- Stage 4 successfully optimizes ≥80% of sequences
- Stage 5 generates ≥30 plasmid backbones
- Stage 6 assembles ≥8 successful plasmids

### Data Integrity (20 points)
- All 6 manifest.json files valid against schema
- FASTA sequences parse correctly
- GenBank features annotated correctly
- No file corruption

### Documentation (15 points)
- docker-compose.yml complete
- Environment variables documented
- Logs reviewed for errors

---

## Key Concepts

### Harbor Container Registry
- **URL:** `https://harbor.innodata.local`
- **Project:** `protein-engineering`
- **Images:** 6 stages, all tagged as `latest` + version tags
- **Security:** Robot account for automation, vulnerability scanning enabled

### Docker Compose Orchestration
- **Network:** `pipeline-network` (bridge)
- **Volume:** `pipeline-data` (local driver, mounted at `/data` in all containers)
- **Dependencies:** Explicit stage ordering (1 → 2 → 3 → 4 → 5 → 6)
- **Logging:** JSON file driver with rotation (10 MB max)

### Shared Data Flow
```
/data/structures/    (Stage 1 output)
/data/scaffolds/     (Stage 2 output)
/data/sequences/     (Stage 3 output)
/data/dna_optimized/ (Stage 4 output)
/data/plasmids/      (Stage 5 output)
/data/assembled_plasmids/  (Stage 6 output ← FINAL)
```

Each stage reads manifest.json from previous stage, processes data, writes new manifest.json for next stage.

### Catalytic Residue Constraints
- **Fixed positions:** 80, 123, 177, 180, 209
- **Must be preserved** in all designs (Stage 2-3)
- **Constraint enforcement:** Stage 2 uses hotspot residues, Stage 3 uses fixed_positions JSONL

### Sequence Integrity
- **Translation fidelity:** DNA codon → protein sequence MUST match (Stage 4)
- **No internal stop codons:** Final plasmids must not have stop codons within CDS
- **Circular topology:** Plasmids must be circular DNA

---

## Troubleshooting

### Image Build Fails
```bash
# Check Docker daemon
docker ps

# Rebuild without cache
docker build --no-cache -f environment/Dockerfile.stage1 \
  -t harbor.innodata.local/protein-engineering/stage1:latest .

# Check disk space
df -h
```

### Pipeline Execution Hangs
```bash
# View running containers
docker ps

# Check logs for errors
docker-compose logs [stage-name]

# Manually check intermediate data
docker exec [container-name] ls -la /data/[stage-output]/
```

### GPU Issues (Stages 2-3)
```bash
# Check NVIDIA Docker
nvidia-smi

# Verify CUDA in container
docker exec stage2-rfdiffusion nvidia-smi
docker exec stage3-proteinmpnn python -c "import torch; print(torch.cuda.is_available())"
```

### Harbor Authentication
```bash
# Test login
docker login harbor.innodata.local -u admin -p <password>

# Check credentials
cat ~/.docker/config.json
```

---

## Additional Resources

- **instruction.md** - Full specification with detailed constraints
- **environment/README.md** - Docker configuration details
- **tool-manifest.json** - Tool interface definitions
- **schemas/** - JSON schema files for all outputs

---

## Next Steps

1. **Review instruction.md** for complete task specification
2. **Review environment/README.md** for Docker setup
3. **Build Dockerfiles** in order (stage 1-6)
4. **Create Harbor project** and robot account
5. **Push images** to Harbor registry
6. **Execute docker-compose.yml** to run pipeline
7. **Validate outputs** against schemas in `schemas/` directory
8. **Check manifest files** at each stage for pipeline integrity

---

## Summary

This task requires:
- ✓ Building 6 Docker images with bioinformatics tools
- ✓ Pushing images to Harbor registry
- ✓ Orchestrating pipeline via docker-compose
- ✓ Validating outputs against strict schemas
- ✓ Ensuring catalytic residue preservation and sequence integrity
- ✓ Successfully assembling ≥8 plasmids in GenBank format

**Expected total runtime:** 30-50 minutes (sequential stages, with GPU for stages 2-3)
