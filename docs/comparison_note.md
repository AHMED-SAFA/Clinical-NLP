# Baseline vs applicability checker

**Weakness:** conditions on cards reach the model only as prose; it may apply a card whose exclusion matches, choose the wrong table row, or not notice a missing detail.
**Change:** deterministic checker on structured conditions -> status + selected variant added to the prompt (same model, cards, retrieval, temperature 0). Extra cost: no LLM call, checker_ms ≈ **, +** prompt chars.
**Hypothesis / failure criterion:** helps if improved passes more restrictions and missing-info checks. Counts as no help if not better on checks 3+4, if it causes a new failure, or if the gap is within baseline variation (** vs ** on repeats).
**Results (6 self-authored cases, not clinical validation):** [paste table]
**Failure or limitation:** [case, what happened, likely cause, plausible alternative (e.g. Groq run-to-run variation, phrase-matching limits of the checker, sparse structured conditions on the cards), next test]
**Untested:** [e.g. unseen phrasing, other protocols' tables]
**Disclosure:** checklists written before running; any outputs seen earlier: \_\_.
