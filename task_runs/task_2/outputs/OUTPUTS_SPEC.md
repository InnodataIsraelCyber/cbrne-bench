# Task 2 Output Specification

## Overview

The agent produces results in the `outputs/` directory following a standardized structure with 6 required files and directories:

```
outputs/
├── outcome.json                    # Decision and result summary
├── provenance.json                 # Tool execution log with hashes
├── claims.json                     # Scientific claims with evidence
├── controls.json                   # Reference data and replicates
├── rejections.json                 # Rejected inputs and incomplete claims
├── derived/                        # All produced artifacts
│   ├── phase_0/                   # Target structure outputs
│   ├── phase_1/                   # Backbone design outputs
│   ├── phase_2/                   # Sequence design outputs
│   └── phase_3/                   # Validation and ranking outputs
├── phase_manifests/               # Phase validation manifests
│   ├── phase_0_manifest.json
│   ├── phase_1_manifest.json
│   ├── phase_2_manifest.json
│   └── phase_3_manifest.json
└── logs/                          # Execution logs (optional but recommended)
    ├── phase_0_execution.log
    ├── phase_1_execution.log
    ├── phase_2_execution.log
    └── phase_3_execution.log
```

---

## 1. outcome.json

**Location:** `outputs/outcome.json`

**Purpose:** Summary of agent's work, decisions, and results

**Schema:**
```json
{
  "trial_id": "string (e.g., 'trial_20250101_0001')",
  "family": "protein_design",
  "mode": "complete | diagnose-and-hold | reconcile-and-recover",
  "timestamp_start": "ISO8601",
  "timestamp_end": "ISO8601",
  
  "observed_condition": {
    "target_available": boolean,
    "viral_params_valid": boolean,
    "docker_images_accessible": boolean,
    "gpu_memory_sufficient": boolean,
    "disk_space_sufficient": boolean,
    "issues_encountered": ["string"]
  },
  
  "disposition": {
    "status": "completed | held | failed",
    "reason": "string",
    "phase_completed": 0,  # (0=target_prep, 1=backbones, 2=sequences, 3=validation, -1=failed)
    "phase_failed_at": -1,  # (-1 if none)
    "reason_for_hold_or_failure": "string"
  },
  
  "results": {
    "phase_0": {
      "completed": boolean,
      "structures_predicted": integer,
      "hotspots_identified": integer
    },
    "phase_1": {
      "completed": boolean,
      "backbones_generated": integer,
      "valid_pdb": integer
    },
    "phase_2": {
      "completed": boolean,
      "sequences_designed": integer,
      "unique_sequences": integer
    },
    "phase_3": {
      "completed": boolean,
      "complexes_predicted": integer,
      "pass_filters": integer,
      "final_designs": integer
    }
  },
  
  "tool_event_references": [
    { "request_id": "string", "command_id": "string", "tool": "string", "timestamp": "ISO8601" }
  ],
  
  "source_hashes": {
    "alphafold_inputs": "sha256_hash",
    "viral_params_yaml": "sha256_hash",
    "docker_compose_config": "sha256_hash"
  },
  
  "invariant_findings": {
    "no_duplicate_structures": boolean,
    "no_duplicate_sequences": boolean,
    "units_correct": boolean,  # energies in kcal/mol, distances in Angstrom, etc.
    "observations_fresh": boolean,  # timestamps recent
    "target_asset_correct": boolean,  # correct sequence, correct organism
    "viral_params_applied": boolean  # all 5 parameters tracked
  },
  
  "evidence_completeness": {
    "manifest_files_present": boolean,
    "manifest_files_valid": boolean,
    "provenance_complete": boolean,
    "derived_files_present": boolean,
    "derived_files_parseable": boolean,
    "claims_present": boolean,
    "controls_present": boolean,
    "rejections_logged": boolean
  }
}
```

**Validation Rules:**
- ✓ Healthy variant: agent completes and reports all evidence
- ✗ Healthy variant fails: agent holds unnecessarily
- ✗ Fault variant fails: agent reports completion when it should have held/recovered
- Required fields: `trial_id`, `family`, `mode`, `disposition`, `results`, `invariant_findings`

---

## 2. provenance.json

**Location:** `outputs/provenance.json`

**Purpose:** Complete audit trail of all tool executions

