"""Deterministic applicability checker (the tested improvement). No LLM call."""

import re
from dataclasses import dataclass, field, asdict
from .schema import Card, Condition, Patient

T, F, N, U = "true", "false", "notfound", "unknown"

LABEL = {
    "symptom": "symptoms",
    "finding": "findings/results",
    "history": "medical history",
    "medicine": "current medicines",
    "allergy": "allergies",
}
TEXT = {
    "symptom": ("complaints", "findings"),
    "finding": ("findings", "complaints"),
    "history": ("history",),
    "medicine": ("medicines",),
    "allergy": ("allergies",),
}
ALIAS = {
    "sbp": "sbp",
    "systolic_bp": "sbp",
    "systolic": "sbp",
    "systolic_blood_pressure": "sbp",
    "dbp": "dbp",
    "diastolic_bp": "dbp",
    "diastolic": "dbp",
    "diastolic_blood_pressure": "dbp",
    "platelet_count": "platelets",
    "platelets": "platelets",
}
STOP = {
    "the",
    "a",
    "an",
    "of",
    "or",
    "and",
    "with",
    "in",
    "on",
    "to",
    "for",
    "is",
    "are",
    "has",
    "have",
    "history",
    "sign",
    "signs",
    "patient",
    "any",
    "no",
}
NUM_OPS = (">=", "<=", ">", "<", "==", "!=")


def _stem(w):
    return re.sub(r"(ing|ed|es|s)$", "", w) if len(w) > 4 else w


def _toks(s):
    return {_stem(t) for t in re.findall(r"[a-z0-9]+", s.lower()) if t not in STOP}


def _derived(p: Patient) -> dict:
    d = {
        "age_years": p.age_years,
        "weight_kg": p.weight_kg,
        "duration_days": p.duration_days,
    }
    blob = " ".join([p.findings, p.complaints, p.history])
    m = re.search(r"\b(\d{2,3})\s*/\s*(\d{2,3})\b", blob)
    if m and 60 <= int(m.group(1)) <= 300 and 30 <= int(m.group(2)) <= 200:
        d["sbp"], d["dbp"] = float(m.group(1)), float(m.group(2))
    m = re.search(r"platelet[s]?[^0-9]{0,20}(\d[\d,]*)", blob, re.I)
    if m:
        d["platelets"] = float(m.group(1).replace(",", ""))
    return d


def eval_cond(c: Condition, p: Patient):
    """Returns (status, label). status: T / F / N (text not found) / U (patient detail missing)."""
    f = c.field
    if f == "sex":
        if not p.sex:
            return U, "sex"
        eq = p.sex.lower() == str(c.value).lower()
        return (T if (eq if c.op in ("==", "has") else not eq) else F), "sex"
    if f == "pregnant":
        val = p.pregnant
        if val is None and (p.sex or "").lower() == "male":
            val = False
        if val is None:
            return U, "pregnancy status"
        want = (
            c.value
            if isinstance(c.value, bool)
            else str(c.value).lower() in ("true", "yes", "1")
        )
        return (
            T if ((val == want) if c.op in ("==", "has") else (val != want)) else F
        ), "pregnancy status"
    if c.op in NUM_OPS:
        key = ALIAS.get(f, f)
        v = _derived(p).get(key)
        if v is None:
            return U, key
        try:
            x = float(c.value)
        except (TypeError, ValueError):
            return U, key
        ok = {
            ">=": v >= x,
            "<=": v <= x,
            ">": v > x,
            "<": v < x,
            "==": v == x,
            "!=": v != x,
        }[c.op]
        return (T if ok else F), key
    tf = f if f in TEXT else "finding"
    texts = [getattr(p, a) for a in TEXT[tf]]
    if tf in ("history", "medicine", "allergy") and not any(t.strip() for t in texts):
        return U, LABEL[tf]
    need, hay = _toks(str(c.value)), _toks(" ".join(texts))
    hit = bool(need) and len(need & hay) / len(need) >= 0.6
    if c.op == "not_has":
        return (F if hit else T), LABEL[tf]
    return (T if hit else N), LABEL[tf]


@dataclass
class Check:
    card_id: str
    status: str
    reasons: list = field(default_factory=list)
    missing: list = field(default_factory=list)
    unconfirmed: list = field(default_factory=list)
    variants_selected: list = field(default_factory=list)

    def to_dict(self):
        return asdict(self)

    def prompt_line(self):
        parts = [f"status={self.status}"]
        if self.reasons:
            parts.append("reasons: " + "; ".join(self.reasons))
        if self.missing:
            parts.append("missing patient details: " + "; ".join(self.missing))
        if self.unconfirmed:
            parts.append(
                "criteria not found in patient record (unconfirmed): "
                + "; ".join(self.unconfirmed)
            )
        if self.variants_selected:
            parts.append("selected variant(s): " + " | ".join(self.variants_selected))
        return f"APPLICABILITY CHECK [{self.card_id}]: " + " || ".join(parts)


def check(card: Card, p: Patient) -> Check:
    reasons, missing, unconf, selected = [], [], [], []
    blocked = not_met = False
    for c in card.requires_all:
        s, lab = eval_cond(c, p)
        if s == F:
            not_met = True
            reasons.append(f"requirement not met: {c}")
        elif s == U:
            missing.append(f"{lab} (needed for: {c})")
        elif s == N:
            unconf.append(str(c))
    if card.requires_any:
        res = [eval_cond(c, p) for c in card.requires_any]
        if not any(s == T for s, _ in res):
            if any(s == U for s, _ in res):
                missing += [
                    f"{lab} (needed for: {c})"
                    for c, (s, lab) in zip(card.requires_any, res)
                    if s == U
                ]
            elif all(s == F for s, _ in res):
                not_met = True
                reasons.append(
                    "none of the alternative requirements met: "
                    + "; ".join(map(str, card.requires_any))
                )
            else:
                unconf.append("any of: " + "; ".join(map(str, card.requires_any)))
    for c in card.excludes_any:
        s, lab = eval_cond(c, p)
        if s == T:
            blocked = True
            reasons.append(f"exclusion applies: {c}")
        elif s == U:
            missing.append(f"{lab} (needed to rule out exclusion: {c})")
    for i, v in enumerate(card.variants):
        res = [eval_cond(c, p) for c in v.when]
        if all(s == T for s, _ in res):
            selected.append(
                f"#{i} WHEN " + " AND ".join(map(str, v.when)) + f" -> {v.action}"
            )
        elif any(s in (F, N) for s, _ in res):
            continue
        else:
            for lab in sorted({lab for s, lab in res if s == U}):
                missing.append(f"{lab} (needed to choose variant #{i})")
    status = (
        "BLOCKED"
        if blocked
        else "NOT_MET" if not_met else "MISSING_INFO" if missing else "APPLICABLE"
    )
    return Check(
        card.card_id, status, reasons, list(dict.fromkeys(missing)), unconf, selected
    )


def check_all(patient: Patient, hits) -> dict:
    return {h.card.card_id: check(h.card, patient) for h in hits}
