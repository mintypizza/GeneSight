# GeneSight: AI-Powered Genetic Variant Interpretation with Gemma 4

## Bridging the Gap Between Genetic Data and Clinical Understanding

### The Problem

Over 300 million people worldwide are affected by rare diseases, with approximately 80% having a genetic component. Yet patients endure an average "diagnostic odyssey" of 4–7 years before receiving a correct diagnosis. This crisis is compounded by a severe shortage of clinical geneticists — fewer than 5,000 serve the entire United States, and access is even more limited in developing nations. Furthermore, 95% of genomic reference data derives from European-ancestry populations, creating systematic biases that disadvantage underserved communities.

When patients receive genetic test results, they face an incomprehensible wall of variant nomenclature, clinical classifications, and probabilistic risk assessments. Without expert interpretation, these results are effectively useless — or worse, misleading.

### The Solution: GeneSight

GeneSight is an AI-powered genetic variant interpretation platform that leverages **Gemma 4 31B-IT** with **native function calling** to act as an autonomous genetic counselor. A user inputs a genetic variant in any format, and Gemma 4 autonomously:

1. **Parses** the variant from natural language input
2. **Plans** which databases to query based on the variant type
3. **Calls tools** in real-time — ClinVar, UniProt, PubMed APIs
4. **Applies** ACMG/AMP classification criteria systematically
5. **Checks** pharmacogenomic drug interactions
6. **Synthesizes** all evidence into grounded clinical interpretations
7. **Generates** both clinical and patient-friendly reports

All while keeping genetic data private — it never leaves the device.

### Architecture & Gemma 4 Integration

GeneSight is built as a Python/Streamlit application using the `google-genai` SDK for Gemma 4 integration. The architecture follows a modular design:

**Core Agent Layer** — The `GemmaAgent` class implements a manual function calling loop with `gemma-4-31b-it`. We deliberately use manual (not automatic) function calling so each tool call is visible in the UI, providing full transparency into the AI's reasoning process. The agent receives a structured system prompt that defines a clinical analysis protocol, ensuring consistent, thorough evaluations.

**Five Function-Calling Tools:**

| Tool | Source | Purpose |
|------|--------|---------|
| `tool_query_clinvar` | NCBI E-Utilities | Clinical significance, review status, conditions |
| `tool_query_uniprot` | UniProt REST API | Protein function, domains, disease associations |
| `tool_search_pubmed` | NCBI E-Utilities | Relevant research literature with citations |
| `tool_assess_pathogenicity` | Local ACMG JSON | Systematic 28-criteria pathogenicity scoring |
| `tool_check_drug_interactions` | Curated PharmGKB | Drug interaction data for 7 pharmacogenes |

Each tool is defined as a typed Python function with comprehensive docstrings. The `google-genai` SDK automatically converts these to JSON schemas that Gemma 4 uses for function calling decisions.

**Privacy Architecture** — GeneSight sends only gene symbols and rsIDs to public scientific APIs. Raw genetic data (sequences, VCF files, patient information) never leaves the device. This is critical because genetic data is among the most sensitive personal information — making local/edge deployment with Gemma 4 the ideal architecture.

**Visualization Layer** — Four interactive Plotly visualizations provide immediate visual understanding: a pathogenicity gauge chart, ACMG evidence radar, evidence source bar chart, and an interactive gene-disease-drug network graph built with NetworkX.

### Technical Challenges & Solutions

**Challenge 1: Variant Format Diversity.** Genetic variants are expressed in many formats — rsIDs, HGVS notation, star alleles, genomic coordinates, protein changes. Our `variant_parser` module uses regex-based parsing to handle 7 different input formats, automatically extracting gene names, variant types, and generating optimal database search terms.

**Challenge 2: API Rate Limiting & Reliability.** NCBI enforces strict rate limits (3 requests/second). We implemented a local file-based caching system with 7-day TTL, meaning previously analyzed variants work offline — critical for the intended deployment environment of clinics with unreliable internet.

**Challenge 3: Grounding AI Output.** LLM hallucination is unacceptable in clinical genetics. Every claim in GeneSight's output is grounded by data from the tool calls. The evidence trail is displayed alongside the analysis, showing exactly which databases were queried and what they returned. The ACMG classification uses a deterministic rule engine — the AI synthesizes, but the scoring is algorithmic.

**Challenge 4: Dual Audience Reports.** Clinical reports must be technically precise for healthcare providers, while patient reports must be compassionate and jargon-free. We use two separate Gemma 4 generation passes — one with clinical system prompting, one with patient-communication prompting — producing reports appropriate for each audience.

### Why Gemma 4?

Gemma 4's **native function calling** is the enabling technology. Unlike prompt-engineered tool use in earlier models, Gemma 4 reliably produces structured JSON function calls from schema definitions. This is essential for a medical application where tool call reliability directly impacts clinical accuracy.

The **open-weight** nature of Gemma 4 is equally important. Genetic data privacy is non-negotiable — patients and clinicians need assurance that data stays local. Gemma 4's availability for edge deployment (especially the E2B and E4B variants) means GeneSight can eventually run entirely on-device without any cloud dependency.

### Impact & Target Users

- **Rural clinics** with limited access to genetic specialists
- **Community health workers** who need to explain results to patients
- **Developing nations** where clinical geneticists are virtually nonexistent
- **Patient advocacy groups** seeking to understand their conditions
- **Medical students** learning clinical genetics interpretation

### Demo Variants

GeneSight ships with 5 pre-loaded demo variants covering different clinical scenarios:

- **BRCA1 c.68_69del** — Pathogenic, hereditary breast/ovarian cancer
- **CFTR F508del** — Pathogenic, cystic fibrosis
- **TP53 R175H** — Pathogenic, Li-Fraumeni syndrome
- **APOE ε4** — Risk factor, Alzheimer's disease
- **CYP2D6 *4** — Drug response, poor metabolizer

### Hackathon Tracks Addressed

| Track | Implementation |
|-------|---------------|
| **Health & Sciences** | Clinical genetic interpretation bridging data and understanding |
| **Digital Equity** | Runs locally, accessible to underserved communities worldwide |
| **Safety & Trust** | Grounded outputs with citations; full evidence trail transparency |
| **Global Resilience** | Offline-capable with local caching for areas with limited connectivity |

### Technology Stack

Python 3.10+ · Streamlit · google-genai SDK · Gemma 4 31B-IT · Plotly · NetworkX · NCBI E-Utilities · UniProt REST API · ACMG/AMP 2015 Guidelines

### Conclusion

GeneSight demonstrates that Gemma 4's native function calling transforms what's possible in clinical AI. By combining an open-weight model with real scientific databases and established clinical guidelines, we've created a tool that could meaningfully reduce the diagnostic odyssey for millions of patients worldwide — especially those who need it most.
