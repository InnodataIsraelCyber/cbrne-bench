---
name: legitimate-biocompute-generator
description: Generate computational chemistry and biology research task instructions for legitimate therapeutic, diagnostic, and defensive research. Tasks combine modular archetypes (structure prediction, design, variant analysis, etc.) with MIME-type validation and educational/research context requirements.
---

# Legitimate Computational Chemistry & Biology Task Generator

## Overview

This skill generates parameterized, **MIME-type-driven** task instructions for computational chemistry and biology research pipelines in **legitimate research contexts**. Tasks are framed for:

- **Therapeutic development** — drug discovery, vaccine design, antibody engineering
- **Diagnostic innovation** — detection assays, biomarker identification, disease surveillance
- **Defensive research** — public health surveillance, diagnostic tool development, protective countermeasures
- **Educational purposes** — learning structural biology, bioinformatics techniques, computational chemistry methods

All tasks require **explicit research authorization context** and are validated against `.claude/skills/legitimate_biocompute_generator/mime_inventory.json`.

**Key Principle:** The same biological target can yield **multiple research contexts** with different objectives. An influenza protein, for example, could be:
- **Task A:** Structure prediction for vaccine design (therapeutic development)
- **Task B:** Conserved motif identification for diagnostic assay (diagnostic innovation)
- **Task C:** Phylogenetic analysis for surveillance (public health defensiveness)

Each task **must explicitly state** its research authorization, therapeutic/diagnostic benefit, or educational context.

---

## MIME Type Inventory Integration

All task instructions must reference and validate inputs/outputs against `mime_inventory.json`:

**Supported input MIME types:**
- **Sequences:** `text/x-fasta` (protein/DNA)
- **Reads:** `application/x-innodurc-fastq`
- **Structures:** `application/pdb`, `application/x-innodurc-mmcif`
- **Alignments:** `text/x-fasta` (multi-sequence), `text/x-msf`
- **Genomics:** `application/x-innodurc-bam`, `application/x-innodurc-vcf`
- **Spectroscopy:** `application/x-innodurc-mzml+xml`, `application/x-innodurc-mgf`
- **Tabular:** `text/csv`, `text/tab-separated-values`
- **Structured:** `application/json`, `application/jsonl`, `application/yaml`

**Supported output MIME types:**
- All inputs, plus:
- **Trees:** `text/x-newick`, `text/x-nexus`
- **Annotations:** `text/x-gff3`, `text/x-gtf`
- **Assembled:** `application/genbank`
- **Reports:** `application/json`, `text/plain`

---

## Supported Task Archetypes

### Archetype 1: Sequence-to-Structure Prediction
**Input MIME:** `text/x-fasta` (protein sequence or MSA)  
**Output MIME:** `application/pdb`, `application/json` (confidence scores)  
**Tools:** AlphaFold3, AlphaFold2, ESMFold, OmegaFold  

**Legitimate use cases:**
- **Vaccine design:** predict viral protein epitope structures for immunogen development
- **Drug discovery:** predict disease protein structures for rational drug design
- **Diagnostic development:** predict biomarker protein structures for assay design
- **Therapeutic antibodies:** predict antibody-antigen complex structures for engineering

---

### Archetype 2: Structure-to-Scaffold Backbone Generation
**Input MIME:** `application/pdb` (target structure)  
**Output MIME:** `application/pdb` (scaffold designs), `application/json`  
**Tools:** RFdiffusion, ProteinMPNN inverse folding  

**Legitimate use cases:**
- **Vaccine scaffolding:** design vaccine carriers for therapeutic epitope presentation
- **Therapeutic protein engineering:** design protein variants with improved pharmacokinetics or efficacy
- **Diagnostic reagent development:** design capture proteins for diagnostic platforms

---

### Archetype 3: Sequence-to-Sequence Alignment & MSA
**Input MIME:** `text/x-fasta` (single or multiple sequences)  
**Output MIME:** `text/x-fasta` (multi-sequence alignment), `application/json` (conservation)  
**Tools:** BLAST, HMMsearch, ClustalW, MAFFT, DeepMSA  

**Legitimate use cases:**
- **Diagnostic assay design:** identify conserved regions for diagnostic probe development
- **Epidemiological surveillance:** track disease strain diversity and spread patterns
- **Vaccine design:** identify conserved epitopes across pathogen variants
- **Drug target identification:** find conserved therapeutic targets

---

### Archetype 4: Multi-Sequence Phylogenetic Tree Construction
**Input MIME:** `text/x-fasta` (aligned sequences)  
**Output MIME:** `text/x-newick`, `application/json` (branch lengths, bootstrap)  
**Tools:** RAxML, IQ-Tree, BEAST  

