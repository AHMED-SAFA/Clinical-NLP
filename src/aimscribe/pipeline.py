import json, time
from datetime import datetime
from pathlib import Path
from . import llm
from .prompts import SYSTEM, build_user_prompt
from .schema import Patient, Recommendation

_RET = None


def get_retriever():
    global _RET
    if _RET is None:
        from .retriever import HybridRetriever

        _RET = HybridRetriever()
    return _RET


def _ids(rec: Recommendation):
    for group in (
        rec.differential,
        rec.investigations,
        rec.medications,
        rec.advice,
        rec.missing_information,
    ):
        for item in group:
            yield from item.card_ids


def run(patient: Patient, mode: str = "baseline", top_k: int = 12) -> dict:
    if mode != "baseline":
        raise NotImplementedError("Improved mode is added later (Q2 continued).")
    t0 = time.perf_counter()
    hits = get_retriever().retrieve(patient.to_query(), k=top_k)
    prompt = build_user_prompt(patient, hits)
    rec = Recommendation.model_validate(
        llm.generate_json(SYSTEM, prompt, Recommendation)
    )
    valid = {h.card.card_id for h in hits}
    invalid = sorted({i for i in _ids(rec) if i not in valid})
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
        prompt=prompt,
        recommendation=rec.model_dump(),
        invalid_citations=invalid,
        elapsed_s=round(time.perf_counter() - t0, 2),
    )


def save(result: dict, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), "utf-8")
