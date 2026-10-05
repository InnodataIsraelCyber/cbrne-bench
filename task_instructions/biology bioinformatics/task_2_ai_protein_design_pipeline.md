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

## Appendix A: Real Viral Protein Data & AI Design Methodology

### A.1 Target Viral Proteins (From Authoritative Sources)

#### EBOV GP (Glycoprotein) - Real Sequence - 613 amino acids
**Source:** UniProt Q05320 (VGP_EBOZM) | Zaire Ebolavirus strain Mayinga-76 | OX=128952  
**File Location:** `tasks/task_2/alphafold_inputs/GP_EBOZM.fasta`  
**Publication:** Volchkov et al., 1992, *Virology* 190(2):840-44

```
>sp|Q05320|VGP_EBOZM Envelope glycoprotein OS=Zaire ebolavirus (strain Mayinga-76) OX=128952 GN=GP PE=1 SV=1
MGVTGILQLP RDRFKRTSFF LWVIILFQRT FSIPLGVIHNS TLQVSDVDKL
VCRDKLSSTN QLRSVGLNLE GNGVATDVPS ATKRWGFRSG VPPKVVNYEA
GEWAENCYNL EIKKPDGSEC LPAAPDGIRG FPRCRYVHKV SGTGPCAGDF
AFHKEGAFFL YDRLASTVIY RGTTFAEGVV AFLILPQAKK DFFSSHPLRE
PVNATEDPSS GYYSTTIRYQ ATGFGTNEYE LFEVDNLTLV QLESRFTPQF
LLQLNETIYE TSGKRSNTTT GKLIWKVNPE IDTTIGEWAF WETKKNLTRK
IRSEELSFTV VSNGAKNIDS GQSPARTSSD PGTNTTEDH KIMASENSAS
AMVQVHSQGR EAAVSHLTTL ATISTSPQSL TTKPGPDNST HNTPVYKLDIS
EATQVEQHHR RTDNDSTASDT PSATTAAGPP KAENTNTSKI STDFLDPATT
TSPQNHSETA GNNNTHHQDT GEESASSGKL GLITNTIAGV AGLITIGGRR
TRREAIVNAQ PKCNPNLHYW TTQDEGAAIGL AWIPYFGPAA EGIYIEGLMH
NQDGLICGLR QLANETTQAL QLFLRATTEL RTFSILNRKA IDFLLQRWGG
TCHILGPDCC IEPHDWTKNI TDKIDQIIHD FVDKTLPDQG DNDNWWTGWR
QWIPAGIGVT GVIIAVIALQ CICKFVF
```

**Sequence Properties (EBOV GP - from UniProt):**
- Total length: 613 amino acids (mature form)
- **Functional domains:**
  - **GP1 (N-terminal):** Receptor-binding domain, heavily glycosylated
  - **Linker region:** Furin cleavage site (KR↓)
  - **GP2 (C-terminal):** Fusion protein, transmembrane
- **Key residues:**
  - Mucin-like domain: residues 1-50 (immune evasion via glycosylation)
  - Known epitopes: mAb114, 13F6, RENG regions
  - NPC1 receptor binding: core structural elements

#### EBOV VP35 (Polymerase Cofactor) - Real Sequence - 340 amino acids
**Source:** UniProt Q05127 (VP35_EBOZM) | Zaire Ebolavirus strain Mayinga-76 | OX=128952  
**File Location:** `tasks/task_2/alphafold_inputs/VP35_EBOZM.fasta`  
**Publication:** Volchkov et al., 1992, *Virology* 190(2):840-44

```
>sp|Q05127|VP35_EBOZM Polymerase cofactor VP35 OS=Zaire ebolavirus (strain Mayinga-76) OX=128952 GN=VP35 PE=1 SV=1
MTTRTKGRGHTAATTQNDRMPGPELSGWISEQLMTGRIPVSDIFCDIENNPGLCYASQMQ
QTKPNPKTRNSQTQTDPICNHSFEEVVQTLASLATVVQQQTIASESLEQRITSLENGLKP
VYDMAKTISSLNRVCAEMVAKYDLLVMTTGRATATAAATEAYWAEHGQPPPGPSLYEESA
IRGKIESRDETVPQSVREAFNNLNSTTSLTEENFGKPDISAKDLRNIMYDHLPGFGTAFH
QLVQVICKLGKDSNSLDIIHAEFQASLAEGDSPQCALIQITKRVPIFQDAAPPVIHIRSR
GDIPRACQKSLRPVPPSPKIDRGWVCVFQLQDGKTLGLKI
```

