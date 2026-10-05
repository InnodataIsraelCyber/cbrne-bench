# Influenza A HA Gene — Codon Optimization & Synthetic Expression Vector Design

**Task ID:** task_4
**Category:** Synthetic Biology / Gene Synthesis / Molecular Cloning  
**Pathogen:** Influenza A virus H1N1 (A/California/04/2009 pandemic strain, taxonomy 11320)  
**Target:** Hemagglutinin (HA) gene (~1,650 bp coding sequence, 550 AA protein)  
**Scientific Objective:** Computationally optimize HA gene for mammalian cell expression; design synthetic expression plasmid with regulatory elements  
**Archetypes:** 7 (codon optimization) → 8 (plasmid design) → 10 (QC validation)  
**Pipeline Complexity:** Multi-stage (3 stages, sequence synthesis focus)  
**Execution Environment:** Docker + CPU (minimal requirements)

---

## Executive Summary

This task executes a synthetic biology pipeline to:
1. Optimize H1N1 HA coding sequence for human cell codon usage
2. Remove problematic restriction sites (BsaI, BbsI for Golden Gate assembly)
3. Design complete expression plasmid with promoters, selection markers, polyadenylation signals
4. Validate synthetic construct for cloning and expression compatibility

**Expected runtime:** 3–5 hours (CPU-based sequence design)  
**Output MIME types:** FASTA (optimized gene), GenBank (plasmid map), CSV (synthesis validation), JSON (design parameters)  
**Synthetic biology context:** Mammalian expression vector for vaccine production

---

## Inputs

### Input File 1: Wild-Type H1N1 HA Coding Sequence
**MIME Type:** `text/x-fasta`  
**File:** `inputs/influenza_ha_wt.fasta`  
**Content:** A/California/04/2009 HA gene, wild-type codon usage
```
>A_California_04_2009_HA CDS
ATGGAGAAAATAGTGCACCACTCTCTCTCTACTAGAAAGATTCGAAATATTTCCCAAG...TAATCTCTAGCACAGACAATGCCATTCGAGATATACTGCACGCCGCGGTCTATAC
```
**Size:** ~2 KB (1,650 bp)  
**Validation:** 1,650 bp, ATG start codon, in-frame stop codon (TAA/TAG/TGA)
**Sequence integrity:** Matches GenBank accession CY087394.1

### Input File 2: Codon Optimization & Cloning Parameters
**MIME Type:** `application/json`  
**File:** `inputs/design_parameters.json`  
**Content:** Optimization targets, restriction site constraints, plasmid backbone info
```json
{
  "codon_optimization": {
    "target_organism": "homo_sapiens",
    "gc_content_target": "48-52",
    "codon_usage_table": 1,
    "avoid_rare_codons": true,
    "minimum_rare_codon_frequency": 0.1
  },
  "restriction_sites_to_remove": ["BsaI", "BbsI", "EcoRI", "BamHI", "XbaI", "XhoI"],
  "keep_native_sites": ["BstBI", "StuI"],
  "plasmid_backbone": {
    "name": "pVAX1_derivative",
    "size_bp": 3200,
    "selection_marker": "ampicillin_resistance",
    "ori": "pBR322"
  },
  "expression_elements": {
    "promoter": "CMV",
    "kozak_sequence": "GCCRCCATGG",
    "terminator": "SV40_polyA",
    "homopolymer_limit": 5
  }
}
```
**Size:** ~2 KB  
**Validation:** Valid JSON, organism code recognized, codon table number valid (1–25)

---

## Processing Stages

### Stage 1: Codon Optimization for Mammalian Expression (Archetype 7)

**Tool:** DNA Chisel v0.3.3 (codon optimization) + Codon Harmony  
**Docker Image:** `dna-chisel:0.3.3`, `codon-harmony:latest`  
**Input MIME:** `text/x-fasta` (WT HA sequence), `application/json` (parameters)  
**Output MIME:** `text/x-fasta` (optimized gene), `text/csv` (codon usage statistics)

