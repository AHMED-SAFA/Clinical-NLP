# Clinical Recommender System Architecture (Question 3)

## 1. System Overview & Architecture Diagram

This architecture represents the end-to-end design of the **AIMScribe Clinical Decision Support Engine** for General Practitioner (GP) clinics in Bangladesh, incorporating knowledge from the four national guidelines (Dengue 2025, Hypertension 2023, Cholera 2024, Chikungunya 2017).

The diagram distinguishes between components **Implemented in the Working Prototype** and **Future Component Extension Points**.

```mermaid
flowchart TB
    %% Styling
    classDef implemented fill:#e1f5fe,stroke:#0288d1,stroke-width:2px,color:#01579b;
    classDef future fill:#fff3e0,stroke:#f57c00,stroke-width:2px,stroke-dasharray: 5 5,color:#e65100;
    classDef data fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#4a148c;
    classDef llm fill:#e8f5e9,stroke:#388e3c,stroke-width:2px,color:#1b5e20;

    subgraph PROTOCOL_PREP ["1. Protocol Preparation & Knowledge Base (Implemented)"]
        P1["Clinical Guidelines (PDFs)<br/>• Dengue 5th Ed 2025<br/>• HTN 2nd Ed 2023<br/>• Cholera WHO 2024<br/>• Chikungunya 2017"]:::data
        P2["Text & Table Extractor<br/>(scripts/extract_pdfs.py)"]:::implemented
        P3["Canonical Protocol Cards<br/>(data/cards/cards.jsonl)<br/>• card_id, disease, category<br/>• requires_all / excludes_any<br/>• variants (tables/dosing)<br/>• verbatim source evidence"]:::data
        P1 --> P2 --> P3
    end

    subgraph INDEXING ["2. Dual Hybrid Indexing (Implemented)"]
        I1["Sparse Index (BM25)<br/>Exact clinical terms, acronyms,<br/>drug names, BP cutoffs"]:::implemented
        I2["Dense Index (Vector Embeddings)<br/>Semantic search via SentenceTransformers<br/>(all-MiniLM-L6-v2)"]:::implemented
        P3 --> I1
        P3 --> I2
    end

    subgraph INTAKE ["3. Patient Intake & Context Assembly"]
        UI_IN["Streamlit Clinical UI<br/>(Chief complaints, duration, age, sex,<br/>vitals/BP, history, meds, allergies)"]:::implemented
        NER_IN["[Future] Clinical ASR & NER Pipeline<br/>(Extracts symptoms, vitals & history<br/>from doctor-patient audio consultation)"]:::future
        
        PAT_SCHEMA["Patient Structured Context<br/>(aimscribe.schema.Patient)"]:::implemented
        UI_IN --> PAT_SCHEMA
        NER_IN -.->|"Extracted clinical entities"| PAT_SCHEMA
    end

    subgraph RETRIEVAL ["4. Hybrid Retrieval & Fusion (Implemented)"]
        RET["Hybrid Retriever (aimscribe.retriever)<br/>Combines BM25 + Dense Ranks<br/>via Reciprocal Rank Fusion (RRF)"]:::implemented
        PAT_SCHEMA -->|"Constructed Patient Query"| RET
        I1 --> RET
        I2 --> RET
        TOP_K["Top-K Candidate Cards <br/>Includes verbatim evidence & source page"]:::data
        RET --> TOP_K
    end

    subgraph CHECKER ["5. Tested Improvement: Deterministic Applicability Checker"]
        APP_CHK["Deterministic Applicability Engine<br/>(aimscribe.applicability.py)<br/>• Evaluates excludes_any (e.g. pregnancy, NSAID)<br/>• Checks requires_all (mandatory criteria)<br/>• Resolves variants (age bands, BP steps)<br/>"]:::implemented
        TOP_K --> APP_CHK
        PAT_SCHEMA --> APP_CHK
        ANNOTATED["Annotated Cards with Status Lines:<br/>• status=OK / BLOCKED / NOT_MET / MISSING_INFO<br/>"]:::data
        APP_CHK --> ANNOTATED
    end

    subgraph LLM_REASONING ["6. Constrained Clinical Inference"]
        PROMPT_ASM["Prompt Assembler<br/>Injects Patient + Annotated Cards + Citation Rules"]:::implemented
        LLM_CORE["Groq LLM Engine<br/>(openai/gpt-oss-120b, temp=0.0)"]:::llm
        OUTPUT_GUARD["JSON Schema Validation<br/>(Pydantic: Recommendation schema)"]:::implemented
        
        ANNOTATED --> PROMPT_ASM
        PAT_SCHEMA --> PROMPT_ASM
        PROMPT_ASM --> LLM_CORE --> OUTPUT_GUARD
    end

    subgraph PRESENTATION ["7. Recommendation Interface"]
        UI_OUT["Streamlit Interactive Clinical View<br/>• Probable Diagnosis & Differential<br/>• Stepwise Investigations with Timings<br/>• Medication Planning <br/>• Warning Signs, Advice<br/>• Clickable Source IDs & Evidence Passages<br/>• Missing Information Notifications"]:::implemented
        OUTPUT_GUARD --> UI_OUT
    end

    subgraph FUTURE_INTEGRATION ["8. Downstream Integration & Governance (Future Extension Points)"]
        DOC_REV["Doctor Review & Feedback Loop<br/>• Accept / Modify / Reject recommendations<br/>• Logs clinician corrections"]:::future
        PRES_ASM["Prescription Assembly Engine<br/>Generates formal bilingual prescription slip"]:::future
        EHR_EXP["EHR / Hospital System Sync<br/>Exports structured diagnosis & order sets"]:::future
        
        UI_OUT -.-> DOC_REV
        DOC_REV -.->|"Accepted treatment plan"| PRES_ASM
        DOC_REV -.->|"Clinical telemetry / fine-tuning dataset"| EHR_EXP
        DOC_REV -.->|"Feedback on card relevance"| P3
    end
```