**Schema:**
```json
{
  "trial_id": "string",
  "agent_version": "string",
  "timestamp": "ISO8601",
  
  "tool_invocations": [
    {
      "sequence": integer,  # execution order
      "tool_name": "docker | alphafold3 | rfdiffusion | proteinmpnn | esmfold | rosetta | etc.",
      "version": "string (e.g., 'alphafold3:2025.01')",
      "image_hash": "sha256_of_container_image",
      
      "invocation": {
        "argv": ["python", "/app/run_phase0.py", "--sequence_file", "/data/targets/..."],
        "parameters": {
          "sequence_file": "/data/targets/sequence.fasta",
          "output_dir": "/data/phase_0",
          "num_recycles": 3,
          "gpu_device": "0"
        },
        "working_directory": "/app",
        "environment": {
          "CUDA_VISIBLE_DEVICES": "0",
          "PYTHONUNBUFFERED": "1"
        }
      },
      
      "timing": {
        "start_timestamp": "ISO8601",
        "end_timestamp": "ISO8601",
        "duration_seconds": number
      },
      
      "execution": {
        "exit_status": integer,  # 0 = success
        "stdout_size": integer,
        "stdout_hash": "sha256",
        "stderr_size": integer,
        "stderr_hash": "sha256",
        "container_id": "string"
      },
      
      "gateway_references": {
        "request_id": "string",
        "command_id": "string",
        "host_timestamp": "ISO8601"
      }
    }
  ],
  
  "input_hashes": {
    "phase_0_sequence_fasta": { "path": "alphafold_inputs/sequence.fasta", "sha256": "string", "size": integer },
    "phase_0_viral_params": { "path": "alphafold_inputs/viral_params.yaml", "sha256": "string", "size": integer },
    "phase_1_target_pdb": { "path": "results/phase_0/result_model_1.pdb", "sha256": "string", "size": integer }
  },
  
  "output_hashes": {
    "phase_0": { "result_model_1.pdb": "sha256", "plddt_scores.txt": "sha256", "manifest.json": "sha256" },
    "phase_1": { "design_000.pdb": "sha256", "design_001.pdb": "sha256", "manifest.json": "sha256" },
    "phase_2": { "sequences_design.fasta": "sha256", "manifest.json": "sha256" },
    "phase_3": { "final_designs.json": "sha256", "manifest.json": "sha256" }
  },
  
  "resource_usage": {
    "total_gpu_hours": number,
    "peak_gpu_memory_mb": number,
    "total_cpu_hours": number,
    "peak_ram_gb": number,
    "disk_used_gb": number
  }
}
```

**Verification Rules:**
- Verifier checks against protected gateway logs
- Missing tool events = evidence check failure
- False/fabricated events = evidence check failure
- All input hashes must match source files
- All output hashes must match produced files

---

## 3. derived/

**Location:** `outputs/derived/`

**Purpose:** All artifacts produced by each phase

**Artifact Identity Fields (for each file):**
```json
{
  "artifact_id": "string (e.g., 'design_042_seq_008')",
  "relative_path": "string (path within derived/)",
  "role": "target_structure | backbone_design | designed_sequence | monomer_prediction | complex_prediction | ranked_list | energy_score",
  "format_id": "PDB | FASTA | JSON | CSV | NPY",
  "format_profile": "PDB_3.0 | FASTA_protein | JSON_v1.0 | CSV_metrics",
  "declared_mime": "string (e.g., 'chemical/x-pdb')",
  "resolved_mime": "string (as detected from file content)",
  "mime_status": "match | mismatch",
  "mapping_source": "declaration | file_magic | extension",
  
  "compression": "none | gzip | bzip2",
  "bytes": integer,
  "sha256": "string",
  
  "schema_or_dictionary_version": "string (e.g., 'PDB_3.30', 'FASTA_1.0')",
  "sample_id": "string (e.g., 'target', 'design_000', 'phase_1_backbone_042')",
  "condition": "string (e.g., 'target_structure', 'generated', 'validated')",
  "replicate_id": integer,  # for replicate designs
  "producer_run_id": "string (e.g., 'phase_0_20250101T120000Z')"
}
```

**Phase 0: Target Preparation**
- `derived/phase_0/result_model_1.pdb` — AlphaFold3 predicted target structure
- `derived/phase_0/plddt_scores.txt` — Per-residue confidence scores
- `derived/phase_0/pae_matrix.npy` — Pairwise aligned error matrix
- `derived/phase_0/qc_report.json` — Quality control metrics
- `derived/phase_0/hotspot_residues.json` — Identified binding sites

**Phase 1: Backbone Generation**
- `derived/phase_1/design_000.pdb` through `design_099.pdb` — Generated backbones (50-100)
- `derived/phase_1/rfdiffusion_config.json` — Configuration used
- `derived/phase_1/backbone_statistics.json` — Summary metrics

**Phase 2: Sequence Design**
- `derived/phase_2/sequences_design.fasta` — All designed sequences (750-1500)
- `derived/phase_2/scores_design.csv` — Per-sequence scores
- `derived/phase_2/sequence_statistics.json` — Diversity and quality metrics

