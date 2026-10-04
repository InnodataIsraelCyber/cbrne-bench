# AI-Driven Protein Design Pipeline: Harbor Docker Production Operations Guide

**Version:** 2.0 (Docker/Harbor)  
**Last Updated:** 2026-10-04  
**Purpose:** Containerized standardized procedures for designing de novo protein binders targeting viral proteins with enhanced biological parameters (e.g., Ebola VP35, GP with viral escape variants)

---

## Table of Contents

1. [Prerequisites & Environment Setup](#prerequisites--environment-setup)
2. [Harbor Registry Configuration](#harbor-registry-configuration)
3. [Docker Container Architecture](#docker-container-architecture)
4. [Viral Protein Design Parameters](#viral-protein-design-parameters)
5. [Phase 0: Target Preparation](#phase-0-target-preparation)
6. [Phase 1: Backbone Generation](#phase-1-backbone-generation)
7. [Phase 2: Sequence Design](#phase-2-sequence-design)
8. [Phase 3: Validation & Ranking](#phase-3-validation--ranking)
9. [Quality Assurance & Checkpoints](#quality-assurance--checkpoints)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites & Environment Setup

### Required Software & Dependencies

#### Local Environment
- **Docker Engine:** v24.0+ with GPU support (nvidia-docker2)
- **Harbor Registry:** v2.8+ (or compatible container registry)
- **Kubernetes (optional):** v1.28+ for distributed execution
- **Harbor Credentials:** Registry URL, username, password stored in `~/.docker/config.json`

#### Container-Based Components (pulled from Harbor)
- **Structure Prediction Models:**
  - `harbor.io/protein-design/alphafold2:latest` (40+ GB GPU memory)
  - `harbor.io/protein-design/alphafold3:latest` (40+ GB GPU memory)
  - `harbor.io/protein-design/esmfold:latest` (8 GB GPU memory)
  - `harbor.io/protein-design/boltz-2:latest` (40+ GB GPU memory)

- **Generative Design Models:**
  - `harbor.io/protein-design/rfdiffusion:latest` (backbone generation)
  - `harbor.io/protein-design/boltzgen:latest` (nanobody/peptide generation)

- **Sequence Design:**
  - `harbor.io/protein-design/proteinmpnn:latest` (inverse folding)

- **Validation & Scoring:**
  - `harbor.io/protein-design/rosetta:latest` (energy calculations)
  - `harbor.io/protein-design/foldx:latest` (binding energy scoring)
  - `harbor.io/protein-design/pymol:latest` (structure visualization)

- **Analysis Tools:**
  - `harbor.io/protein-design/analysis-toolkit:latest` (BioPython, NumPy/SciPy)

### Compute Resources

| Task | Minimum GPU | Recommended GPU | CPU Cores | Memory |
|------|-------------|-----------------|-----------|--------|
| AF2/AF3 predictions | 8 GB | 40+ GB (A100/H100) | 4 | 32 GB |
| RFdiffusion (50 structures) | 16 GB | 40+ GB | 8 | 64 GB |
| ProteinMPNN batch (1000 designs) | 8 GB | 24+ GB | 8 | 32 GB |
| Rosetta scoring | - | - | 16+ | 64 GB |

### Input Data Repository Structure

```
project_root/
├── targets/
│   ├── ebola_vp35_iid/
│   │   ├── sequence.fasta
│   │   └── viral_params.yaml
│   └── ebola_gp/
│       ├── sequence.fasta
│       └── viral_params.yaml
├── designs/
│   ├── backbones/
│   ├── sequences/
│   └── validated/
├── results/
│   ├── phase_0/
│   ├── phase_1/
│   ├── phase_2/
│   └── phase_3/
├── logs/
├── docker/
│   ├── Dockerfile.phase0
│   ├── Dockerfile.phase1
│   ├── Dockerfile.phase2
│   └── Dockerfile.phase3
└── docker-compose.yml
```

---

## Harbor Registry Configuration

### 1. Harbor Registry Setup

```yaml
# harbor-config.yaml
harbor_url: https://harbor.internal.domain
harbor_project: protein-design
harbor_username: ${HARBOR_USER}
harbor_password: ${HARBOR_PASSWORD}
```

### 2. Docker Authentication

```bash
# Login to Harbor registry
docker login -u ${HARBOR_USER} -p ${HARBOR_PASSWORD} harbor.internal.domain

# Test connectivity
docker pull harbor.internal.domain/protein-design/analysis-toolkit:latest
```

### 3. Container Image Tagging & Versioning

All container images follow semantic versioning:
```
harbor.internal.domain/protein-design/<component>:<version>-<model-variant>
Example: harbor.internal.domain/protein-design/alphafold3:2.3.0-gpu
```

### 4. Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Phase 0: Target Preparation
  phase0-target-prep:
    image: harbor.internal.domain/protein-design/alphafold3:latest
    container_name: phase0_target_prep
    volumes:
      - ./targets:/data/targets
      - ./results/phase_0:/data/results
      - ./logs:/data/logs
    environment:
      - GPU_DEVICE=0
      - CUDA_VISIBLE_DEVICES=0
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  # Phase 1: Backbone Generation
  phase1-backbone-gen:
    image: harbor.internal.domain/protein-design/rfdiffusion:latest
    container_name: phase1_backbone_gen
    volumes:
      - ./targets:/data/targets
      - ./results/phase_0:/data/phase0_input
      - ./results/phase_1:/data/results
      - ./logs:/data/logs
    environment:
      - GPU_DEVICE=0
      - CUDA_VISIBLE_DEVICES=0
    depends_on:
      - phase0-target-prep
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  # Phase 2: Sequence Design
  phase2-seq-design:
    image: harbor.internal.domain/protein-design/proteinmpnn:latest
    container_name: phase2_seq_design
    volumes:
      - ./results/phase_1:/data/backbones
      - ./results/phase_2:/data/results
      - ./logs:/data/logs
    environment:
      - GPU_DEVICE=0
      - CUDA_VISIBLE_DEVICES=0
    depends_on:
      - phase1-backbone-gen
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  # Phase 3a: Monomer Validation
  phase3a-monomer:
    image: harbor.internal.domain/protein-design/esmfold:latest
    container_name: phase3a_monomer
    volumes:
      - ./results/phase_2:/data/sequences
      - ./results/phase_1:/data/backbones
      - ./results/phase_3/step_3a_monomer:/data/results
      - ./logs:/data/logs
    environment:
      - GPU_DEVICE=0
      - CUDA_VISIBLE_DEVICES=0
    depends_on:
      - phase2-seq-design
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  # Phase 3b: Complex Prediction
  phase3b-complex:
    image: harbor.internal.domain/protein-design/alphafold3:latest
    container_name: phase3b_complex
    volumes:
      - ./results/phase_2:/data/sequences
      - ./results/phase_3/step_3a_monomer:/data/monomer_input
      - ./results/phase_3/step_3b_complex:/data/results
      - ./logs:/data/logs
    environment:
      - GPU_DEVICE=0
      - CUDA_VISIBLE_DEVICES=0
    depends_on:
      - phase3a-monomer
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  # Phase 3c: Ranking
  phase3c-ranking:
    image: harbor.internal.domain/protein-design/analysis-toolkit:latest
    container_name: phase3c_ranking
    volumes:
      - ./results/phase_3:/data/input
      - ./results/phase_3/step_3c_ranking:/data/results
      - ./logs:/data/logs

  # Phase 3d: Energy Scoring
  phase3d-energy:
    image: harbor.internal.domain/protein-design/rosetta:latest
    container_name: phase3d_energy
    volumes:
      - ./results/phase_3/step_3c_ranking:/data/structures
      - ./results/phase_3/step_3d_energy_scoring:/data/results
      - ./logs:/data/logs
    depends_on:
      - phase3c-ranking
```

---

## Docker Container Architecture

### Phase 0 Dockerfile (Target Preparation)

```dockerfile
# Dockerfile.phase0
FROM nvidia/cuda:12.2.2-devel-ubuntu22.04

WORKDIR /app

# Install base dependencies
RUN apt-get update && apt-get install -y \
    wget curl git python3.10 python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install AlphaFold3 and dependencies
RUN pip install --no-cache-dir \
    biopython==1.83 \
    dm-tree \
    dm-haiku \
    dm-sonnet \
    ml-collections \
    numpy==1.25.2 \
    pandas \
    jax[cuda12_cudnn82]==0.4.20

# Copy AlphaFold3 code
COPY alphafold3/ /app/alphafold3/
RUN pip install -e /app/alphafold3/

# Copy entrypoint script
COPY scripts/run_phase0.py /app/run_phase0.py

ENV CUDA_VISIBLE_DEVICES=0
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python3", "/app/run_phase0.py"]
```

### Phase 1 Dockerfile (Backbone Generation)

```dockerfile
# Dockerfile.phase1
FROM nvidia/cuda:12.2.2-devel-ubuntu22.04

WORKDIR /app

RUN apt-get update && apt-get install -y \
    wget curl git python3.10 python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install RFdiffusion dependencies
RUN pip install --no-cache-dir \
    biopython==1.83 \
    dm-tree \
    dm-haiku \
    numpy==1.25.2 \
    pandas \
    pytorch::pytorch=*[build=py*_cuda*] \
    pytorch::pytorch-cuda=12.2

# Copy RFdiffusion code
COPY rfdiffusion/ /app/rfdiffusion/
RUN pip install -e /app/rfdiffusion/

COPY scripts/run_phase1.py /app/run_phase1.py

ENV CUDA_VISIBLE_DEVICES=0
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python3", "/app/run_phase1.py"]
```

### Phase 2 Dockerfile (Sequence Design)

```dockerfile
# Dockerfile.phase2
FROM nvidia/cuda:12.2.2-devel-ubuntu22.04

WORKDIR /app

RUN apt-get update && apt-get install -y \
    wget curl git python3.10 python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install ProteinMPNN dependencies
RUN pip install --no-cache-dir \
    biopython==1.83 \
    numpy==1.25.2 \
    pandas \
    pytorch::pytorch=*[build=py*_cuda*] \
    pytorch::pytorch-cuda=12.2

COPY proteinmpnn/ /app/proteinmpnn/
RUN pip install -e /app/proteinmpnn/

COPY scripts/run_phase2.py /app/run_phase2.py

ENV CUDA_VISIBLE_DEVICES=0
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python3", "/app/run_phase2.py"]
```

### Phase 3 Dockerfile (Validation & Ranking)

```dockerfile
# Dockerfile.phase3
FROM nvidia/cuda:12.2.2-devel-ubuntu22.04

WORKDIR /app

RUN apt-get update && apt-get install -y \
    wget curl git python3.10 python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install validation tools
RUN pip install --no-cache-dir \
    biopython==1.83 \
    numpy==1.25.2 \
    pandas \
    scikit-learn \
    pytorch::pytorch=*[build=py*_cuda*] \
    pytorch::pytorch-cuda=12.2

# Install Rosetta (if using)
RUN wget https://release.bagellab.org/latest/rosetta.tar.gz && \
    tar -xzf rosetta.tar.gz && \
    rm rosetta.tar.gz

# Install FoldX (if using)
COPY foldx/ /app/foldx/

COPY scripts/run_phase3.py /app/run_phase3.py

ENV CUDA_VISIBLE_DEVICES=0
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python3", "/app/run_phase3.py"]
```

---

## Viral Protein Design Parameters

### Overview of Target Parameters

This pipeline now incorporates advanced viral adaptation parameters based on EBOV (Ebola) VP35 and GP mutations observed in field isolates (2018-2020 outbreak). These parameters guide design toward enhanced biological function while enabling immune evasion analysis.

---

### Parameter 1: Receptor Binding Affinity (GP-V75A)

**Biological Context:**
- The GP-V75A substitution emerged during the 2018-2020 outbreak
- Increases binding affinity to human receptor NPC1 (Niemann-Pick C1)
- Enhances viral entry while reducing neutralizing antibody efficacy
- Creates a trade-off between receptor engagement and antibody recognition

**Design Integration:**

```yaml
# receptor_binding_params.yaml
receptor_binding_affinity:
  target_residues:
    - position: 75
      wt_residue: V  # Wild-type valine
      variant: A     # Alanine substitution
      target: NPC1   # Human receptor
  
  optimization_metrics:
    - kd_target: <100 nM           # Binding dissociation constant
    - binding_energy_delta: -5 to -8 kcal/mol  # Favorable binding
    - contact_count_min: 15        # Minimum interface contacts
    - interface_area_min: 400 Ų    # Solvent-accessible surface area
  
  design_constraints:
    - preserve_gp_fold: true       # Maintain GP structural integrity
    - maintain_trimerization: true # GP forms trimeric spikes
    - allow_epitope_escape: true   # Can reduce antibody recognition
    - npc1_hotspots: ["Y127", "H151", "E164"]  # NPC1 binding sites
```

**Pipeline Integration (Phase 1-3):**

```python
# In RFdiffusion backbone generation
hotspot_residues = ["A75"]  # Force GP-V75A position into interface
additional_constraints = {
    "npc1_binding_sites": ["Y127", "H151", "E164"],
    "binding_affinity_target": "<100 nM",
    "design_for_escape": True
}

# In Phase 3b (Complex Prediction)
interface_metrics = {
    "ipTM_threshold": 0.5,  # Interface predicted TM-score
    "interface_pae": "<5 Å",
    "binding_energy": "<-5 kcal/mol",
    "contact_predictions": 15  # Minimum residue pairs within 5 Å
}
```

**Validation Checkpoints:**
- [ ] GP-V75A position successfully incorporated into binder interface
- [ ] Predicted binding energy: -5 to -8 kcal/mol
- [ ] Interface contacts: ≥15 residue pairs within 5 Å
- [ ] NPC1 receptor contacts preserved in complex prediction

---

### Parameter 2: Antibody Escape Sites (Watch List)

**Biological Context:**
- 127 mutations across 21 sites computationally identified via FoldX
- Predicted to disrupt antibody binding (ΔΔG_Bind > 2 kcal/mol)
- Maintain GP folding and trimerization while evading mAbs

**Key Epitope Targets:**
1. **GP1/GP2 Interface** → mAb114 (clinically approved therapy)
2. **Mucin-Like Domain** → 13F6-1-2
3. **RBD (Receptor Binding Domain)** → 1A10-Fc, RENG-3471

**Design Integration:**

```yaml
# antibody_escape_params.yaml
escape_site_watch_list:
  epitope_1_gp1_gp2_interface:
    antibody: mAb114
    escape_positions: [40, 42, 43, 85, 88, 89, 90]
    binding_disruption_target: "ΔΔG_Bind > 2 kcal/mol"
    notes: "Clinically approved antibody target"
    
  epitope_2_mucin_like_domain:
    antibody: 13F6-1-2
    escape_positions: [15, 16, 17, 20, 25, 32, 38]
    binding_disruption_target: "ΔΔG_Bind > 2 kcal/mol"
    notes: "Glycan shield domain"
    
  epitope_3_rbd:
    antibody: 1A10-Fc, RENG-3471
    escape_positions: [71, 72, 73, 74, 75, 76, 77]
    binding_disruption_target: "ΔΔG_Bind > 2 kcal/mol"
    notes: "V75A reduces 1A10-Fc potency"
    
  conformational_constraints:
    - maintain_prefusion_stability: true
    - gp_folding_tolerance: "ΔΔG_fold < 1 kcal/mol"
    - trimer_stability: "Maintain inter-monomer contacts"
    - backbone_rmsd_tolerance: "< 2.0 Å to WT"

foldx_mutation_scan:
  output_metrics:
    - ddg_bind: "Change in binding energy"
    - ddg_fold: "Change in folding stability"
    - pdb_contact_analysis: "Residue-residue interactions"
    - sasa_change: "Change in solvent exposure"
```

**Pipeline Integration:**

```python
# FoldX mutation scanning (Phase 3d)
escape_mutations = [40, 42, 43, 85, 88, 89, 90, 15, 16, 17, 71, 72, 73, 74, 75, 76, 77]

for position in escape_mutations:
    for wt_aa in gp_sequence[position]:
        for variant_aa in 'ACDEFGHIKLMNPQRSTVWY':
            if wt_aa != variant_aa:
                ddg_bind = foldx_mutate(complex_pdb, position, variant_aa)
                ddg_fold = foldx_mutate(monomer_pdb, position, variant_aa)
                
                if ddg_bind > 2.0 and ddg_fold < 1.0:
                    log_escape_mutation(position, variant_aa, ddg_bind, ddg_fold)
```

**Validation Checkpoints:**
- [ ] FoldX scan identifies ≥10 escape mutations with ΔΔG_Bind > 2 kcal/mol
- [ ] Escape mutations maintain GP folding stability (ΔΔG_fold < 1 kcal/mol)
- [ ] Epitope positions 71-77 variant-analyzed for 1A10-Fc/RENG-3471 escape
- [ ] Manually review top escape candidates in PyMOL

---

### Parameter 3: Protease Dependence (Entry Pathway)

**Biological Context:**
- GP-V75A reduces dependence on endosomal cysteine proteases
- Mutations destabilize prefusion conformation
- Enhance proteolysis by alternative host proteases
- Reduce fusion activation threshold across cell types

**Design Integration:**

```yaml
# protease_dependence_params.yaml
protease_pathway:
  endosomal_cysteine_proteases:
    - cathepsin_L
    - cathepsin_B
    - cathepsin_S
  
  gp1_gp2_cleavage_dependency:
    current: "High - requires cathepsin L/B"
    target_design: "Reduced - enables cathepsin-independent entry"
    cleavage_sites: [461, 462]  # Known cleavage positions
    destabilization_regions: [440, 450, 460, 470]
  
  prefusion_stability:
    target_stability_free_energy: "-3 to -5 kcal/mol"  # Moderately stable
    fusion_trigger_sensitivity: "Lower threshold for activation"
    alternative_protease_sensitivity:
      - trypsin: "Sensitive (preferred)"
      - plasmin: "Sensitive (preferred)"
      - elastase: "Neutral"
  
  design_mutations:
    - position_range: [440, 470]  # Prefusion conformation region
      design_principle: "Subtle destabilization without complete unfolding"
      constraint: "Maintain tri-molecular assembly"
      
  host_cell_variability:
    target: "Enhanced infectivity across protease-diverse cell types"
    cell_types_included:
      - epithelial: "Low cathepsin expression"
      - macrophage: "High cathepsin expression"
      - dendritic: "Varied protease profile"
```

**Scoring Metrics:**

```python
# Protease pathway scoring (Phase 3)
prefusion_stability_score = calculate_rosetta_stability(
    pdb_file,
    region=[440, 470],
    target_ddg=-3 to -5  # kcal/mol
)

protease_cleavage_accessibility = calculate_foldx_interaction_energy(
    gp1_gp2_interface,
    accessibility_target="moderate"
)

fusion_threshold_assessment = qualitative_review(
    prefusion_conformation,
    mutation_sites=[461, 462],
    conformational_flexibility="increased"
)
```

**Validation Checkpoints:**
- [ ] Prefusion stability score: -3 to -5 kcal/mol (moderately destabilized)
- [ ] Cleavage site accessibility increased vs. WT
- [ ] Trimer contacts maintained (RMSD <2 Å in inter-monomer interfaces)
- [ ] No unintended loss of GP folding stability

---

### Parameter 4: Immune Evasion via Steric Shielding

**Biological Context:**
- Mucin-like domain acts as "glycan umbrella"
- Occludes access to epitopes and host protein binding sites
- Reduces T cell MHC-I recognition by 10-50 fold
- Existing parameter; does NOT require de novo design

**Design Integration:**

```yaml
# immune_evasion_steric_params.yaml
mucin_like_domain:
  position_range: [1, 50]  # N-terminal mucin-like region
  mechanism: "Glycan shield"
  epitope_occlusion_fold_reduction: 10 to 50
  
  design_consideration:
    principle: "PRESERVE existing mucin domain"
    action: "Do NOT design mutations in positions 1-50"
    rationale: "Evolutionary optimized; disruption reduces evasion"
  
  glycosylation_sites:
    - N88
    - N117
    - N130
    - N149
    - N176
    - N227
    - N238
    - S128
    - T140
    - S156
  
  glycan_shield_function:
    target_epitope_reduction: "10-50 fold"
    mechanism_list:
      - "Physical steric occlusion of antibody epitopes"
      - "Reduction of MHC-I presentation efficiency"
      - "Prevention of accessory protein (tetherin, SERINC) recognition"
  
  validation_metrics:
    - buried_surface_area_epitope: "> 50% buried by glycans"
    - accessibility_score: "Low for RBD epitopes 71-77"
    - mhc_presentation_inhibition: "Measured qualitatively from literature"
```

**Pipeline Handling:**

```python
# Constraint definition for Phase 1 (Backbone Generation)
preserved_regions = {
    "mucin_like_domain": [1, 50],  # PRESERVE - do not design
    "glycosylation_sites": [88, 117, 130, 149, 176, 227, 238]
}

# During Phase 1 RFdiffusion
rfdiffusion_contig = "A1-50/0 DESIGN_BINDER"  # Include mucin domain in anchor
rfdiffusion_constraints = {
    "chain_break_after": 50,  # Separate after mucin shield
    "fixed_regions": [1, 50],  # Do NOT design in mucin
    "design_regions": [51, end]  # Design only post-mucin
}

# During Phase 3c/3d validation
validate_glycosylation_integrity(
    backbone_structures,
    expected_sites=[88, 117, 130, 149, 176, 227, 238]
)
```

**Validation Checkpoints:**
- [ ] Mucin-like domain (positions 1-50) PRESERVED - no mutations introduced
- [ ] Glycosylation sites intact in all designs
- [ ] Interface design focused on RBD and GP1/GP2 junction (post-position 50)
- [ ] Visual inspection confirms glycan shield preserved

---

### Parameter 5: Interferon Antagonism (VP35)

**Biological Context:**
- VP35 interferon inhibitory domain (IID) critical for evasion
- Central basic patch centered on R312 required for dsRNA binding
- Mutations in basic patch impair IFN antagonism
- VP35 modifications generally reduce virulence rather than enhance it
- Screening focuses on maintaining antagonism while evading adaptive immunity

**Design Integration:**

```yaml
# interferon_antagonism_vp35_params.yaml
vp35_iid_domain:
  position_range: [240, 330]  # IFN inhibitory domain
  critical_residue: R312  # Central basic patch anchor
  
  mechanism:
    primary: "dsRNA binding and sequestration"
    target: "MDA5 and RIG-I recognition evasion"
    functional_output: "IFN-β antagonism"
  
  basic_patch_definition:
    central_residue: R312
    cluster_radius: 15  # Angstroms
    essential_residues: [R302, R312, K313, K314]
    function_maintained_threshold: "≥70% basic patch charge retained"
  
  screening_strategy:
    goal: "Maintain IFN antagonism while evading host adaptive immunity"
    variant_categories:
      - surface_conservative: "R→K substitutions (maintain charge)"
      - epitope_escape: "L→V, I→L substitutions (near-surface)"
      - hidden_cryptic: "Substitutions fully buried in dsRNA interface"
  
  optimization_metrics:
    - dsrna_binding_affinity: "Maintain within 2-fold of WT (Kd)"
    - ifd_folding_stability: "ΔΔG_fold < 1 kcal/mol"
    - epitope_accessibility: "Modified epitopes >50% buried"
    - adaptive_immunity_evasion: "Predicted mAb escape sites"
  
  variant_watch_list:
    exempt_from_design: true
    reason: "VP35 modifications generally reduce virulence"
    optional_screening:
      - R302K  # Charge-conservative
      - R312K  # Central patch variant (test only)
      - Surface loops near R312  # Epitope escape without function loss
```

**Scoring Metrics:**

```python
# VP35 antagonism validation (Phase 3d)
dsrna_binding_score = calculate_rosetta_stability(
    vp35_iid_pdb,
    ligand="synthetic_dsRNA",
    target_binding_affinity="maintain_within_2fold_WT"
)

basic_patch_charge = sum_residue_charge(
    positions=[302, 312, 313, 314],
    threshold_retained=0.70
)

epitope_escape_mutations = foldx_scan(
    vp35_structure,
    target_epitopes=["adaptive_immunity_sites"],
    ddg_bind_threshold=2.0  # kcal/mol
)

antagonism_prediction = qualitative_assessment(
    dsrna_binding_intact=True,
    basic_patch_functional=True,
    adaptive_escape=True
)
```

**Validation Checkpoints:**
- [ ] dsRNA binding affinity maintained within 2-fold of WT
- [ ] Basic patch (R302, R312, K313, K314) ≥70% charge retained
- [ ] VP35 IID domain folding stability: ΔΔG_fold < 1 kcal/mol
- [ ] Optional R→K mutations at surface positions validated
- [ ] Confirm enhanced adaptive immunity evasion without function loss

---

## Phase 0: Target Preparation

### Objective
Obtain high-quality 3D structure and identify binding site on viral target protein.

### Step 0a: Predict Target Structure (Docker Container)

**Input Requirements:**
- Target protein sequence (FASTA format)
- Optional: Multiple Sequence Alignment (a3m or sto format)
- Optional: Homologous template structure (PDB format)

**Procedure:**

#### Docker Execution

```bash
# Run Phase 0 in containerized environment
docker run --gpus all \
  --name phase0_target_prep \
  -v ${PWD}/targets:/data/targets \
  -v ${PWD}/results/phase_0:/data/results \
  -v ${PWD}/logs:/data/logs \
  -e GPU_DEVICE=0 \
  -e CUDA_VISIBLE_DEVICES=0 \
  harbor.internal.domain/protein-design/alphafold3:latest \
  --sequence_file /data/targets/target_sequence.fasta \
  --output_dir /data/results \
  --num_recycles 3 \
  --diffusion_steps 50 \
  --model alphafold3
```

#### Container Entry Script (run_phase0.py)

```python
#!/usr/bin/env python3
import os
import argparse
from pathlib import Path
import json
import logging

logging.basicConfig(
    filename='/data/logs/phase0_execution.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def predict_target_structure(sequence_file, output_dir, model='alphafold3'):
    """
    Predict 3D structure of viral target protein.
    
    Parameters:
    - sequence_file: FASTA format target sequence
    - output_dir: Directory for outputs
    - model: 'alphafold3', 'alphafold2', or 'esmfold'
    """
    
    logging.info(f"Starting target structure prediction with {model}")
    
    # Step 1: Obtain and validate sequence
    with open(sequence_file, 'r') as f:
        fasta_content = f.read()
    
    logging.info(f"Loaded FASTA: {len(fasta_content)} bytes")
    
    # Step 2: Generate MSA if needed (AF2/AF3)
    if model in ['alphafold2', 'alphafold3']:
        logging.info("Generating MSA with MMseqs2...")
        os.system(f"colabfold_search {sequence_file} /tmp/msa")
        msa_file = "/tmp/msa/query.a3m"
    else:
        msa_file = None
    
    # Step 3: Run structure prediction
    logging.info(f"Running {model} inference...")
    
    if model == 'alphafold3':
        cmd = f"""
        python /app/alphafold3/run_inference.py \
          --input {sequence_file} \
          --output_dir {output_dir} \
          --model_name alphafold3 \
          --num_recycles 3
        """
    elif model == 'alphafold2':
        cmd = f"""
        python /app/alphafold/run_alphafold.py \
          --input_dir {os.path.dirname(sequence_file)} \
          --output_dir {output_dir} \
          --fasta_paths {sequence_file} \
          --bsz 4
        """
    elif model == 'esmfold':
        cmd = f"""
        python /app/esmfold/run_fold.py \
          --fasta {sequence_file} \
          --output {output_dir}
        """
    
    os.system(cmd)
    
    # Step 4: Extract confidence metrics
    logging.info("Extracting confidence metrics...")
    pdb_file = f"{output_dir}/result_model_1.pdb"
    
    plddt_scores = extract_plddt_from_pdb(pdb_file)
    pae_matrix = extract_pae_if_available(pdb_file, model)
    
    # Step 5: Validate output
    validation_results = validate_structure(
        pdb_file,
        min_plddt=70,
        min_ptm=0.8,
        expected_size=(100, 1000)
    )
    
    # Step 6: Write QC report
    qc_report = {
        'model': model,
        'sequence_length': len(fasta_content),
        'plddt_avg': float(np.mean(plddt_scores)),
        'plddt_min': float(np.min(plddt_scores)),
        'plddt_high_conf_fraction': float(np.sum(plddt_scores > 90) / len(plddt_scores)),
        'pae_min': float(np.min(pae_matrix)) if pae_matrix is not None else None,
        'validation_passed': validation_results['passed'],
        'validation_warnings': validation_results['warnings']
    }
    
    with open(f"{output_dir}/qc_report.json", 'w') as f:
        json.dump(qc_report, f, indent=2)
    
    logging.info(f"Phase 0 complete. QC report written.")
    
    return validation_results['passed']

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--sequence_file', type=str, required=True)
    parser.add_argument('--output_dir', type=str, required=True)
    parser.add_argument('--model', type=str, default='alphafold3')
    args = parser.parse_args()
    
    success = predict_target_structure(args.sequence_file, args.output_dir, args.model)
    exit(0 if success else 1)
```

**Output Validation (Step 0a):**

✓ **Success Criteria:**
- PDB file generated with all backbone atoms (N, CA, C, O)
- pLDDT score per residue available
- PAE matrix generated (if AF3)
- pTM score ≥ 0.8 (indicates reliable topology)
- File size: 500 KB – 5 MB (typical range)

✓ **Confidence Checks:**
- pLDDT values: >90 for high-confidence regions, <50 flags disorder
- PAE values: <5 Å between confident domains indicates good alignment
- Visual inspection: No obvious clashes or gaps in backbone

**Failure Actions:**
| Issue | Root Cause | Action |
|-------|-----------|--------|
| pLDDT < 70 globally | Target too novel/long | Use ESMFold instead of AF2; increase num_recycles |
| pTM < 0.5 | Poor folding | Verify sequence accuracy; check for anomalies |
| No PAE output | AF2 used (PAE only in AF3) | Re-run with AF3 model |
| Missing regions | Intrinsically disordered | Flag for downstream pipeline; may still proceed |

**Output Storage:**
```
results/phase_0/target_structure/
├── result_model_1.pdb
├── plddt_scores.txt
├── pae_matrix.npy
├── qc_report.json
└── target_sequence.fasta
```

---

### Step 0b: Identify Binding Site with Viral Parameters

**Input Requirements:**
- Target protein PDB file (from Step 0a)
- Target protein sequence (from Step 0a)
- Viral parameter specifications (YAML)

**Docker Execution:**

```bash
# Run binding site detection
docker run --gpus all \
  --name phase0_binding_site \
  -v ${PWD}/targets:/data/targets \
  -v ${PWD}/results/phase_0:/data/results \
  -v ${PWD}/logs:/data/logs \
  harbor.internal.domain/protein-design/analysis-toolkit:latest \
  python /app/detect_binding_site.py \
    --pdb /data/results/result_model_1.pdb \
    --sequence /data/targets/target_sequence.fasta \
    --viral_params /data/targets/viral_params.yaml \
    --method fpocket
```

#### Binding Site Detection Script

```python
#!/usr/bin/env python3
import os
import yaml
import json
import logging
from pathlib import Path
import numpy as np
from Bio import PDB

logging.basicConfig(level=logging.INFO)

def detect_binding_site_with_viral_params(pdb_file, sequence_file, viral_params_file, method='fpocket'):
    """
    Detect cryptic binding sites with viral parameter guidance.
    
    For EBOV-GP targets:
    - Focus on RBD region (positions 71-77) for receptor binding
    - Account for GP1/GP2 interface (positions 40-90)
    - Consider mucin-like domain shielding (positions 1-50)
    """
    
    logging.info(f"Detecting binding site using {method} with viral params")
    
    # Load viral parameters
    with open(viral_params_file, 'r') as f:
        viral_params = yaml.safe_load(f)
    
    # Run detection method
    if method == 'fpocket':
        os.system(f"fpocket -f {pdb_file}")
        pocket_file = pdb_file.replace('.pdb', '_out/pockets/pocket1_atm.pdb')
    elif method == 'cryptobank':
        pocket_file = run_cryptobank(sequence_file)
    
    # Extract pocket residues
    parser = PDB.PDBParser(QUIET=True)
    pocket_structure = parser.get_structure('pocket', pocket_file)
    
    pocket_residues = []
    for model in pocket_structure:
        for chain in model:
            for residue in chain:
                pocket_residues.append(residue.get_id()[1])
    
    # Apply viral parameter constraints
    constrained_hotspots = filter_by_viral_params(
        pocket_residues,
        viral_params
    )
    
    # Generate output
    hotspot_data = {
        'detected_residues': sorted(list(set(pocket_residues))),
        'constrained_hotspots': constrained_hotspots,
        'viral_parameters_applied': {
            'receptor_binding_affinity': viral_params.get('receptor_binding_affinity'),
            'escape_sites': viral_params.get('escape_site_watch_list')
        }
    }
    
    with open('hotspot_residues.json', 'w') as f:
        json.dump(hotspot_data, f, indent=2)
    
    logging.info(f"Identified {len(constrained_hotspots)} hotspot residues")
    
    return constrained_hotspots

def filter_by_viral_params(pocket_residues, viral_params):
    """Apply viral parameter-based filtering to hotspots."""
    
    priority_regions = []
    
    # For EBOV GP
    if 'receptor_binding_affinity' in viral_params:
        priority_regions.extend(viral_params['receptor_binding_affinity']['target_residues'])
    
    # RBD epitope regions
    if 'escape_site_watch_list' in viral_params:
        escape_list = viral_params['escape_site_watch_list']
        if 'epitope_3_rbd' in escape_list:
            priority_regions.extend(escape_list['epitope_3_rbd']['escape_positions'])
    
    # Filter pocket residues to those in priority regions
    constrained_hotspots = [r for r in pocket_residues if r in priority_regions or r in range(40, 90)]
    
    return sorted(constrained_hotspots)[:8]  # Return top 8

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--pdb', required=True)
    parser.add_argument('--sequence', required=True)
    parser.add_argument('--viral_params', required=True)
    parser.add_argument('--method', default='fpocket')
    args = parser.parse_args()
    
    detect_binding_site_with_viral_params(
        args.pdb, args.sequence, args.viral_params, args.method
    )
```

**Output Validation (Step 0b):**

✓ **Success Criteria:**
- Hotspot list: 3–8 residue positions identified
- Crypticity score (if available): ≥0.5
- Pocket volume: 200–800 Ų
- Viral parameter constraints applied (receptor binding, epitope sites)
- Visual confirmation: Pocket identifiable in PyMOL

**Output Storage:**
```
results/phase_0/binding_site/
├── pocket_coordinates.pdb
├── hotspot_residues.json
├── viral_parameters_applied.yaml
├── binding_site_visualization.png
└── binding_site_qc.txt
```

---

## Phase 1: Backbone Generation

### Objective
Generate novel protein backbones geometrically complementary to target binding site with viral parameter constraints.

### Step 1: De Novo Backbone Design with RFdiffusion (Docker Container)

**Docker Execution:**

```bash
docker run --gpus all \
  --name phase1_backbone_gen \
  -v ${PWD}/targets:/data/targets \
  -v ${PWD}/results/phase_0:/data/phase0 \
  -v ${PWD}/results/phase_1:/data/results \
  -v ${PWD}/logs:/data/logs \
  harbor.internal.domain/protein-design/rfdiffusion:latest \
  python /app/run_phase1.py \
    --target_pdb /data/phase0/result_model_1.pdb \
    --hotspots '["A71", "A72", "A75"]' \
    --num_designs 50 \
    --binder_length_range 50 150 \
    --num_diffusion_steps 50 \
    --viral_params /data/targets/viral_params.yaml
```

#### Phase 1 Execution Script

```python
#!/usr/bin/env python3
import os
import yaml
import json
import logging
from pathlib import Path
import numpy as np

logging.basicConfig(
    filename='/data/logs/phase1_execution.log',
    level=logging.INFO
)

def run_rfdiffusion_with_viral_params(
    target_pdb, hotspots, num_designs, binder_length_range, 
    num_diffusion_steps, viral_params_file, output_dir='/data/results'
):
    """
    Run RFdiffusion backbone generation with viral parameter constraints.
    
    Parameters:
    - target_pdb: Target protein structure
    - hotspots: List of hotspot residues (e.g., ["A71", "A72", "A75"])
    - num_designs: Number of backbones to generate (50-100)
    - binder_length_range: (min_length, max_length)
    - num_diffusion_steps: Sampling steps (50-100)
    - viral_params_file: YAML with viral design parameters
    """
    
    logging.info("Starting RFdiffusion backbone generation")
    
    # Load viral parameters
    with open(viral_params_file, 'r') as f:
        viral_params = yaml.safe_load(f)
    
    # Build contig string
    # Example: "A10-100/0 50-150" means keep chain A 10-100, generate binder 50-150 aa
    contig = build_contig_with_viral_constraints(target_pdb, viral_params)
    
    # Create configuration
    config = {
        'input_pdb': target_pdb,
        'contigs': contig,
        'hotspot_res': hotspots,
        'num_designs': num_designs,
        'num_diffusion_steps': num_diffusion_steps,
        'T_temp': 1.0,
        'inference_steps': 200,
        'binder_chain': 'B',  # Binder on chain B
        'checkpoint': '/app/rfdiffusion/model_params/RFdiffusion_model_559dd337.pt'
    }
    
    # Save config
    config_file = f"{output_dir}/rfdiffusion_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    # Run RFdiffusion
    logging.info(f"Contig: {contig}")
    logging.info(f"Hotspots: {hotspots}")
    logging.info(f"Generating {num_designs} backbone structures...")
    
    cmd = f"""
    python /app/rfdiffusion/run_inference.py \
      --config-name=inference \
      inference.output_prefix={output_dir}/design \
      inference.input_pdb={target_pdb} \
      'inference.contigs=[\"{contig}\"]' \
      'inference.hotspot_res={json.dumps(hotspots)}' \
      inference.num_designs={num_designs} \
      inference.num_diffusion_steps={num_diffusion_steps}
    """
    
    os.system(cmd)
    
    # Validate and catalog outputs
    logging.info("Validating generated backbones...")
    
    backbone_catalog = validate_generated_backbones(
        output_dir, expected_count=num_designs, hotspots=hotspots
    )
    
    # Write statistics
    stats = {
        'num_designs_generated': len(backbone_catalog),
        'avg_rmsd_to_hotspot': float(np.mean([b['rmsd_to_hotspot'] for b in backbone_catalog])),
        'all_pass_validation': all(b['valid'] for b in backbone_catalog),
        'viral_parameter_constraints_applied': {
            'hotspot_residues': hotspots,
            'binder_length_range': binder_length_range,
            'receptor_binding_focus': 'GP-V75A region' if 'V75A' in str(viral_params) else 'N/A'
        }
    }
    
    with open(f"{output_dir}/backbone_statistics.json", 'w') as f:
        json.dump(stats, f, indent=2)
    
    logging.info(f"Phase 1 complete: {len(backbone_catalog)} backbones validated")
    
    return backbone_catalog

def build_contig_with_viral_constraints(target_pdb, viral_params):
    """
    Build RFdiffusion contig string that respects viral design parameters.
    
    For EBOV GP:
    - Preserve mucin-like domain (positions 1-50)
    - Target RBD/V75A region (positions 71-77)
    - Design binder chain: 50-150 aa
    """
    
    mucin_domain_end = 50  # PRESERVE positions 1-50
    rbd_start = 71  # RBD region
    rbd_end = 77
    gp_end = 150  # Approximate
    
    # Contig format: "CHAIN_START-END/0 BINDER_START-BINDER_END"
    contig = f"A{mucin_domain_end+1}-{gp_end}/0 50-150"
    
    logging.info(f"Built contig: {contig} (preserving mucin domain 1-{mucin_domain_end})")
    
    return contig

def validate_generated_backbones(output_dir, expected_count, hotspots):
    """Validate all generated backbone structures."""
    
    backbone_catalog = []
    pdb_files = sorted(Path(output_dir).glob("design_*.pdb"))
    
    for pdb_file in pdb_files:
        try:
            validation = {
                'file': str(pdb_file),
                'valid': True,
                'rmsd_to_hotspot': calculate_rmsd_to_hotspots(pdb_file, hotspots),
                'num_atoms': count_atoms_in_pdb(pdb_file),
                'residue_count': count_residues_in_pdb(pdb_file)
            }
            
            # Check validation criteria
            if validation['rmsd_to_hotspot'] > 15.0:
                validation['valid'] = False
                validation['warning'] = 'RMSD to hotspot >15 Å'
            
            backbone_catalog.append(validation)
            
        except Exception as e:
            logging.error(f"Error validating {pdb_file}: {e}")
    
    return backbone_catalog

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--target_pdb', required=True)
    parser.add_argument('--hotspots', type=json.loads, required=True)
    parser.add_argument('--num_designs', type=int, default=50)
    parser.add_argument('--binder_length_range', nargs=2, type=int, default=[50, 150])
    parser.add_argument('--num_diffusion_steps', type=int, default=50)
    parser.add_argument('--viral_params', required=True)
    args = parser.parse_args()
    
    run_rfdiffusion_with_viral_params(
        args.target_pdb,
        args.hotspots,
        args.num_designs,
        tuple(args.binder_length_range),
        args.num_diffusion_steps,
        args.viral_params
    )
```

**Output Validation (Step 1):**

✓ **Success Criteria:**
- 50–100 backbone PDB files generated
- Each file: ~500 bytes – 50 KB
- All files contain valid PDB format
- RMSD to hotspot residues: <15 Å
- Viral parameter constraints respected (hotspot targeting, length range)

**Output Storage:**
```
results/phase_1/backbones/
├── design_000.pdb
├── design_001.pdb
├── ...
├── generation_log.txt
├── rfdiffusion_config.json
└── backbone_statistics.json
```

---

## Phase 2: Sequence Design

### Step 2: Inverse Folding with ProteinMPNN (Docker Container)

**Docker Execution:**

```bash
docker run --gpus all \
  --name phase2_seq_design \
  -v ${PWD}/results/phase_1:/data/backbones \
  -v ${PWD}/results/phase_2:/data/results \
  -v ${PWD}/logs:/data/logs \
  harbor.internal.domain/protein-design/proteinmpnn:latest \
  python /app/run_phase2.py \
    --backbone_dir /data/backbones \
    --output_dir /data/results \
    --design_chain B \
    --num_seq_per_struct 15 \
    --sampling_temp 0.1
```

#### Phase 2 Execution Script

```python
#!/usr/bin/env python3
import os
import json
import logging
from pathlib import Path
import pandas as pd
import numpy as np

logging.basicConfig(
    filename='/data/logs/phase2_execution.log',
    level=logging.INFO
)

def run_proteinmpnn_sequence_design(
    backbone_dir, output_dir, design_chain='B', 
    num_seq_per_struct=15, sampling_temp=0.1
):
    """
    Run ProteinMPNN inverse folding on generated backbones.
    
    Parameters:
    - backbone_dir: Directory containing PDB backbone files
    - output_dir: Output directory for sequences
    - design_chain: Which chain to design (B = binder)
    - num_seq_per_struct: Sequences per backbone
    - sampling_temp: Sampling temperature (lower = more deterministic)
    """
    
    logging.info(f"Starting ProteinMPNN sequence design")
    logging.info(f"Temperature: {sampling_temp}, Sequences per backbone: {num_seq_per_struct}")
    
    # Collect backbone PDB files
    backbone_files = sorted(Path(backbone_dir).glob("design_*.pdb"))
    
    # Create input list
    input_list = []
    for pdb_file in backbone_files:
        input_list.append({
            'pdb_path': str(pdb_file),
            'chain': design_chain
        })
    
    # Save input file list
    input_json = f"{output_dir}/input_list.json"
    with open(input_json, 'w') as f:
        json.dump(input_list, f, indent=2)
    
    # Run ProteinMPNN
    logging.info(f"Running ProteinMPNN on {len(input_list)} backbone structures...")
    
    cmd = f"""
    python /app/proteinmpnn/protein_mpnn_run.py \
      --input_path {input_json} \
      --out_folder {output_dir} \
      --num_seq_per_target {num_seq_per_struct} \
      --sampling_temp {sampling_temp} \
      --autoregressive_score_threshold -5.0 \
      --device cuda:0
    """
    
    os.system(cmd)
    
    # Process and validate outputs
    logging.info("Processing ProteinMPNN outputs...")
    
    sequence_data = parse_proteinmpnn_output(output_dir)
    
    # Write FASTA
    fasta_output = f"{output_dir}/sequences_design.fasta"
    write_fasta(sequence_data, fasta_output)
    
    # Write scores
    scores_output = f"{output_dir}/scores_design.csv"
    df = pd.DataFrame(sequence_data)
    df.to_csv(scores_output, index=False)
    
    # Statistics
    stats = {
        'total_sequences_generated': len(sequence_data),
        'unique_sequences': len(set([s['sequence'] for s in sequence_data])),
        'avg_score': float(np.mean([s['score'] for s in sequence_data])),
        'score_range': [float(np.min([s['score'] for s in sequence_data])), 
                       float(np.max([s['score'] for s in sequence_data]))]
    }
    
    with open(f"{output_dir}/sequence_statistics.json", 'w') as f:
        json.dump(stats, f, indent=2)
    
    logging.info(f"Phase 2 complete: {len(sequence_data)} sequences generated")
    
    return sequence_data

def parse_proteinmpnn_output(output_dir):
    """Parse ProteinMPNN output files."""
    
    sequence_data = []
    
    # Read scores file
    scores_file = f"{output_dir}/scores.txt"
    if not os.path.exists(scores_file):
        logging.warning("Scores file not found; using default scores")
        return []
    
    with open(scores_file, 'r') as f:
        for line in f:
            if line.startswith('>'):
                seq_id = line.strip()
            else:
                sequence = line.strip()
                score = calculate_sequence_score(sequence)  # Simplified
                sequence_data.append({
                    'sequence_id': seq_id,
                    'sequence': sequence,
                    'length': len(sequence),
                    'score': score
                })
    
    return sequence_data

def calculate_sequence_score(sequence):
    """Calculate log-probability score for sequence."""
    return -np.random.uniform(0, 10)  # Placeholder

def write_fasta(sequence_data, output_file):
    """Write sequences to FASTA file."""
    with open(output_file, 'w') as f:
        for data in sequence_data:
            f.write(f">{data['sequence_id']}\n")
            f.write(f"{data['sequence']}\n")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--backbone_dir', required=True)
    parser.add_argument('--output_dir', required=True)
    parser.add_argument('--design_chain', default='B')
    parser.add_argument('--num_seq_per_struct', type=int, default=15)
    parser.add_argument('--sampling_temp', type=float, default=0.1)
    args = parser.parse_args()
    
    run_proteinmpnn_sequence_design(
        args.backbone_dir, args.output_dir,
        args.design_chain, args.num_seq_per_struct, args.sampling_temp
    )
```

**Output Validation (Step 2):**

✓ **Success Criteria:**
- FASTA file with 750–1500 sequences
- CSV file with matching sequence IDs and scores
- Sequence length matches backbone (no gaps)
- Score distribution shows sequence diversity

**Output Storage:**
```
results/phase_2/sequences/
├── sequences_design.fasta
├── scores_design.csv
├── input_list.json
├── sequence_statistics.json
└── execution_log.txt
```

---

## Phase 3: Validation & Ranking

### Step 3a: Self-Consistency Check (Docker Container)

```bash
docker run --gpus all \
  --name phase3a_monomer \
  -v ${PWD}/results/phase_2:/data/sequences \
  -v ${PWD}/results/phase_1:/data/backbones \
  -v ${PWD}/results/phase_3/step_3a_monomer:/data/results \
  -v ${PWD}/logs:/data/logs \
  harbor.internal.domain/protein-design/esmfold:latest \
  python /app/run_phase3a.py \
    --sequences /data/sequences/sequences_design.fasta \
    --output_dir /data/results \
    --model esmfold
```

---

### Step 3b: Complex Prediction with Viral Parameters (Docker Container)

```bash
docker run --gpus all \
  --name phase3b_complex \
  -v ${PWD}/results/phase_2:/data/sequences \
  -v ${PWD}/results/phase_3/step_3a_monomer:/data/monomer \
  -v ${PWD}/results/phase_3/step_3b_complex:/data/results \
  -v ${PWD}/targets:/data/targets \
  -v ${PWD}/logs:/data/logs \
  harbor.internal.domain/protein-design/alphafold3:latest \
  python /app/run_phase3b.py \
    --sequences /data/sequences/sequences_design.fasta \
    --target_sequence /data/targets/target_sequence.fasta \
    --output_dir /data/results \
    --viral_params /data/targets/viral_params.yaml
```

#### Phase 3b Script with Viral Parameter Validation

```python
#!/usr/bin/env python3
import os
import yaml
import json
import logging
from pathlib import Path
import numpy as np
import pandas as pd

logging.basicConfig(
    filename='/data/logs/phase3b_execution.log',
    level=logging.INFO
)

def run_complex_prediction_with_viral_validation(
    sequences_fasta, target_sequence, output_dir, viral_params_file, model='alphafold3'
):
    """
    Run complex prediction with viral parameter-based filtering.
    """
    
    logging.info("Starting complex prediction with viral parameter validation")
    
    # Load viral parameters
    with open(viral_params_file, 'r') as f:
        viral_params = yaml.safe_load(f)
    
    # Run AF3 complex predictions
    logging.info(f"Running {model} complex predictions...")
    
    complex_results = []
    
    # Parse input sequences
    with open(sequences_fasta, 'r') as f:
        seq_id = None
        binder_seq = None
        for line in f:
            if line.startswith('>'):
                seq_id = line.strip()[1:]
            else:
                binder_seq = line.strip()
                
                # Run complex prediction
                complex_result = predict_complex(
                    target_sequence, binder_seq, seq_id, model
                )
                
                # Evaluate with viral parameters
                viral_validation = validate_against_viral_params(
                    complex_result, viral_params
                )
                
                complex_result['viral_validation'] = viral_validation
                complex_results.append(complex_result)
    
    # Filter and rank
    passed_designs = filter_by_viral_parameters(complex_results, viral_params)
    
    # Write results
    results_df = pd.DataFrame(passed_designs)
    results_df.to_csv(f"{output_dir}/interface_metrics.csv", index=False)
    
    logging.info(f"Phase 3b complete: {len(passed_designs)} designs passed viral parameter filters")
    
    return passed_designs

def predict_complex(target_seq, binder_seq, seq_id, model='alphafold3'):
    """Predict complex structure."""
    
    # Create input JSON for AF3
    input_json = {
        'sequences': [
            {'sequence': target_seq, 'proteinToken': True},
            {'sequence': binder_seq, 'proteinToken': True}
        ]
    }
    
    # Run AF3
    output_pdb = f"/tmp/{seq_id}_complex.pdb"
    # ... (run AF3 prediction)
    
    return {
        'sequence_id': seq_id,
        'target_sequence': target_seq,
        'binder_sequence': binder_seq,
        'complex_pdb': output_pdb,
        'ipTM': np.random.random(),  # Placeholder
        'interface_pae': np.random.uniform(0, 1)  # Placeholder
    }

def validate_against_viral_params(complex_result, viral_params):
    """Validate complex against viral design parameters."""
    
    validation = {
        'passes_ipTM': complex_result['ipTM'] >= 0.5,
        'passes_pae': complex_result['interface_pae'] <= 0.35,
        'receptor_binding_affinity_compatible': True,
        'escape_site_compatible': True,
        'viral_parameter_score': 0.0
    }
    
    # Check receptor binding affinity (GP-V75A)
    if 'receptor_binding_affinity' in viral_params:
        if complex_result['ipTM'] >= 0.5 and complex_result['interface_pae'] <= 0.25:
            validation['receptor_binding_affinity_compatible'] = True
    
    # Check escape site compatibility
    if 'escape_site_watch_list' in viral_params:
        validation['escape_site_compatible'] = analyze_escape_site_compatibility(
            complex_result, viral_params
        )
    
    return validation

def filter_by_viral_parameters(complex_results, viral_params):
    """Filter designs by viral parameter thresholds."""
    
    passed = []
    
    for result in complex_results:
        validation = result['viral_validation']
        
        # Mandatory thresholds
        if validation['passes_ipTM'] and validation['passes_pae']:
            # Viral compatibility bonus
            if validation['receptor_binding_affinity_compatible']:
                result['viral_parameter_score'] = result['ipTM'] * 0.5
            passed.append(result)
    
    return passed

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--sequences', required=True)
    parser.add_argument('--target_sequence', required=True)
    parser.add_argument('--output_dir', required=True)
    parser.add_argument('--viral_params', required=True)
    parser.add_argument('--model', default='alphafold3')
    args = parser.parse_args()
    
    run_complex_prediction_with_viral_validation(
        args.sequences, args.target_sequence, args.output_dir, 
        args.viral_params, args.model
    )
```

---

### Step 3c: Ranking & Final Filtering (Docker Container)

```bash
docker run \
  --name phase3c_ranking \
  -v ${PWD}/results/phase_3:/data/input \
  -v ${PWD}/results/phase_3/step_3c_ranking:/data/results \
  -v ${PWD}/logs:/data/logs \
  harbor.internal.domain/protein-design/analysis-toolkit:latest \
  python /app/run_phase3c.py \
    --input_dir /data/input \
    --output_dir /data/results
```

---

### Step 3d: Physics-Based Energy Scoring (Docker Container)

```bash
docker run \
  --name phase3d_energy \
  -v ${PWD}/results/phase_3/step_3c_ranking:/data/structures \
  -v ${PWD}/results/phase_3/step_3d_energy_scoring:/data/results \
  -v ${PWD}/logs:/data/logs \
  harbor.internal.domain/protein-design/rosetta:latest \
  python /app/run_phase3d.py \
    --pdb_dir /data/structures \
    --output_dir /data/results
```

---

## Quality Assurance & Checkpoints

### Design Pipeline Validation Checklist

**After Phase 0:**
- [ ] Target structure PDB generated and visually inspected
- [ ] pLDDT average >70 across entire protein
- [ ] pTM score ≥0.8
- [ ] Hotspot residues identified (3–8 residues, accounting for viral parameters)
- [ ] Binding site volume: 200–800 Ų
- [ ] Viral parameters documented in QC report

**After Phase 1:**
- [ ] 50–100 backbone structures generated (in Docker containers)
- [ ] All backbones contain backbone atoms only (N, CA, C, O)
- [ ] Backbones cluster near hotspot residues (<15 Å RMSD)
- [ ] Viral parameter constraints respected (mucin domain preserved, RBD targeted)
- [ ] No atomic clashes or coordinate anomalies

**After Phase 2:**
- [ ] 750–1500 sequences generated (Docker container verified)
- [ ] All sequences valid (standard 20 amino acids)
- [ ] Sequence length matches backbone
- [ ] ProteinMPNN scores show diversity
- [ ] Top 20% of sequences selected for Phase 3

**After Phase 3a:**
- [ ] 200–500 monomer structures folded (Docker container)
- [ ] RMSD to original backbone <2.5 Å for ≥50% of designs
- [ ] pLDDT >70 for interface regions
- [ ] Low-confidence designs removed

**After Phase 3b:**
- [ ] 100–300 complex structures predicted (Docker container with viral params)
- [ ] ipTM ≥0.5 for ≥30% of designs
- [ ] Interface PAE ≤0.35 for high-confidence designs
- [ ] Viral parameter validation applied (receptor binding affinity, escape sites)
- [ ] Interfaces visually inspected (sample of top 5)

**After Phase 3c:**
- [ ] Final shortlist: 10–20 designs
- [ ] All designs pass mandatory AND viral parameter filters
- [ ] Ranking criteria documented
- [ ] Top design metrics: ipTM ≥0.6, interface PAE ≤0.25

**After Phase 3d:**
- [ ] Energy scores computed for top designs (Rosetta/FoldX in Docker)
- [ ] ΔG <-3 kcal/mol for ≥50% of top designs
- [ ] Shape complementarity >0.55
- [ ] Results correlate with AI metrics
- [ ] Viral parameter compatibility verified

---

### Key Performance Indicators (KPIs)

| KPI | Target | Viral Parameter Note |
|-----|--------|---------------------|
| Design generation rate | >50 backbones/run | RFdiffusion with hotspot constraints |
| Sequence diversity | >80% unique sequences | ProteinMPNN sampling temp=0.1 |
| Self-consistency pass rate | >50% | ESMFold validation |
| Interface confidence pass rate | >30% | AF3 complex prediction |
| Receptor binding affinity designs | ≥5 high-confidence | V75A-compatible binders |
| Escape site compatibility | ≥3 designs | FoldX mutation scanning |
| Final shortlist size | ≥10 designs | Docker pipeline completion |
| Top design ipTM | ≥0.6 | Likely successful in wet-lab |

---

## Troubleshooting

### Docker Container Troubleshooting

| Issue | Symptom | Resolution |
|-------|---------|------------|
| GPU not detected | CUDA error in logs | Run `docker run --gpus all nvidia/cuda:12.2.2 nvidia-smi` |
| Out of memory | CUDA OOM error | Reduce batch size in config; use smaller model |
| Harbor pull failures | `Error pulling image` | Verify Harbor credentials: `docker login harbor.internal.domain` |
| Volume mount errors | `Permission denied` | Use `sudo` or add user to docker group: `usermod -aG docker $USER` |
| Slow inference | Phase takes >24 hrs | Check GPU utilization; consider distributed execution via Kubernetes |

### Data Validation Troubleshooting

| Issue | How to Detect | Fix |
|-------|----------------|-----|
| Corrupt input FASTA | Parse error in Phase 0 | Validate with `seqkit` or BioPython |
| Mismatched sequence/structure | Atom count ≠ residue count | Verify PDB format; check insertion codes |
| Wrong viral parameters file | Phase 1/3 constraints not applied | Confirm YAML syntax and file path |

### Viral Parameter Troubleshooting

| Issue | Root Cause | Solution |
|-------|-----------|----------|
| No designs compatible with receptor binding | Hotspots too constrained | Expand hotspot radius; lower ipTM threshold |
| Escape sites not generated | FoldX scan incomplete | Increase mutation scan coverage; review threshold |
| Protease pathway incompatible | Prefusion stability too high | Relax stability constraints; allow moderate destabilization |
| All designs fail immune evasion | Epitope sites unavoidable | Focus on surface-conservative mutations; use charge-conservative R→K |

---

## Output Summary & Next Steps

### Final Deliverables (After Phase 3, Docker Pipeline)

1. **Top 10–20 designs** with:
   - Complex PDB structure file
   - Amino acid sequence (FASTA)
   - AI confidence metrics (ipTM, PAE, pLDDT)
   - Physics-based energy scores (ΔG, shape complementarity)
   - **Viral parameter validation** (receptor binding affinity, escape site compatibility)

2. **Summary Report** including:
   - Design ranking table with viral parameter scores
   - Docker execution logs and container versions
   - Viral parameter validation results
   - Recommended designs for wet-lab testing

3. **Sequence Files** ready for:
   - Gene synthesis
   - Cloning into expression vectors
   - Recombinant expression trials

### Wet-Lab Next Steps

**Experimental Validation Informed by Viral Parameters:**

1. **Gene synthesis** of top 3–5 designs (prioritize those compatible with:
   - Receptor binding affinity optimization
   - High escape site diversity)

2. **Expression and purification** in E. coli or mammalian cells

3. **Binding assays:**
   - SPR/BLI to measure K_d (target: <100 nM for receptor binding)
   - ELISA with neutralizing antibodies (assess escape compatibility)

4. **Functional assays** (viral inhibition context-dependent):
   - GP-NPC1 binding inhibition (measure displacement)
   - Pseudotyped virus neutralization (assess antibody escape)
   - Protease sensitivity assay (assess fusion pathway dependency)

**Success Criteria:**
- K_d <100 nM for target/receptor binding (viral affinity optimization)
- Reduced neutralization by at least 2 of 3 tested mAbs (escape validation)
- Functional complementarity (inhibit virus entry via GP-dependent mechanisms)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | 2026-10-04 | Docker/Harbor containerization, viral protein parameters |
| 1.0 | 2026-10-04 | Initial production release |

---

**Document Owner:** Protein Design Team  
**Last Reviewed:** 2026-10-04  
**Next Review:** 2027-04-04  
**Harbor Registry:** harbor.internal.domain/protein-design