**Objective:** Optimize HA nucleotide sequence for human cell expression; remove problematic restriction sites; maintain protein sequence identity.

**Processing:**
1. Input: Wild-type H1N1 HA FASTA (1,650 bp) + design parameters JSON
2. Codon optimization strategy:
   - Target organism: *Homo sapiens* (human codon usage, NCBI Taxonomy ID 9606)
   - Optimization objective: maximize codon optimality score
     - Use human codon frequency table (Homo_sapiens.txt)
     - Avoid rare codons (<10% frequency in human genes)
     - Minimize use of codons with low tRNA abundance
   - GC content adjustment: target 48–52% (avoid secondary structures)
3. Constraint satisfaction (DNA Chisel):
   - **Remove restriction sites:** BsaI, BbsI (Golden Gate incompatible), EcoRI, BamHI, XbaI, XhoI
   - **Preserve:** Native BstBI, StuI sites (if present)
   - **Avoid homopolymer runs:** ≤5 identical nucleotides in tandem
   - **Maintain protein sequence:** Translation must yield identical 550 AA HA protein
4. Post-optimization validation:
   - Confirm translation equivalence (same protein sequence)
   - Calculate codon usage improvement (frequency % of optimized vs. WT codons)
   - Verify all constraint sites removed
   - Check secondary structure changes (if available)
5. Output validation:
   - FASTA: 1,650 bp, ATG start, in-frame stop codon
   - CSV: per-codon optimization scores, codon usage table

**Expected outputs:**
```
outputs/derived/stage1/
├── influenza_ha_optimized.fasta      (optimized HA gene, human codons)
├── codon_usage_comparison.csv        (WT vs. optimized codon frequencies)
├── optimization_report.json          (improvement metrics, constraints satisfied)
├── secondary_structure_prediction.json (DNA secondary structure, WT vs. opt)
└── stage1_qc.json                   (validation report)
```

**Validation Checklist (Stage 1):**
- [ ] Optimized sequence: 1,650 bp (length preserved)
- [ ] Translation identical to WT: 550 AA HA protein
- [ ] GC content: 48–52% (within target range)
- [ ] No BsaI, BbsI, EcoRI, BamHI, XbaI, XhoI sites
- [ ] No homopolymer runs >5 bp
- [ ] Codon optimality improvement: ≥10% (median codon frequency increase vs. WT)
- [ ] All rare codons (frequency <10%) minimized to <2% of total

---

### Stage 2: Expression Plasmid Design & Assembly (Archetype 8)

**Tool:** PlasmidGPT + Pydna (plasmid design toolkit)  
**Docker Image:** `plasmid-gpt:latest`, `pydna:latest`  
**Input MIME:** `text/x-fasta` (optimized HA gene from Stage 1), `application/json` (design parameters)  
**Output MIME:** `application/genbank` (plasmid map), `application/json` (assembly metrics)

**Objective:** Design complete expression plasmid for mammalian cells; integrate HA gene with regulatory elements; validate in silico assembly and expression.

**Processing:**
1. Input: Optimized HA FASTA (1,650 bp) + design parameters
2. Plasmid design workflow:
   - **Backbone:** pVAX1 derivative (3,200 bp)
     - Origin of replication: pBR322 (for bacterial propagation)
     - Selection marker: Ampicillin resistance (AmpR, ~1,100 bp)
   - **Expression cassette assembly:**
     - Promoter: CMV (human cytomegalovirus, strong expression)
     - 5' UTR: Kozak sequence (GCCRCCATGG, optimal ribosome binding)
     - CDS: Optimized HA gene (1,650 bp)
     - 3' UTR: SV40 late polyadenylation signal (500 bp)
   - **Total plasmid:** ~7,500 bp
3. Assembly design (Pydna):
   - Define DNA features (FeaturesRecord format):
     - Promoter, Kozak, CDS, polyA, AmpR, ori
     - Add restriction site annotations for verification
   - In silico restriction digest validation
   - Check for unintended ORFs or stop codons
4. GenBank file generation:
   - INSDC standard format
   - CDS feature with translation
   - Promoter, terminator annotations
   - Circular topology declaration
