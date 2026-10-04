# Task 1 Output Specification

## Required Output Files

All pipeline outputs must be written to `/app/output/` (mapped from `/outputs` in docker-compose).

### 1. `outcome.json` - Pipeline Execution Result

**Required fields:**
```json
{
  "trial_id": "task_1_run_20261004_001",
  "family": "protein_engineering_pipeline",
  "mode": "complete|diagnose-and-hold|reconcile-and-recover",
  "observed_condition": "string describing what was found",
  "disposition": {
    "status": "success|partial|failure",
    "reason": "string explanation",
    "reason_code": "string code"
  },
  "stage_results": {
    "stage_1": {"status": "success|failure", "message": "..."},
    "stage_2": {"status": "success|failure", "message": "..."},
    "stage_3": {"status": "success|failure", "message": "..."},
    "stage_4": {"status": "success|failure", "message": "..."},
    "stage_5": {"status": "success|failure", "message": "..."},
    "stage_6": {"status": "success|failure", "message": "..."}
  },
  "tool_event_references": [
    {"request_id": "...", "command": "docker build", "exit_code": 0},
    {"request_id": "...", "command": "docker-compose up", "exit_code": 0}
  ],
  "source_hashes": {
    "source_pdb_files": "sha256:...",
    "dockerfiles": "sha256:...",
    "scripts": "sha256:..."
  },
  "invariant_findings": [
    "catalytic_residues_preserved: true|false",
    "sequence_translation_fidelity: true|false",
    "plasmid_circular_topology: true|false",
    "no_internal_stop_codons: true|false"
  ],
  "evidence_completeness": {
    "manifest_files_present": true|false,
    "output_schemas_valid": true|false,
    "logs_captured": true|false,
    "missing": ["..."]
  },
  "timestamp": "ISO8601",
  "duration_seconds": 1800
}
```

**Status Rules:**
- `success`: All 6 stages complete, ≥8 plasmids assembled, all schemas valid
- `partial`: Some stages complete, but missing final outputs or constraint violations
- `failure`: Pipeline halted before completion, critical errors encountered

### 2. `provenance.json` - Execution Log

**Required fields:**
```json
{
  "trial_id": "task_1_run_20261004_001",
  "tool_invocations": [
    {
      "request_id": "req_001",
      "tool_name": "docker_build",
      "version": "20.10.x",
      "argv": ["docker", "build", "-f", "Dockerfile.stage1", ...],
      "parameters": {...},
      "working_directory": "/workspace",
      "start_timestamp": "ISO8601",
      "end_timestamp": "ISO8601",
      "exit_status": 0,
      "stdout": "...",
      "stderr": "..."
    },
    {
      "request_id": "req_002",
      "tool_name": "docker_compose_up",
      "version": "2.x.x",
      "argv": ["docker-compose", "-f", "docker-compose.yml", "up", "--build"],
      "start_timestamp": "ISO8601",
      "end_timestamp": "ISO8601",
      "exit_status": 0,
      "containers_started": 6,
      "failed_services": []
    }
  ],
  "input_hashes": {
    "1IFS.cif": "sha256:abc123...",
    "1UQ4.cif": "sha256:def456...",
    "2P8N.cif": "sha256:ghi789..."
  },
  "output_hashes": {
    "assembled_plasmids.gb": "sha256:jkl012...",
    "all_manifest_files": "sha256:mno345..."
  },
  "environment": {
    "docker_version": "20.10.x",
    "docker_compose_version": "2.x.x",
    "cuda_version": "12.2.0",
    "gpu_available": true|false
  },
  "timestamp": "ISO8601"
}
```

### 3. `derived/` Folder - Pipeline Output Artifacts

All intermediate and final outputs from the pipeline:

```
derived/
├── stage1/
│   ├── 1IFS.pdb
│   ├── 1UQ4.pdb
│   ├── 2P8N.pdb
│   ├── residues.csv
│   └── manifest.json
├── stage2/
│   ├── scaffolds_1.pdb
│   ├── scaffolds_2.pdb
│   ├── ... (10 scaffolds)
│   └── manifest.json
├── stage3/
│   ├── designed_sequences.fasta
│   └── manifest.json
├── stage4/
│   ├── optimized_sequences.fasta
│   └── manifest.json
├── stage5/
│   ├── backbones_generated.fasta
│   └── manifest.json
└── stage6/
    ├── assembled_plasmids.gb
    └── manifest.json
```

**Artifact metadata for each file:**
```json
{
  "artifact_id": "task_1_stage6_plasmids_001",
  "relative_path": "derived/stage6/assembled_plasmids.gb",
  "role": "final_output",
  "format_id": "genbank",
  "format_profile": "INSDC_compliant",
  "declared_mime": "application/x-genbank",
  "resolved_mime": "application/x-genbank",
  "mime_status": "valid",
  "compression": "none",
  "bytes": 125000,
  "sha256": "abc123...",
  "schema_or_dictionary_version": "genbank_5.0",
  "condition": "assembled_plasmids",
  "producer_run_id": "stage6_run_001"
}
```

