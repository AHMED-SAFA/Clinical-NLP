# AIMScribe prototype (clinical NLP assessment)

Protocol cards -> hybrid RAG (ChromaDB + BM25, RRF) -> LLM -> cited recommendations (Streamlit).

## Setup

```bash
python -m venv .venv && source .venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env   
# set GROQ_API_KEY (aistudio.google.com/apikey) or LLM_PROVIDER=ollama
```

## Build

```bash
# put 4 PDFs in data/protocols/ (names in src/aimscribe/config.py)
python scripts/extract_pdfs.py        # page text, tables, PNGs -> data/extracted/
python scripts/draft_cards.py         # optional LLM drafts -> data/cards/drafts.jsonl (review manually)
python scripts/validate_cards.py      # schema, evidence-in-page check, coverage
python scripts/build_index.py         # rebuild RAG index -> data/index/
```

## Launch

```bash
streamlit run app.py
```

## Model

Gemini (`gemini-2.5-flash`, temperature 0, JSON-schema output) or Ollama `qwen2.5:7b`. Embeddings: `BAAI/bge-small-en-v1.5`.

## AI assistance disclosure

See docs/ai_disclosure.md.