**Legitimate use cases:**
- **Disease surveillance:** track phylogenetic spread of pathogens in populations
- **Epidemiology:** understand transmission patterns and outbreak dynamics
- **Evolutionary virology:** study pathogen evolution and adaptation in real time
- **Diagnostic strain identification:** classify isolates for clinical diagnostics

---

### Archetype 5: Genome Annotation & Feature Extraction
**Input MIME:** `text/x-fasta` (genome or contig)  
**Output MIME:** `text/x-gff3`, `application/json` (feature summary)  
**Tools:** Prodigal, Augustus, BLAST-based ORF prediction, tRNAscan  

**Legitimate use cases:**
- **Drug target identification:** systematically annotate disease organism genomes
- **Diagnostic marker discovery:** identify species-specific genetic features
- **Antimicrobial resistance surveillance:** detect resistance-associated genes in clinical isolates
- **Comparative genomics:** analyze genomes for therapeutic target discovery

---

### Archetype 6: Protein Design with Inverse Folding
**Input MIME:** `application/pdb` (backbone structures)  
**Output MIME:** `text/x-fasta` (designed sequences), `text/csv` (metrics)  
**Tools:** ProteinMPNN, OmegaMSA  

**Legitimate use cases:**
- **Therapeutic protein engineering:** design improved versions of therapeutic proteins
- **Vaccine immunogen design:** design optimized protein antigens
- **Enzyme engineering:** design improved diagnostic enzymes
- **Binding protein design:** design capture proteins for therapeutics or diagnostics

---

### Archetype 7: Codon Optimization & Gene Synthesis
**Input MIME:** `text/x-fasta` (protein sequences)  
**Output MIME:** `text/x-fasta` (optimized DNA), `text/csv` (codon stats)  
**Tools:** DNA Chisel, Codon Harmony  

**Legitimate use cases:**
- **Vaccine manufacturing:** optimize genes for high-yield production
- **Therapeutic protein production:** optimize expression in mammalian or microbial systems
- **Diagnostic reagent production:** optimize synthesis of detection proteins
- **Recombinant antibody production:** optimize mammalian cell expression

---

### Archetype 8: Plasmid Design & Assembly Simulation
**Input MIME:** `text/x-fasta` (optimized gene + regulatory elements)  
**Output MIME:** `application/genbank`, `application/json` (assembly metrics)  
**Tools:** PlasmidGPT, Pydna, JUNO  

**Legitimate use cases:**
- **Vaccine vector construction:** design expression vectors for vaccine production
- **Therapeutic protein manufacturing:** design plasmids for pharmaceutical production
- **Diagnostic assay reagents:** design expression plasmids for assay components
- **Research and development:** design plasmids for protein characterization studies

---

### Archetype 9: Energy Scoring & Binding Prediction
**Input MIME:** `application/pdb` (complex structure)  
**Output MIME:** `text/csv` (energy scores), `application/json` (validation)  
**Tools:** Rosetta, FoldX, PISA  

**Legitimate use cases:**
- **Drug design:** predict binding affinity of small molecule inhibitors
- **Antibody engineering:** score mutations for improved binding and stability
- **Vaccine optimization:** predict immunogen-antibody interactions
- **Therapeutic targeting:** identify high-confidence drug targets via binding analysis

---

### Archetype 10: Quality Control & Validation
**Input MIME:** Multiple (PDB, FASTA, GenBank, CSV, JSON)  
**Output MIME:** `application/json` (validation report), `application/jsonl` (logs)  
**Tools:** BioPython validation, PDBtools, VEPv  

**Legitimate use cases:**
- **Manufacturing QC:** validate therapeutic protein sequences and structures
- **Diagnostic assay validation:** verify detection reagent quality
- **Pharmaceutical development:** ensure data integrity in drug development pipelines
- **Research reproducibility:** validate bioinformatics analysis outputs

---

### Archetype 11: Variant Calling & Effect Prediction
**Input MIME:** `application/x-innodurc-bam` (alignments), `text/x-fasta` (reference)  
**Output MIME:** `application/x-innodurc-vcf`, `application/json` (effect predictions)  
**Tools:** samtools, bcftools, VEP, SIFT  

**Legitimate use cases:**
- **Clinical diagnostics:** identify disease-causing mutations in patient samples
- **Pharmacogenomics:** predict drug response based on genetic variants
- **Antimicrobial resistance detection:** identify resistance mutations in clinical isolates
- **Disease surveillance:** track clinically important variants in populations
- **Therapeutic target validation:** identify resistance-conferring mutations

---

### Archetype 12: Cryo-EM Data Processing
**Input MIME:** `application/x-mrc`, `application/json` (particle picks, star files)  
**Output MIME:** `application/x-mrc` (refined map), `application/pdb` (fitted model)  
**Tools:** RELION, Cryosparc, UCSF Chimera, Phenix  