**Sequence Properties (EBOV VP35 - from UniProt):**
- Total length: 340 amino acids (37.5 kDa)
- **Functional role:** Polymerase cofactor, interferon antagonist
- **Structural features:**
  - dsRNA-binding domain (IID domain)
  - Zinc finger-like structural elements
  - Dimeric oligomerization interface
- **Key functions:**
  - Inhibits RIG-I-like receptor signaling
  - Binds double-stranded RNA
  - Blocks interferon-beta production
  - Essential for viral replication

**Functional annotation:**
- Inhibits RIG-I-like receptor signaling
- Binds double-stranded RNA (dsRNA)
- Blocks interferon-beta production
- Essential for viral pathogenesis

**Cross-reference:**
- UniProt: https://www.uniprot.org/uniprotkb/P49951/
- NCBI Protein: https://www.ncbi.nlm.nih.gov/protein/NP_066345.1/
- PubMed: Search "EBOV VP35" for functional studies

---

### A.2 Viral Parameters Configuration (YAML Methodology)

#### ebov_gp_viral_params.yaml
```yaml
---
target_protein: "EBOV_GP"
organism: "Zaire Ebolavirus"
sequence_length: 676
design_objective: "Generate binder for EBOV GP with immune escape and protease sensitivity"

# Parameter 1: Receptor Binding Affinity (GP-V75A mutation impact)
receptor_binding_affinity:
  target_residue: "V75"
  mutation: "V75A"
  optimization_metric: "Kd_reduction"
  target_kd_nm: 50
  binding_energy_range: [-8.0, -5.0]  # kcal/mol
  design_constraints:
    - "Preserve GP fold (RMSD < 2.5 Å)"
    - "Maintain trimerization contacts"
    - "Allow epitope escape"
  validation_checkpoint:
    ipTM_min: 0.5
    PAE_max_angstrom: 5.0
    contact_count_min: 15

# Parameter 2: Antibody Escape Sites
antibody_escape:
  epitope_list:
    - name: "mAb114"
      positions: [77, 78, 79, 80]
      bound_residues: ["G77", "G82", "R89"]
    - name: "13F6-1-2"
      positions: [1, 50]
      bound_residues: ["N1", "S2"]
    - name: "RENG-3471"
      positions: [240, 280]
      bound_residues: ["L240", "E280"]
  num_escape_mutations: 127
  predicted_by: "FoldX"
  validation:
    ddg_bind_threshold: 2.0  # kcal/mol
    ddg_fold_threshold: 1.0  # kcal/mol
    escape_mutations_required: 10

# Parameter 3: Protease Dependence (Entry Pathway)
protease_dependence:
  target: "Reduce_endosomal_cysteine_protease_dependence"
  prefusion_stability_range: [-5.0, -3.0]  # kcal/mol (destabilized)
  alternative_protease_sensitivity:
    - "Trypsin"
    - "Plasmin"
    - "Elastase"
  cleavage_site_accessibility: "Increased"
  constraint: "Maintain trimer contacts"

# Parameter 4: Immune Evasion via Steric Shielding
immune_evasion:
  position_range: [1, 50]
  mechanism: "Glycan_umbrella_occludes_epitopes"
  principle: "PRESERVE_existing_mucin_domain"
  validation:
    glycosylation_sites_intact: true
    epitope_burial_percent: 50.0
    conservation_threshold: 0.95

# Parameter 5: Interferon Antagonism (VP35 IID Mimic)
interferon_antagonism:
  position_range: [240, 330]
  target_residue: "R312"
  mechanism: "Mimic_VP35_basic_patch"
  basic_patch_charge_retention: 0.70
  validation:
    dsRNA_binding_fold: 2.0
    basic_patch_functional: true
    charge_conservation: 0.70

binder_design_spec:
  min_length: 50
  max_length: 150
  secondary_structure_preference: "alpha_helix_rich"
  hydrophobic_core_required: true

ai_model_config:
  alphafold_version: 3.0
  rfdiffusion_inference_steps: 50
  proteinmpnn_temperature: 0.1
  sequence_design_rounds: 15
```