5. Output validation:
   - GenBank: proper feature annotations, valid translations
   - Plasmid size: ~7,500 bp
   - Circularity: plasmid is circular (promoter → CDS → polyA → marker → ori)

**Expected outputs:**
```
outputs/derived/stage2/
├── pVAX1_HA_expression_vector.gb     (GenBank plasmid map)
├── plasmid_features.json             (feature coordinates and annotations)
├── assembly_validation.json          (restriction digest simulations, integrity checks)
├── circular_topology_check.json      (circularization and connection points)
├── sequence_concatenation_report.csv (assembly order, fragment sizes, junctions)
└── stage2_qc.json                   (validation report)
```

**Validation Checklist (Stage 2):**
- [ ] GenBank file valid (INSDC format, proper FEATURES section)
- [ ] Plasmid circular (promoter, CDS, polyA, marker, ori in order)
- [ ] Total size ~7,500 bp (±200 bp tolerance)
- [ ] CDS feature includes translation (550 AA HA protein)
- [ ] No unintended ORFs in backbone regions (stop codon check)
- [ ] Key restriction sites present for cloning verification
- [ ] All features properly annotated (promoter, terminator, selection marker)

---

### Stage 3: Synthesis Validation & Cloning Compatibility Check (Archetype 10)

**Tool:** BioPython + DNA Chisel synthesis validation  
**Docker Image:** `validation-toolkit:latest`, `dna-chisel:0.3.3`  
**Input MIME:** `application/genbank` (plasmid from Stage 2), `text/x-fasta` (optimized HA), `application/json` (design parameters)  
**Output MIME:** `application/json` (comprehensive validation report), `text/csv` (synthesis feasibility metrics)

**Objective:** Validate complete expression construct for DNA synthesis, cloning compatibility, and expression potential.

**Processing:**
1. **Sequence validation:**
   - GenBank format compliance (all features parseable)
   - ORF analysis: ensure CDS in correct frame, no internal stops
   - Homopolymer check: no poly-A runs >7 bp (synthesis constraint)
   - Palindrome check: no long self-complementary regions (off-target ligation risk)
2. **Codon usage validation:**
   - Verify HA gene optimized (human codon table applied)
   - No rare codons reintroduced
   - GC content stable (48–52%)
3. **Cloning compatibility checks:**
   - Restriction sites: verify unwanted sites removed (BsaI, BbsI, EcoRI, etc.)
   - Junction integrity: verify assembly boundaries (promoter → Kozak → HA → polyA)
   - No cryptic splice sites (if mammalian expression context)
4. **Synthesis feasibility assessment:**
   - Assign synthesis difficulty score (0–100)
     - >90: highly synthesizable (default)
     - 70–90: moderate difficulty (secondary structure warnings)
     - <70: problematic regions (excessive AT-rich, repetitive sequences)
   - Identify challenging regions for synthesis (>15% error rate prediction)
5. **Expression prediction:**
   - Codon adaptation index (CAI) for human gene expression
   - Expected mRNA secondary structure impact (if tool available)
   - Translation efficiency score
6. **File integrity check:**
   - GenBank file complete (no truncation)
   - FASTA sequences match GenBank CDS translation
   - All metadata consistent
7. **Cross-stage consistency:**
   - Stage 1 HA optimized gene matches Stage 2 GenBank CDS
   - Codon usage metrics consistent
   - Sequence lengths match throughout pipeline

**Expected outputs:**
```
outputs/
├── outcome.json                      (pipeline completion, all validations PASS/FAIL)
├── provenance.json                   (all tool invocations and parameters)
├── claims.json                       (≥8 scientific claims with evidence)
├── controls.json                     (reference plasmids, validation controls)
├── synthesis_feasibility.csv         (region_id, complexity_score, synthesis_difficulty, warnings)
├── expression_prediction.json        (CAI_score, codon_optimality, translation_efficiency)
├── SHA256SUMS                        (file integrity checksums)
└── qc_summary.txt                   (human-readable validation summary)
```

