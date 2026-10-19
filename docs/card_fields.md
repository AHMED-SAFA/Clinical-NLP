# Card fields
card_id (XXX-CAT-nnn) | disease | category (probable_diagnosis, investigation, medication, advice) | title |
symptoms_or_prerequisites (readable) | requires_all / requires_any / excludes_any (machine-checkable conditions) |
variants (table/conditional branches) | recommended_action | medication (name, dose, route, frequency, duration,
instructions, restrictions; null = not stated) | exclusions | missing_info | source (title, version, pdf_pages) |
evidence (verbatim passage + page; several allowed) | reviewed (human-checked).

## Reasoning example: [card_id, e.g. a hypertension or dengue fluid/dose card with a condition or table]
**Representation A (simple):** one flat card; the condition is only in the `recommended_action` prose.
**Representation B (chosen):** structured `requires_all` / `excludes_any` plus `variants` per table row.
**Why B:** [conditions stay explicit and checkable; each table row keeps its own page evidence; missing fields are visible].
**Where A fails:** [a real patient, e.g. one with the exception/comorbidity/weight band that the prose buries,
so the model applies the default branch]. Implemented: B only.