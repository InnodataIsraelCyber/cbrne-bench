# Task 1: Input Data Specification

## Source PDB Structure Inputs

The pipeline uses **pre-seeded CIF (mmCIF) format** protein structure files located in the `source_pdb_structure_inputs/` folder.

### Input Files

| File | Format | Size | PDB ID | Description |
|------|--------|------|--------|-------------|
| `1IFS.cif` | mmCIF | 243 KB | 1IFS | Glycosyltransferase structure |
| `1UQ4.cif` | mmCIF | 296 KB | 1UQ4 | Nucleotide-binding protein |
| `2P8N.cif` | mmCIF | 262 KB | 2P8N | Enzyme complex structure |

**Total Input Size:** ~800 KB

### mmCIF Format Details

**mmCIF (macromolecular Crystallographic Information File)** is the standard format for PDB structure data:
- More compact and semantically complete than legacy PDB format
- Supports larger structures and additional metadata
- Standard crystallographic notation for atomic coordinates

**Key mmCIF Blocks:**
- `_atom_site` - Atomic coordinates and B-factors
- `_struct_asym` - Asymmetric unit definition
- `_chemical_formula` - Molecular composition
- `_exptl` - Experimental conditions

### Stage 1 Processing

**Task:** Convert CIF → PDB format and extract catalytic residue annotations

**Input Mount:** Stage 1 container reads from volume-mounted `source_pdb_structure_inputs/`

```dockerfile
VOLUME /workspace/input_structures  # Read-only mount of source_pdb_structure_inputs/
```

**docker-compose.yml configuration:**
```yaml
stage1-preparation:
  volumes:
    - ./source_pdb_structure_inputs:/workspace/input_structures:ro
    - pipeline-data:/data
  environment:
    INPUT_SOURCE: /workspace/input_structures
    OUTPUT_DIR: /data/structures
```

### Offline/Air-Gapped Deployment

This pipeline is designed for **offline deployment** (no internet required):

✓ **No download from RCSB PDB servers**
✓ **No external API calls** (except optional Harbor registry)
✓ **No dependency on network connectivity**
✓ **All inputs pre-seeded locally**

**Advantages:**
- Faster pipeline execution (no network latency)
- Can run in air-gapped or isolated networks
- Reproducible (no version drift from RCSB updates)
- Suitable for secure/regulated environments

### Residue Extraction (Stage 1 Output)

**Catalytic Residues** annotated in Stage 1:

| Residue | Position | Type | Role |
|---------|----------|------|------|
| Glu177 | 177 | GLU | Key catalytic residue; stabilizes oxycarbonium ion |
| Arg180 | 180 | ARG | Protonates adenine at N3; transition state stabilization |
| Tyr80 | 80 | TYR | Stacks on substrate adenine ring |
| Tyr123 | 123 | TYR | Stacks on opposite side of adenine |
| Asn209 | 209 | ASN | Substrate binding |

**These residues are preserved throughout:**
- Stage 2: RFdiffusion hotspot constraints
- Stage 3: ProteinMPNN fixed positions
- Stage 4+: Translation fidelity checks

### Input Data Flow

```
source_pdb_structure_inputs/
  ├── 1IFS.cif ──┐
  ├── 1UQ4.cif ──├──→ Stage 1 ──→ /data/structures/
  └── 2P8N.cif ──┘   (conversion)   ├── 1IFS.pdb
                                     ├── 1UQ4.pdb
                                     ├── 2P8N.pdb
                                     ├── 1IFS.cif (cached)
                                     ├── 1UQ4.cif (cached)
                                     ├── 2P8N.cif (cached)
                                     ├── residues.csv
                                     └── manifest.json
```

### Deployment Instructions

1. **Verify source inputs exist:**
   ```bash
   ls -lh source_pdb_structure_inputs/
   # Should show 3 .cif files (243K, 296K, 262K)
   ```

2. **Mount source inputs in docker-compose.yml:**
   ```yaml
   stage1-preparation:
     volumes:
      - ./source_pdb_structure_inputs:/workspace/input_structures:ro
      - pipeline-data:/data
   ```

3. **Run Stage 1:**
   ```bash
   docker-compose up stage1-preparation
   ```

4. **Verify output:**
   ```bash
   docker exec stage1-preparation ls -lh /data/structures/
   # Should show 3 .pdb files + residues.csv + manifest.json
   ```

### Alternative: Pre-Seeding the Volume

If the input files should be pre-loaded into the `pipeline-data` volume:

```bash
# Create and pre-seed volume
docker volume create pipeline-data

# Copy inputs to volume
docker run --rm -v pipeline-data:/data -v $(pwd)/source_pdb_structure_inputs:/input \
  busybox cp -r /input/* /data/

# Verify
docker run --rm -v pipeline-data:/data busybox ls -lh /data/
```

### Validation

**Input validation checks (Stage 1):**

```python
# CIF file parsing
parser = MMCIFParser()
structure = parser.get_structure(pdb_id, cif_file)

# Expected atoms: ~3,000-5,000 atoms per structure
# Expected chains: Usually 1-2 chains (A, B)
# Expected residues: ~200-400 residues per structure
```

**Success Criteria:**
- ✓ All 3 CIF files parse successfully
- ✓ All structures contain catalytic residues at specified positions
- ✓ Conversion to PDB format preserves atomic coordinates
- ✓ Residue CSV generated with all 5 catalytic residues (Present: Yes/No)

---

## Notes

- **Format Conversion:** BioPython handles CIF ↔ PDB conversion with full fidelity
- **Coordinate Precision:** mmCIF maintains higher precision than legacy PDB (4 decimal places vs 2)
- **Caching:** Original CIF files cached in `/data/structures/` for reference/auditing
- **No Dependencies:** Only requires BioPython + standard Python libraries (no external services)

---

For full pipeline specification, see [instruction.md](instruction.md).
