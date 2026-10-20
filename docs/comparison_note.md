# Baseline vs Applicability Checker Comparison Note

**Weakness in Basic Recommender:**
In the baseline mode, clinical preconditions, exclusions, and multi-step table branches reach the language model solely as natural language prose within the card text. The model frequently risks:
1. Overlooking negative contraindications buried deep in text (e.g. prescribing contraindicated ARB/ACEi or NSAIDs).
2. Misaligning multi-step table branches (e.g., escalating therapy incorrectly or picking adult/severe doses for moderate presentations).
3. Guessing unstated parameters instead of explicitly reporting missing information.

**Tested Improvement:**
A deterministic, rule-based applicability checker (`src/aimscribe/applicability.py`) executed programmatically before prompt assembly. It parses each card's structured fields (`requires_all`, `excludes_any`, and `variants`) against patient vitals, demographics, and complaints. It computes a status line (`OK`, `BLOCKED`, `NOT_MET`, or `MISSING_INFO`) and selects the appropriate table variant. This line is appended directly to each card in the user prompt, with strict instructions in `SYSTEM_IMPROVED` to obey the machine-evaluated status.
* **Extra computational cost:** 0 extra LLM calls; local checker execution time $\approx 0.5 - 1.0\text{ ms}$; prompt overhead $\approx +1,500 - 2,500\text{ chars}$.

**Hypothesis & Failure Criterion:**
* *Hypothesis:* The improved mode will reduce restriction violations and improve missing information identification by explicitly flagging exclusions and prerequisites before generation.
* *Failure Criterion:* The improvement is judged ineffective if it fails to improve on checks 3 (`restrictions_preserved`) or 4 (`missing_info_handled`), causes regressions on previously passing cases, or produces differences indistinguishable from API run-to-run variation.

---

## Results Table (6 Self-Authored Cases, 12 Saved Runs)

> **Important Disclosure:** These results are derived from six self-authored fictional test cases designed to test guideline boundaries, not independent clinical trial validation.

| Case | Mode | Key behaviour | Cited/supported | Restrictions | Missing info | Time (s) | Failure note |
|---|---|---|---|---|---|---|---|
| C1 | baseline | pass | pass | pass | pass | 22.85 | |
| C1 | improved | pass | pass | pass | pass | 17.64 | |
| C2 | baseline | pass | pass | pass | pass | 17.06 | |
| C2 | improved | pass | pass | pass | pass | 17.27 | |
| C3 | baseline | fail | pass | fail | pass | 16.94 | Overtreated: IV Ringers recommended for non-severe dehydration |
| C3 | improved | fail | pass | fail | pass | 33.01 | Overtreated: IV Ringers recommended for non-severe dehydration |
| C4 | baseline | pass | pass | pass | pass | 17.82 | |
| C4 | improved | pass | pass | pass | pass | 33.11 | |
| C5 | baseline | pass | pass | pass | pass | 18.35 | |
| C5 | improved | pass | pass | pass | pass | 33.48 | |
| C6 | baseline | pass | pass | pass | pass | 17.38 | |
| C6 | improved | pass | pass | pass | pass | 18.28 | |

### Aggregate Summary

| Mode | key_behaviour | supported_by_citation | restrictions_preserved | missing_info_handled | mean time (s) |
|---|---|---|---|---|---|
| **baseline** | 5/6 (83.3%) | 6/6 (100%) | 5/6 (83.3%) | 6/6 (100%) | 18.4 s |
| **improved** | 5/6 (83.3%) | 6/6 (100%) | 5/6 (83.3%) | 6/6 (100%) | 25.5 s |

---

## Discussion of Failure & Limitations

### 1. The Shared Failure in Case C3 (Cholera Dehydration Overtreatment)
* **What Happened:**
  In Case C3 (30M with acute watery diarrhoea, thirst, restless, sunken eyes), the guideline (*WHO Cholera clinical tools 2024, pp. 6, 9*) classifies the patient as having **Some Dehydration**, mandating **Plan B oral rehydration solution (ORS)**: 75 mL/kg over 4 hours (2,200–4,000 mL for 60 kg). Both baseline and improved modes incorrectly recommended **IV Ringer’s lactate 100 mL/kg (Plan C)**, which is strictly indicated only for severe dehydration or shock.
* **Root Cause:**
  1. *Retrieval bias:* The hybrid search strongly ranked `CHO-RX-014` (IV Ringer's lactate) near the top due to high lexical overlap with "rice water diarrhoea, dehydration".
  2. *Checker representation gap:* The card `CHO-RX-014` lacked an explicit negative rule in `excludes_any` for `some_dehydration`. Because the card's structured prerequisite only stated `"dehydration"`, the applicability checker evaluated the condition as `OK`, failing to block the card. Consequently, the LLM defaulted to the more aggressive intervention.
* **Plausible Alternative Explanation:**
  LLMs inherently display an "aggressive intervention bias" when presented with alarming symptom phrases such as "rice water diarrhoea" and "sunken eyes", prioritizing immediate intensive intervention over oral rehydration unless the negative boundary is explicitly enforced.
* **Next Test:**
  Add a strict mutually exclusive enum to cholera rehydration cards (`Plan_A`, `Plan_B`, `Plan_C`) with explicit `excludes_any: [{"field": "dehydration_severity", "op": "!=", "value": "severe"}]` on all IV fluid cards.

### 2. False Positive in Keyword-Based Automated Heuristic (Case C5)
* In Case C5, automated regex matching flagged an avoid-violation on `ibuprofen|diclofenac|naproxen|aspirin` because the output contained the token `"aspirin"`.
* **Clinical Verification:** Manual inspection showed the model generated: *"Avoid aspirin and NSAIDs during the first 10 days of illness until dengue is excluded"* (`CHI-ADV-013`). The model strictly obeyed the guideline restriction. This highlights the vital necessity of manual clinical verification over naive keyword filtering.

### 3. Latency & Resource Trade-offs
* While the Python applicability checker itself adds $< 1\text{ ms}$, the improved mode had a higher overall wall-clock latency (mean 25.5 s vs 18.4 s). This increase was driven entirely by cloud LLM inference time over longer prompt token lengths (+1,500–2,500 characters of applicability metadata).

---

## Untested Areas
1. Unseen syntactic variations in local Bengali-English clinical transcriptions (e.g. colloquial descriptions of postural dizziness, irregular pulse).
2. Complex comorbidities involving multi-drug interactions (e.g. concurrent ACEi + spironolactone + bilateral renal artery stenosis).
3. Paediatric weight-band fluid tables in dengue shock requiring hourly dynamic titration.

## Disclosures
* Evaluation checklists (`eval/checklists/case_1.yaml`–`case_6.yaml`) and cryptographic hashes (`eval/FROZEN.json`) were frozen prior to running the comparative evaluation.
* Runs were conducted using `groq:openai/gpt-oss-120b` with temperature fixed at 0.0. No post-hoc prompt alterations were made to accommodate model failures.
