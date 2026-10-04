# Task 2: AI-Driven Protein Design Pipeline with Harbor Docker

## Quick Summary

This directory contains complete documentation for deploying and executing a **4-phase containerized protein design pipeline** with Harbor registry, incorporating **5 viral protein design parameters** for targeting EBOV VP35 and GP.

### What's Included

1. **[instruction.md](instruction.md)** — Complete task specification
   - Objectives, inputs, outputs for all 4 phases
   - Viral parameter definitions (receptor binding, escape sites, protease pathway, immune evasion, VP35 antagonism)
   - Scored constraints and evaluation rubric (100 points)

2. **[tool-manifest.json](tool-manifest.json)** — Tool interface definitions
   - All Docker commands and Harbor API endpoints
   - Tool versions and dependencies
   - Viral parameter tracking

3. **schemas/** — Output validation schemas
   - Phase manifest schema
   - Complex prediction metrics schema (Phase 3b)
   - Energy scoring schema (Phase 3d)

4. **environment/** — Docker configuration
   - `Dockerfile.phase0` through `Dockerfile.phase3`
   - `README.md` — Docker setup and orchestration guide

---

## Phase Overview

### Phase 0: Target Preparation (15 pts)
- **Input:** Viral protein sequence (FASTA)
- **Output:** 3D structure + hotspot binding site
- **Container:** AlphaFold3
- **GPU:** 40+ GB VRAM
- **Success:** pLDDT >70, pTM ≥0.8

### Phase 1: Backbone Generation (20 pts)
- **Input:** Target structure + hotspots + viral parameters
- **Output:** 50-100 backbone structures (PDB files)
- **Container:** RFdiffusion
- **GPU:** 40+ GB VRAM
- **Success:** All backbones <15 Å RMSD to hotspots, mucin domain preserved

### Phase 2: Sequence Design (15 pts)
- **Input:** Backbone structures
- **Output:** 750-1500 protein sequences (FASTA)
- **Container:** ProteinMPNN
- **GPU:** 24 GB VRAM
- **Success:** All sequences valid, diversity demonstrated

### Phase 3: Validation & Ranking (50 pts)
- **3a:** Self-consistency check (ESMFold) — 5 pts
- **3b:** Complex prediction with viral parameters (AlphaFold3) — 15 pts
- **3c:** Ranking by combined scoring — 5 pts
- **3d:** Physics-based energy scoring (Rosetta/FoldX) — 15 pts
- **Final:** 10-20 designs, top 3 with ipTM ≥0.6 — 10 pts

---

## Viral Design Parameters (5 integrated constraints)

| Parameter | Focus | Validation |
|-----------|-------|-----------|
| **1. Receptor Binding Affinity** | GP-V75A optimization for NPC1 | ipTM ≥0.5, PAE <5 Å |
| **2. Antibody Escape Sites** | 127 mutations across 21 epitopes | ΔΔG_Bind >2 kcal/mol |
| **3. Protease Dependence** | Reduce cathepsin L/B reliance | Prefusion ΔG: -3 to -5 kcal/mol |
| **4. Immune Evasion** | Preserve mucin-like domain (1-50) | Zero mutations in positions 1-50 |
| **5. VP35 Antagonism** | Maintain dsRNA binding (R312) | ≥70% basic patch charge retained |

---

## Quick Start

### Prerequisites
```bash
# Check requirements
docker --version          # Docker 24.0+
nvidia-smi               # GPU with ≥40 GB VRAM
docker-compose --version # 2.0+
```

### Setup
```bash
# 1. Login to Harbor
docker login harbor.internal.domain -u admin -p <password>

# 2. Build all images
cd environment/
for phase in 0 1 2 3; do
  docker build -f Dockerfile.phase${phase} -t harbor.internal.domain/protein-design/phase${phase}:latest .
done

# 3. Push to Harbor
for phase in 0 1 2 3; do
  docker push harbor.internal.domain/protein-design/phase${phase}:latest
done
```

### Execute Pipeline
```bash
# Run all 4 phases in sequence
docker-compose -f docker-compose.yml up --build

# Or run individual phases
docker-compose up phase0-target-prep
docker-compose up phase1-backbone-gen
docker-compose up phase2-seq-design
docker-compose up phase3-monomer phase3-complex phase3-ranking phase3-energy
```

### Verify Outputs
```bash
# Check each phase's manifest
for phase in 0 1 2 3; do
  jq . results/phase_${phase}/manifest.json
done

# Review final designs
jq . results/phase_3/step_3d_energy_scoring/final_designs.json | head -20
```

---

## File Structure

```
task_2/
├── README.md                      # This file
├── instruction.md                 # Complete task specification
├── tool-manifest.json             # Tool interface definitions
├── environment/                   # Docker configuration
│   ├── README.md                 # Docker setup guide
│   ├── Dockerfile.phase0          # Target preparation
│   ├── Dockerfile.phase1          # Backbone generation
│   ├── Dockerfile.phase2          # Sequence design
│   └── Dockerfile.phase3          # Validation & ranking
├── schemas/                       # Output validation schemas
│   ├── phase_manifest_schema.json
│   ├── phase3b_metrics_schema.json
│   └── phase3d_energy_schema.json
├── alphafold_inputs/              # Input data (FASTA + YAML)
│   ├── ebola_vp35_iid/
│   │   ├── sequence.fasta
│   │   └── viral_params.yaml
│   └── ebola_gp/
│       ├── sequence.fasta
│       └── viral_params.yaml
├── outputs/                       # Agent outputs (6 required files)
│   ├── outcome.json              # Decision and result summary
│   ├── provenance.json           # Tool execution audit trail
│   ├── claims.json               # Scientific claims with evidence
│   ├── controls.json             # Reference data and replicates
│   ├── rejections.json           # Invalid inputs and incomplete claims
│   ├── OUTPUTS_SPEC.md           # Complete output specification
│   ├── derived/                  # Produced artifacts
│   │   ├── phase_0/              # Target structures
│   │   ├── phase_1/              # Backbone designs
│   │   ├── phase_2/              # Sequences
│   │   └── phase_3/              # Predictions and rankings
│   ├── phase_manifests/          # Phase validation files
│   └── logs/                     # Execution logs
└── results/                       # Pipeline output directory (created)
    ├── phase_0/
    ├── phase_1/
    ├── phase_2/
    └── phase_3/
        ├── step_3a_monomer/
        ├── step_3b_complex/
        ├── step_3c_ranking/
        └── step_3d_energy_scoring/
```

---

## Success Criteria (100 points)

### Build & Registry (10 pts)
- All 4 Dockerfiles build without errors
- All images push to Harbor successfully
- Container versions locked in Dockerfiles

### Phase 0 (15 pts)
- Target structure generated (pLDDT >70, pTM ≥0.8)
- Hotspot residues identified with viral constraints
- QC report validates structure quality

### Phase 1 (20 pts)
- 50-100 backbones generated
- All valid PDB format, <15 Å RMSD to hotspots
- Mucin domain preserved, viral parameters applied

### Phase 2 (15 pts)
- 750-1500 sequences generated
- All valid (standard 20 AAs, correct length)
- Sequence diversity demonstrated

### Phase 3 (35 pts)
- Phase 3a: ≥50% RMSD <2.5 Å to backbone (5 pts)
- Phase 3b: ≥30% pass ipTM ≥0.5, PAE ≤0.35 filters (10 pts)
- Phase 3b: Viral parameters validated for all complexes (5 pts)
- Phase 3c: Final shortlist of 10-20 designs (5 pts)
- Phase 3d: Top 3 designs ipTM ≥0.6, PAE ≤0.25 (5 pts)
- Phase 3d: Energy scores correlate with AI metrics (5 pts)

### Documentation (5 pts)
- All manifest.json files present and valid
- Viral parameter tracking documented

---

## Expected Output

### After Pipeline Completes (48-72 hours)

The pipeline produces results in the `outputs/` directory with 6 required files:

**1. outcome.json** — Agent decision and results
- Trial ID, execution mode, completion status
- Phase completed, reasons for any holds
- Invariant findings (no duplicates, units correct, etc.)
- Evidence completeness checklist

**2. provenance.json** — Complete audit trail
- Every tool invocation (version, parameters, timestamps)
- Input/output hashes (SHA-256)
- Gateway request/command IDs for verification
- Resource usage (GPU hours, peak memory)

**3. derived/** — All produced artifacts
- Phase 0: Target structure, hotspots, QC report
- Phase 1: 50-100 backbone PDB files
- Phase 2: 750-1500 sequences (FASTA)
- Phase 3: Monomer predictions, complex predictions, final designs

**4. claims.json** — Scientific claims with evidence
- Structure quality (pLDDT >70 for target)
- Interface predictions (ipTM ≥0.5, PAE ≤0.35 for ≥30% designs)
- Binding energy predictions (kcal/mol)
- Viral parameter compatibility (all 5 parameters validated)

**5. controls.json** — Reference structures and replicates
- ≥3 independent reference structures
- Replicate validation runs (same backbone, folded 3x)
- Benchmark metrics for accuracy assessment

**6. rejections.json** — Invalid inputs and incomplete claims
- Malformed FASTA sequences
- YAML parsing errors
- Incomplete claims (missing evidence legs)

**Final Deliverables:**
1. **Top 10-20 designs** with:
   - Complex structure (PDB)
   - Sequence (FASTA)
   - AI metrics (ipTM, PAE, pLDDT)
   - Energy scores (ΔG, shape complementarity)
   - **Viral parameter validation** (all 5 parameters checked)

2. **Summary Report:**
   - Design ranking table
   - Viral parameter compatibility matrix
   - Docker execution logs
   - Recommended designs for wet-lab

3. **Analysis:**
   - Interface metrics CSV
   - Energy scoring results
   - Ranking criteria applied

See [outputs/OUTPUTS_SPEC.md](outputs/OUTPUTS_SPEC.md) for complete output specification.

---

## Viral Parameter Integration

Each phase automatically applies viral constraints:

**Phase 1 (RFdiffusion):**
- Hotspot residues for GP-V75A (position 75)
- Preserve mucin-like domain (positions 1-50 in target)
- Design binder length: 50-150 AA

**Phase 3b (AlphaFold3 Complex):**
- Validate receptor binding affinity (ipTM, PAE, contacts)
- Check antibody escape site compatibility
- Verify protease pathway parameters
- Confirm immune evasion (mucin domain)
- Assess VP35 antagonism maintenance

**Phase 3d (Rosetta/FoldX):**
- Energy scores reflect viral parameter compatibility
- Final designs certified for all 5 parameters

---

## Monitoring & Troubleshooting

### View Logs
```bash
# Real-time phase logs
docker-compose logs -f phase1-backbone-gen

# All logs
tail -f results/logs/*.log
```

### Check GPU Status
```bash
# During execution
docker exec phase1-backbone-gen nvidia-smi

# Check memory usage
docker stats phase1-backbone-gen
```

### Common Issues

| Problem | Solution |
|---------|----------|
| `CUDA out of memory` | Reduce batch size or use smaller model |
| Harbor pull fails | Verify credentials: `docker login harbor.internal.domain` |
| Phase timeout (>24 hrs) | Check GPU utilization; consider distributed execution via Kubernetes |
| Manifest missing | Phase did not complete; check logs for errors |
| Viral params not applied | Verify YAML syntax in `alphafold_inputs/{target}/viral_params.yaml` |

---

## Next Steps

1. **Review instruction.md** for complete specification
2. **Review environment/README.md** for Docker setup
3. **Prepare input targets** in `alphafold_inputs/` folder with FASTA + YAML
4. **Build and push images** to Harbor
5. **Execute docker-compose** to run pipeline
6. **Validate manifests** at each phase
7. **Select top designs** for wet-lab synthesis

---

## Notes

- **Execution Time:** 48-72 hours (sequential phases, single GPU)
- **GPU Memory:** 40+ GB required for phases 0 and 3b
- **Disk Space:** 500 GB total for all outputs and intermediate files
- **Model Versions:** All locked in Dockerfile base images
- **Reproducibility:** Full provenance recorded in logs and manifests

---

## Additional Resources

- **Full specification:** [instruction.md](instruction.md)
- **Docker setup:** [environment/README.md](environment/README.md)
- **Tool interfaces:** [tool-manifest.json](tool-manifest.json)
- **Output schemas:** `schemas/` directory

---

For task evaluation, all outputs in `/data/phase_*/` are validated against schemas in `schemas/` directory.
