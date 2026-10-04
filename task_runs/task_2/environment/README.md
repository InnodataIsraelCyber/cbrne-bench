# Task 2 Environment Configuration

## Docker Container Architecture

### Phase 0: Target Preparation
- **Image:** `harbor.internal.domain/protein-design/alphafold3:latest`
- **Base:** `nvidia/cuda:12.2.2-devel-ubuntu22.04`
- **Purpose:** Predict 3D structure of viral target protein
- **GPU:** Required (40+ GB VRAM recommended)
- **Key Dependencies:** JAX, dm-haiku, AlphaFold3
- **Entrypoint:** `python /app/run_phase0.py`
- **Output:** PDB structure, pLDDT scores, PAE matrix, QC report

### Phase 1: Backbone Generation
- **Image:** `harbor.internal.domain/protein-design/rfdiffusion:latest`
- **Base:** `nvidia/cuda:12.2.2-devel-ubuntu22.04`
- **Purpose:** Generate novel protein backbones with viral parameter constraints
- **GPU:** Required (16-40 GB VRAM)
- **Key Dependencies:** PyTorch, dm-haiku, RFdiffusion
- **Entrypoint:** `python /app/run_phase1.py`
- **Output:** 50-100 backbone PDB files, configuration, statistics
- **Viral Parameters Applied:** Hotspot targeting, mucin domain preservation, binder length constraints

### Phase 2: Sequence Design
- **Image:** `harbor.internal.domain/protein-design/proteinmpnn:latest`
- **Base:** `nvidia/cuda:12.2.2-devel-ubuntu22.04`
- **Purpose:** Inverse folding to design sequences for backbones
- **GPU:** Required (8-24 GB VRAM)
- **Key Dependencies:** PyTorch, ProteinMPNN
- **Entrypoint:** `python /app/run_phase2.py`
- **Output:** 750-1500 sequences (FASTA), scores (CSV), statistics

### Phase 3: Validation & Ranking
- **Image:** `harbor.internal.domain/protein-design/phase3:latest` (composite)
- **Base:** `nvidia/cuda:12.2.2-devel-ubuntu22.04`
- **Subphases:**
  - **3a (ESMFold):** Self-consistency check (8-24 GB VRAM)
  - **3b (AlphaFold3):** Complex prediction with viral parameters (40+ GB VRAM)
  - **3c (Analysis):** Ranking and filtering (CPU only)
  - **3d (Rosetta/FoldX):** Energy scoring (CPU heavy, 64+ GB RAM recommended)

## Dockerfile Specifications

### Build Matrix

| Phase | Base Image | Size | GPU | Build Time | Key Components |
|-------|-----------|------|-----|-----------|-----------------|
| 0 | cuda:12.2.2 | 8 GB | Yes | 30 min | JAX, AF3, BioPython |
| 1 | cuda:12.2.2 | 6 GB | Yes | 20 min | PyTorch, RFdiffusion |
| 2 | cuda:12.2.2 | 5 GB | Yes | 15 min | PyTorch, ProteinMPNN |
| 3 | cuda:12.2.2 | 10 GB | Mixed | 25 min | ESMFold, AF3, Rosetta |

**Total Build Time:** ~90 minutes (sequential)

### Published Docker Images

All images are pushed to Harbor registry:
```
harbor.internal.domain/protein-design/
├── alphafold3:latest (40 GB)
├── rfdiffusion:latest (6 GB)
├── proteinmpnn:latest (5 GB)
├── esmfold:latest (4 GB)
├── analysis-toolkit:latest (2 GB)
└── rosetta:latest (8 GB)
```

## Environment Variables

### Global Configuration
```bash
CUDA_VISIBLE_DEVICES=0              # GPU device number
PYTHONUNBUFFERED=1                  # Real-time logging
NVIDIA_VISIBLE_DEVICES=all          # GPU visibility
```

### Phase-Specific Variables

**Phase 0:**
```bash
MODEL=alphafold3                    # Structure prediction model
NUM_RECYCLES=3                      # Prediction recycles
DIFFUSION_STEPS=50                  # Diffusion sampling steps
```

**Phase 1:**
```bash
NUM_DESIGNS=50                      # Backbone designs to generate
BINDER_LENGTH_MIN=50                # Minimum binder length
BINDER_LENGTH_MAX=150               # Maximum binder length
NUM_DIFFUSION_STEPS=50              # Diffusion steps
```

**Phase 2:**
```bash
DESIGN_CHAIN=B                      # Chain to design (B = binder)
NUM_SEQ_PER_STRUCT=15               # Sequences per backbone
SAMPLING_TEMP=0.1                   # Sampling temperature
```

**Phase 3:**
```bash
IPTM_THRESHOLD=0.5                  # Minimum interface confidence
PAE_THRESHOLD=0.35                  # Maximum PAE (Ångströms)
CONTACT_THRESHOLD=15                # Minimum interface contacts
```

## Viral Parameter Integration

All Dockerfiles support viral parameter injection via YAML:

**Receptor Binding Affinity (GP-V75A):**
- Hotspot residues: [75]
- Target Kd: <100 nM
- Validation: ipTM ≥0.5, PAE <5 Å