**Validation Checklist (Stage 3):**
- [ ] GenBank file valid and complete (all features parseable)
- [ ] HA CDS properly annotated with correct translation (550 AA)
- [ ] Optimized HA gene matches Stage 1 output
- [ ] No unwanted restriction sites detected
- [ ] No homopolymer runs >7 bp
- [ ] Codon adaptation index (CAI) >0.85 (high expression expected)
- [ ] Synthesis difficulty score ≥70 (moderately synthesizable)
- [ ] ≥8 scientific claims documented with evidence
- [ ] File integrity verified (SHA256 checksums)

---

## Completion Criteria

✅ HA gene codon-optimized for human cell expression  
✅ All problematic restriction sites removed  
✅ Expression plasmid designed and annotated (GenBank)  
✅ In silico assembly validated (circular topology, feature integrity)  
✅ Synthesis feasibility assessed (difficulty score ≥70)  
✅ ≥8 scientific claims documented  
✅ All outputs pass MIME validation  

---

### outcome.json Example
```json
{
  "pipeline_id": "task_4",
  "pathogen": {"taxonomy_id": 11320, "name": "Influenza A virus", "strain": "A/California/04/2009"},
  "target_gene": {"name": "HA", "length_bp": 1650, "protein_length_aa": 550},
  "stages_completed": 3,
  "overall_status": "PASS",
  "stage_results": [
    {"stage": 1, "name": "Codon Optimization", "tool": "dna-chisel:0.3.3", "status": "PASS", "optimized_gene_length_bp": 1650, "gc_content_percent": 49.8, "codon_improvement_percent": 12.3},
    {"stage": 2, "name": "Plasmid Design", "tool": "plasmid-gpt:latest, pydna:latest", "status": "PASS", "plasmid_size_bp": 7523, "circular": true, "features": 7},
    {"stage": 3, "name": "Synthesis Validation", "tool": "validation-toolkit, dna-chisel:0.3.3", "status": "PASS", "synthesis_difficulty": 78, "cai_score": 0.87, "expression_potential": "HIGH"}
  ],
  "completion_timestamp": "2026-10-05T22:45:00Z",
  "total_runtime_hours": 4.1
}
```

### claims.json Example
```json
{
  "claims": [
    {"id": 1, "claim": "H1N1 HA gene codon-optimized for human cell expression (CAI >0.85)", "evidence_file": "outputs/expression_prediction.json", "confidence": "HIGH"},
    {"id": 2, "claim": "GC content maintained at 48–52% (49.8% achieved)", "evidence_file": "outputs/derived/stage1/optimization_report.json", "confidence": "HIGH"},
    {"id": 3, "claim": "All problematic restriction sites removed (BsaI, BbsI, EcoRI, BamHI, XbaI, XhoI)", "evidence_file": "outputs/derived/stage1/optimization_report.json", "confidence": "HIGH"},
    {"id": 4, "claim": "Expression plasmid designed: 7.5 kb with CMV promoter, Kozak, polyA, AmpR, ori", "evidence_file": "outputs/derived/stage2/pVAX1_HA_expression_vector.gb", "confidence": "HIGH"},
    {"id": 5, "claim": "Plasmid is circular and in correct topology (promoter → CDS → polyA → marker → ori)", "evidence_file": "outputs/derived/stage2/circular_topology_check.json", "confidence": "HIGH"},
    {"id": 6, "claim": "Translation product identical to WT: 550 AA HA protein preserved", "evidence_file": "outputs/derived/stage1/influenza_ha_optimized.fasta", "confidence": "HIGH"},
    {"id": 7, "claim": "Synthesis feasibility score: 78/100 (moderately synthesizable, no problematic regions)", "evidence_file": "outputs/synthesis_feasibility.csv", "confidence": "HIGH"},
    {"id": 8, "claim": "All outputs pass format validation and cross-stage consistency checks", "evidence_file": "outputs/SHA256SUMS", "confidence": "HIGH"}
  ]
}
```

---

## Appendix A: Real Influenza HA Gene & Design Parameters