#### ebov_vp35_viral_params.yaml
```yaml
---
target_protein: "EBOV_VP35"
organism: "Zaire Ebolavirus"
sequence_length: 340
design_objective: "Generate VP35-competitive inhibitor with dsRNA binding disruption"

# Parameter 1-5: Similar structure as GP, but focused on dsRNA binding domain
basic_patch_protection:
  target_residues: [312, 313, 316, 320]
  total_basic_residues: 8
  target_positive_charge: 4
  validation:
    charge_per_residue: 1.0
    dsRNA_binding_preserved: true

zinc_finger_domain:
  positions: [250, 270]
  structural_motif: "beta_sheets"
  constraint: "Maintain fold"

dimeric_interface:
  positions: [280, 340]
  homodimer_assembly: "Required"
  interface_area_angstrom2: 1200
```

---

### A.3 Phase 0 AlphaFold3 Output Validation Methodology

**AlphaFold3 outputs (real structure):**
When you run AlphaFold3 on a viral protein target, you get:

1. **result_model_1.pdb** (PDB v3.0 format)
   - All backbone atoms (N, CA, C, O) + side-chain atoms
   - Coordinates with B-factors encoding per-residue confidence (pLDDT)
   - File size: typically 500 KB – 5 MB depending on protein length

2. **pae_matrix.npy** (NumPy array, binary)
   - Pairwise Aligned Error matrix: NxN where N = sequence length
   - Values represent predicted confidence in distance predictions (Ångströms)
   - PAE ≤ 5 Å = high confidence in relative positions
   - PAE > 10 Å = low confidence, possible domain boundaries

3. **plddt_scores.txt** (text file, one float per line)
   - Per-residue confidence score (0–100)
   - pLDDT > 70 = high confidence
   - pLDDT 50–70 = medium confidence
   - pLDDT < 50 = low confidence (likely incorrect)

**Quality control checks (methodology, not fabricated data):**

```json
{
  "validation_rules": {
    "plddt_avg_threshold": ">70 required for pipeline acceptance",
    "plddt_high_conf_fraction": ">80% of residues with pLDDT>70 recommended",
    "pae_statistics": "Check median PAE (should be <20 Å for globular proteins)",
    "ptm_score": "AlphaFold2 metric; not used in AF3 (ignore if present)",
    "iptm_score": "Interface predicted TM-score (only for complexes); not applicable for monomers",
    "file_size_check": "500 KB – 5 MB for typical viral protein",
    "coordinate_anomalies": "Check for Inf, NaN, or outlier coordinates"
  }
}
```

**How to obtain hotspot residues (real methodology):**

1. **Map known epitopes** (from literature):
   - mAb114 epitope (from PDB co-crystal or paper)
   - 13F6 epitope (from published data)
   - RENG epitope (if available)
   
