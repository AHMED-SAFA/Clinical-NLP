from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator

Category = Literal["probable_diagnosis", "investigation", "medication", "advice"]
Disease = Literal["dengue", "hypertension", "cholera", "chikungunya"]
NS = "not stated"


# ---------- Card (canonical knowledge unit) ----------
class Condition(BaseModel):
    """field: age_years|sex|pregnant|weight_kg|duration_days|symptom|history|medicine|allergy|finding"""

    field: str
    op: Literal[">=", "<=", ">", "<", "==", "!=", "has", "not_has"]
    value: str | float | bool
    note: Optional[str] = None

    def __str__(self):
        return f"{self.field} {self.op} {self.value}" + (
            f" ({self.note})" if self.note else ""
        )


class Medication(BaseModel):
    name: Optional[str] = None
    dose: Optional[str] = None
    route: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    instructions: Optional[str] = None
    restrictions: Optional[str] = None  # None = not stated in source

    def __str__(self):
        f = lambda v: v if v else NS
        return (
            f"{f(self.name)} | dose: {f(self.dose)} | route: {f(self.route)} | freq: {f(self.frequency)} "
            f"| duration: {f(self.duration)} | instructions: {f(self.instructions)} "
            f"| restrictions: {f(self.restrictions)}"
        )


class Variant(BaseModel):
    """One branch of a table/conditional recommendation (e.g. by weight, age, comorbidity, severity)."""

    when: list[Condition]
    action: str
    medication: Optional[Medication] = None


class Source(BaseModel):
    title: str
    version: str
    pdf_pages: list[int]  # cover = page 1


class Evidence(BaseModel):
    page: int
    passage: str  # verbatim from the PDF page


class Card(BaseModel):
    card_id: str = Field(pattern=r"^(DEN|HTN|CHO|CHI)-(DX|IX|RX|ADV)-\d{3}$")
    disease: Disease
    category: Category
    title: str
    symptoms_or_prerequisites: list[str]
    requires_all: list[Condition] = []  # every one must hold
    requires_any: list[Condition] = []  # at least one must hold (if non-empty)
    excludes_any: list[Condition] = []  # if any holds, card is blocked
    variants: list[Variant] = []  # conditional branches of the action
    recommended_action: str
    medication: Optional[Medication] = None
    exclusions: list[str] = []  # plain-text exclusions / cautions
    missing_info: list[str] = []  # patient details needed to apply the card
    source: Source
    evidence: list[Evidence] = Field(min_length=1)
    reviewed: bool = False

    @model_validator(mode="after")
    def _check(self):
        prefix = {
            "dengue": "DEN",
            "hypertension": "HTN",
            "cholera": "CHO",
            "chikungunya": "CHI",
        }[self.disease]
        if not self.card_id.startswith(prefix):
            raise ValueError("card_id prefix does not match disease")
        if not {e.page for e in self.evidence} <= set(self.source.pdf_pages):
            raise ValueError("evidence page not in source.pdf_pages")
        if self.category == "medication" and not (
            self.medication or any(v.medication for v in self.variants)
        ):
            raise ValueError("medication card needs medication or variant medication")
        return self

    def index_text(self) -> str:
        parts = [
            self.disease,
            self.category,
            self.title,
            *self.symptoms_or_prerequisites,
            self.recommended_action,
            *[str(c) for c in self.requires_all + self.requires_any],
            *[e.passage for e in self.evidence],
        ]
        return ". ".join(p for p in parts if p)

    def prompt_text(self) -> str:
        L = [
            f"[{self.card_id}] disease={self.disease} category={self.category} | {self.title}",
            "Prerequisites: " + ("; ".join(self.symptoms_or_prerequisites) or NS),
        ]
        if self.requires_all:
            L.append("Applies only if ALL: " + "; ".join(map(str, self.requires_all)))
        if self.requires_any:
            L.append("Applies if ANY: " + "; ".join(map(str, self.requires_any)))
        if self.excludes_any:
            L.append("BLOCKED if ANY: " + "; ".join(map(str, self.excludes_any)))
        L.append("Action: " + self.recommended_action)
        for v in self.variants:
            L.append(
                "  Variant WHEN "
                + " AND ".join(map(str, v.when))
                + f": {v.action}"
                + (f" || {v.medication}" if v.medication else "")
            )
        if self.medication:
            L.append(f"Medication: {self.medication}")
        if self.exclusions:
            L.append("Exclusions/cautions: " + "; ".join(self.exclusions))
        if self.missing_info:
            L.append("Needs patient details: " + "; ".join(self.missing_info))
        L.append(
            f"Source: {self.source.title} ({self.source.version}), PDF p.{','.join(map(str, self.source.pdf_pages))}"
        )
        L += [f'Evidence (p.{e.page}): "{e.passage}"' for e in self.evidence]
        return "\n".join(L)


# ---------- Patient input ----------
class Patient(BaseModel):
    complaints: str
    duration_days: Optional[float] = None
    age_years: Optional[float] = None
    sex: Optional[str] = None
    pregnant: Optional[bool] = None
    weight_kg: Optional[float] = None
    history: str = ""
    medicines: str = ""
    allergies: str = ""
    findings: str = ""  # vitals / lab results already available

    def to_query(self) -> str:
        bits = [self.complaints]
        if self.duration_days is not None:
            bits.append(f"for {self.duration_days:g} days")
        if self.age_years is not None:
            bits.append(f"{self.age_years:g} year old")
        if self.sex:
            bits.append(self.sex)
        if self.pregnant:
            bits.append("pregnant")
        for x in (self.findings, self.history, self.medicines):
            if x:
                bits.append(x)
        return ". ".join(bits)

    def prompt_text(self) -> str:
        n = lambda v: NS if v in (None, "") else v
        return "\n".join(
            [
                f"Chief complaints: {n(self.complaints)}",
                f"Illness duration (days): {n(self.duration_days)}",
                f"Age (years): {n(self.age_years)}",
                f"Sex: {n(self.sex)}",
                f"Pregnant: {n(self.pregnant)}",
                f"Weight (kg): {n(self.weight_kg)}",
                f"Medical history: {n(self.history)}",
                f"Current medicines: {n(self.medicines)}",
                f"Allergies: {n(self.allergies)}",
                f"Findings/results available: {n(self.findings)}",
            ]
        )


# ---------- Model output (no defaults: required by Gemini structured output) ----------
class Diagnosis(BaseModel):
    disease: str
    likelihood: Literal["most_likely", "possible", "less_likely"]
    status: Literal["probable", "confirmed"]
    reason: str
    supporting_findings: list[str]
    card_ids: list[str]


class Investigation(BaseModel):
    test: str
    purpose: str
    timing_or_condition: str
    card_ids: list[str]


class MedItem(BaseModel):
    name: str
    dose: str
    route: str
    frequency: str
    duration: str
    instructions: str
    restrictions_for_this_patient: str
    missing_fields: list[str]
    card_ids: list[str]


class AdviceItem(BaseModel):
    type: Literal["self_care", "follow_up", "warning_signs", "referral"]
    text: str
    card_ids: list[str]


class MissingItem(BaseModel):
    field: str
    why_needed: str
    card_ids: list[str]


class Recommendation(BaseModel):
    differential: list[Diagnosis]
    investigations: list[Investigation]
    medications: list[MedItem]
    advice: list[AdviceItem]
    missing_information: list[MissingItem]