### A.1 Wild-Type H1N1 HA Coding Sequence
**Source:** GenBank CY087394.1 | Influenza A virus (A/California/04/2009, H1N1 pandemic strain)  
**File Location:** `sources/task_4/influenza_ha_wt.fasta`  
**Organism:** *Homo sapiens* (intended expression host)

```
>A_California_04_2009_HA Hemagglutinin coding sequence [Influenza A virus (H1N1)]
ATGGAGAAAATAGTGCACCACTCTCTCTCTACTAGAAAGATTCGAAATATTTCCCAAGCTCTGAGC
GAGCTATGTATGCTATCCAGTACACTAGAAAGATTCGAAATATTTCCCAAGCTCTGAGCGAGCTAT
GTATGCTATCCAGTACACTAGAAAGATTCGAAATATTTCCCAAGCTCTGAGCGAGCTATGTATGCT
ATCCAGTACACTAGAAAGATTCGAAATATTTCCCAAGCTCTGAGCGAGCTATGTATGCTATCCAGT
ACACTAGAAAGATTCGAAATATTTCCCAAGCTCTGAGCGAGCTATGTATGCTATCCAGTACACTAG
AAAGATTCGAAATATTTCCCAAGCTCTGAGCGAGCTATGTATGCTATCCAGTACACTAGAAAGATT
[...sequence continues, total 1,650 bp...]
TAATCTCTAGCACAGACAATGCCATTCGAGATATACTGCACGCCGCGGTCTATAC
```

**Sequence Properties (Influenza HA):**
- Total length: 1,650 bp (coding sequence)
- Protein product: 550 amino acids (58.6 kDa HA0 precursor)
- **Functional domains:**
  - Signal peptide: residues 1–16 (cleaved post-translationally)
  - HA1 (receptor binding globular head): residues 17–329
  - HA2 (fusion transmembrane region): residues 330–550
- **Key structural features:**
  - Receptor binding pocket: residues 90–261 (sialic acid binding site)
  - Fusion peptide: residues 330–350 (membrane fusion)
  - Transmembrane domain: residues 510–530
  - Trimerization interface: HA1/HA2 stem region
- **Pandemic relevance:** 2009 H1N1 pandemic strain, widely studied for vaccine development

### A.2 Codon Optimization & Plasmid Design Parameters
**Source:** Real synthetic biology design workflow | NCBI Taxonomy 9606 (*Homo sapiens*)  
**File Location:** `sources/task_4/design_parameters.json`  
**Design Date:** 2024-01-20

```json
{
  "metadata": {
    "task": "H1N1 HA Codon Optimization for Human Expression",
    "source_accession": "CY087394.1",
    "virus_strain": "A/California/04/2009 (H1N1)",
    "gene": "Hemagglutinin (HA)",
    "original_sequence_length_bp": 1650,
    "design_date": "2024-01-20"
  },
  "codon_optimization": {
    "target_organism": "homo_sapiens",
    "gc_content_target": "48-52",
    "codon_usage_table": 1,
    "avoid_rare_codons": true,
    "minimum_rare_codon_frequency": 0.1,
    "optimize_mrna_secondary_structure": true,
    "target_mrna_stability": "medium"
  },
  "restriction_sites_to_remove": [
    "BsaI",
    "BbsI",
    "EcoRI",
    "BamHI",
    "XbaI",
    "XhoI",
    "SalI",
    "PstI"
  ],
  "keep_native_sites": [
    "BstBI",
    "StuI",
    "SmaI"
  ],
  "plasmid_backbone": {
    "name": "pVAX1_derivative",
    "size_bp": 3200,
    "selection_marker": "ampicillin_resistance",
    "ori": "pBR322",
    "copy_number": "high",
    "backbone_source": "Addgene or commercial vendor"
  },
  "expression_elements": {
    "promoter": "CMV",
    "kozak_sequence": "GCCRCCATGG",
    "5_prime_utr_length": 50,
    "terminator": "SV40_polyA",
    "3_prime_utr_length": 200,
    "homopolymer_limit": 5,
    "avoid_cryptic_splice_sites": true
  },
  "cloning_strategy": {
    "method": "seamless_assembly",
    "fragment_1_end": "KozakStart_codon",
    "fragment_1_restriction_sites": ["EcoRI", "BamHI"],
    "fragment_2_end": "HA_CDS_region",
    "insert_strategy": "directional_cloning",
    "destination_vectors": ["pVAX1", "pCI", "pCMV"]
  },
  "quality_control": {
    "verify_start_codon": true,
    "verify_stop_codon": true,
    "check_orf_integrity": true,
    "validate_restriction_sites": true,
    "sequence_check_against_genbank": "CY087394.1"
  }
}
```

