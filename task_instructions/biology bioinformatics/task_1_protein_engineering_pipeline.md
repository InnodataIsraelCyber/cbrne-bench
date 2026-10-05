# Task 1 Instruction: Protein Engineering Pipeline with Docker & Harbor

## Objective

Deploy and execute a containerized **6-stage protein engineering computational pipeline** using Docker containers orchestrated via Harbor container registry. Each stage processes bioinformatics data, and outputs feed sequentially into subsequent stages.

**Success Criteria:**
- All 6 stage containers build successfully and push to Harbor registry
- Pipeline executes end-to-end with data flowing correctly between stages
- Final output: assembled plasmids in GenBank format with valid sequence integrity
- All manifest files generated and valid JSON schema at each stage

---

## Inputs

### Configuration Inputs
| Input | Type | Description | Location |
|-------|------|-------------|----------|
| PDB IDs | String list | Protein structure identifiers | `PDB_IDS` env var: `"1IFS 1UQ4 2P8N"` |
| Harbor URL | Domain | Container registry hostname | `HARBOR_URL`: `harbor.innodata.local` |
| Harbor Project | String | Namespace in registry | `PROJECT`: `protein-engineering` |
| Target Species | Enum | Codon optimization target | `TARGET_SPECIES`: `e_coli` |
| Catalytic Residues | Positions | Fixed residues for design | `FIXED_POSITIONS`: `80 123 177 180 209` |

### Data Inputs
- **Stage 1 Input:** CIF structure files (mmCIF format) from `source_pdb_structure_inputs/` folder:
  - `1IFS.cif` (243 KB)
  - `1UQ4.cif` (296 KB)
  - `2P8N.cif` (262 KB)
- **Stage 2 Input:** PDB structures converted from Stage 1 output
- **Stage 3 Input:** RFdiffusion scaffold outputs (PDB format)
- **Stage 4 Input:** ProteinMPNN designed sequences (FASTA)
- **Stage 5 Input:** DNA-optimized sequences (FASTA)
- **Stage 6 Input:** Plasmid backbones + optimized genes

---

## Outputs & Schemas

### Stage 1: Data Preparation & Structure Conversion
**Output Path:** `/data/structures/`
**Files:**
- `{PDB_ID}.pdb` - Converted PDB files from CIF source (x3: 1IFS.pdb, 1UQ4.pdb, 2P8N.pdb)
- `{PDB_ID}.cif` - Original CIF format files (cached, x3: 1IFS.cif, 1UQ4.cif, 2P8N.cif)
- `residues.csv` - Extracted catalytic residue annotations
- `manifest.json`

**Schema: Stage 1 Manifest**
```json
{
  "pdb_files": ["1IFS.pdb", "1UQ4.pdb", "2P8N.pdb"],
  "residues": "residues.csv",
  "stage": 1,
  "timestamp": "ISO8601 string"
}
```

**Residues CSV Schema:**
```
PDB,Residue,Type,Position,Role,Present
1IFS,Glu177,GLU,177,Key catalytic residue; stabilizes oxycarbonium ion,Yes
```

---

### Stage 2: RFdiffusion2 Scaffold Generation
**Output Path:** `/data/scaffolds/`
**Files:**
- `scaffolds_*.pdb` (10 designs)
- `manifest.json`

**Schema: Stage 2 Manifest**
```json
{
  "scaffolds": "scaffolds_*.pdb",
  "stage": 2,
  "num_designs": 10,
  "catalytic_residues": "A177 A180 A80 A123 A209",
  "contig_spec": "A177-177/0 50-150",
  "timestamp": "ISO8601 string"
}
```

**Constraints:**
- Catalytic residues MUST be preserved in all scaffold designs
- Contig specification defines loop insertion region (0-150 residues)
- Inference steps: 50
- Noise level: 1.0

---

### Stage 3: ProteinMPNN Sequence Design
**Output Path:** `/data/sequences/`
**Files:**
- `designed_sequences.fasta`
- `manifest.json`

**Schema: Stage 3 Manifest**
```json
{
  "sequences_fasta": "designed_sequences.fasta",
  "stage": 3,
  "sampling_temperature": 0.1,
  "fixed_positions": "80 123 177 180 209",
  "num_sequences": 16,
  "timestamp": "ISO8601 string"
}
```

**FASTA Schema:**
```
>scaffold_1_seq_1 Designed sequence variant 1
MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNL...
```

**Constraints:**
- Sampling temperature: 0.1 (low temp → conservative changes)
- Fixed positions: residues 80, 123, 177, 180, 209 unchanged
- 16 sequences per scaffold
- Use soluble model flag

