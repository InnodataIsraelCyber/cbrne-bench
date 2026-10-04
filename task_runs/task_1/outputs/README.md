# Task 1 Outputs Directory

This directory contains the specification for all required outputs from the protein engineering pipeline.

## Overview

All pipeline outputs must be written to `/app/output/` and validated against the schemas defined here.

**See [OUTPUTS_SPEC.md](OUTPUTS_SPEC.md) for the complete output specification.**

## Quick Summary

### Required Output Files

1. **outcome.json** — Pipeline execution result
   - Trial ID, execution mode, overall status
   - Per-stage results (success/failure)
   - Invariant findings (boolean assertions)
   - Evidence completeness

2. **provenance.json** — Complete execution log
   - All tool invocations with versions and parameters
   - Input/output hashes (SHA-256)
   - Environment details (Docker, CUDA versions)

3. **derived/** — All pipeline artifacts organized by stage
   ```
   derived/stage1/  → PDB files + residues.csv + manifest.json
   derived/stage2/  → 10 scaffold PDB files + manifest.json
   derived/stage3/  → designed_sequences.fasta + manifest.json
   derived/stage4/  → optimized_sequences.fasta + manifest.json
   derived/stage5/  → backbones_generated.fasta + manifest.json
   derived/stage6/  → assembled_plasmids.gb + manifest.json
   ```

4. **claims.json** — Scientific claims (≥8 for successful plasmids)
   - One claim per assembled plasmid
   - Complete evidence legs (source, process, control)
   - Operator chains (DET + ID + EST)
   - Claim status: `triangulated`, `provisional`, or `unsupported`

5. **controls.json** — Reference controls
   - Catalytic residue truth set (all 5 residues with positions)
   - Codon optimization standards
   - Replicate statistics (160 replicates: 10 scaffolds × 16 sequences)

6. **rejections.json** — Validation failures (empty if successful)
   - Rejected inputs with hash mismatches
   - Incomplete claims with missing evidence legs

## Output Structure

```
/app/output/
├── outcome.json              # ← Required: Success/failure status
├── provenance.json           # ← Required: Execution log with tool invocations
├── claims.json               # ← Required: ≥8 scientific claims
├── controls.json             # ← Required: Reference controls
├── rejections.json           # ← Required: (empty if clean)
└── derived/
    ├── stage1/
    │   ├── 1IFS.pdb
    │   ├── 1UQ4.pdb
    │   ├── 2P8N.pdb
    │   ├── residues.csv
    │   └── manifest.json
    ├── stage2/
    │   ├── scaffolds_1.pdb
    │   ├── ... (10 total)
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

## Key Validation Rules

### outcome.json
- All 6 stages must have `status: "success"`
- All invariant findings must be `true`:
  - `catalytic_residues_preserved: true`
  - `sequence_translation_fidelity: true`
  - `plasmid_circular_topology: true`
  - `no_internal_stop_codons: true`
- Overall status must be `"success"`

### provenance.json
- Include tool versions: Docker, docker-compose, BioPython, pydna, etc.
- All input CIF file hashes must match source_pdb_structure_inputs/
- All output hashes must match files in derived/
- Timestamps in ISO8601 format (UTC)

### derived/
- All 6 stage subdirectories must exist
- Each stage must have manifest.json with correct schema
- Files must not be corrupted or truncated
- Total size ~2-3 MB

### claims.json
- Must have ≥8 claims (one per successful plasmid assembly)
- Each claim must have `claim_status: "triangulated"` (3 valid legs)
- Operator chain must be complete: DET + ID + EST
- Evidence must include source, process, and control

### controls.json
- Truth set must include all 5 catalytic residues:
  - Glu177 (position 177)
  - Arg180 (position 180)
  - Tyr80 (position 80)
  - Tyr123 (position 123)
  - Asn209 (position 209)
- Replicate statistics required (mean, std dev, GC content)

### rejections.json
- Must be empty if pipeline succeeds (no validation failures)
- If populated, must document specific failures with SHA-256 hashes

## Points Breakdown (100 total)

| Component | Points |
|-----------|--------|
| outcome.json (valid, all stages success) | 20 |
| provenance.json (complete tool log, correct hashes) | 20 |
| derived/ folder (all files, valid manifests) | 30 |
| claims.json (≥8 triangulated claims) | 15 |
| controls.json (reference set + replicates) | 10 |
| rejections.json (empty, no failures) | 5 |

## Docker Integration

The outputs directory is typically mounted in docker-compose.yml:

```yaml
services:
  stage1:
    volumes:
      - ./source_pdb_structure_inputs:/workspace/input_structures:ro
      - pipeline-data:/data
      - ./outputs:/app/output

  stage2:
    volumes:
      - pipeline-data:/data
      - ./outputs:/app/output
  
  # ... etc for stages 3-6
```

At the end of pipeline execution, verify outputs:

```bash
# Check that all output files exist
ls -la /app/output/
ls -la /app/output/derived/stage*/

# Validate JSON files
jq . /app/output/outcome.json
jq . /app/output/provenance.json
jq . /app/output/claims.json
jq . /app/output/controls.json

# Check artifact sizes
du -sh /app/output/derived/stage*
```

## Example outcome.json Structure

```json
{
  "trial_id": "task_1_run_20261004_001",
  "family": "protein_engineering_pipeline",
  "mode": "complete",
  "observed_condition": "All stages completed successfully",
  "disposition": {
    "status": "success",
    "reason": "All 6 stages passed, 10 plasmids assembled",
    "reason_code": "COMPLETE"
  },
  "stage_results": {
    "stage_1": {"status": "success", "message": "Downloaded and parsed 3 PDB structures"},
    "stage_2": {"status": "success", "message": "Generated 10 scaffolds with preserved catalytic residues"},
    "stage_3": {"status": "success", "message": "Designed 160 sequences (10×16)"},
    "stage_4": {"status": "success", "message": "Optimized 160 sequences for E. coli"},
    "stage_5": {"status": "success", "message": "Generated 30 plasmid backbones (10×3)"},
    "stage_6": {"status": "success", "message": "Assembled 10 plasmids (GenBank format)"}
  },
  "invariant_findings": [
    "catalytic_residues_preserved: true",
    "sequence_translation_fidelity: true",
    "plasmid_circular_topology: true",
    "no_internal_stop_codons: true"
  ],
  "evidence_completeness": {
    "manifest_files_present": true,
    "output_schemas_valid": true,
    "logs_captured": true,
    "missing": []
  },
  "timestamp": "2026-10-04T18:30:45Z",
  "duration_seconds": 1800
}
```

---

For complete specifications, see [OUTPUTS_SPEC.md](OUTPUTS_SPEC.md).