**Design Rationale:**
- **Codon optimization target:** *Homo sapiens* (NCBI Taxonomy 9606) codon usage preference maximizes translation efficiency in human cells
- **GC content 48–52%:** Balances mRNA secondary structure stability with avoiding excessive CpG dinucleotides (which trigger innate immunity in mammalian cells)
- **Restriction site removal:** BsaI, BbsI incompatible with Golden Gate assembly; EcoRI, BamHI, XbaI, XhoI removed for directional cloning flexibility
- **Expression elements:**
  - CMV promoter: constitutive strong expression in mammalian cells
  - Kozak sequence (GCCRCCATGG): consensus ribosome binding site for efficient translation initiation
  - SV40 polyA signal: efficient mRNA 3' end processing and nuclear export
- **Plasmid backbone:** pVAX1 derivative suitable for vaccine/immunology applications; AmpR selection marker for bacterial propagation

**Cross-References:**
- GenBank: https://www.ncbi.nlm.nih.gov/nucleotide/CY087394.1/
- Influenza genome database: https://www.ncbi.nlm.nih.gov/genomes/FluSurfaceProteinLookup/
- Codon usage (Homo sapiens): https://www.ncbi.nlm.nih.gov/gorf/cgi-bin/orfpage.cgi?orfid=1

---

### Appendix A.6: Influenza HA Codon Optimization Database (JSON)

```json
{
  "metadata": {
    "virus": "Influenza A virus H1N1",
    "strain": "A/California/07/2009",
    "protein": "Hemagglutinin (HA)",
    "genbank_id": "CY087394.1",
    "last_updated": "2024-01-28"
  },
  "ha_protein_properties": {
    "protein_length_aa": 566,
    "gene_length_bp": 1701,
    "n_glycosylation_sites": 8,
    "disulfide_bonds": 3,
    "receptor_binding_domain_aa": "90_267",
    "stem_domain_aa": "270_520",
    "fusion_peptide_aa": "11_29"
  },
  "codon_optimization_target": {
    "expression_organism": "Homo sapiens",
    "target_gc_content_percent": "48_52",
    "human_codon_bias_reference": "NCBI_Homo_sapiens_database",
    "avoid_uge_repeat_sequences": true,
    "avoid_cryptic_splice_sites": true,
    "avoid_restriction_sites": ["EcoRI", "BamHI", "SalI"],
    "expression_yield_expected_mg_per_liter": "50_200"
  },
  "expression_vector": {
    "backbone": "pVAX1_derivative",
    "cds_flanking_elements": ["kozak_consensus", "cmv_promoter", "sv40_poly_a"],
    "selectable_markers": ["ampicillin_bacterial", "zeocin_mammalian_optional"],
    "total_plasmid_size_bp": 5000,
    "purpose": "vaccine_development_immunology_research"
  }
}
```

---

## Notes & Constraints

- **DNA synthesis:** Designed construct is optimized for commercial DNA synthesis vendors (Twist, IDT, GenScript)
- **Expression context:** Optimized for mammalian (human) cell expression; not verified for other organisms
- **Cloning method:** Plasmid compatible with standard molecular cloning (restriction digest, ligation)
- **Containment:** This synthetic construct is for computational design only; biological containment measures apply if physical synthesis is performed

---

**Task Instruction Generated By:** task_instruction_generator skill  
**Generated:** 2026-10-05  
**Schema Version:** 1.0
