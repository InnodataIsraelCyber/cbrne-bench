# Task 2 Instruction: AI-Driven Protein Design Pipeline with Harbor Docker

**Task ID:** task_2

## Objective

Execute a containerized **4-phase protein design pipeline** to generate de novo protein binders targeting viral proteins (EBOV VP35, GP) with enhanced biological parameters. Each phase uses specialized Docker containers orchestrated through Harbor registry, incorporating:

- **Viral protein design parameters** (receptor binding affinity, antibody escape sites, protease dependence, immune evasion, interferon antagonism)
- **AI-driven structure and sequence design** (AlphaFold3, RFdiffusion, ProteinMPNN)
- **Validation and physics-based scoring** (ESMFold, Rosetta, FoldX)
- **Systematic filtering and ranking** with viral parameter compatibility

**Success Criteria:**
- All 4 phases complete without errors
- ≥10 final designs pass all validation filters
- Top 3 designs achieve ipTM ≥0.6 and viral parameter compatibility
- All manifest and metric files generated and validated against schemas
- Complete provenance recorded for all tool invocations

---

## Inputs

### Configuration Inputs
| Input | Type | Description | Location |
|-------|------|-------------|----------|
| Target protein | FASTA + YAML | Viral protein sequence + design parameters | `alphafold_inputs/` folder |
| Viral parameters | YAML | Receptor binding, escape sites, protease pathway, immune evasion, VP35 antagonism | `alphafold_inputs/{target}/viral_params.yaml` |
| Design templates | PDB (optional) | Homologous structures (templates for AF3) | `alphafold_inputs/templates/` |
| Harbor registry | URL + credentials | Container image repository | `harbor.internal.domain/protein-design/` |

### Viral Protein Parameter Specifications

**Parameter 1: Receptor Binding Affinity (GP-V75A)**
- Target residues: Position 75 (V→A substitution)
- Optimization metrics: Kd <100 nM, binding energy -5 to -8 kcal/mol
- Design constraints: Preserve GP fold, maintain trimerization, allow epitope escape
- Validation checkpoint: ipTM ≥0.5, PAE <5 Å, interface ≥15 contacts

**Parameter 2: Antibody Escape Sites (Watch List)**
- 127 mutations across 21 sites predicted by FoldX
- Key epitopes: mAb114 (GP1/GP2), 13F6-1-2 (mucin), 1A10-Fc/RENG-3471 (RBD)
- Validation: ΔΔG_Bind >2 kcal/mol, ΔΔG_fold <1 kcal/mol
- Checkpoint: ≥10 escape mutations identified, maintained folding stability

**Parameter 3: Protease Dependence (Entry Pathway)**
- Target: Reduce endosomal cysteine protease dependence
- Prefusion stability: -3 to -5 kcal/mol (moderately destabilized)
- Alternative protease sensitivity: Increase sensitivity to trypsin, plasmin
- Validation: Cleavage site accessibility increased, trimer contacts maintained

**Parameter 4: Immune Evasion via Steric Shielding (Mucin-like Domain)**
- Position range: 1-50 (PRESERVED - no mutations)
- Mechanism: Glycan umbrella occludes antibody epitopes
- Design principle: PRESERVE existing mucin domain structure
- Validation: Glycosylation sites intact, epitopes >50% buried

**Parameter 5: Interferon Antagonism (VP35 IID)**
- Position range: 240-330 (VP35 IFN inhibitory domain)
- Critical residue: R312 (central basic patch)
- Maintenance threshold: ≥70% basic patch charge retained
- Validation: dsRNA binding within 2-fold of WT, basic patch functional

---

## Phase 0: Target Preparation

### Inputs
- Target protein sequence (FASTA)
- Optional: MSA (a3m or sto format)
- Optional: Template structures (PDB)

### Outputs
**Path:** `/data/phase_0/`

| File | Description | Schema |
|------|-------------|--------|
| `result_model_1.pdb` | Predicted target structure | PDB 3.0 format, all backbone atoms |
| `plddt_scores.txt` | Per-residue confidence scores | One float per line, 0-100 range |
| `pae_matrix.npy` | Pairwise aligned error matrix | NumPy array, NxN shape |
| `qc_report.json` | Quality control metrics | phase0_qc_schema |
| `hotspot_residues.json` | Predicted binding site residues | phase0_hotspot_schema |
| `manifest.json` | Phase metadata | phase_manifest_schema |

**Schema: phase0_qc_schema**
```json
{
  "model": "alphafold3|alphafold2|esmfold",
  "sequence_length": integer,
  "plddt_avg": float (0-100),
  "plddt_min": float,
  "plddt_high_conf_fraction": float (>0.7 required),
  "pae_min": float (Ångströms),
  "validation_passed": boolean,
  "validation_warnings": ["string"],
  "timestamp": "ISO8601"
}
```

**Validation Rules:**
- ✓ pLDDT average >70 across entire protein
- ✓ pTM score ≥0.8 (topology confidence)
- ✓ File size: 500 KB – 5 MB
- ✓ All backbone atoms present (N, CA, C, O)
- ✓ No coordinate anomalies (Inf, NaN)