2. **Compute conservation** using:
   - MSA (Multiple Sequence Alignment) of EBOV strains
   - ConSurf webserver (http://consurf.tau.ac.il/)
   - or manual alignment comparison

3. **Identify predicted interface residues:**
   - Use AlphaFold's PAE to detect contact regions (PAE < 5 Å in local regions)
   - Not by assuming "position 75" has specific role

4. **Cross-reference with PDB structures:**
   - If EBOV GP crystal structure exists (e.g., PDB 5JQ3, 6P5Z), compare
   - Map real epitope coordinates from published structures
   - Document source of each functional annotation

---

### A.4 Phase 1-2 Designed Sequence Output Validation

**Real ProteinMPNN/RFdiffusion outputs (methodology):**

When Phase 1-2 complete, you will generate 750–1,500 FASTA sequences. **Characteristics of real designed sequences:**

1. **Diversity:** Sequences should vary significantly from each backbone due to ProteinMPNN sampling temperature (0.1 = mostly conserved, 1.0 = high diversity)

2. **Validity checks:**
   - All 20 standard amino acids (no X, U, Z, B, ambiguous residues)
   - No gaps (continuous, no "-" or ".")
   - Length: 50–150 residues (matches backbone length ±1)
   - No internal stop codons (no "*")

3. **Expected sequence properties:**
   - Mean hydrophobic core score: should reflect binder design (not fully exposed)
   - Secondary structure prediction: should favor alpha-helices if designed for binding
   - Disorder prediction: should be low (<30% disordered residues for structured binder)

**Validation (real methodology):**

```python
from Bio import SeqIO
import numpy as np

# Load designed sequences
sequences = SeqIO.parse("sequences_design.fasta", "fasta")

# Check validity
valid_residues = set("ACDEFGHIKLMNPQRSTVWY")
for record in sequences:
    assert len(record.seq) >= 50 and len(record.seq) <= 150, "Length out of range"
    assert all(aa in valid_residues for aa in record.seq), "Invalid residue"
    assert record.seq[-1] != "*", "Stop codon present"

print(f"✓ All {len(sequences)} sequences valid")
```

**Important:** Do NOT trust the fabricated "design_001, design_002, ..." examples from the previous version. Those sequences were repetitive and identical-looking. Real AI-designed sequences will show diversity and may include unusual compositions depending on the target binding site.

---

### A.5 Phase 3b Complex Prediction Metrics (Validation Framework, Not Fabricated Data)

**What Phase 3b AlphaFold3 complex prediction actually generates:**

When you run AlphaFold3 on binder + target complexes, you get:

1. **complex_*.pdb** files
   - Contains both chains: target (A) + binder (B)
   - Predicted coordinates with confidence scores (B-factors)
   - File size: 1–10 MB depending on complex size

2. **ipTM score** (interaction pTM)
   - Predicts confidence in predicted relative chain orientation
   - Range: 0.0–1.0
   - ipTM > 0.5 = reasonable interface prediction
   - ipTM > 0.7 = high confidence (likely real interaction)

3. **PAE (Pairwise Aligned Error)**
   - Interface PAE: median PAE at residue-residue contacts
   - Lower PAE = higher confidence
   - Typical interface: PAE 10–30 Å
   - Very good interface: PAE < 5 Å

4. **Interface metrics to compute (not predict):**
   - Contact count: use DSSP or PyMOL to count inter-chain contacts
   - Interface area: buried surface area calculation (NACCESS, PISA)
   - Binding energy: **cannot be directly predicted from AF3; requires Rosetta/FoldX**

**Real validation methodology (what you should do):**

```python
import os
import subprocess
from biopython import SeqIO
from Bio.PDB import PDBParser

# For each designed complex:
for pdb_file in glob.glob("complex_*.pdb"):
    # 1. Check ipTM from AF3 output (in PAE file or PLDDT field)
    ipTM = extract_ipTM_from_plddt_scores(pdb_file)
    
    # 2. Compute interface PAE from pae_matrix.npy
    interface_pae = compute_interface_pae(pae_matrix_npy, chain_A_len, chain_B_len)
    
    # 3. Count contacts using DSSP
    contact_count = count_inter_chain_contacts(pdb_file)
    
    # 4. Compute buried surface area using NACCESS
    buried_area = compute_buried_sasa(pdb_file)
    
    # 5. DO NOT make up binding energy; run Rosetta/FoldX instead
    # rosetta: `rosetta_scripts.default.linuxgccrelease -s complex.pdb -parser:protocol score.xml`
```

**Do NOT use the fabricated metrics CSV from the previous version.** Those values were invented with suspicious precision (e.g., "contact_count: 18, 22, 24, 26"). Real AF3 predictions are noisier and require computational validation.

---

### A.6 Phase 3d Rosetta/FoldX Energy Scoring (Real Methodology)

**What Rosetta and FoldX actually compute:**

**Rosetta (per-design scoring):**
- **ddg_bind:** Change in binding free energy (kcal/mol)
  - Negative = favorable binding
  - Rosetta typically produces values in range -15 to +15
  - Real binders often -3 to -8 kcal/mol
- **ddg_fold:** Change in monomer folding stability
  - Small positive values = slightly destabilized
  - Large positive values = unfolded
  - Should be < 2.0 kcal/mol for viable designs

**FoldX (per-design scoring):**
- **Binding affinity:** Solvent-accessible surface area burial
- **Folding stability:** Per-residue energy decomposition
- **Output format:** CSV with residue-level contributions

**Real workflow (what you actually do):**

```bash
# 1. Prepare Rosetta scorefunction
rosetta_scripts.default.linuxgccrelease \
  -s complex.pdb \
  -parser:protocol score.xml \
  -out:file:scorefile scores.sc

# 2. Extract key metrics from scorefile
# Look for: dG_separated, dG_mono, interface_delta_X (X-ray mode)

# 3. Run FoldX
foldx --command=AnalyzeComplex --pdb=complex.pdb

# 4. Combine results for ranking
```

**Expected output ranges (real data):**
- Strong binders: ddg_bind -7 to -10 kcal/mol
- Moderate binders: ddg_bind -4 to -6 kcal/mol
- Weak binders: ddg_bind -1 to -3 kcal/mol
- Non-binders: ddg_bind > 0 kcal/mol

**Do NOT use the fabricated "design_007: -7.2, design_004: -6.9" data from the previous version.** Those values were:
1. Too precise (real Rosetta has noise ±0.5 kcal/mol)
2. Suspiciously ranged (-7.2 to -5.5 with no outliers)
3. Rank-ordered perfectly with other metrics (correlation = 1.0, biologically impossible)

---

### A.7 Final Design GenBank Record Generation (Real Framework)

**GenBank record structure for AI-designed proteins:**

A proper GenBank record for a synthetic binder gene includes:

```
LOCUS       binder_design_001         450 bp    DNA     linear   SYN 05-OCT-2026
DEFINITION  EBOV GP-binding domain; AI-designed de novo protein.
ACCESSION   AI_DESIGN_001_v1
VERSION     AI_DESIGN_001_v1.1
KEYWORDS    synthetic; protein_design; AlphaFold3; viral_binder.
SOURCE      synthetic construct
  ORGANISM  synthetic construct
COMMENT     Generated by AI-Protein Design Pipeline, Phase 3d.
            Input: EBOV GP target (residues 1-676)
            Design method: RFdiffusion (backbone) + ProteinMPNN (sequence)
            Validation: AlphaFold3 complex prediction + Rosetta energy scoring
            
            Metrics documented in Phase 3d output (DO NOT INVENT):
            - ipTM: [actual value from AF3 output]
            - Interface PAE: [computed from pae_matrix.npy]
            - Rosetta ddg_bind: [actual Rosetta scorefunction output]
            
            This record is a TEMPLATE. For actual designs:
            1. Replace protein sequence with designed sequence
            2. Compute actual codon-optimized DNA sequence
            3. Calculate real SHA-256 hash: sha256sum design.gb
            4. Verify circular closure if plasmid construct
FEATURES             Location/Qualifiers
     source          1..450
                     /organism="synthetic construct"
                     /mol_type="DNA"
                     /topology="linear"
                     
     CDS             1..450
                     /product="EBOV_GP_binding_protein"
                     /note="De novo designed binder to EBOV glycoprotein"
                     /note="Design method: RFdiffusion + ProteinMPNN"
                     /note="Validation: ipTM=[computed], PAE=[computed]"
                     /translation="[ACTUAL SEQUENCE, NOT FABRICATED]"
                     /codon_start=1
                     /db_xref="AlphaFold3:design_complex_metrics"
                     
ORIGIN
        1 [ACTUAL DNA SEQUENCE, NOT FABRICATED]
       [Continue with real sequence]
//
```

**CRITICAL VALIDATION:**
- [ ] Protein sequence: actual output from ProteinMPNN Phase 2
- [ ] DNA sequence: actual output from codon optimization (NOT invented)
- [ ] Metrics: copied directly from Rosetta/FoldX output files
- [ ] SHA-256 hash: computed from actual file (`sha256sum` command), NOT fabricated
- [ ] Translation: reverse-translate DNA → must match protein 100%

**Do NOT use the fabricated GenBank records from the previous version (design_007, design_004, design_010).** Those were fabricated with:
1. Made-up protein sequences
2. Truncated DNA sequences (missing actual nucleotides)
3. Fabricated ipTM and Rosetta scores

---

### A.8 Ranking Summary & Selection Methodology (Real Framework)

**Ranking workflow (actual process, not fabricated results):**

**Step 1: Collect all metrics from phases 0–3d**
- ipTM from AlphaFold3 complex predictions
- Interface PAE (computed from pae_matrix.npy)
- Rosetta ddg_bind scores (from scorefunction output)
- Contact count (computed from PDB structures)
- Viral parameter validation results (binary: PASS/FAIL)

**Step 2: Apply mandatory filters**
```
ipTM ≥ 0.5 AND
interface_PAE ≤ 0.35 AND
ddg_bind ≤ -3.0 kcal/mol AND
All_5_viral_parameters == PASS
```

**Step 3: Compute combined score**
```
score = (ipTM × 0.40) + ((1.0 - PAE/1.0) × 0.30) + (viral_compatibility × 0.30)
```

**Step 4: Rank by score**
- Sort descending (highest score first)
- Take top 10–20 designs

**Real example ranking logic (pseudocode, not fabricated numbers):**
```python
import pandas as pd

# Load all metrics from Phase 3
metrics = pd.read_csv("phase3_all_metrics.csv")

# Apply filters
filtered = metrics[
    (metrics['ipTM'] >= 0.5) &
    (metrics['interface_PAE'] <= 0.35) &
    (metrics['ddg_bind'] <= -3.0) &
    (metrics['viral_compatibility'] == 'PASS')
]

# Compute score
filtered['score'] = (
    filtered['ipTM'] * 0.40 +
    (1.0 - filtered['interface_PAE'] / 1.0) * 0.30 +
    filtered['viral_score'] * 0.30
)

# Rank and select top 20
ranked = filtered.sort_values('score', ascending=False)
top_20 = ranked.head(20)

# Save results
top_20.to_csv("ranked_designs.csv", index=False)
```

**Expected ranking characteristics (real results differ from fabricated version):**
- Scores will have noise and scatter (not perfectly ordered)
- ipTM and ddg_bind may not correlate perfectly (common in protein design)
- Some high ipTM designs may have poor viral compatibility (and thus lower rank)
- Viral parameter compatibility will show variability (not all designs pass all 5 parameters)

**Do NOT expect results like the fabricated ranking CSV (design_007: 0.97, design_004: 0.96, design_010: 0.96).** Those were:
1. Too close together (real scores have wider spread)
2. Perfectly rank-ordered with ipTM, PAE, and ddg_bind (correlation ≠ 1.0 in real data)
3. All passing all viral parameters (real designs trade off parameters)

---

### A.9: Complete EBOV Protein Design Database (JSON)

```json
{
  "metadata": {
    "project": "EBOV glycoprotein and polymerase cofactor AI design",
    "source": "UniProt and Zaire ebolavirus sequence data",
    "target_proteins": ["GP", "VP35"],
    "virus": "Zaire ebolavirus (EBOZ)",
    "strain": "Mayinga-76",
    "last_updated": "2024-01-28"
  },
  "target_proteins": [
    {
      "protein_name": "Glycoprotein (GP)",
      "uniprot_id": "Q05320",
      "gene_name": "GP",
      "length_aa": 613,
      "strain": "Mayinga-76",
      "function": "viral_entry_receptor_binding_membrane_fusion",
      "signal_peptide_aa": "1-34",
      "mature_protein_aa": "35-613",
      "disulfide_bonds": 5,
      "n_glycosylation_sites": 8,
      "receptor_binding_domain": "88-193_mucin_like_domain",
      "fusion_peptide": "503-510",
      "transmembrane_domain": "550-572",
      "hla_epitopes_known": 12,
      "neutralizing_antibody_targets": 4,
      "immunodominant_region": "44_65_base_of_major_antibody_response"
    },
    {
      "protein_name": "Polymerase Cofactor (VP35)",
      "uniprot_id": "Q05127",
      "gene_name": "VP35",
      "length_aa": 340,
      "strain": "Mayinga-76",
      "function": "viral_replication_complex_assembly_innate_immune_suppression",
      "zinc_finger_motif": "119_139_dsRNA_binding",
      "oligomerization_domain": "1_110",
      "interferon_antagonist_activity": "yes_blocks_rIG_I_RLR_signaling",
      "interaction_partners": ["L_polymerase", "NP_nucleoprotein", "VP40_matrix"],
      "key_residues": ["C121", "C124", "C127", "H139"],
      "catalytic_activity": "none_scaffold_protein_only"
    }
  ],
  "alphafold3_design_parameters": {
    "model": "AlphaFold3",
    "confidence_metrics": ["pAE", "pLDDT", "ipTM"],
    "plddt_threshold_high_confidence": 70.0,
    "pae_threshold_nm": 2.5,
    "iptm_target_minimum": 0.50,
    "rmsd_to_template_angstrom": 2.0,
    "clash_score_maximum": 10.0
  },
  "viral_parameters_for_constraint": {
    "parameter_1": {
      "name": "Receptor binding domain (RBD) exposed",
      "target_region_aa": "88_193",
      "sasa_percent_minimum": 50.0,
      "rationale": "must_maintain_human_ACE2_equivalent_receptor_binding"
    },
    "parameter_2": {
      "name": "Fusion peptide accessible",
      "target_region_aa": "503_510",
      "burial_percent_maximum": 20.0,
      "rationale": "must_be_available_for_membrane_insertion_during_fusion"
    },
    "parameter_3": {
      "name": "Glycosylation sites maintained",
      "target_motifs": "N_x_S_N_x_T",
      "site_count_minimum": 6,
      "rationale": "glycosylation_shields_from_antibodies_essential_for_evasion"
    },
    "parameter_4": {
      "name": "Oligomerization domain integrity",
      "target_region_aa": "1_110",
      "rmsd_vs_wild_type_angstrom_maximum": 1.5,
      "rationale": "disruption_would_prevent_viral_replication_complex_assembly"
    },
    "parameter_5": {
      "name": "Fold stability (free energy)",
      "ddg_kcal_mol_maximum": 1.0,
      "rationale": "destabilization_causes_misfolding_loss_of_function"
    }
  },
  "rfdiffusion_protein_design_parameters": {
    "steps": 50,
    "diversity_sampling": 0.85,
    "trajectory_samples": 16,
    "plddt_confidence_filter": 70.0,
    "model_weights": "default_reference_set"
  },
  "proteinmpnn_sequence_design_parameters": {
    "sampling_temperature": 1.0,
    "num_seq_per_target": 8,
    "model_type": "ca_model_with_context",
    "autoregressive_order": "backward",
    "context_radius_angstrom": 10.0
  },
  "foldx_energy_scoring": {
    "force_field": "FoldX4",
    "energy_terms": ["total_energy", "solvation_energy", "backbone_hbond", "side_chain_hbond"],
    "reference_wild_type_kcal_mol": -45.2,
    "ddg_threshold_kcal_mol": 2.0
  },
  "design_workflow_outputs": {
    "total_designs_generated": 24,
    "designs_passing_vp_filters": "12_18_typical_tradeoff",
    "mean_plddt_expected": 80.0,
    "mean_pae_expected": 1.2,
    "mean_iptm_expected": 0.72,
    "designs_selected_for_synthesis": 3
  }
}
```

---

## Notes
- **GPU Requirements:** Phases 0, 3b require 40+ GB VRAM (A100/H100). Phases 1, 2, 3a require 8-24 GB VRAM.
- **Execution Time:** Typical runtime 48-72 hours (4 phases in series). Parallelization via Kubernetes possible.
- **Model Versions:** Use latest AlphaFold3, RFdiffusion, ProteinMPNN from Harbor. Versions locked in Dockerfile.
- **Viral Parameter Flexibility:** Parameters can be customized per target in YAML. Five key parameters incorporated.
- **Wet-Lab Readiness:** Top 10 designs suitable for gene synthesis, expression, and binding validation.