---

## 2. Component Breakdown

### Implemented Components (Current Working Prototype)
1. **Protocol Extraction (`scripts/extract_pdfs.py`):** Parses national guidelines into structured Markdown and tables.
2. **Canonical Card Knowledge Base (`data/cards/cards.jsonl`):** 158 structured cards with deterministic fields (`requires_all`, `excludes_any`, `variants`, `missing_info`) and linked verbatim evidence passages with page citations.
3. **Hybrid Search Index (`src/aimscribe/retriever.py`):** Dual-indexer combining BM25 keyword matching (for medical terminology, exact dosages, and lab tests) and Dense semantic embeddings (via `all-MiniLM-L6-v2`) fused using Reciprocal Rank Fusion (RRF).
4. **Interactive Clinical UI (`app.py`):** Streamlit interface allowing freeform case entry, 1-click loading of benchmark cases, baseline/improved mode toggle, and structured clinical output cards.
5. **Deterministic Applicability Checker (`src/aimscribe/applicability.py`):** **The tested improvement.** Executes locally in `<1 ms` without LLM calls. Evaluates structured criteria against patient fields and attaches machine-evaluated status tags (`OK`, `BLOCKED`, `NOT_MET`, `MISSING_INFO`) directly into the prompt.
6. **Strict Schema-Constrained Generation (`src/aimscribe/llm.py` & `prompts.py`):** Leverages `gpt-oss-120b` at temperature `0.0` with Pydantic JSON enforcement, strictly prohibiting ungrounded drug recommendations or hallucinations outside retrieved cards.

### Future Extension Points (Architectural Roadmap)
1. **Speech-to-Text & Clinical NER Intake:** An automated transcription pipeline (e.g. Whisper Bengali/English + BioClinicalBERT) that parses doctor-patient dialogue directly into the structured `Patient` schema.
2. **Clinician Feedback & Active Learning:** Doctor acceptance, editing, or rejection buttons for each card, logging clinician interaction telemetry to identify protocol gaps or ambiguous cards.
3. **Prescription Assembly Engine:** Formats verified medication regimens into standardized clinic prescription templates ready for printing or patient SMS.
4. **EHR / Hospital Information System (HIS) Integration:** REST/FHIR APIs syncing recommendations directly with hospital electronic health records.

---

## 3. Defense of Architectural Choices vs. Simpler Alternatives

### Choice 1: Hybrid Retrieval (BM25 + Dense RRF) vs. Pure Vector Search

 Pure vector search struggles severely with precise clinical tokens (e.g. "NS1", "SGOT/SGPT", "156/98 mmHg", "Plan B", "Amlodipine"). BM25 guarantees that exact acronyms, blood pressure numbers, and drug names receive high priority. Combining them with Reciprocal Rank Fusion (RRF) prevents retrieval failure across varied clinical phrasings.

### Choice 2: Deterministic Pre-LLM Checker vs. Pure Prompt-Based Reasoning

As proven in Reasoning Challenge and comparative evaluation, LLMs frequently experience "exclusion blindness" when contraindications are buried inside prose paragraphs. Moving hard constraints (such as age cutoffs, blood pressure thresholds, and pregnancy contraindications) into programmatic Python logic guarantees 100% mathematical consistency.

---

## 4. How a New Patient Detail Dynamically Changes Recommendations

The engine is completely dynamic. Modifying a single patient parameter cascades through the pipeline to alter the recommendations:

### Concrete Example: Patient C1 to Patient C6 (Dengue Severity Escalation)

* **Initial State (C1):** 24-year-old female, Day 3 fever, retro-orbital pain, drinking fluids well, no vomiting.
  * *Retriever:* Fetches dengue outpatient management cards (`DEN-ADV-008`, `DEN-RX-001`).
  * *Applicability Checker:* Warning signs criteria evaluate to `NOT_MET`. Home care criteria evaluate to `OK`.
  * *Recommendation:* **Home management**, oral hydration (2,400 mL/day), Paracetamol max 3 g/day, warning sign counseling, daily CBC monitoring.
* **New Patient Details Added (C6):** Clinician records `"persistent vomiting, severe abdominal pain, drinking poorly"`.
  * *Retriever:* Re-ranks warning sign cards (`DEN-ADV-001`, `DEN-ADV-011`) to top rank based on complaint tokens.
  * *Applicability Checker:* Warning sign rule (`persistent vomiting >=3 episodes`) triggers to Card `DEN-ADV-001` status becomes `TRIGGERED`. Outpatient home care card is marked `BLOCKED`.
  * *Recommendation Shift:* Home management is completely suppressed; the engine issues an urgent **Referral / Inpatient Admission Alert** for close monitoring of plasma leakage and impending dengue shock (*Dengue Guideline, p. 28, Table 7, p. 47*).

### Concrete Example 2: Pregnancy Flag in Hypertension
* A patient with Stage 1 Hypertension has `HTN-RX-001` (stepped care algorithm) retrieved.
* When `pregnant: true` is set, the applicability checker immediately marks the ARB escalation steps (`variants 3 & 4` — Losartan) as `BLOCKED`.
* The prompt explicitly notifies the LLM: `status=BLOCKED: pregnant -> ARB contraindicated (p. 64)`. The engine safely diverts to calcium channel blockers or methyldopa.
