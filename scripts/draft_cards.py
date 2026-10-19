"""Draft cards from extracted pages. Output needs HUMAN REVIEW before use."""

import sys, json, time, argparse
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aimscribe import llm
from aimscribe.config import PROTOCOLS, EXTRACT_DIR, DRAFTS_PATH, CAT_CODE
from aimscribe.schema import Card

SYS = """You convert clinical protocol text into structured recommendation cards. Use ONLY the supplied pages.
Return JSON: {"cards":[{
 "category": "probable_diagnosis|investigation|medication|advice",
 "title": str,
 "symptoms_or_prerequisites": [str],
 "requires_all": [Condition], "requires_any": [Condition], "excludes_any": [Condition],
 "variants": [{"when":[Condition],"action":str,"medication":Medication|null}],
 "recommended_action": str,
 "medication": Medication|null,
 "exclusions": [str], "missing_info": [str],
 "evidence": [{"page": int, "passage": str}]}]}
Condition = {"field": one of age_years|sex|pregnant|weight_kg|duration_days|symptom|history|medicine|allergy|finding,
 "op": one of >=,<=,>,<,==,!=,has,not_has, "value": str|number|bool, "note": str|null}
 (use has/not_has with a short lowercase string for symptom/history/medicine/finding)
Medication = {"name","dose","route","frequency","duration","instructions","restrictions"}; use null for anything NOT stated.
Rules:
- evidence.passage must be copied VERBATIM from the page (1-3 sentences or a table row); page = the PDF page number in the marker.
- One card = one recommendation. Link several evidence passages if needed.
- Put conditions, exceptions, thresholds and table dependencies (age/weight/severity/comorbidity) into requires_*/excludes_any/variants, not only in prose.
- Never invent doses, thresholds or pages. Skip content that is not a recommendation.
- Cover: probable diagnosis (symptoms/criteria), investigations (purpose + timing), medication, advice (self-care, follow-up, warning signs, referral).
- age_years is always in YEARS: convert months (6 months = 0.5, 12 months = 1, 24 months = 2). weight_kg is in kg. For a range use two conditions (>= and <).
- Copy evidence passages exactly as printed. Never change numbers, units or wording, and never append words.
- Do not add prerequisites the page does not state.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=list(PROTOCOLS))
    ap.add_argument("--group", type=int, default=3, help="pages per LLM call")
    a = ap.parse_args()
    counters, cards, bad = defaultdict(int), [], 0
    for key, meta in PROTOCOLS.items():
        if a.only and key != a.only:
            continue
        ex = json.loads((EXTRACT_DIR / f"{key}.json").read_text("utf-8"))
        nums = sorted(map(int, ex["pages"]))
        for i in range(0, len(nums), a.group):
            chunk = nums[i : i + a.group]
            txt = "\n\n".join(
                f"=== PDF PAGE {p} ===\n{ex['pages'][str(p)]['text']}\n"
                + "\n".join(ex["pages"][str(p)]["tables_md"])
                for p in chunk
            )
            print(f"{key} pages {chunk} ...", flush=True)
            try:
                raw = llm.generate_json(
                    SYS, f"Protocol: {meta['title']} ({meta['version']})\n\n{txt}"
                )
            except Exception as e:
                print("  LLM error:", e)
                continue
            for r in raw.get("cards", []):
                cat = r.get("category")
                if cat not in CAT_CODE:
                    bad += 1
                    continue
                counters[(key, cat)] += 1
                pages = sorted({e["page"] for e in r.get("evidence", [])})
                r.update(
                    card_id=f"{meta['prefix']}-{CAT_CODE[cat]}-{counters[(key, cat)]:03d}",
                    disease=key,
                    reviewed=False,
                    source=dict(
                        title=meta["title"], version=meta["version"], pdf_pages=pages
                    ),
                )
                try:
                    cards.append(Card.model_validate(r))
                except Exception as e:
                    bad += 1
                    print("  invalid draft skipped:", str(e)[:150])
            time.sleep(20)  # stay under free-tier rate limit
    DRAFTS_PATH.write_text(
        "\n".join(c.model_dump_json() for c in cards) + "\n", "utf-8"
    )
    print(f"{len(cards)} draft cards -> {DRAFTS_PATH} ({bad} skipped)")


if __name__ == "__main__":
    main()
