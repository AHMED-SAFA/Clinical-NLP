"""Freeze -> run both modes on 6 cases -> grading scaffold -> results table."""

import sys, json, hashlib, argparse, re, csv, time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import yaml
from aimscribe import pipeline
from aimscribe.config import ROOT, CASES_PATH, CARDS_PATH, OUTPUT_DIR
from aimscribe.schema import Patient

CK = ROOT / "eval" / "checklists"
FREEZE = ROOT / "eval" / "FROZEN.json"
GRADING = ROOT / "eval" / "grading.csv"
TABLE_MD = ROOT / "eval" / "results_table.md"
MODES = ["baseline", "improved"]
CHECKS = [
    "key_behaviour",
    "supported_by_citation",
    "restrictions_preserved",
    "missing_info_handled",
]
COLS = [
    "case_id",
    "mode",
    *CHECKS,
    "reason",
    "source_page",
    "auto_key_hint",
    "auto_avoid_hint",
    "invalid_citations",
    "blocked_citations",
    "elapsed_s",
    "prompt_chars",
    "failure_note",
]


def _files():
    return [CASES_PATH, CARDS_PATH, *sorted(CK.glob("case_*.yaml"))]


def _hashes():
    return {
        f.relative_to(ROOT).as_posix(): hashlib.sha256(f.read_bytes()).hexdigest()
        for f in _files()
    }


def freeze():
    FREEZE.write_text(
        json.dumps(
            dict(
                frozen_at=datetime.now().isoformat(timespec="seconds"), files=_hashes()
            ),
            indent=2,
        )
    )
    print("Frozen:", FREEZE)


def verify(force):
    if not FREEZE.exists():
        sys.exit(
            "Run --freeze first (after cards, cases and checklists are final; rebuild the index before freezing)."
        )
    old, cur = json.loads(FREEZE.read_text())["files"], _hashes()
    diff = [k for k in set(old) | set(cur) if old.get(k) != cur.get(k)]
    if diff and not force:
        sys.exit(
            f"Frozen files changed: {diff}. Use --force only if you will disclose it."
        )


def load_cases():
    return json.loads(CASES_PATH.read_text("utf-8"))


def run(only, repeats):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for case in load_cases():
        if only and case["id"] not in only:
            continue
        ret = {}
        for mode in MODES:
            for rep in range(repeats):
                tag = f"{case['id']}_{mode}" + (f"_rep{rep + 1}" if rep else "")
                try:
                    res = pipeline.run(Patient(**case["patient"]), mode)
                except Exception as e:
                    res = dict(error=str(e), mode=mode)
                res["case_id"] = case["id"]
                pipeline.save(res, OUTPUT_DIR / f"{tag}.json")
                print(tag, res.get("elapsed_s"), res.get("error", ""))
                if rep == 0 and "retrieved" in res:
                    ret[mode] = [h["card_id"] for h in res["retrieved"]]
                time.sleep(15)  # free-tier rate limit
        if len(ret) == 2 and ret["baseline"] != ret["improved"]:
            print(f"WARNING {case['id']}: retrieval differs between modes")


def hints(case_id, res):
    f = CK / f"case_{case_id[1:]}.yaml"
    if not f.exists() or "recommendation" not in res:
        return "", ""
    h = (yaml.safe_load(f.read_text("utf-8")) or {}).get("auto_hints") or {}
    rec = res["recommendation"]
    text = json.dumps(rec).lower()
    acts = json.dumps(
        {k: rec[k] for k in ("investigations", "medications", "advice")}
    ).lower()
    miss = [m for m in h.get("must_mention", []) if not re.search(m, text, re.I)]
    viol = [a for a in h.get("must_not_recommend", []) if re.search(a, acts, re.I)]
    return ("auto-pass" if not miss else f"auto-fail: missing {miss}"), (
        f"CHECK {viol}" if viol else "ok"
    )


def scaffold():
    if GRADING.exists():
        sys.exit(
            f"{GRADING} exists; delete it to regenerate (do not lose manual grades)."
        )
    rows = []
    for case in load_cases():
        for mode in MODES:
            f = OUTPUT_DIR / f"{case['id']}_{mode}.json"
            res = json.loads(f.read_text("utf-8")) if f.exists() else {}
            k, a = hints(case["id"], res)
            rows.append(
                dict(
                    case_id=case["id"],
                    mode=mode,
                    auto_key_hint=k,
                    auto_avoid_hint=a,
                    invalid_citations=";".join(res.get("invalid_citations", [])),
                    blocked_citations=";".join(res.get("blocked_citations", [])),
                    elapsed_s=res.get("elapsed_s", ""),
                    prompt_chars=res.get("prompt_chars", ""),
                    failure_note=res.get("error", ""),
                )
            )
    with GRADING.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in COLS})
    print(
        f"Wrote {GRADING}: fill the 4 check columns with pass/fail/na plus reason and source_page."
    )


def table():
    rows = list(csv.DictReader(GRADING.open(encoding="utf-8-sig")))
    for r in rows:
        for c in CHECKS:
            if r[c].strip().lower() not in ("pass", "fail", "na"):
                sys.exit(f"{r['case_id']} {r['mode']}: '{c}' must be pass/fail/na")
    L = [
        "| Case | Mode | Key behaviour | Cited/supported | Restrictions | Missing info | Time (s) | Failure note |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        L.append(
            f"| {r['case_id']} | {r['mode']} | "
            + " | ".join(r[c].lower() for c in CHECKS)
            + f" | {r['elapsed_s']} | {r['failure_note']} |"
        )
    L += [
        "",
        "| Mode | " + " | ".join(CHECKS) + " | mean time (s) |",
        "|---|---|---|---|---|---|",
    ]
    for m in MODES:
        sub = [r for r in rows if r["mode"] == m]
        cells = []
        for c in CHECKS:
            p = sum(r[c].lower() == "pass" for r in sub)
            f = sum(r[c].lower() == "fail" for r in sub)
            cells.append(f"{p}/{p + f} (n/a {len(sub) - p - f})")
        t = [float(r["elapsed_s"]) for r in sub if r["elapsed_s"]]
        L.append(
            f"| {m} | " + " | ".join(cells) + f" | {sum(t) / len(t):.1f} |"
            if t
            else f"| {m} | " + " | ".join(cells) + " | - |"
        )
    TABLE_MD.write_text("\n".join(L), "utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--scaffold", action="store_true")
    ap.add_argument("--table", action="store_true")
    ap.add_argument("--only", default="", help="e.g. C1,C3")
    ap.add_argument(
        "--repeats",
        type=int,
        default=1,
        help="2 = extra reps for variability (not in the 12)",
    )
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    if a.freeze:
        freeze()
    if a.run:
        verify(a.force)
        run([x for x in a.only.split(",") if x], a.repeats)
    if a.scaffold:
        scaffold()
    if a.table:
        table()