---

## Phase 1: Backbone Generation

### Inputs
- Target PDB structure (from Phase 0)
- Hotspot residues (from Phase 0)
- Viral parameters (receptor binding affinity, mucin domain preservation)

### Outputs
**Path:** `/data/phase_1/`

| File | Description | Schema |
|------|-------------|--------|
| `design_*.pdb` | Generated backbone structures (50-100 files) | PDB 3.0 format, backbone-only |
| `rfdiffusion_config.json` | RFdiffusion configuration | phase1_config_schema |
| `backbone_statistics.json` | Validation metrics for all backbones | phase1_stats_schema |
| `manifest.json` | Phase metadata | phase_manifest_schema |

**Schema: phase1_stats_schema**
```json
{
  "num_designs_generated": integer (50-100),
  "avg_rmsd_to_hotspot": float (<15 Å),
  "all_pass_validation": boolean,
  "viral_parameter_constraints_applied": {
    "hotspot_residues": ["string"],
    "binder_length_range": [integer, integer],
    "receptor_binding_focus": "string",
    "mucin_domain_preserved": boolean
  },
  "timestamp": "ISO8601"
}
```

**Validation Rules:**
- ✓ 50-100 PDB files generated
- ✓ Each file: 500 bytes – 50 KB
- ✓ All backbones contain only backbone atoms (N, CA, C, O)
- ✓ RMSD to hotspot residues <15 Å
- ✓ Binder length within 50-150 amino acids
- ✓ Mucin-like domain (positions 1-50) PRESERVED in target protein
- ✓ Viral parameter constraints respected

---

## Phase 2: Sequence Design

### Inputs
- Backbone structures (from Phase 1)
- Design chain specification (B = binder)
- Sampling parameters (temperature, sequences per backbone)

### Outputs
**Path:** `/data/phase_2/`

| File | Description | Schema |
|------|-------------|--------|
| `sequences_design.fasta` | Designed protein sequences | phase2_fasta_schema |
| `scores_design.csv` | Sequence scoring metrics | phase2_scores_schema |
| `sequence_statistics.json` | Diversity and distribution metrics | phase2_stats_schema |
| `manifest.json` | Phase metadata | phase_manifest_schema |

**Schema: phase2_fasta_schema**
- FASTA format with ≥750 sequences
- Header format: `>design_{backbone_id}_seq_{seq_id}`
- Sequence: 50-150 amino acids, standard 20 residue alphabet
- No gaps, no ambiguous residues

**Schema: phase2_scores_schema**
```csv
sequence_id,sequence,length,score
design_000_seq_001,"MKVVS...",95,-4.23
```

**Validation Rules:**
- ✓ 750-1500 total sequences generated (50 backbones × 15 sequences)
- ✓ All sequences valid (standard 20 amino acids, no gaps)
- ✓ Sequence length matches backbone length (±1 residue tolerance)
- ✓ Score distribution shows diversity (std dev >0.5)
- ✓ Top 20% sequences selected for Phase 3

---

## Phase 3: Validation & Ranking

### Phase 3a: Self-Consistency Check

**Inputs:** Sequences from Phase 2  
**Outputs Path:** `/data/phase_3/step_3a_monomer/`

| File | Description |
|------|-------------|
| `monomer_*.pdb` | Folded monomer structures |
| `monomer_metrics.json` | pLDDT and confidence scores |

**Validation:**
- ✓ RMSD to original backbone <2.5 Å (≥50% of designs)
- ✓ pLDDT >70 for interface regions
- ✓ Remove low-confidence designs (pLDDT <60)

### Phase 3b: Complex Prediction with Viral Parameters

**Inputs:** Monomers (Phase 3a) + Target sequence + Viral parameters  
**Outputs Path:** `/data/phase_3/step_3b_complex/`

| File | Description | Schema |
|------|-------------|--------|
| `complex_*.pdb` | Predicted complex structures | PDB format |
| `interface_metrics.csv` | Binding metrics | phase3b_metrics_schema |
| `viral_validation.json` | Parameter compatibility scores | phase3b_validation_schema |

**Schema: phase3b_metrics_schema**
```csv
sequence_id,ipTM,interface_pae,contact_count,binding_energy_pred,receptor_binding_compatible,escape_site_compatible,viral_score
design_000_seq_001,0.68,0.28,18,-6.2,true,true,0.95
```

**Viral Parameter Validation Rules:**
- ✓ **Receptor binding affinity:** ipTM ≥0.5, interface PAE ≤0.35, ≥15 contacts
- ✓ **Escape sites:** Must NOT occlude antibody epitopes
- ✓ **Protease dependence:** No unintended stabilization of prefusion state
- ✓ **Immune evasion:** Mucin domain preserved (positions 1-50 in target)
- ✓ **VP35 antagonism:** dsRNA binding sites intact (R312 region)

### Phase 3c: Ranking & Final Filtering

**Inputs:** Complex predictions (Phase 3b)  
**Outputs Path:** `/data/phase_3/step_3c_ranking/`

