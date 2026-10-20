import sys, json, html
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
import streamlit as st
from aimscribe.config import CASES_PATH
from aimscribe.schema import Patient
from aimscribe import pipeline

st.set_page_config(
    page_title="AIMScribe",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═════════════════════════════════ Dark theme ════════════════════════════════
DARK = """
color-scheme:dark;
--ink:#E8F2F1; --ink-2:#B6C9CC; --ink-3:#8CA3A8; --muted:#6F878C;
--paper:#0B1517; --card:#122125; --line:#223A3F; --line-2:#1A2E32;
--teal:#35BFB0; --teal-d:#86E3D7; --teal-bg:rgba(53,191,176,.16);
--amber:#F0B95A; --amber-bg:rgba(240,185,90,.14);
--rose:#F08A99; --rose-bg:rgba(240,138,153,.14);
--blue:#8DB6F2; --blue-bg:rgba(110,160,235,.15);
--slate-bg:#1A2C30;
--quote-line:#2E5B58; --cite-blue-line:rgba(141,182,242,.3); --cite-rose-line:rgba(240,138,153,.3);
--tabs-bg:#0F1D20; --tab-active:#1D3A3F; --tab-active-ink:#9BEDE2;
--btn-a:#11998B; --btn-b:#0A6F66; --code-bg:#0F1D20;
--shadow:rgba(0,0,0,.55);
"""

VARS = ":root{" + DARK + "}"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,500;6..72,600;6..72,700&family=Public+Sans:wght@400;500;600;700&display=swap');
/*VARS*/

html, body, .stApp, [class*="css"]{font-family:'Public Sans',system-ui,sans-serif;}
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"]{background:var(--paper)!important; color:var(--ink)!important;}
.block-container{padding-top:1.6rem; padding-bottom:4rem; max-width:1180px;}
header[data-testid="stHeader"]{background:transparent!important;}
header[data-testid="stHeader"] *{color:var(--ink-2)!important;}
#MainMenu, footer{visibility:hidden;}
h1,h2,h3,h4{font-family:'Newsreader',Georgia,serif; color:var(--ink); letter-spacing:-.01em;}

/* ══ Inputs (all widgets) ══ */
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div{
  background:var(--paper)!important; border:1px solid var(--line)!important; border-radius:10px!important;}
[data-baseweb="base-input"]{background:transparent!important; border:0!important;}
input, textarea{background:transparent!important; color:var(--ink)!important; -webkit-text-fill-color:var(--ink)!important; caret-color:var(--teal);}
input::placeholder, textarea::placeholder{color:var(--muted)!important; -webkit-text-fill-color:var(--muted)!important; opacity:1;}
[data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within, [data-baseweb="select"] > div:focus-within{
  border-color:var(--teal)!important; box-shadow:0 0 0 3px var(--teal-bg)!important;}
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] *{color:var(--ink-2)!important; font-weight:600; font-size:.82rem;}

/* ══ Select + dropdown menu (renders in a portal) ══ */
[data-baseweb="select"] *{color:var(--ink)!important; -webkit-text-fill-color:var(--ink)!important;}
[data-baseweb="select"] svg{fill:var(--ink-3)!important; color:var(--ink-3)!important;}
[data-baseweb="popover"], [data-baseweb="popover"] > div{background:transparent!important;}
[data-baseweb="popover"] [data-baseweb="menu"], [data-baseweb="popover"] ul{
  background:var(--card)!important; border:1px solid var(--line)!important; border-radius:12px!important;
  box-shadow:0 18px 36px -14px var(--shadow)!important; padding:.3rem!important;}
[data-baseweb="popover"] li{background:transparent!important; color:var(--ink)!important; border-radius:8px!important; margin:1px 0;}
[data-baseweb="popover"] li *{color:inherit!important; -webkit-text-fill-color:inherit!important;}
[data-baseweb="popover"] li:hover, [data-baseweb="popover"] li[data-highlighted="true"]{background:var(--teal-bg)!important; color:var(--teal-d)!important;}
[data-baseweb="popover"] li[aria-selected="true"]{background:var(--teal-bg)!important; color:var(--teal-d)!important; font-weight:600;}
[data-baseweb="tooltip"], [data-baseweb="popover"] [data-testid="stTooltipContent"]{background:var(--card)!important; color:var(--ink)!important; border:1px solid var(--line);}

/* ══ Number-input steppers ══ */
[data-testid="stNumberInput"] button{background:var(--paper)!important; border:0!important; color:var(--ink-2)!important;}
[data-testid="stNumberInput"] button:hover{background:var(--teal-bg)!important; color:var(--teal-d)!important;}
[data-testid="stNumberInput"] button svg{fill:currentColor!important; color:inherit!important;}

/* ══ Radio + slider (recolour Streamlit's default red accent to teal) ══ */
[data-testid="stRadio"] label p, [data-testid="stRadio"] label span{color:var(--ink)!important; font-weight:500; font-size:.86rem;}
[data-testid="stRadio"] [data-baseweb="radio"] > div:first-child{filter:hue-rotate(172deg) saturate(.85);}
[data-testid="stSlider"] [data-baseweb="slider"]{filter:hue-rotate(172deg) saturate(.85);}
[data-testid="stSlider"] [data-testid="stTickBarMin"], [data-testid="stSlider"] [data-testid="stTickBarMax"]{color:var(--ink-3)!important;}

/* ══ Buttons ══ */
button[kind="primary"], [data-testid="stBaseButton-primary"]{
  background:linear-gradient(135deg,var(--btn-a),var(--btn-b))!important; border:0!important; border-radius:12px!important;
  padding:.7rem 1rem!important; font-weight:600!important; box-shadow:0 10px 22px -12px var(--shadow); transition:transform .15s, filter .15s;}
button[kind="primary"], button[kind="primary"] *, [data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primary"] *{color:#FFFFFF!important; -webkit-text-fill-color:#FFFFFF!important;}
button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover{transform:translateY(-1px); filter:brightness(1.1);}
button[kind="primary"]:active, [data-testid="stBaseButton-primary"]:active{transform:translateY(0); filter:brightness(.95);}
button[kind="primary"]:focus-visible, [data-testid="stBaseButton-primary"]:focus-visible{outline:3px solid var(--teal-bg)!important; outline-offset:2px;}

/* ══ Sidebar ══ */
[data-testid="stSidebar"]{background:var(--card)!important; border-right:1px solid var(--line);}
[data-testid="stSidebarContent"]{padding-top:1rem;}
.brand{display:flex; align-items:center; gap:.65rem; margin:.2rem 0 1rem;}
.brand .mark{width:38px;height:38px;border-radius:11px;display:grid;place-items:center;font-size:1.2rem;
  background:linear-gradient(135deg,var(--btn-a),var(--teal)); box-shadow:0 6px 14px -6px var(--shadow);}
.brand .name{font-family:'Newsreader',serif; font-weight:700; font-size:1.35rem; line-height:1; color:var(--ink);}
.brand .tag{font-size:.74rem; color:var(--ink-3); margin-top:.2rem;}
.side-label{display:flex; align-items:center; gap:.5rem; margin:1.1rem 0 .5rem; font-weight:700; font-size:.9rem; color:var(--ink);}
.side-label::before{content:""; width:4px; height:16px; border-radius:2px; background:var(--teal);}
.side-label small{font-weight:500; color:var(--ink-3); font-size:.76rem; margin-left:auto;}

/* ══ Hero ══ */
.hero{position:relative; overflow:hidden; border-radius:22px; padding:2rem 2.2rem 1.9rem; margin-bottom:1.2rem;
  background:radial-gradient(900px 300px at 100% 0%, rgba(19,168,155,.45), transparent 60%),
   linear-gradient(135deg,#0B2F34 0%,#0C4A4A 60%,#0C6A62 100%);}
.hero svg.ecg{position:absolute; right:-10px; bottom:6px; width:58%; opacity:.22;}
.hero h1{font-size:2.5rem; margin:0 0 .35rem; color:#FFFFFF!important; font-weight:600;}
.hero p{margin:0; max-width:620px; font-size:1rem; line-height:1.55; color:#CFE6E2!important;}
.hero .pill{display:inline-flex; align-items:center; gap:.45rem; margin-top:1.1rem; padding:.38rem .8rem;
  border-radius:999px; background:rgba(255,255,255,.12); border:1px solid rgba(255,255,255,.2); font-size:.78rem; color:#E7F5F2;}
.hero .pill i{width:7px;height:7px;border-radius:50%;background:#F2C063;display:inline-block;}

/* ══ Section headings ══ */
.sec{display:flex; align-items:baseline; gap:.8rem; margin:2.1rem 0 .9rem; padding-bottom:.55rem; border-bottom:1px solid var(--line);}
.sec h2{font-size:1.55rem; margin:0; font-weight:600; color:var(--ink)!important;}
.sec span{font-size:.85rem; color:var(--ink-3);}

/* ══ Stat strip ══ */
.stats{display:grid; grid-template-columns:repeat(4,1fr); gap:.8rem;}
.stat{background:var(--card); border:1px solid var(--line); border-radius:16px; padding:.9rem 1.05rem;}
.stat .k{font-size:.76rem; color:var(--ink-3); font-weight:500;}
.stat .v{font-family:'Newsreader',serif; font-size:1.3rem; font-weight:600; margin-top:.15rem; color:var(--ink); word-break:break-word;}

/* ══ Patient tiles ══ */
.tiles{display:grid; grid-template-columns:repeat(auto-fill,minmax(210px,1fr)); gap:.7rem;}
.tile{background:var(--card); border:1px solid var(--line); border-radius:14px; padding:.75rem .95rem;}
.tile.wide{grid-column:span 2;}
.tile .k{font-size:.74rem; color:var(--ink-3); font-weight:500; margin-bottom:.15rem;}
.tile .v{font-size:.95rem; font-weight:500; color:var(--ink); line-height:1.4;}
.tile .v.muted{color:var(--muted); font-weight:400; font-style:italic;}

/* ══ Chips & citations ══ */
.chip{display:inline-flex; align-items:center; padding:.18rem .62rem; border-radius:999px; font-size:.74rem; font-weight:600;
  margin-right:.3rem; background:var(--slate-bg); color:var(--ink-2); white-space:nowrap;}
.chip.good{background:var(--teal-bg); color:var(--teal-d);}
.chip.warn{background:var(--amber-bg); color:var(--amber);}
.chip.bad{background:var(--rose-bg); color:var(--rose);}
.chip.info{background:var(--blue-bg); color:var(--blue);}
.cites{margin-top:.75rem; display:flex; flex-wrap:wrap; gap:.35rem;}
.cite{display:inline-flex; align-items:center; gap:.3rem; padding:.2rem .6rem; border-radius:8px; font-size:.75rem;
  background:var(--blue-bg); color:var(--blue); font-weight:600; border:1px solid var(--cite-blue-line);}
.cite.bad{background:var(--rose-bg); color:var(--rose); border-color:var(--cite-rose-line);}
.cite.none{background:var(--slate-bg); color:var(--ink-3); border-color:var(--line);}

/* ══ Cards ══ */
.card{background:var(--card); border:1px solid var(--line); border-radius:16px; padding:1.1rem 1.25rem; margin-bottom:.85rem; border-left:4px solid var(--teal);}
.card.amber{border-left-color:#E3A53A;} .card.blue{border-left-color:#4C82CF;} .card.rose{border-left-color:#D45A6D;}
.card-head{display:flex; justify-content:space-between; align-items:flex-start; gap:1rem; flex-wrap:wrap;}
.card h4{margin:0; font-size:1.2rem; font-weight:600; color:var(--ink)!important;}
.card p{margin:.55rem 0 0; color:var(--ink-2); font-size:.93rem; line-height:1.6;}
.card .kv{margin-top:.6rem; font-size:.85rem; color:var(--ink-2); line-height:1.55;}
.card .kv b, .card p b{color:var(--ink);}
.dose{display:grid; grid-template-columns:repeat(4,1fr); gap:.5rem; margin-top:.8rem;}
.dose div{background:var(--paper); border:1px solid var(--line-2); border-radius:12px; padding:.5rem .7rem;}
.dose small{display:block; font-size:.7rem; color:var(--ink-3); font-weight:500;}
.dose span{font-size:.9rem; font-weight:600; color:var(--ink);}
.missing{margin-top:.7rem; padding:.55rem .75rem; border-radius:10px; background:var(--amber-bg); color:var(--amber); font-size:.84rem; font-weight:500;}
.empty{padding:1.4rem; text-align:center; color:var(--ink-3); background:var(--card); border:1px dashed var(--line); border-radius:14px;}

/* ══ Evidence expanders ══ */
[data-testid="stExpander"]{background:var(--card)!important; border:1px solid var(--line)!important; border-radius:14px!important; margin-bottom:.55rem; overflow:hidden;}
[data-testid="stExpander"] details, [data-testid="stExpanderDetails"]{background:var(--card)!important;}
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary *{color:var(--ink)!important; font-weight:600; font-size:.92rem;}
[data-testid="stExpander"] summary:hover{background:var(--paper)!important;}
[data-testid="stExpander"] summary svg{color:var(--ink-3)!important; fill:var(--ink-3)!important;}
.act{background:var(--teal-bg); color:var(--teal-d); padding:.7rem .9rem; border-radius:12px; font-size:.92rem; line-height:1.55; margin-bottom:.6rem;}
.src{font-size:.78rem; color:var(--ink-3); margin-bottom:.7rem;}
.quote{border-left:3px solid var(--quote-line); background:var(--paper); padding:.6rem .9rem; margin:.45rem 0; border-radius:0 10px 10px 0;
  font-size:.88rem; color:var(--ink-2); line-height:1.6;}
.quote em{display:block; margin-top:.25rem; font-size:.74rem; color:var(--ink-3); font-style:normal; font-weight:600;}

/* ══ Table ══ */
.tbl{background:var(--card); border:1px solid var(--line); border-radius:14px; overflow-x:auto;}
.tbl table{width:100%; border-collapse:collapse; font-size:.86rem;}
.tbl th{text-align:left; padding:.65rem .9rem; background:var(--paper); color:var(--ink-3); font-weight:600; font-size:.76rem; border-bottom:1px solid var(--line);}
.tbl td{padding:.65rem .9rem; border-bottom:1px solid var(--line-2); vertical-align:top; color:var(--ink-2);}
.tbl td b{color:var(--ink);}
.tbl tr:last-child td{border-bottom:0;}

/* ══ Tabs (labels always visible, not only on hover) ══ */
.stTabs [data-baseweb="tab-list"]{gap:.4rem; background:var(--tabs-bg)!important; padding:.3rem; border-radius:14px; border:0!important; flex-wrap:wrap;}
.stTabs [data-baseweb="tab"]{height:auto; padding:.5rem 1rem; border-radius:10px; background:transparent!important; transition:background .15s;}
.stTabs [data-baseweb="tab"], .stTabs [data-baseweb="tab"] *{color:var(--ink-2)!important; -webkit-text-fill-color:var(--ink-2)!important; opacity:1!important; font-weight:600; font-size:.88rem;}
.stTabs [data-baseweb="tab"]:hover{background:var(--card)!important;}
.stTabs [data-baseweb="tab"]:hover, .stTabs [data-baseweb="tab"]:hover *{color:var(--ink)!important; -webkit-text-fill-color:var(--ink)!important;}
.stTabs [aria-selected="true"]{background:var(--tab-active)!important; box-shadow:0 2px 8px -3px var(--shadow);}
.stTabs [aria-selected="true"], .stTabs [aria-selected="true"] *{color:var(--tab-active-ink)!important; -webkit-text-fill-color:var(--tab-active-ink)!important;}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"]{display:none!important;}
.stTabs [data-baseweb="tab-panel"]{padding-top:1.1rem;}

/* ══ Alerts, code ══ */
[data-testid="stAlert"]{background:var(--card)!important; border:1px solid var(--line)!important; border-left:4px solid var(--blue)!important; border-radius:12px!important;}
[data-testid="stAlert"], [data-testid="stAlert"] *{color:var(--ink)!important;}
[data-testid="stAlert"]:has([data-testid="stAlertContentError"]){border-left-color:#D45A6D!important; background:var(--rose-bg)!important;}
[data-testid="stAlert"]:has([data-testid="stAlertContentWarning"]){border-left-color:#E3A53A!important; background:var(--amber-bg)!important;}
[data-testid="stSpinner"] *{color:var(--ink-2)!important;}
[data-testid="stCode"], [data-testid="stCode"] pre{background:var(--code-bg)!important; border:1px solid var(--line); border-radius:12px;}
[data-testid="stCode"] *{color:var(--ink-2)!important;}

/* ══ Empty-state steps ══ */
.steps{display:grid; grid-template-columns:repeat(3,1fr); gap:.9rem; margin-top:.4rem;}
.step{background:var(--card); border:1px solid var(--line); border-radius:16px; padding:1.1rem 1.2rem;}
.step .ic{width:38px;height:38px;border-radius:11px;display:grid;place-items:center;background:var(--teal-bg);font-size:1.1rem;margin-bottom:.6rem;}
.step h4{margin:0 0 .25rem; font-size:1.05rem; color:var(--ink)!important;}
.step p{margin:0; font-size:.88rem; color:var(--ink-2); line-height:1.55;}

@media (max-width:900px){
  .stats{grid-template-columns:repeat(2,1fr);} .steps{grid-template-columns:1fr;}
  .dose{grid-template-columns:repeat(2,1fr);} .tile.wide{grid-column:span 1;} .hero h1{font-size:2rem;}
}
</style>
"""
st.markdown(CSS.replace("/*VARS*/", VARS), unsafe_allow_html=True)


# ═════════════════════════════ Helpers ═════════════════════════════
def esc(x):
    return html.escape(str(x))


def html_out(s: str):
    st.markdown(s, unsafe_allow_html=True)


def chip(text, kind=""):
    return f'<span class="chip {kind}">{esc(text)}</span>'


def section(title, sub=""):
    html_out(f'<div class="sec"><h2>{esc(title)}</h2><span>{esc(sub)}</span></div>')


def side_label(title, note=""):
    html_out(f'<div class="side-label">{esc(title)}<small>{esc(note)}</small></div>')


def likelihood_tone(s):
    s = str(s).lower()
    if "unlikely" in s or "low" in s:
        return "bad"
    if "mod" in s or "med" in s or "possible" in s:
        return "warn"
    if "high" in s or "likely" in s or "probable" in s:
        return "good"
    return "info"


def status_tone(s):
    s = str(s).lower()
    if any(w in s for w in ("block", "not ", "fail", "exclu", "contra", "invalid")):
        return "bad"
    if any(
        w in s
        for w in (
            "unconf",
            "partial",
            "condition",
            "uncertain",
            "missing",
            "caution",
            "needs",
        )
    ):
        return "warn"
    return "good"


def cites(ids, hits):
    out = []
    for i in ids:
        h = hits.get(i)
        if h:
            pages = ",".join(map(str, h["source"]["pdf_pages"]))
            out.append(f'<span class="cite">📄 {esc(i)} · p.{esc(pages)}</span>')
        else:
            out.append(f'<span class="cite bad">⚠ {esc(i)} invalid</span>')
    if not out:
        out.append('<span class="cite none">no citation</span>')
    return f'<div class="cites">{"".join(out)}</div>'


def empty(msg):
    html_out(f'<div class="empty">{esc(msg)}</div>')


# ═════════════════════════════ Data / state ═════════════════════════════
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


# ═════════════════════════════ Sidebar ═════════════════════════════
with st.sidebar:
    html_out(
        '<div class="brand"><div class="mark">🩺</div><div>'
        '<div class="name">AIMScribe</div><div class="tag">Protocol-grounded decision support</div>'
        "</div></div>"
    )

    side_label("Start from", "optional")
    st.selectbox(
        "Load sample case",
        ["(new case)"] + [c["label"] for c in CASES],
        key="case_pick",
        on_change=load_case,
    )

    side_label("Presentation", "required")
    st.text_area(
        "Chief complaints / symptoms *",
        key="complaints",
        height=90,
        placeholder="e.g. fever, cough and breathlessness for 3 days",
    )
    st.number_input(
        "Illness duration, days (0 = not stated)",
        min_value=0.0,
        step=0.5,
        key="duration_days",
    )

    side_label("Patient")
    c1, c2 = st.columns(2)
    c1.number_input(
        "Age, years (0 = not stated)", min_value=0.0, step=0.5, key="age_years"
    )
    c2.number_input(
        "Weight, kg (0 = not stated)", min_value=0.0, step=0.5, key="weight_kg"
    )
    c3, c4 = st.columns(2)
    c3.selectbox("Sex", ["not stated", "male", "female"], key="sex")
    c4.selectbox("Pregnant", ["not stated", "yes", "no"], key="pregnant")

    side_label("Background")
    st.text_area("Medical history", key="history", height=60)
    st.text_area("Current medicines", key="medicines", height=60)
    st.text_area("Allergies", key="allergies", height=50)
    st.text_area(
        "Findings / results available (vitals, labs)", key="findings", height=60
    )

    side_label("Engine")
    mode = st.radio(
        "Mode",
        ["baseline", "improved"],
        horizontal=True,
        help="improved = baseline + deterministic applicability check",
    )
    top_k = st.slider("Cards retrieved (top-k)", 4, 25, 12)
    st.write("")
    go = st.button("Get recommendations", type="primary", use_container_width=True)

# ═════════════════════════════ Hero ═════════════════════════════
ECG = (
    '<svg class="ecg" viewBox="0 0 600 120" fill="none" stroke="#fff" stroke-width="2.5" '
    'stroke-linecap="round" stroke-linejoin="round"><path d="M0 70 H120 L140 70 L160 30 L185 105 '
    'L205 55 L222 70 H330 L350 70 L370 20 L395 100 L415 50 L432 70 H600"/></svg>'
)
html_out(
    f'<div class="hero">{ECG}<h1>Protocol-grounded recommendations</h1>'
    "<p>Describe a patient in plain language. AIMScribe retrieves matching protocol cards, "
    "suggests a probable diagnosis and cites every recommendation back to its source page.</p>"
    '<div class="pill"><i></i>Fictional demo. Output comes from 4 supplied protocols and is not clinical advice.</div>'
    "</div>"
)

# ═════════════════════════════ Run ═════════════════════════════
if go:
    if not st.session_state.complaints.strip():
        st.warning("Enter chief complaints or symptoms to continue.")
    else:
        try:
            with st.spinner("Retrieving cards and generating..."):
                st.session_state.result = pipeline.run(build_patient(), mode, top_k)
        except Exception as e:
            st.error(f"Run failed: {e}")

res = st.session_state.get("result")
if not res:
    section("How it works", "three steps")
    html_out(
        '<div class="steps">'
        '<div class="step"><div class="ic">📝</div><h4>Enter a case</h4>'
        "<p>Fill in the sidebar. Only chief complaints are required, and no disease name is needed.</p></div>"
        '<div class="step"><div class="ic">🔎</div><h4>Retrieve evidence</h4>'
        "<p>The most relevant protocol cards are found with dense and keyword search combined.</p></div>"
        '<div class="step"><div class="ic">📋</div><h4>Review the plan</h4>'
        "<p>Read the probable diagnosis, investigations, medicines and advice, each with page citations.</p></div>"
        "</div>"
    )
    st.stop()

rec, hits = res["recommendation"], {h["card_id"]: h for h in res["retrieved"]}

# ═════════════════════════════ Run summary ═════════════════════════════
html_out(
    '<div class="stats">'
    f'<div class="stat"><div class="k">Mode</div><div class="v">{esc(res["mode"])}</div></div>'
    f'<div class="stat"><div class="k">Model</div><div class="v">{esc(res["model"])}</div></div>'
    f'<div class="stat"><div class="k">Time</div><div class="v">{esc(res["elapsed_s"])} s</div></div>'
    f'<div class="stat"><div class="k">Cards retrieved</div><div class="v">{len(hits)}</div></div>'
    "</div>"
)
if res["invalid_citations"]:
    st.error(f"Citations not in retrieved cards: {res['invalid_citations']}")

# ═════════════════════════════ 1. Patient ═════════════════════════════
section("Patient information", "as understood by the system")
tiles = []
for k, v in res["patient"].items():
    missing = v in (None, "")
    wide = " wide" if (not missing and len(str(v)) > 40) else ""
    val = "not stated" if missing else str(v)
    tiles.append(
        f'<div class="tile{wide}"><div class="k">{esc(k.replace("_", " ").capitalize())}</div>'
        f'<div class="v{" muted" if missing else ""}">{esc(val)}</div></div>'
    )
html_out(f'<div class="tiles">{"".join(tiles)}</div>')

# ═════════════════════════════ 2. Evidence ═════════════════════════════
section("Retrieved evidence", f"{len(res['retrieved'])} protocol cards, ranked")
for h in res["retrieved"]:
    with st.expander(
        f"{h['card_id']}  ·  {h['disease']} / {h['category']}  ·  {h['title']}"
    ):
        pages = ",".join(map(str, h["source"]["pdf_pages"]))
        html_out(
            f'<div style="margin-bottom:.6rem">'
            f'{chip("RRF " + str(h["rrf"]), "good")}'
            f'{chip("dense #" + str(h["dense_rank"]), "info")}'
            f'{chip("bm25 #" + str(h["bm25_rank"]), "info")}</div>'
            f'<div class="act"><b>Action:</b> {esc(h["action"])}</div>'
            f'<div class="src">{esc(h["source"]["title"])} ({esc(h["source"]["version"])}), PDF p.{esc(pages)}</div>'
            + "".join(
                f'<div class="quote">{esc(e["passage"])}<em>page {esc(e["page"])}</em></div>'
                for e in h["evidence"]
            )
        )

if res.get("applicability"):
    section("Applicability check", "improved mode")
    rows = []
    for cid, a in res["applicability"].items():
        rows.append(
            "<tr>"
            f"<td><b>{esc(cid)}</b></td>"
            f'<td>{chip(a["status"], status_tone(a["status"]))}</td>'
            f'<td>{esc("; ".join(a["missing"]) or "-")}</td>'
            f'<td>{esc("; ".join(a["unconfirmed"]) or "-")}</td>'
            f'<td>{esc("; ".join(a["reasons"]) or "-")}</td>'
            "</tr>"
        )
    html_out(
        '<div class="tbl"><table><thead><tr><th>Card</th><th>Status</th><th>Missing</th>'
        f'<th>Unconfirmed</th><th>Reasons</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
    )
if res.get("blocked_citations"):
    st.warning(
        f"Cited as support although the checker blocked them: {res['blocked_citations']}"
    )

# ═════════════════════════════ 3. Recommendations ═════════════════════════════
section("Recommendations", "every item is cited to a retrieved card")
t1, t2, t3, t4, t5 = st.tabs(
    [
        f"Probable diagnosis ({len(rec['differential'])})",
        f"Investigations ({len(rec['investigations'])})",
        f"Medication planning ({len(rec['medications'])})",
        f"Advice ({len(rec['advice'])})",
        f"Missing information ({len(rec['missing_information'])})",
    ]
)

with t1:
    if not rec["differential"]:
        empty("No probable diagnosis was suggested.")
    for d in rec["differential"]:
        html_out(
            '<div class="card"><div class="card-head">'
            f'<h4>{esc(d["disease"])}</h4>'
            f'<div>{chip(str(d["likelihood"]).replace("_", " "), likelihood_tone(d["likelihood"]))}'
            f'{chip(d["status"], status_tone(d["status"]))}</div></div>'
            f'<p>{esc(d["reason"])}</p>'
            f'<div class="kv"><b>Supporting findings:</b> '
            f'{esc(", ".join(d["supporting_findings"]) or "none stated")}</div>'
            f'{cites(d["card_ids"], hits)}</div>'
        )

with t2:
    if not rec["investigations"]:
        empty("No investigations were suggested.")
    for i in rec["investigations"]:
        html_out(
            '<div class="card blue">'
            f'<div class="card-head"><h4>{esc(i["test"])}</h4></div>'
            f'<p><b>Purpose:</b> {esc(i["purpose"])}</p>'
            f'<div class="kv"><b>Timing / condition:</b> {esc(i["timing_or_condition"])}</div>'
            f'{cites(i["card_ids"], hits)}</div>'
        )

with t3:
    if not rec["medications"]:
        empty("No medicines were suggested.")
    for m in rec["medications"]:
        miss = (
            f'<div class="missing">Missing fields: {esc(", ".join(m["missing_fields"]))}</div>'
            if m["missing_fields"]
            else ""
        )
        html_out(
            '<div class="card amber">'
            f'<div class="card-head"><h4>{esc(m["name"])}</h4></div>'
            '<div class="dose">'
            f'<div><small>Dose</small><span>{esc(m["dose"])}</span></div>'
            f'<div><small>Route</small><span>{esc(m["route"])}</span></div>'
            f'<div><small>Frequency</small><span>{esc(m["frequency"])}</span></div>'
            f'<div><small>Duration</small><span>{esc(m["duration"])}</span></div></div>'
            f'<div class="kv"><b>Instructions:</b> {esc(m["instructions"])}</div>'
            f'<div class="kv"><b>Restrictions for this patient:</b> {esc(m["restrictions_for_this_patient"])}</div>'
            f"{miss}{cites(m['card_ids'], hits)}</div>"
        )

with t4:
    if not rec["advice"]:
        empty("No advice was generated.")
    for a in rec["advice"]:
        html_out(
            '<div class="card">'
            f'<div class="card-head"><h4>{esc(a["type"].replace("_", " ").title())}</h4></div>'
            f'<p>{esc(a["text"])}</p>{cites(a["card_ids"], hits)}</div>'
        )

with t5:
    if not rec["missing_information"]:
        empty("Nothing further is needed.")
    for x in rec["missing_information"]:
        html_out(
            '<div class="card rose">'
            f'<div class="card-head"><h4>{esc(x["field"])}</h4></div>'
            f'<p>{esc(x["why_needed"])}</p>{cites(x["card_ids"], hits)}</div>'
        )

st.write("")
with st.expander("Prompt sent to model / raw JSON"):
    st.code(res["prompt"])
    st.code(json.dumps(rec, indent=2, ensure_ascii=False), language="json")