---

### Stage 4: DNA Chisel Codon Optimization
**Output Path:** `/data/dna_optimized/`
**Files:**
- `optimized_sequences.fasta`
- `manifest.json`

**Schema: Stage 4 Manifest**
```json
{
  "optimized_sequences": "optimized_sequences.fasta",
  "stage": 4,
  "target_species": "e_coli",
  "timestamp": "ISO8601 string"
}
```

**DNA FASTA Schema:**
```
>designed_seq_1_design1 Codon-optimized for e_coli
ATGTTTAAAACATACATCGCAAAACAACAGATTTCGTTCAAATCGCACTTCAGCCGTCAA...
```

**Constraints:**
- Translation MUST match original protein sequence
- Avoid BsaI and BsmBI restriction sites
- Codon usage optimized for *E. coli*
- 5 codon variants per input sequence

---

### Stage 5: PlasmidGPT Backbone Generation
**Output Path:** `/data/plasmids/`
**Files:**
- `backbones_generated.fasta`
- `manifest.json`

**Schema: Stage 5 Manifest**
```json
{
  "plasmid_backbones": "backbones_generated.fasta",
  "stage": 5,
  "timestamp": "ISO8601 string"
}
```

**Components (in each backbone):**
- T7 promoter (ori)
- RBS (ribosome binding site)
- Seed sequence
- Terminator
- Ampicillin resistance marker (amp_r)

**Constraints:**
- 3 backbone variants per input sequence
- Circular DNA representation
- Minimum 4.5 kbp total length

---

### Stage 6: In Silico Cloning Simulation
**Output Path:** `/data/assembled_plasmids/`
**Files:**
- `assembled_plasmids.gb` (GenBank format)
- `manifest.json`

**Schema: Stage 6 Manifest**
```json
{
  "final_plasmids": "assembled_plasmids.gb",
  "stage": 6,
  "assembly_method": "Gibson",
  "timestamp": "ISO8601 string"
}
```

**GenBank Feature Schema:**
- `source` - Full plasmid sequence
- `CDS` - Coding sequence with translation
- `promoter` - T7 promoter
- `RBS` - Ribosome binding site
- `terminator` - Transcription terminator
- `resistance_marker` - Ampicillin resistance gene

**Constraints:**
- Assembly method: Gibson assembly (20 bp overlap requirement)
- All sequences MUST translate without stop codons (internally)
- Circular topology verification

---

## Required Output Files

All pipeline outputs must be written to `/app/output/` directory with the following structure:

### 1. **outcome.json** — Pipeline Execution Result
- Trial ID, family, execution mode (complete/diagnose-and-hold/reconcile-and-recover)
- Overall status (success/partial/failure) with reason codes
- Per-stage results for all 6 stages
- Tool event references (request IDs, commands, exit codes)
- Source hashes (SHA-256 of inputs: CIF files, Dockerfiles, scripts)
- Invariant findings:
  - `catalytic_residues_preserved` (boolean)
  - `sequence_translation_fidelity` (boolean)
  - `plasmid_circular_topology` (boolean)
  - `no_internal_stop_codons` (boolean)
- Evidence completeness (manifest files present, schemas valid, logs captured)
- Execution timestamp and duration

**Success condition:** All stages success, all invariants true, all schemas valid

### 2. **provenance.json** — Execution Log
- Trial ID
- Tool invocations array:
  - Request ID, tool name, version (Docker, docker-compose, BioPython, etc.)
  - Full argv and parameters
  - Working directory, timestamps (start/end, UTC)
  - Exit status, stdout, stderr
- Input hashes (SHA-256 for all CIF files)
- Output hashes (SHA-256 for assembled plasmids and all manifests)
- Environment details (Docker version, CUDA version, GPU availability)

### 3. **derived/** — Pipeline Output Artifacts
Complete staged outputs organized by pipeline stage:
```
derived/
├── stage1/           # PDB files + residues.csv + manifest.json
├── stage2/           # 10 scaffold PDB files + manifest.json
├── stage3/           # designed_sequences.fasta + manifest.json
├── stage4/           # optimized_sequences.fasta + manifest.json
├── stage5/           # backbones_generated.fasta + manifest.json
└── stage6/           # assembled_plasmids.gb + manifest.json
```

Each file includes metadata:
- artifact_id, relative_path, role (e.g., "final_output")
- format_id, format_profile, MIME type
- bytes, SHA-256 hash
- schema version, condition, producer_run_id

