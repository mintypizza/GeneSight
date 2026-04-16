# 🧬 GeneSight — AI-Powered Genetic Variant Interpreter

> **Powered by Gemma 4** | Built for the Gemma 4 Impact Challenge

GeneSight uses Gemma 4's native function calling to bring clinical-grade genetic variant interpretation to any device — no cloud required, no genetic data ever leaves the device.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square)
![Gemma 4](https://img.shields.io/badge/Gemma_4-31B--IT-green?style=flat-square)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-red?style=flat-square)
![License](https://img.shields.io/badge/License-Apache_2.0-yellow?style=flat-square)

---

## 🎯 The Problem

- **300+ million people** worldwide are affected by rare diseases
- Patients wait an average of **4–7 years** for a correct diagnosis
- **95% of genomic data** comes from European-ancestry populations
- Access to clinical geneticists is severely limited in underserved communities

## 💡 The Solution

GeneSight is an **autonomous AI genetic counselor** that:

1. 🔍 **Parses** variant input in any format (rsID, HGVS, gene+variant)
2. 🧠 **Reasons** about what information is needed using Gemma 4
3. 🔧 **Calls tools** — ClinVar, UniProt, PubMed — via native function calling
4. ⚖️ **Applies** ACMG/AMP clinical classification criteria
5. 💊 **Checks** pharmacogenomic drug interactions
6. 📄 **Generates** both clinical and patient-friendly reports

All while keeping **genetic data private** — it never leaves your device.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────┐
│                User Interface (Streamlit)         │
│  ┌────────────┬──────────┬─────────┬──────────┐  │
│  │  Analyze   │ Results  │ Reports │  About   │  │
│  └─────┬──────┴────┬─────┴────┬────┴──────────┘  │
│        │           │          │                   │
│  ┌─────▼───────────▼──────────▼────────────────┐  │
│  │        Gemma 4 Agent (Function Calling)      │  │
│  │  ┌─────────┬──────────┬─────────┬─────────┐ │  │
│  │  │ ClinVar │ UniProt  │ PubMed  │  ACMG   │ │  │
│  │  │  Tool   │  Tool    │  Tool   │  Tool   │ │  │
│  │  └────┬────┴────┬─────┴────┬────┴────┬────┘ │  │
│  └───────┼─────────┼──────────┼─────────┼──────┘  │
│          │         │          │         │          │
│    ┌─────▼────┐ ┌──▼──────┐ ┌▼──────┐ ┌▼───────┐ │
│    │  NCBI    │ │ UniProt │ │ NCBI  │ │ Local  │ │
│    │ E-Utils  │ │ REST API│ │E-Utils│ │ JSON   │ │
│    └──────────┘ └─────────┘ └───────┘ └────────┘ │
└──────────────────────────────────────────────────┘
```

### Key Technical Features

| Feature | Implementation |
|---------|---------------|
| **Gemma 4 Function Calling** | `google-genai` SDK with manual agentic loop |
| **Multi-Database Queries** | ClinVar, UniProt, PubMed via REST APIs |
| **ACMG Classification** | Structured rule engine with 28 criteria |
| **Pharmacogenomics** | Curated knowledge base from PharmGKB/CPIC |
| **Privacy Architecture** | Only gene names/rsIDs sent to public APIs |
| **Caching** | Local file cache for offline re-analysis |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- A free [Google AI Studio API key](https://aistudio.google.com/apikey)

### Installation

```bash
# Clone or navigate to the project
cd GeneSight

# Install dependencies
pip install -r requirements.txt

# Set your API key (optional — can also enter in the app)
set GEMINI_API_KEY=your_api_key_here

# Run the app
streamlit run app.py
```

### Demo Variants

Try these well-known variants to see GeneSight in action:

| Variant | Gene | Significance |
|---------|------|-------------|
| `BRCA1 c.68_69del` | BRCA1 | Pathogenic — Breast/Ovarian Cancer |
| `CFTR F508del` | CFTR | Pathogenic — Cystic Fibrosis |
| `TP53 R175H` | TP53 | Pathogenic — Li-Fraumeni Syndrome |
| `APOE ε4` | APOE | Risk Factor — Alzheimer's Disease |
| `CYP2D6 *4` | CYP2D6 | Drug Response — Poor Metabolizer |

---

## 📁 Project Structure

```
GeneSight/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── .streamlit/
│   └── config.toml             # Dark theme configuration
├── core/
│   ├── gemma_agent.py          # Gemma 4 agent with function calling
│   ├── tools.py                # 5 tool definitions for function calling
│   └── report_generator.py     # Clinical & patient report generation
├── data/
│   ├── acmg_guidelines.json    # ACMG/AMP variant classification criteria
│   ├── sample_variants.json    # Pre-loaded demo variants
│   └── gene_panels.json        # Gene panels (cancer, cardio, neuro, etc.)
├── services/
│   ├── clinvar_service.py      # NCBI ClinVar API integration
│   ├── uniprot_service.py      # UniProt REST API integration
│   └── pubmed_service.py       # PubMed literature search
├── ui/
│   ├── styles.py               # Premium dark theme CSS
│   ├── components.py           # Reusable UI components
│   └── visualizations.py       # Plotly charts & network graphs
└── utils/
    ├── variant_parser.py       # Multi-format variant parser
    └── cache_manager.py        # Local result caching
```

---

## 🎯 Hackathon Tracks

| Track | How GeneSight Addresses It |
|-------|--------------------------|
| **Health & Sciences** | Bridges the gap between raw genetic data and actionable clinical insight |
| **Digital Equity & Inclusivity** | Runs locally — accessible to rural clinics and developing nations |
| **Safety & Trust** | Outputs grounded in ClinVar, UniProt, PubMed with full citations |
| **Global Resilience** | Offline-first architecture with local caching |

---

## ⚠️ Disclaimer

GeneSight is an **educational and research tool**. It is NOT a substitute for professional genetic counseling or clinical diagnosis. All findings should be reviewed by a qualified healthcare professional before any clinical decisions are made.

---

## 📜 License

Apache License 2.0

## 🙏 Acknowledgments

- [Google Gemma 4](https://ai.google.dev/gemma) — Open-weight AI model
- [NCBI ClinVar](https://www.ncbi.nlm.nih.gov/clinvar/) — Variant clinical significance
- [UniProt](https://www.uniprot.org/) — Protein function database
- [PubMed](https://pubmed.ncbi.nlm.nih.gov/) — Biomedical literature
- [ACMG/AMP Guidelines](https://www.acmg.net/) — Variant classification standards
- [PharmGKB](https://www.pharmgkb.org/) — Pharmacogenomics knowledge base
