import sys, re, json
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import pandas as pd
from aimscribe.config import EXTRACT_DIR
from aimscribe.indexer import load_cards


def norm(s):
    return re.sub(r"\s+", " ", re.sub(r"-\s*\n", "", s)).lower().strip()


cards, errs, rows = load_cards(), 0, []
ids = [c.card_id for c in cards]
assert len(ids) == len(set(ids)), "duplicate card IDs"
ex = {
    k: json.loads((EXTRACT_DIR / f"{k}.json").read_text("utf-8"))
    for k in {c.disease for c in cards}
}
for c in cards:
    for e in c.evidence:
        pg = ex[c.disease]["pages"].get(str(e.page))
        if not pg:
            print(f"{c.card_id}: page {e.page} not extracted")
            errs += 1
            continue
        hay = norm(pg["text"] + " " + " ".join(pg["tables_md"]))
        p = norm(e.passage)
        if p in hay:
            continue
        m = SequenceMatcher(None, p, hay, autojunk=False).find_longest_match(
            0, len(p), 0, len(hay)
        )
        r = m.size / max(len(p), 1)
        if r >= 0.8:
            print(f"{c.card_id} p.{e.page}: fuzzy match {r:.0%} - check manually")
        else:
            toks = re.findall(r"\w+", p)
            pt = set(re.findall(r"\w+", hay))
            cov = sum(t in pt for t in toks) / max(len(toks), 1)
            bad_nums = [t for t in toks if t.isdigit() and t not in pt]
            if cov >= 0.9 and not bad_nums:
                print(f"{c.card_id} p.{e.page}: reordered/table text (tokens {cov:.0%}) - check vs PNG")
            else:
                print(f"{c.card_id} p.{e.page}: NOT FOUND (match {r:.0%}, tokens {cov:.0%}, numbers missing {bad_nums})")
                errs += 1
    rows.append((c.disease, c.category, c.reviewed))
df = pd.DataFrame(rows, columns=["disease", "category", "reviewed"])
print("\nCoverage:\n", pd.crosstab(df.disease, df.category))
print(
    f"\n{len(cards)} cards, {int(df.reviewed.sum())} reviewed, {errs} evidence errors"
)
sys.exit(1 if errs else 0)