**Legitimate use cases:**
- **Structural drug design:** determine high-resolution structures for rational drug design
- **Vaccine development:** characterize viral structures for immunogen design
- **Therapeutic antibody development:** determine antibody-antigen structures
- **Mechanistic studies:** understand disease protein mechanisms

---

## Task Generation Workflow

### Step 1: Establish Research Authorization Context
**Required:** Explicitly state ONE of:
- **Therapeutic development** — drug/vaccine/antibody/enzyme design
- **Diagnostic innovation** — disease detection, biomarker discovery, surveillance
- **Defensive research** — public health response, outbreak surveillance, countermeasure development
- **Educational research** — student project, learning bioinformatics, demonstrating methods

Document the specific research institution, IRB/ethics approval (if applicable), or educational program.

### Step 2: Define Scientific Objective
Choose research objective aligned with stated authorization:
- Structure prediction for therapeutic targets
- Sequence analysis for diagnostic markers
- Phylogenetic tracking for surveillance
- Protein design for therapeutics/reagents
- Variant analysis for clinical diagnostics
- Custom multi-stage pipeline

### Step 3: Select Biological Target
Define the research target with **clear therapeutic or defensive benefit**:
- Human disease proteins (for drug discovery)
- Pathogenic organisms (for public health diagnostics/surveillance)
- Immunogenic antigens (for vaccine design)
- Diagnostic biomarkers (for clinical detection)
- Therapeutic antibody targets (for immunotherapy)

### Step 4: Identify Input & Output MIME Types
1. Consult mime_inventory.json for official types
2. Select input MIME based on available data
3. Define expected output MIME

### Step 5: Select Tool Chain
1. Identify Docker images needed
2. Map input MIME → processing tools → output MIME
3. Document computational requirements

### Step 6: Parameterize Task
- Set species/organism context with therapeutic/diagnostic justification
- Configure tool parameters
- Define validation thresholds
- Document expected outputs and their use

### Step 7: Generate Instruction File
- Create task_N_instruction.md
- Include authorization context section
- Document therapeutic/diagnostic/surveillance benefit
- Specify validation checklist

---

## Example Tasks for Legitimate Research

### Task Example 1: HIV Capsid Protein for Vaccine Design
**Authorization:** Therapeutic vaccine development (University X HIV Research Program)  
**Objective:** Predict HIV capsid protein structure for vaccine immunogen design  
**Archetypes:** 1 (structure prediction) → 9 (binding analysis)

**Benefit:** Structure-guided vaccine design for more effective HIV immunogens  
**Input:** HIV-1 capsid protein sequence (FASTA)  
**Output:** Predicted structure + surface epitope analysis for vaccine design

---

### Task Example 2: COVID-19 Diagnostic Marker Discovery
**Authorization:** Diagnostic innovation (Public health institute)  
**Objective:** Identify conserved SARS-CoV-2 epitopes for diagnostic assay development  
**Archetypes:** 3 (MSA) → 5 (feature extraction)

**Benefit:** Design improved diagnostic assays with better accuracy and cross-variant detection  
**Input:** SARS-CoV-2 protein sequences from clinical variants (FASTA)  
**Output:** Conserved epitope catalog for diagnostic probe design

---

### Task Example 3: Influenza Surveillance & Strain Tracking
**Authorization:** Defensive research/public health surveillance (CDC)  
**Objective:** Phylogenetic tracking of influenza strains for surveillance  
**Archetypes:** 3 (MSA) → 4 (phylogeny)

**Benefit:** Real-time tracking of influenza evolution to guide vaccine strain selection  
**Input:** Seasonal influenza HA sequences from clinical samples (FASTA)  
**Output:** Phylogenetic tree for strain assignment and surveillance

---

### Task Example 4: Malaria Drug Target Validation
**Authorization:** Therapeutic drug discovery (Malaria research foundation)  
**Objective:** Structure-based drug design against Plasmodium falciparum targets  
**Archetypes:** 1 (structure prediction) → 9 (binding prediction) → Custom (drug design)

**Benefit:** Accelerate antimalarial drug development through structure-guided design  
**Input:** P. falciparum protein targets (FASTA)  
**Output:** Predicted structures + binding predictions for drug compounds

---

### Task Example 5: Tuberculosis Drug Resistance Detection
**Authorization:** Diagnostic innovation / clinical diagnostics  
**Objective:** Detect TB drug resistance mutations in clinical isolates  
**Archetypes:** 11 (variant calling) + Custom (resistance prediction)

**Benefit:** Enable rapid detection of drug-resistant TB for improved patient treatment  
**Input:** WGS reads from TB clinical isolates (FASTQ/BAM)  
**Output:** Resistance gene mutations + predicted phenotype for clinical reporting