### 4. `claims.json` - Biological Claims (Measurement Task)

**Required for each plasmid assembled:**
```json
{
  "claim_id": "claim_plasmid_001",
  "assertion": "Plasmid successfully assembled with correct gene insertion and catalytic residues preserved",
  "operator_chain": "DET+ID+EST",
  "evidence_legs": {
    "source": {
      "file_path": "derived/stage6/assembled_plasmids.gb",
      "format": "genbank",
      "format_profile": "INSDC",
      "sha256": "abc123...",
      "size_bytes": 125000,
      "raw_indices": [
        {"record": 1, "feature": "source", "location": "1..4500"},
        {"record": 1, "feature": "CDS", "location": "150..2000"}
      ]
    },
    "process": {
      "tools": [
        {"name": "stage4", "version": "dnachisel_3.20.27", "command": "codon_optimize"},
        {"name": "stage5", "version": "plasmidgpt", "command": "backbone_generate"},
        {"name": "stage6", "version": "pydna_3.2.1", "command": "gibson_assembly"}
      ]
    },
    "control": {
      "reference": "controls.json#catalytic_residue_positions",
      "expected_positions": [80, 123, 177, 180, 209],
      "tolerance": 0
    }
  },
  "operator_evidence": {
    "DET": {
      "candidates": 10,
      "threshold_applied": "sequence_length_and_cds_validity",
      "false_discovery_estimate": 0.0,
      "method": "genbank_feature_validation"
    },
    "ID": {
      "label": "assembled_plasmid_1",
      "score": 1.0,
      "reference_library": "RCSB_PDB_20261004",
      "match_quality": "perfect"
    },
    "EST": {
      "value": 1,
      "value_interpretation": "successfully_assembled",
      "units": "binary_success",
      "sample_size": 1,
      "method": "in_silico_assembly_simulation"
    }
  },
  "claim_status": "triangulated|provisional|unsupported",
  "validation_notes": "All constraints satisfied, catalytic residues preserved, plasmid topology circular"
}
```

### 5. `controls.json` - Reference Controls

**Required controls for validation:**
```json
{
  "controls": [
    {
      "control_id": "catalytic_residue_positions",
      "type": "reference_truth_set",
      "description": "Expected catalytic residue positions from literature",
      "values": [
        {"residue": "Glu177", "position": 177, "pdb_id": "1IFS"},
        {"residue": "Arg180", "position": 180, "pdb_id": "1IFS"},
        {"residue": "Tyr80", "position": 80, "pdb_id": "1IFS"},
        {"residue": "Tyr123", "position": 123, "pdb_id": "1IFS"},
        {"residue": "Asn209", "position": 209, "pdb_id": "1IFS"}
      ],
      "hash": "sha256:control_cat_res_001"
    },
    {
      "control_id": "codon_optimization_standards",
      "type": "reference_standards",
      "description": "E. coli codon usage frequencies",
      "reference": "codon_usage_ecoli.tsv",
      "hash": "sha256:control_codon_001"
    },
    {
      "control_id": "plasmid_assembly_replicates",
      "type": "replicate_controls",
      "description": "10 scaffold × 16 sequences = 160 design replicates",
      "sample_size": 160,
      "per_replicate_statistics": {
        "mean_sequence_length": 1250,
        "std_dev_length": 45,
        "gc_content_mean": 0.52,
        "gc_content_std": 0.03
      },
      "hash": "sha256:control_replicates_001"
    }
  ]
}
```

### 6. `rejections.json` - Validation Failures

**Required for any inputs or intermediate outputs that fail validation:**
```json
{
  "rejected_inputs": [
    {
      "file": "1IFS.cif",
      "reason": "hash_mismatch|malformed_profile|unsupported_format",
      "expected_hash": "sha256:abc123...",
      "actual_hash": "sha256:xyz789...",
      "details": "CIF file corrupted or modified"
    }
  ],
  "incomplete_claims": [
    {
      "claim_id": "incomplete_001",
      "assertion": "Partial assembly with missing gene segment",
      "missing_legs": ["process", "control"],
      "reason": "Assembly simulation failed at step 5",
      "envelope_version": "incomplete_claim_v1"
    }
  ]
}
```

---

## Stage-by-Stage Output Requirements

### Stage 1 Output (`/data/structures/`)
**Must include:**
- 3 PDB files (1IFS.pdb, 1UQ4.pdb, 2P8N.pdb)
- residues.csv (catalytic residue annotations)
- manifest.json (stage 1 metadata)