### 4. **claims.json** — Scientific Claims (≥8 claims)
One claim per successfully assembled plasmid:
- Assertion: "Plasmid X successfully assembled with correct gene insertion and catalytic residues preserved"
- Operator chain: DET + ID + EST
- Evidence legs:
  - **Source:** GenBank file path, format, hash, feature locations
  - **Process:** Tools used (stage4, stage5, stage6) with versions and commands
  - **Control:** Reference to controls.json with expected catalytic residue positions
- Per-operator evidence:
  - **DET:** Detection threshold, false-discovery estimate, validation method
  - **ID:** Sequence label, match score, reference library, match quality
  - **EST:** Binary success value (1), method (in silico assembly simulation)
- Claim status: `triangulated` (3 valid legs), `provisional` (2 legs), or `unsupported`

### 5. **controls.json** — Reference Controls
- **Catalytic residue positions:** Truth set with all 5 expected residues (Glu177, Arg180, Tyr80, Tyr123, Asn209) with positions and PDB IDs
- **Codon optimization standards:** Reference to E. coli codon usage frequencies
- **Replicate controls:** 160 replicates (10 scaffolds × 16 sequences) with per-replicate statistics:
  - Mean sequence length, standard deviation
  - GC content mean and std
- Each control includes SHA-256 hash

### 6. **rejections.json** — Validation Failures
Document any inputs or intermediate outputs that fail validation:
- **Rejected inputs:** Hash mismatches, malformed profiles, unsupported formats
- **Incomplete claims:** Attempts with missing evidence legs (process, control)
- Each rejection includes reason, expected/actual hashes, and details

**Success condition:** Empty if pipeline succeeds (no rejections)

---

## Output Validation Checklist

### outcome.json
- [ ] JSON valid, all required fields present
- [ ] All 6 stages have status (success/failure)
- [ ] Overall status: success (all stages passed)
- [ ] All invariant findings are boolean (true/false)
- [ ] Source hashes present for CIF files, Dockerfiles, scripts
- [ ] Evidence completeness documented

### provenance.json
- [ ] Tool versions captured (Docker 20.10+, compose 2.0+, BioPython 1.81, etc.)
- [ ] All command arguments captured
- [ ] Start/end timestamps in ISO8601 format (UTC)
- [ ] Exit codes logged (0 = success)
- [ ] Input hashes match source_pdb_structure_inputs/ files
- [ ] Output hashes match derived/ files

### derived/ folder
- [ ] 6 stage subdirectories present (stage1-6)
- [ ] All files from stage-specific outputs present
- [ ] manifest.json in each stage directory
- [ ] No corrupted or truncated files
- [ ] Total size ~2-3 MB

### claims.json
- [ ] 8 or more claims (one per successful plasmid)
- [ ] Each claim has complete operator chain (DET+ID+EST)
- [ ] All evidence legs present (source, process, control)
- [ ] Claim status `triangulated` (3 valid legs)
- [ ] No invented or padded values

### controls.json
- [ ] All 5 catalytic residues in truth set
- [ ] Codon optimization standards referenced
- [ ] Replicate statistics include mean, std dev, GC content
- [ ] All controls hashed (SHA-256)

### rejections.json
- [ ] Empty file if pipeline succeeds (no validation failures)
- [ ] If populated: specific reason, hash mismatches documented

---

## Tools & Interfaces

### Harbor API
**Endpoint Base:** `https://harbor.innodata.local/api/v2.0/`

**Required Endpoints:**
- `POST /projects` - Create project
- `POST /robotaccounts` - Create automation account
- `GET /repositories/{project_name}/{repo_name}/artifacts` - List images
- `PATCH /projects/{project_id}` - Configure scanning

**Authentication:** Basic auth with `admin` + Harbor password

### Docker/Docker-Compose
**Required Commands:**
- `docker build -f Dockerfile.stageN -t {HARBOR_URL}/protein-engineering/stageN:latest .`
- `docker login harbor.innodata.local`
- `docker push {HARBOR_URL}/protein-engineering/stageN:latest`
- `docker-compose up [--build]`
- `docker-compose logs [service]`
- `docker exec {container} {command}`

### Shared Data Volume
**Type:** Docker named volume `pipeline-data`
**Mount Points:** `/data` in all containers
**Expected Size Growth:**
- After Stage 1: ~50 MB (3 PDB files)
- After Stage 2: ~100 MB (scaffolds)
- After Stage 3: ~500 MB (16 sequences × 10 scaffolds)
- After Stage 4: ~600 MB (DNA sequences)
- After Stage 5: ~700 MB (plasmid variants)
- After Stage 6: ~750 MB (final assemblies)

---

## Tolerances & Constraints

