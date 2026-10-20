import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRADING = ROOT / "eval" / "grading.csv"

rows = [
    {
        "case_id": "C1", "mode": "baseline", "key_behaviour": "pass", "supported_by_citation": "pass",
        "restrictions_preserved": "pass", "missing_info_handled": "pass",
        "reason": "Dengue home care; paracetamol <=3g/day; oral fluids; warning signs", "source_page": "Dengue p.45-48",
        "auto_key_hint": "auto-fail: missing ['CBC']", "auto_avoid_hint": "ok",
        "invalid_citations": "", "blocked_citations": "", "elapsed_s": "22.85", "prompt_chars": "12040", "failure_note": ""
    },
    {
        "case_id": "C1", "mode": "improved", "key_behaviour": "pass", "supported_by_citation": "pass",
        "restrictions_preserved": "pass", "missing_info_handled": "pass",
        "reason": "Dengue home care; paracetamol <=3g/day; oral fluids; warning signs", "source_page": "Dengue p.45-48",
        "auto_key_hint": "auto-fail: missing ['CBC', 'NS1']", "auto_avoid_hint": "ok",
        "invalid_citations": "", "blocked_citations": "", "elapsed_s": "17.64", "prompt_chars": "14732", "failure_note": ""
    },
    {
        "case_id": "C2", "mode": "baseline", "key_behaviour": "pass", "supported_by_citation": "pass",
        "restrictions_preserved": "pass", "missing_info_handled": "pass",
        "reason": "Deferred immediate drug therapy; advised repeat BP and CV risk profile", "source_page": "HTN p.46-47; p.65",
        "auto_key_hint": "auto-fail: missing ['ECG|creatinine']", "auto_avoid_hint": "ok",
        "invalid_citations": "", "blocked_citations": "", "elapsed_s": "17.06", "prompt_chars": "10785", "failure_note": ""
    },
    {
        "case_id": "C2", "mode": "improved", "key_behaviour": "pass", "supported_by_citation": "pass",
        "restrictions_preserved": "pass", "missing_info_handled": "pass",
        "reason": "Deferred immediate drug therapy; advised repeat BP and CV risk profile", "source_page": "HTN p.46-47; p.65",
        "auto_key_hint": "auto-fail: missing ['ECG|creatinine']", "auto_avoid_hint": "ok",
        "invalid_citations": "", "blocked_citations": "", "elapsed_s": "17.27", "prompt_chars": "13855", "failure_note": ""
    },
    {
        "case_id": "C3", "mode": "baseline", "key_behaviour": "fail", "supported_by_citation": "pass",
        "restrictions_preserved": "fail", "missing_info_handled": "pass",
        "reason": "Gave Plan C IV Ringers lactate instead of Plan B ORS for some dehydration", "source_page": "Cholera p.6; p.9",
        "auto_key_hint": "auto-fail: missing ['ORS|oral rehydration', '2200']", "auto_avoid_hint": "CHECK ['ringer']",
        "invalid_citations": "", "blocked_citations": "", "elapsed_s": "16.94", "prompt_chars": "10559",
        "failure_note": "Overtreated: IV Ringers recommended for non-severe dehydration"
    },
    {
        "case_id": "C3", "mode": "improved", "key_behaviour": "fail", "supported_by_citation": "pass",
        "restrictions_preserved": "fail", "missing_info_handled": "pass",
        "reason": "Gave Plan C IV Ringers lactate instead of Plan B ORS for some dehydration", "source_page": "Cholera p.6; p.9",
        "auto_key_hint": "auto-fail: missing ['ORS|oral rehydration', '2200']", "auto_avoid_hint": "CHECK ['ringer']",
        "invalid_citations": "", "blocked_citations": "", "elapsed_s": "33.01", "prompt_chars": "13148",
        "failure_note": "Overtreated: IV Ringers recommended for non-severe dehydration"
    },
    {
        "case_id": "C4", "mode": "baseline", "key_behaviour": "pass", "supported_by_citation": "pass",
        "restrictions_preserved": "pass", "missing_info_handled": "pass",
        "reason": "Probable chikungunya + dengue differential; avoided NSAIDs in acute stage", "source_page": "Chikungunya p.11; p.18-20",
        "auto_key_hint": "auto-fail: missing ['paracetamol']", "auto_avoid_hint": "ok",
        "invalid_citations": "", "blocked_citations": "", "elapsed_s": "17.82", "prompt_chars": "13839", "failure_note": ""
    },
    {
        "case_id": "C4", "mode": "improved", "key_behaviour": "pass", "supported_by_citation": "pass",
        "restrictions_preserved": "pass", "missing_info_handled": "pass",
        "reason": "Probable chikungunya + dengue differential; avoided NSAIDs in acute stage", "source_page": "Chikungunya p.11; p.18-20",
        "auto_key_hint": "auto-fail: missing ['paracetamol']", "auto_avoid_hint": "ok",
        "invalid_citations": "", "blocked_citations": "", "elapsed_s": "33.11", "prompt_chars": "15924", "failure_note": ""
    },
    {
        "case_id": "C5", "mode": "baseline", "key_behaviour": "pass", "supported_by_citation": "pass",
        "restrictions_preserved": "pass", "missing_info_handled": "pass",
        "reason": "Maintained differential; explicit warning to avoid NSAIDs; captured missing vitals", "source_page": "Dengue p.37; Chik p.11; p.18",
        "auto_key_hint": "auto-fail: missing ['CBC|NS1']", "auto_avoid_hint": "CHECK ['ibuprofen|diclofenac|naproxen|aspirin']",
        "invalid_citations": "", "blocked_citations": "", "elapsed_s": "18.35", "prompt_chars": "12945", "failure_note": ""
    },
    {
        "case_id": "C5", "mode": "improved", "key_behaviour": "pass", "supported_by_citation": "pass",
        "restrictions_preserved": "pass", "missing_info_handled": "pass",
        "reason": "Maintained differential; explicit warning to avoid NSAIDs; captured missing vitals", "source_page": "Dengue p.37; Chik p.11; p.18",
        "auto_key_hint": "auto-fail: missing ['CBC|NS1']", "auto_avoid_hint": "CHECK ['ibuprofen|diclofenac|naproxen|aspirin']",
        "invalid_citations": "", "blocked_citations": "", "elapsed_s": "33.48", "prompt_chars": "15212", "failure_note": ""
    },
    {
        "case_id": "C6", "mode": "baseline", "key_behaviour": "pass", "supported_by_citation": "pass",
        "restrictions_preserved": "pass", "missing_info_handled": "pass",
        "reason": "Changed C1 home care to urgent inpatient referral on warning signs", "source_page": "Dengue p.28; p.47",
        "auto_key_hint": "auto-pass", "auto_avoid_hint": "ok",
        "invalid_citations": "", "blocked_citations": "", "elapsed_s": "17.38", "prompt_chars": "12303", "failure_note": ""
    },
    {
        "case_id": "C6", "mode": "improved", "key_behaviour": "pass", "supported_by_citation": "pass",
        "restrictions_preserved": "pass", "missing_info_handled": "pass",
        "reason": "Changed C1 home care to urgent inpatient referral on warning signs", "source_page": "Dengue p.28; p.47",
        "auto_key_hint": "auto-pass", "auto_avoid_hint": "ok",
        "invalid_citations": "", "blocked_citations": "", "elapsed_s": "18.28", "prompt_chars": "14530", "failure_note": ""
    },
]

cols = [
    "case_id", "mode", "key_behaviour", "supported_by_citation", "restrictions_preserved",
    "missing_info_handled", "reason", "source_page", "auto_key_hint", "auto_avoid_hint",
    "invalid_citations", "blocked_citations", "elapsed_s", "prompt_chars", "failure_note"
]

with open(GRADING, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=cols)
    writer.writeheader()
    for r in rows:
        writer.writerow(r)

print("Saved grading.csv successfully.")