**Schema validation:** All files must match stage_manifest.schema.json (stage: 1)

### Stage 2 Output (`/data/scaffolds/`)
**Must include:**
- 10 scaffold PDB files (scaffolds_*.pdb)
- manifest.json (stage 2 metadata with num_designs: 10)

**Constraints:**
- Catalytic residues MUST be present in all scaffolds
- All scaffolds must parse as valid PDB

### Stage 3 Output (`/data/sequences/`)
**Must include:**
- designed_sequences.fasta (≥160 sequences: 10 scaffolds × 16 sequences)
- manifest.json (stage 3 metadata)

**Constraints:**
- FASTA format must be valid
- Fixed positions (80, 123, 177, 180, 209) MUST match original residues

### Stage 4 Output (`/data/dna_optimized/`)
**Must include:**
- optimized_sequences.fasta (codon-optimized DNA)
- manifest.json (stage 4 metadata)

**Constraints:**
- DNA sequence length = protein length × 3 (codons)
- Reverse translation MUST match original protein sequence (100% fidelity)
- No BsaI or BsmBI restriction sites

### Stage 5 Output (`/data/plasmids/`)
**Must include:**
- backbones_generated.fasta (plasmid backbones, ≥30 total)
- manifest.json (stage 5 metadata)

**Constraints:**
- Each backbone ≥4.5 kbp
- Circular topology
- Contains T7 promoter, RBS, terminator, amp_r

### Stage 6 Output (`/data/assembled_plasmids/`)
**Must include:**
- assembled_plasmids.gb (GenBank format, ≥8 successful plasmids)
- manifest.json (stage 6 metadata)

**Constraints:**
- Valid INSDC GenBank format
- All features properly annotated
- CDS translatable without internal stop codons
- Circular topology
- ≥80% assembly success rate (≥8 of 10 plasmids)

---

## Output Validation Checklist

### For `outcome.json`
- [ ] All 6 stages have status: success/failure
- [ ] Overall status is success (all stages passed)
- [ ] All invariant findings are boolean (true/false)
- [ ] Source hashes present for all inputs
- [ ] Evidence completeness documented

### For `provenance.json`
- [ ] Tool invocations include versions (Docker, compose, BioPython, etc.)
- [ ] All command arguments captured
- [ ] Start/end timestamps present
- [ ] Exit codes logged
- [ ] Input/output hashes match derived/ files

### For `derived/` folder
- [ ] All 6 stage subdirectories present
- [ ] All required files from instruction.md present
- [ ] manifest.json in each stage directory
- [ ] No corrupted or truncated files

### For `claims.json`
- [ ] One claim per successfully assembled plasmid
- [ ] All operator chains complete (DET+ID+EST)
- [ ] Evidence legs present for source, process, control
- [ ] Claim status derived from evidence (not guessed)

### For `controls.json`
- [ ] Reference truth set includes all 5 catalytic residues
- [ ] Codon optimization standards referenced
- [ ] Replicate statistics computed (160 replicates)

### For `rejections.json`
- [ ] Empty if pipeline succeeds (no rejections)
- [ ] If populated, documents specific failures with hashes

---

## Output Directory Structure

```
/app/output/
├── outcome.json                          # Pipeline result
├── provenance.json                       # Execution log
├── claims.json                           # Scientific claims (≥8)
├── controls.json                         # Reference controls
├── rejections.json                       # Failed validations (empty if clean)
└── derived/
    ├── stage1/
    │   ├── 1IFS.pdb
    │   ├── 1UQ4.pdb
    │   ├── 2P8N.pdb
    │   ├── residues.csv
    │   └── manifest.json
    ├── stage2/
    │   ├── scaffolds_1.pdb
    │   ├── ... (10 scaffolds)
    │   └── manifest.json
    ├── stage3/
    │   ├── designed_sequences.fasta
    │   └── manifest.json
    ├── stage4/
    │   ├── optimized_sequences.fasta
    │   └── manifest.json
    ├── stage5/
    │   ├── backbones_generated.fasta
    │   └── manifest.json
    └── stage6/
        ├── assembled_plasmids.gb
        └── manifest.json
```

**Total expected size:** ~2-3 MB (all outputs combined)

---

## Success Criteria (Evaluation)

| File | Status | Points |
|------|--------|--------|
| outcome.json | Valid JSON, all stages success, invariants true | 20 |
| provenance.json | Complete tool invocations, hashes correct | 20 |
| derived/ | All files present, manifest schemas valid | 30 |
| claims.json | ≥8 claims, all legs triangulated | 15 |
| controls.json | Reference set + replicates complete | 10 |
| rejections.json | Empty (no failures) | 5 |

**Total: 100 points**

---

For the task evaluation, all output files in `/app/output/` are captured, hashed, and validated against the schemas defined in this document.