| File | Description |
|------|-------------|
| `ranked_designs.csv` | Final ranked list (top 10-20 designs) |
| `ranking_criteria.json` | Ranking methodology and thresholds |

**Ranking Criteria:**
1. **Mandatory filters:** ipTM ≥0.5, PAE ≤0.35
2. **Viral parameter compatibility:** All 5 parameters validated
3. **Combined score:** ipTM × 0.5 + (1 - PAE/1.0) × 0.3 + viral_compatibility × 0.2

### Phase 3d: Physics-Based Energy Scoring

**Inputs:** Ranked designs (Phase 3c)  
**Outputs Path:** `/data/phase_3/step_3d_energy_scoring/`

| File | Description | Schema |
|------|-------------|--------|
| `energy_scores.csv` | Rosetta/FoldX results | phase3d_energy_schema |
| `final_designs.json` | Top 10-20 designs with all metrics | phase3d_final_schema |

**Schema: phase3d_energy_schema**
```csv
design_id,ddg_bind,ddg_fold,shape_complementarity,interface_area,buried_sasa
top_design_001,-4.2,0.3,0.62,850,1200
```

**Validation Rules:**
- ✓ ΔG <-3 kcal/mol for ≥50% of top designs
- ✓ Shape complementarity >0.55
- ✓ Results correlate with AI metrics (ipTM)
- ✓ Viral parameter compatibility verified

---

## Tools & Interfaces

### Harbor Container Images

**Required Images:**
```
harbor.internal.domain/protein-design/alphafold3:latest
harbor.internal.domain/protein-design/rfdiffusion:latest
harbor.internal.domain/protein-design/proteinmpnn:latest
harbor.internal.domain/protein-design/esmfold:latest
harbor.internal.domain/protein-design/analysis-toolkit:latest
harbor.internal.domain/protein-design/rosetta:latest
```

### Docker Compose Orchestration

All phases execute via docker-compose with:
- Volume mounts for data persistence
- GPU allocation (phases 0-3a require NVIDIA GPU)
- Dependency specification (Phase N depends on Phase N-1)
- Logging configuration

**Docker execution:**
```bash
docker-compose -f docker-compose.yml up --build
```

### Tool Versions & Dependencies

| Tool | Version | Phase | Purpose |
|------|---------|-------|---------|
| AlphaFold3 | 2.3.0+ | 0, 3b | Structure prediction |
| RFdiffusion | Latest | 1 | Backbone generation |
| ProteinMPNN | Latest | 2 | Inverse folding |
| ESMFold | Latest | 3a | Self-consistency |
| Rosetta | 2023.48+ | 3d | Energy scoring |
| FoldX | 5.0+ | 3d | Mutation scanning |
| BioPython | 1.83+ | All | Sequence handling |
| PyYAML | 6.0+ | All | Parameter loading |

---

## Execution Checklist

### Pre-Execution
- [ ] Harbor registry accessible at `harbor.internal.domain`
- [ ] Docker daemon running with GPU support (nvidia-docker2 installed)
- [ ] Target FASTA sequence in `alphafold_inputs/` folder
- [ ] Viral parameters YAML file in `alphafold_inputs/{target}/viral_params.yaml`
- [ ] Docker images pulled from Harbor (all 6 image types)
- [ ] Sufficient disk space: ≥500 GB for pipeline-data
- [ ] GPU memory ≥40 GB (for phases 0, 3b; 8 GB minimum for others)

### Execution Flow
1. **Phase 0:** Run target structure prediction + hotspot detection
2. **Phase 1:** Generate backbones with RFdiffusion (50-100 structures)
3. **Phase 2:** Design sequences with ProteinMPNN (750-1500 sequences)
4. **Phase 3a:** Fold sequences with ESMFold (self-consistency check)
5. **Phase 3b:** Predict complexes with AlphaFold3 + viral parameter validation
6. **Phase 3c:** Rank designs by combined scoring
7. **Phase 3d:** Score with Rosetta/FoldX (final energy evaluation)

### Post-Execution Validation
- [ ] All 4 phases completed without errors
- [ ] All manifest.json files valid against schema
- [ ] ≥10 designs in final shortlist
- [ ] Top 3 designs: ipTM ≥0.6, PAE ≤0.25
- [ ] All 5 viral parameters validated for top designs
- [ ] Complete provenance recorded (all tool invocations logged)
- [ ] Final designs ready for wet-lab synthesis and testing

---

## Notes
- **GPU Requirements:** Phases 0, 3b require 40+ GB VRAM (A100/H100). Phases 1, 2, 3a require 8-24 GB VRAM.
- **Execution Time:** Typical runtime 48-72 hours (4 phases in series). Parallelization via Kubernetes possible.
- **Model Versions:** Use latest AlphaFold3, RFdiffusion, ProteinMPNN from Harbor. Versions locked in Dockerfile.
- **Viral Parameter Flexibility:** Parameters can be customized per target in YAML. Five key parameters incorporated.
- **Wet-Lab Readiness:** Top 10 designs suitable for gene synthesis, expression, and binding validation.
