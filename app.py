import sys, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
import streamlit as st
from aimscribe.config import CASES_PATH
from aimscribe.schema import Patient
from aimscribe import pipeline

st.set_page_config(page_title="AIMScribe Prototype", layout="wide")
CASES = (
    json.loads(CASES_PATH.read_text("utf-8"))
    if CASES_PATH.exists() and CASES_PATH.stat().st_size
    else []
)
DEF = dict(
    complaints="",
    duration_days=0.0,
    age_years=0.0,
    sex="not stated",
    pregnant="not stated",
    weight_kg=0.0,
    history="",
    medicines="",
    allergies="",
    findings="",
)
for k, v in DEF.items():
    st.session_state.setdefault(k, v)
st.session_state.setdefault("case_pick", "(new case)")


def load_case():
    pick = st.session_state.case_pick
    p = next((c["patient"] for c in CASES if c["label"] == pick), {})
    for k, v in DEF.items():
        val = p.get(k)
        if k == "pregnant":
            val = {True: "yes", False: "no"}.get(val, "not stated")
        elif k == "sex":
            val = val or "not stated"
        st.session_state[k] = v if val is None else val


def build_patient() -> Patient:
    s = st.session_state
    return Patient(
        complaints=s.complaints.strip(),
        duration_days=s.duration_days or None,
        age_years=s.age_years or None,
        sex=None if s.sex == "not stated" else s.sex,
        pregnant={"yes": True, "no": False}.get(s.pregnant),
        weight_kg=s.weight_kg or None,
        history=s.history.strip(),
        medicines=s.medicines.strip(),
        allergies=s.allergies.strip(),
        findings=s.findings.strip(),
    )


with st.sidebar:
    st.header("Patient case")
    st.selectbox(
        "Load sample case",
        ["(new case)"] + [c["label"] for c in CASES],
        key="case_pick",
        on_change=load_case,
    )
    st.text_area("Chief complaints / symptoms *", key="complaints", height=90)
    st.number_input(
        "Illness duration, days (0 = not stated)",
        min_value=0.0,
        step=0.5,
        key="duration_days",
    )
    c1, c2 = st.columns(2)
    c1.number_input(
        "Age, years (0 = not stated)", min_value=0.0, step=0.5, key="age_years"
    )
    c2.number_input(
        "Weight, kg (0 = not stated)", min_value=0.0, step=0.5, key="weight_kg"
    )
    st.selectbox("Sex", ["not stated", "male", "female"], key="sex")
    st.selectbox("Pregnant", ["not stated", "yes", "no"], key="pregnant")
    st.text_area("Medical history", key="history", height=60)
    st.text_area("Current medicines", key="medicines", height=60)
    st.text_area("Allergies", key="allergies", height=50)
    st.text_area(
        "Findings / results available (vitals, labs)", key="findings", height=60
    )
    st.divider()
    mode = st.radio("Mode", ["baseline"], help="'improved' is added later")
    top_k = st.slider("Cards retrieved (top-k)", 4, 25, 12)
    go = st.button("Get recommendations", type="primary", use_container_width=True)

st.title("AIMScribe - protocol-grounded recommendations")
st.caption(
    "Fictional/demo use. Output is a probable diagnosis from 4 supplied protocols, not clinical advice."
)

if go:
    if not st.session_state.complaints.strip():
        st.warning("Enter chief complaints or symptoms.")
    else:
        try:
            with st.spinner("Retrieving cards and generating..."):
                st.session_state.result = pipeline.run(build_patient(), mode, top_k)
        except Exception as e:
            st.error(f"Run failed: {e}")

res = st.session_state.get("result")
if not res:
    st.info("Enter a case (no disease name needed) and click **Get recommendations**.")
    st.stop()

rec, hits = res["recommendation"], {h["card_id"]: h for h in res["retrieved"]}


def ref(ids):
    out = []
    for i in ids:
        h = hits.get(i)
        out.append(
            f"`{i}` p.{','.join(map(str, h['source']['pdf_pages']))}"
            if h
            else f":red[`{i}` invalid]"
        )
    return "📄 " + (", ".join(out) if out else ":red[no citation]")


st.caption(
    f"Mode: **{res['mode']}** | Model: **{res['model']}** | Time: **{res['elapsed_s']} s** | "
    f"Cards retrieved: **{len(hits)}**"
)
if res["invalid_citations"]:
    st.error(f"Citations not in retrieved cards: {res['invalid_citations']}")

st.subheader("1. Patient information")
st.table(
    [
        {"Field": k, "Value": ("not stated" if v in (None, "") else str(v))}
        for k, v in res["patient"].items()
    ]
)

st.subheader("2. Retrieved evidence")
for h in res["retrieved"]:
    with st.expander(
        f"{h['card_id']} | {h['disease']} / {h['category']} | {h['title']} "
        f"(RRF {h['rrf']}, dense #{h['dense_rank']}, bm25 #{h['bm25_rank']})"
    ):
        st.markdown(f"**Action:** {h['action']}")
        st.caption(
            f"{h['source']['title']} ({h['source']['version']}), PDF p."
            f"{','.join(map(str, h['source']['pdf_pages']))}"
        )
        for e in h["evidence"]:
            st.markdown(f"> {e['passage']}  \n> *(p.{e['page']})*")

st.subheader("3. Recommendations")
t1, t2, t3, t4, t5 = st.tabs(
    [
        "Probable diagnosis",
        "Investigations",
        "Medication planning",
        "Advice",
        "Missing information",
    ]
)
with t1:
    for d in rec["differential"]:
        st.markdown(
            f"**{d['disease']}** - {d['likelihood'].replace('_', ' ')} ({d['status']})  \n"
            f"{d['reason']}  \nSupporting: {', '.join(d['supporting_findings']) or 'none stated'}  \n{ref(d['card_ids'])}"
        )
with t2:
    for i in rec["investigations"]:
        st.markdown(
            f"**{i['test']}**  \nPurpose: {i['purpose']}  \nTiming/condition: {i['timing_or_condition']}  \n{ref(i['card_ids'])}"
        )
with t3:
    for m in rec["medications"]:
        st.markdown(
            f"**{m['name']}**  \nDose: {m['dose']} | Route: {m['route']} | Frequency: {m['frequency']} | "
            f"Duration: {m['duration']}  \nInstructions: {m['instructions']}  \n"
            f"Restrictions for this patient: {m['restrictions_for_this_patient']}  \n"
            + (
                f":orange[Missing fields: {', '.join(m['missing_fields'])}]  \n"
                if m["missing_fields"]
                else ""
            )
            + ref(m["card_ids"])
        )
with t4:
    for a in rec["advice"]:
        st.markdown(
            f"**{a['type'].replace('_', ' ').title()}:** {a['text']}  \n{ref(a['card_ids'])}"
        )
with t5:
    for x in rec["missing_information"]:
        st.markdown(f"**{x['field']}** - {x['why_needed']}  \n{ref(x['card_ids'])}")

with st.expander("Prompt sent to model / raw JSON"):
    st.code(res["prompt"])
    st.json(rec)
