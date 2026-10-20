import json, time
from datetime import datetime
from pathlib import Path
from . import llm, applicability
from .prompts import SYSTEM, SYSTEM_IMPROVED, build_user_prompt
from .schema import Patient, Recommendation

_RET = None


def get_retriever():
    global _RET
    if _RET is None:
        from .retriever import HybridRetriever

        _RET = HybridRetriever()
    return _RET


def _ids(
    rec,
    groups=(
        "differential",
        "investigations",
        "medications",
        "advice",
        "missing_information",
    ),
):
    for g in groups:
        for item in getattr(rec, g):
            yield from item.card_ids


def run(patient: Patient, mode: str = "baseline", top_k: int = 12) -> dict:
    if mode not in ("baseline", "improved"):
        raise ValueError(mode)
    t0 = time.perf_counter()
    hits = get_retriever().retrieve(
        patient.to_query(), k=top_k
    )  # identical for both modes
    checks, checker_ms = None, 0.0
    if mode == "improved":
        t1 = time.perf_counter()
        checks = applicability.check_all(patient, hits)
        checker_ms = round((time.perf_counter() - t1) * 1000, 2)
    prompt = build_user_prompt(patient, hits, checks)
    system = SYSTEM_IMPROVED if mode == "improved" else SYSTEM
    rec = Recommendation.model_validate(
        llm.generate_json(system, prompt, Recommendation)
    )
    valid = {h.card.card_id for h in hits}
    invalid = sorted({i for i in _ids(rec) if i not in valid})
    blocked = []
    if (
        checks
    ):  # cited as support for a recommendation although the checker blocked it (verify manually)
        bad = {c for c, k in checks.items() if k.status in ("BLOCKED", "NOT_MET")}
        blocked = sorted(
            set(_ids(rec, ("differential", "investigations", "medications", "advice")))
            & bad
        )
    return dict(
        timestamp=datetime.now().isoformat(timespec="seconds"),
        mode=mode,
        model=llm.model_info(),
        patient=patient.model_dump(),
        patient_query=patient.to_query(),
        retrieved=[
            dict(
                card_id=h.card.card_id,
                disease=h.card.disease,
                category=h.card.category,
                title=h.card.title,
                source=h.card.source.model_dump(),
                action=h.card.recommended_action,
                evidence=[e.model_dump() for e in h.card.evidence],
                rrf=round(h.rrf, 5),
                dense_rank=h.dense_rank,
                bm25_rank=h.bm25_rank,
            )
            for h in hits
        ],
        applicability={k: v.to_dict() for k, v in checks.items()} if checks else None,
        prompt=prompt,
        prompt_chars=len(system) + len(prompt),
        checker_ms=checker_ms,
        recommendation=rec.model_dump(),
        invalid_citations=invalid,
        blocked_citations=blocked,
        elapsed_s=round(time.perf_counter() - t0, 2),
    )


def save(result: dict, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), "utf-8")
