# AIMScribe - Clinical Decision Support Engine

## 🌟 Key Features

- **Canonical Protocol Cards (`data/cards/cards.jsonl`)**: Structured clinical knowledge representation with machine-evaluable prerequisites.
- **Dual Hybrid Retrieval (BM25 + Dense RRF)**: Combines sparse BM25 indexing (capturing exact clinical terms, lab tests, and drug names) with dense vector embeddings (`BAAI/bge-small-en-v1.5` in ChromaDB) fused via Reciprocal Rank Fusion (RRF).
- **Deterministic Applicability Checker (`aimscribe.applicability`)**: Fast rule-based pre-inference guard that flags candidate cards to prevent contraindications and over-treatment.
- **Interactive Clinical Cockpit (`app.py`)**: Dark-mode Streamlit interface with clinical test cases (C1–C6), dynamic differential diagnosis view, medication dosing tables, and interactive citation inspector.

---

## 📚 Supported Clinical Guidelines

| Disease | Guideline |  Authority |
|---|---|---|
| **Dengue** | National Guideline for Clinical Management of Dengue | 5th Edition (2025), DGHS Bangladesh |
| **Hypertension** | National Guideline on Hypertension | 2nd Edition (2023), DGHS Bangladesh |
| **Cholera** | Clinical Tools for Cholera Treatment Facilities | Version 1.0 (2024), World Health Organization (WHO) |
| **Chikungunya** | National Guideline on Clinical Management of Chikungunya Fever | 1st Edition (2017), IEDCR / DGHS Bangladesh |

---

## 🚀 Quickstart & Project Launch (Bash)

### 1. Prerequisites
- Python 3.10 to 3.12 installed
- Git Bash or Linux/macOS shell (for Windows PowerShell, see note below)

### 2. Environment Setup & Dependency Installation

```bash
cd project

# Create a venv
python -m venv .venv

#bash
source .venv/Scripts/activate

pip install --upgrade pip
pip install -r requirements.txt
```

Open `.env` and configure your chosen LLM backend:

#### Option A: Groq Cloud
```env
LLM_PROVIDER=groq
GROQ_MODEL=openai/gpt-oss-120b
GROQ_API_KEY=groq_api_key
EMBED_MODEL=BAAI/bge-small-en-v1.5
TEMPERATURE=0
```

### 4. Launch the Streamlit Web Application

```bash
streamlit run app.py
```

Once launched, open your browser at **`http://localhost:8501`**.



## 🛠️ Data Pipeline & Knowledge Base Construction

To extract, validate, and build the hybrid search index from raw guideline PDFs:

```bash
# 1. Extract text, tables, and page metadata from guideline PDFs
python scripts/extract_pdfs.py

# 2. (Optional) Draft initial protocol cards using LLM assistance
# python scripts/draft_cards.py

# 3. Validate canonical cards against schema and verbatim PDF evidence
python scripts/validate_cards.py

# 4. Build/rebuild sparse BM25 and dense ChromaDB vector indices
python scripts/build_index.py
```

---

## 🧪 Evaluation & Benchmarking

The evaluation framework includes a frozen benchmark of 6 clinical scenarios (C1–C6) testing dengue severity grading, hypertension therapy timing, cholera rehydration protocols (Plan B vs. Plan C), chikungunya joint pain, and ambiguous fever presentations:

```bash
# Run unit tests verifying card schema and coverage
pytest tests/

# Execute evaluation pipeline across both baseline and improved modes
python scripts/run_eval.py --run

# Scaffold grading table with automated regex hints
python scripts/run_eval.py --scaffold

# Generate Markdown evaluation summary table
python scripts/run_eval.py --table
```

---

## 📁 Repository Structure

```text
project/
├── app.py                     # Streamlit clinical UI and interactive dashboard
├── architecturar_README.md    # Detailed architectural design and component specifications
├── data/
│   ├── cards/                 # Canonical protocol cards (cards.jsonl)
│   ├── cases/                 # Benchmark clinical patient profiles (cases.json)
│   ├── extracted/             # Extracted guideline text, tables, and metadata
│   ├── index/                 # ChromaDB and BM25 persistent indices
│   └── protocols/             # Raw PDF clinical guidelines
├── eval/
│   ├── checklists/            # Ground-truth YAML checklists for benchmark cases (C1–C6)
│   ├── FROZEN.json            # SHA-256 integrity freeze of cases and checklists
│   ├── grading.csv            # Structured per-case evaluation scores and notes
│   ├── outputs/               # Raw model inference outputs (baseline & improved)
│   └── results_table.md       # Compiled evaluation report
├── scripts/
│   ├── build_index.py         # Script to generate hybrid search indices
│   ├── draft_cards.py         # Card drafting utility
│   ├── extract_pdfs.py        # PDF text/table parser
│   ├── populate_grading.py    # Grading utility
│   ├── run_eval.py            # Evaluation and benchmarking runner
│   └── validate_cards.py      # Verbatim passage and card validator
├── src/aimscribe/
│   ├── applicability.py       # Deterministic pre-inference safety & contraindication checker
│   ├── config.py              # Central project configuration and protocol metadata
│   ├── indexer.py             # Dual BM25 + Dense vector index builder
│   ├── llm.py                 # Structured JSON model interface (Groq / Ollama)
│   ├── pipeline.py            # End-to-end patient-to-recommendation pipeline
│   ├── prompts.py             # Clinical system and reasoning prompts
│   ├── retriever.py           # Hybrid retrieval and Reciprocal Rank Fusion engine
│   └── schema.py              # Pydantic data models for patients, cards, and recommendations
├── tests/
│   └── test_cards.py          # Pytest suite for card uniqueness and protocol coverage
├── .env.example               # Template environment configuration
└── requirements.txt           # Core Python package dependencies
```