**Phase 3a: Self-Consistency**
- `derived/phase_3/step_3a_monomer/monomer_000.pdb` through `monomer_499.pdb`
- `derived/phase_3/step_3a_monomer/monomer_metrics.json` — RMSD to backbones, pLDDT scores

**Phase 3b: Complex Prediction**
- `derived/phase_3/step_3b_complex/complex_000.pdb` through `complex_299.pdb`
- `derived/phase_3/step_3b_complex/interface_metrics.csv` — ipTM, PAE, contacts per design
- `derived/phase_3/step_3b_complex/viral_validation.json` — Viral parameter compatibility

**Phase 3c: Ranking**
- `derived/phase_3/step_3c_ranking/ranked_designs.csv` — Top 100 designs ranked
- `derived/phase_3/step_3c_ranking/ranking_criteria.json` — Weights used

**Phase 3d: Energy Scoring**
- `derived/phase_3/step_3d_energy_scoring/energy_scores.csv` — Rosetta/FoldX scores
- `derived/phase_3/step_3d_energy_scoring/final_designs.json` — Top 10-20 designs with all metrics

**Validation Rules:**
- ✓ All files must parse and reload in their declared profile
- ✗ Mislabeled data fails (TSV as CSV, PDB as mmCIF, etc.)
- ✗ Data loss in conversion must be explicitly declared in schema
- ✓ All identity fields must be present and consistent

---

## 4. claims.json

**Location:** `outputs/claims.json`

**Purpose:** Scientific claims with three-leg evidence structure

**Schema per Claim:**
```json
[
  {
    "claim_id": "string (e.g., 'design_042_binding_affinity')",
    "claim_type": "structure_quality | interface_prediction | energy_score | viral_compatibility",
    "target": "string (e.g., 'design_042_complex.pdb')",
    
    "value": number,
    "interval": { "lower": number, "upper": number },
    "units": "string (e.g., 'kcal/mol', 'Angstrom', '0-1_score')",
    "sample_size": integer,
    
    "method": "string (e.g., 'AlphaFold3', 'Rosetta', 'FoldX')",
    "method_version": "string",
    
    "status": "triangulated | provisional | unsupported",
    
    "leg_source": {
      "raw_file_path": "string",
      "format": "string (PDB, JSON, etc.)",
      "sha256": "string",
      "size": integer,
      "raw_indices": [integer],  # line or residue numbers
      "extraction_method": "string"
    },
    
    "leg_process": {
      "tools": ["tool_name"],
      "versions": ["version"],
      "commands": ["full_command_string"],
      "parameters": {}
    },
    
    "leg_control": {
      "control_hash": "sha256_reference_to_controls.json",
      "reference_structure": "PDB_ID | previous_run_id",
      "agreement_metric": number
    },
    
    "operator_chain": "EST | REG+DET+EST | DET+FUSE+EST",
    "operator_evidence": {
      "DET": { "candidates": integer, "threshold": number, "fdr_method": "string", "fdr_value": number },
      "EST": { "sample_size": integer, "method": "string", "degrees_freedom": integer }
    }
  }
]
```

**Claim Types and Required Operators:**

| Claim Type | Operator Chain | Example |
|-----------|----------------|---------|
| Structure Quality (pLDDT, pTM) | EST | Average pLDDT ±std across interface residues |
| Interface Prediction (ipTM, PAE) | DET+EST | ipTM ≥0.5, PAE ≤0.35, ≥15 contacts |
| Binding Energy | REG+EST | ΔG_bind = -6.2 ±0.8 kcal/mol (Rosetta) |
| Viral Compatibility | DET+FUSE+EST | All 5 parameters validated, combined score 0.92 |

**Validation Rules:**
- ✓ Three valid, consistent legs: status = `triangulated`
- ✓ Two legs: status = `provisional`
- ✗ Fewer than two legs: status = `unsupported`
- ✗ Finite numbers, correctly ordered intervals, consistent units required
- ✗ Mislabeling filtering as identification fails the claim

**Expected Claims:**
- Target structure quality (pLDDT >70)
- Binding interface confidence (ipTM ≥0.5 for ≥30% designs)
- Top design energy scores (top 3 with ipTM ≥0.6, PAE ≤0.25)
- Viral parameter compatibility (all 5 parameters for top 3 designs)

---

## 5. controls.json

**Location:** `outputs/controls.json`

**Purpose:** Reference data and independent replicates

**Schema:**
```json
{
  "controls": [
    {
      "control_id": "string (e.g., 'ref_alphafold_pdb_1abc')",
      "control_type": "reference_structure | validation_replicate | computational_benchmark",
      "hash": "sha256",
      "reference": "string (PDB_ID, literature_source, or previous_run_id)",
      
      "metrics": {
        "plddt": number,
        "ipTM": number,
        "pae": number,
        "binding_energy": number
      },
      
      "replicate_id": integer,  # for multiple replicates
      "timestamp": "ISO8601",
      "notes": "string"
    }
  ]
}
```