**Antibody Escape Sites:**
- 127 mutations across 21 sites
- Validation: ΔΔG_Bind >2 kcal/mol

**Protease Dependence:**
- Moderate destabilization of prefusion state
- Validation: Increased cleavage accessibility

**Immune Evasion:**
- Preserve mucin-like domain (positions 1-50)
- Validation: Glycosylation sites intact

**Interferon Antagonism (VP35):**
- Basic patch center: R312
- Validation: ≥70% charge retained

## Volume Mounts

### Standard Mount Points

```yaml
volumes:
  - ./alphafold_inputs:/data/targets      # Input targets
  - ./results/phase_0:/data/phase_0       # Phase 0 outputs
  - ./results/phase_1:/data/phase_1       # Phase 1 outputs
  - ./results/phase_2:/data/phase_2       # Phase 2 outputs
  - ./results/phase_3:/data/phase_3       # Phase 3 outputs
  - ./logs:/data/logs                     # All execution logs
```

### Data Directory Structure

```
results/
├── phase_0/
│   ├── result_model_1.pdb
│   ├── plddt_scores.txt
│   ├── pae_matrix.npy
│   ├── qc_report.json
│   ├── hotspot_residues.json
│   └── manifest.json
├── phase_1/
│   ├── design_000.pdb to design_099.pdb
│   ├── rfdiffusion_config.json
│   ├── backbone_statistics.json
│   └── manifest.json
├── phase_2/
│   ├── sequences_design.fasta
│   ├── scores_design.csv
│   ├── sequence_statistics.json
│   └── manifest.json
└── phase_3/
    ├── step_3a_monomer/
    │   ├── monomer_*.pdb
    │   ├── monomer_metrics.json
    │   └── manifest.json
    ├── step_3b_complex/
    │   ├── complex_*.pdb
    │   ├── interface_metrics.csv
    │   ├── viral_validation.json
    │   └── manifest.json
    ├── step_3c_ranking/
    │   ├── ranked_designs.csv
    │   ├── ranking_criteria.json
    │   └── manifest.json
    └── step_3d_energy_scoring/
        ├── energy_scores.csv
        ├── final_designs.json
        └── manifest.json
```

## Docker Compose Orchestration

### Service Dependencies

```mermaid
phase0-target-prep
        ↓
phase1-backbone-gen
        ↓
phase2-seq-design
        ↓
phase3a-monomer (parallel)
        ↓
phase3b-complex
        ↓
phase3c-ranking
        ↓
phase3d-energy
```

### Resource Allocation

```yaml
phase0-target-prep:
  gpu_count: 1
  gpu_memory: "40GB"
  cpu_cores: 4
  memory: "32GB"

phase1-backbone-gen:
  gpu_count: 1
  gpu_memory: "40GB"
  cpu_cores: 8
  memory: "64GB"

phase2-seq-design:
  gpu_count: 1
  gpu_memory: "24GB"
  cpu_cores: 8
  memory: "32GB"

phase3a-monomer:
  gpu_count: 1
  gpu_memory: "8GB"
  cpu_cores: 4
  memory: "16GB"

phase3b-complex:
  gpu_count: 1
  gpu_memory: "40GB"
  cpu_cores: 8
  memory: "64GB"

phase3c-ranking:
  gpu_count: 0
  cpu_cores: 4
  memory: "16GB"

phase3d-energy:
  gpu_count: 0
  cpu_cores: 16
  memory: "64GB"
```

## Deployment Checklist

- [ ] Harbor registry accessible at `harbor.internal.domain`
- [ ] Docker daemon installed with NVIDIA Docker runtime
- [ ] GPU available with ≥40 GB VRAM (for phases 0, 3b)
- [ ] All 6 Docker images built and pushed to Harbor
- [ ] `alphafold_inputs/` folder contains sequence FASTA + viral_params.yaml
- [ ] `results/` directory structure created
- [ ] Docker Compose v1.29+ installed
- [ ] Sufficient disk space (≥500 GB for pipeline outputs)

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| GPU out of memory | Model too large for available VRAM | Reduce batch size or use smaller model |
| Harbor pull fails | Registry credentials incorrect | `docker login harbor.internal.domain` |
| Phase timeout | Inference too slow | Check GPU utilization; consider distributed execution |
| Volume mount errors | Permission denied | Use `sudo` or add user to docker group |
| Viral params not applied | YAML parsing error | Validate YAML syntax in `alphafold_inputs/{target}/viral_params.yaml` with `yamllint` |

## Monitoring & Logging

All phases log to `/data/logs/`:

```bash
# Monitor logs in real-time
tail -f logs/phase0_execution.log
docker-compose logs -f phase1-backbone-gen
```

## Post-Pipeline Tasks

After all phases complete:

1. **Verify manifests:** Check manifest.json at each phase for validation status
2. **Review top designs:** Examine final_designs.json (top 10-20 designs)
3. **Validate viral parameters:** Confirm all 5 parameters met for top 3 designs
4. **Prepare for synthesis:** Extract sequences from top designs
5. **Documentation:** Archive logs and configuration for reproducibility