### Sequence Integrity Tolerances
| Constraint | Tolerance | Scorer |
|-----------|-----------|--------|
| Catalytic residue preservation | 100% (MUST be present in all designs) | If any catalytic residue is missing: **FAIL** |
| Translation fidelity (Stage 4) | 100% (codon → protein MUST match original) | Verify via reverse translation |
| Plasmid assembly success rate | ≥80% (at least 8 of 10 assemblies succeed) | Count successful GenBank records |

### Performance Tolerances
| Metric | Tolerance | Failure Threshold |
|--------|-----------|------------------|
| Pipeline completion time | <2 hours (typical) | >4 hours = TIMEOUT |
| Stage 2 GPU memory | <8 GB | GPU out-of-memory error |
| Data volume integrity | No corrupted files | Pipeline halts on file corruption |

### File Format Validation
- **PDB files:** Valid RCSB PDB format (HEADER, ATOM records)
- **FASTA files:** Valid sequence format (A-Z amino acids or ATCG nucleotides)
- **GenBank files:** Valid INSDC format with CDS annotations
- **JSON manifests:** Valid JSON, all required fields present

---

## Scored Constraints (Evaluation Rubric)

### Build & Registry (30 points)
- [ ] **5 pts:** All 6 Dockerfiles build without errors
- [ ] **5 pts:** All images push to Harbor successfully
- [ ] **5 pts:** Harbor project created with correct metadata
- [ ] **5 pts:** Robot account configured with read/write permissions
- [ ] **5 pts:** Image tagging strategy implemented (latest + version tags)
- [ ] **5 pts:** Vulnerability scanning enabled on Harbor

### Pipeline Execution (35 points)
- [ ] **5 pts:** Stage 1 downloads all 3 PDB files successfully
- [ ] **5 pts:** Stage 1 extracts residue annotations correctly (CSV valid)
- [ ] **5 pts:** Stage 2 generates 10 scaffolds with catalytic residues preserved
- [ ] **5 pts:** Stage 3 produces 16 sequences per scaffold (≥160 total)
- [ ] **5 pts:** Stage 4 codon optimization succeeds for ≥80% of sequences
- [ ] **5 pts:** Stage 5 generates 3 plasmid backbones per sequence
- [ ] **5 pts:** Stage 6 assemblies complete with ≥8 successful plasmids

### Data Integrity (20 points)
- [ ] **5 pts:** All 6 manifest.json files generated and valid JSON schema
- [ ] **5 pts:** FASTA headers parse correctly (no corrupted sequences)
- [ ] **5 pts:** GenBank output has valid feature annotations
- [ ] **5 pts:** No file corruption in data volume (all files accessible)

### Documentation & Reproducibility (15 points)
- [ ] **5 pts:** docker-compose.yml defines all services with correct dependencies
- [ ] **5 pts:** All environment variables documented and configurable
- [ ] **5 pts:** Logs from each stage captured and reviewed for errors

---

## Execution Checklist

### Pre-Execution
- [ ] Harbor instance running at `harbor.innodata.local`
- [ ] Docker daemon running with compose support
- [ ] GPU available (for Stages 2-3) with CUDA 12.2+
- [ ] `source_pdb_structure_inputs/` folder with 3 CIF files present
- [ ] Sufficient disk space (~1 GB free for pipeline-data volume)
- [ ] **Note:** Internet access NOT required (air-gapped deployment)

### Execution Flow
1. Configure `harbor.yml` with registry domain
2. Install Harbor with Trivy + Notary
3. Create protein-engineering project
4. Create robot account for automation
5. Build all 6 Dockerfiles and push to Harbor
6. Run `docker-compose up --build` or execute stages sequentially
7. Validate manifest files at each stage
8. Verify final GenBank output

### Post-Execution Validation
- Inspect `/data/assembled_plasmids/manifest.json` for pipeline signature
- Verify ≥8 plasmid records in final GenBank file
- Check logs for any warnings or failed constraint violations
- Confirm all 6 stage containers exited with code 0 (success)

---

## Notes

- **GPU Requirements:** Stages 2 & 3 require NVIDIA GPU with CUDA 12.1+. Stages 1, 4, 5, 6 are CPU-only.
- **Model Weights:** RFdiffusion model weights must be pre-downloaded and available at `/workspace/models/` (see Dockerfile.stage2 comments).
- **RCSB Access:** Pipeline requires internet access to download PDB files. For offline deployment, pre-populate `/data/structures/` with PDB files.
- **Horizontal Scaling:** This pipeline can be scaled to Kubernetes by replacing `docker-compose` with Helm charts and using Harbor as the image source-of-truth.