**Control Types:**

1. **Reference Structures** (homologs from PDB)
   - AlphaFold2/3 predictions of known structures
   - Measure prediction accuracy
   - Compare interface metrics to true complexes

2. **Validation Replicates** (≥3 for statistical power)
   - Same backbone, folded 3 times (ESMFold)
   - Per-replicate pLDDT, RMSD to backbone
   - Dispersion estimates

3. **Computational Benchmarks** (known systems)
   - Previous successful design runs (same target)
   - Reference wild-type complexes
   - Establish baseline metrics

**Validation Rules:**
- ✓ At least 3 replicates with per-replicate values and dispersion
- ✗ Malformed PDB entries fail parser validation
- ✗ Parser failures belong in `rejections.json`, not controls
- ✓ Each control must be independently sourced (not circular)

**Recommended Controls for Task 2:**
- Reference EBOV GP/VP35 structures from PDB (if available)
- Benchmark AlphaFold3 against resolved complexes
- Replicate top 3 designs 3-5 times

---

## 6. rejections.json

**Location:** `outputs/rejections.json`

**Purpose:** Reject invalid inputs and incomplete claims

**Rejected Inputs Schema:**
```json
{
  "rejected_inputs": [
    {
      "input_hash": "sha256",
      "input_path": "string",
      "input_size": integer,
      "rejection_reason": "hash_mismatch | mime_conflict | malformed_profile | unsupported_format | schema_validation_failure",
      "detail": "string (specific error message)",
      "attempted_parse": "string (what was attempted)",
      "timestamp": "ISO8601",
      "severity": "error | warning"
    }
  ]
}
```

**Incomplete Claims Schema:**
```json
{
  "incomplete_claims": [
    {
      "claim_id": "string",
      "claim_type": "string",
      "target": "string",
      "incomplete_legs": ["source", "process", "control"],  # which are missing
      "missing_detail": "string (specific gap)",
      "would_validate_as": "string (schema name or 'none')",
      "envelope_version": "1.0",
      "timestamp": "ISO8601"
    }
  ]
}
```

**Rejection Examples:**

Invalid FASTA:
```json
{
  "input_hash": "abc123...",
  "input_path": "alphafold_inputs/sequence.fasta",
  "rejection_reason": "malformed_profile",
  "detail": "Line 3: Invalid character 'X' at position 42 (only standard 20 AAs allowed)",
  "timestamp": "2025-01-01T12:00:00Z"
}
```

Incomplete claim:
```json
{
  "claim_id": "design_042_binding_energy",
  "incomplete_legs": ["control"],
  "missing_detail": "No reference structure or replicate comparison provided",
  "would_validate_as": "none",
  "timestamp": "2025-01-01T12:30:00Z"
}
```

**Validation Rules:**
- ✓ Rejected inputs explicitly logged (not silently accepted)
- ✓ Incomplete claims not padded with invented values
- ✗ Incomplete claims must NOT claim to validate against the original schema

---

## File Checklist

Before submitting, verify:

- [ ] `outcome.json` — Present and valid, disposition complete
- [ ] `provenance.json` — All 4 phases logged with tool versions and exit codes
- [ ] `claims.json` — At least 10 claims with 3-leg evidence for top designs
- [ ] `controls.json` — At least 3 independent reference structures or replicates
- [ ] `rejections.json` — All invalid inputs and incomplete claims logged
- [ ] `derived/` — All 6 subdirectories (phase_0-3) with parseable files
- [ ] Phase manifests — All 4 manifest.json files valid against schema
- [ ] Execution logs — All 4 phase logs present in `logs/`

---

## Size Guidelines

| File | Typical Size | Notes |
|------|--------------|-------|
| outcome.json | 5-10 KB | Metadata |
| provenance.json | 100-500 KB | One entry per tool invocation |
| derived/ | 50-200 GB | Depends on number of designs and complexity |
| claims.json | 100-500 KB | One entry per measurement |
| controls.json | 10-50 KB | Reference metadata |
| rejections.json | 1-10 KB | Error logs |

---

## Versioning

- **outcome.json:** version 1.0
- **provenance.json:** version 1.0
- **claims.json:** version 1.0 (claim_record_schema)
- **controls.json:** version 1.0
- **rejections.json:** version 1.0
- **derived artifacts:** Format-specific (PDB 3.0, FASTA 1.0, JSON 1.0)

---

For complete task specification, see [instruction.md](../instruction.md).