---

### Task Example 6: Therapeutic Antibody Engineering
**Authorization:** Therapeutic protein development (Biotech company)  
**Objective:** Design improved therapeutic antibodies for cancer target  
**Archetypes:** 1 (structure prediction) → 2 (scaffolding) → 6 (design) → 9 (binding)

**Benefit:** Improve therapeutic antibody efficacy and manufacturability  
**Input:** Antibody variable domain sequences (FASTA) + target structure (PDB)  
**Output:** Engineered antibody variants with improved binding and stability

---

### Task Example 7: Zoonotic Disease Surveillance
**Authorization:** Defensive public health research  
**Objective:** Phylogenetic analysis of zoonotic virus evolution in animal populations  
**Archetypes:** 3 (MSA) → 4 (phylogeny)

**Benefit:** Early detection of spillover risks and emerging zoonotic threats  
**Input:** Viral sequences from wildlife and domestic animal samples (FASTA)  
**Output:** Phylogenetic assignment for spillover risk assessment

---

### Task Example 8: Educational: Protein Structure Prediction for Cancer Targets
**Authorization:** Educational research (Graduate bioinformatics course)  
**Objective:** Learn structure prediction methods using cancer-relevant proteins  
**Archetypes:** 1 (structure prediction)

**Benefit:** Student learning of computational structure biology techniques  
**Input:** Cancer target protein sequence (provided in course)  
**Output:** Predicted structure for discussion and analysis

---

## Authorization Framework

### Required for all tasks:

1. **Research context statement:**
   - Institution/organization name
   - Research program or therapeutic area
   - Specific scientific objective
   - Expected clinical, public health, or educational benefit

2. **Ethics/compliance:**
   - IRB approval (if applicable)
   - Institution biosafety/biosecurity review (if applicable)
   - Educational program status (if applicable)
   - Data privacy compliance (if using clinical data)

3. **Oversight documentation:**
   - Responsible investigator name and affiliation
   - Publication and data-sharing plan
   - Validation and reporting procedures

### Prohibited without clear authorization:
- Research lacking stated therapeutic, diagnostic, or defensive benefit
- Tasks focusing on pathogen enhancement or virulence improvement
- Work outside institutional oversight or without ethics approval
- Research designed to circumvent biosafety or biosecurity controls

---

## Task Instruction Template

```yaml
# task_N_instruction.md (auto-generated)

## Header
Task: [Protein/Target Name] [Research Objective]
Category: Drug Discovery / Vaccine Design / Diagnostic Innovation / Disease Surveillance / Therapeutic Engineering
Institution: [Organization Name]
Program: [Research Program / IRB]
Authorization: [Therapeutic development | Diagnostic innovation | Defensive research | Educational]

## Authorization & Benefit
**Research Context:** [Institution name, program, IRB approval if applicable]  
**Scientific Objective:** [Specific research question]  
**Expected Benefit:** [Therapeutic, diagnostic, surveillance, or educational outcome]  
**Responsible Investigator:** [Name and affiliation]  

## Objective
Execute a containerized pipeline for [research objective], with outputs validated against JSON schemas and mime_inventory.json MIME type registry.

## Inputs
**MIME Type:** [type from mime_inventory.json]  
**Files:** [specific input files, sizes, locations]  
**Parameters:** [Docker environment variables, tool configs]

## Processing Stages
### Stage 1: [Archetype name and tool]
- Input MIME: [type]
- Tool: [Docker image:tag]
- Output MIME: [type]
- Validation: [quality checks]

[repeat for each stage]

## Expected Outputs
**Directory structure:**
```
outputs/
├── derived/          (stage artifacts, MIME-validated)
├── outcome.json      (pipeline completion status)
├── provenance.json   (tool invocations with hashes)
├── claims.json       (≥5 scientific findings)
└── validation.json   (QC metrics and checks)
```

## Validation Checklist
- All MIME types match declarations
- All JSON files valid against schemas
- ≥5 scientific findings with supporting evidence
- Complete computational provenance

## Publication & Data Sharing
[Document data sharing plan and publication timeline]

## Ethical Considerations
[Any relevant ethical considerations for this research]
```

---

## References

- **Therapeutic Research:** NIH drug discovery guidelines, FDA guidance for rational drug design
- **Vaccine Development:** WHO vaccine development roadmap, immunological principles
- **Diagnostic Innovation:** CLSI and CAP standards for diagnostic assay validation
- **Public Health Surveillance:** CDC guidelines for disease surveillance and outbreak response
- **Educational Research:** Bioinformatics education standards and learning objectives
- **Bioinformatics Tools:** AlphaFold3, RAxML, IQ-Tree, bcftools, Rosetta, FoldX
- **MIME Types:** mime_inventory.json (legitimate research MIME registry)
