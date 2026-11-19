import hashlib
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image

ROOT   = Path(__file__).resolve().parent
MODELS = ROOT / "models"
REPORTS = ROOT / "reports"
USERS_FILE = ROOT / "users.json"
sys.path.insert(0, str(ROOT / "src"))
from image_features import extract_features  # noqa: E402

st.set_page_config(page_title="AgriSmart AI", page_icon="🌱", layout="wide",
                   initial_sidebar_state="expanded")

# ═══════════════════════════════════════════════════════════════════
#  CSS  (login + app shared)
# ═══════════════════════════════════════════════════════════════════
CSS = """
<style>
:root{
  --green:#2e7d32; --green-d:#1b5e20; --green-l:#66bb6a;
  --bg:#f6f9f4; --card:#ffffff; --line:#e3e8e0; --ink:#1f2d27; --muted:#5f6f63;
}
/* ── global ── */
.stApp{ background: var(--bg); }
h1,h2,h3,h4{ color:var(--ink)!important; letter-spacing:.2px; }
.stApp p,.stApp li{ color:#243027; }
.stCaption{ color:var(--muted)!important; }
hr{ border-color:var(--line)!important; }

/* ── login page ── */
.login-wrap{
  min-height:100vh; display:flex; align-items:center; justify-content:center;
  background:linear-gradient(135deg,#1b5e20 0%,#2e7d32 50%,#43a047 100%);
}
.login-card{
  background:#fff; border-radius:24px; padding:2.6rem 2.4rem 2rem;
  width:100%; max-width:420px;
  box-shadow:0 24px 60px rgba(0,0,0,.18);
}
.login-logo{
  display:flex; align-items:center; justify-content:center; gap:.7rem;
  margin-bottom:1.6rem;
}
.login-logo-icon{
  width:52px; height:52px; border-radius:16px;
  background:linear-gradient(135deg,#2e7d32,#66bb6a);
  display:flex; align-items:center; justify-content:center;
  font-size:1.6rem;
}
.login-logo-text h2{ margin:0; color:#1b5e20; font-size:1.5rem; font-weight:800; }
.login-logo-text p { margin:0; color:#5f6f63; font-size:.82rem; }
.login-title{ text-align:center; color:#1f2d27!important; font-size:1.15rem!important;
  font-weight:700!important; margin-bottom:.2rem!important; }
.login-sub{ text-align:center; color:#5f6f63; font-size:.88rem; margin-bottom:1.4rem; }
.login-err{
  background:#fdecea; border:1px solid #f5c6cb; border-radius:10px;
  padding:.6rem 1rem; color:#c0392b; font-size:.88rem; margin-bottom:.8rem;
  display:flex; align-items:center; gap:.5rem;
}
.login-hint{
  background:#f1f8e9; border:1px solid #c8e6c9; border-radius:10px;
  padding:.6rem 1rem; color:#2e7d32; font-size:.82rem; margin-top:.9rem;
}
.login-hint b{ display:block; margin-bottom:.3rem; color:#1b5e20; }
.login-cred{ display:flex; gap:1rem; flex-wrap:wrap; }
.login-cred span{
  background:#e8f5e9; border-radius:7px; padding:.2rem .6rem;
  font-family:monospace; font-size:.8rem; color:#1b5e20;
}
/* hide default Streamlit chrome on login */
.login-page section[data-testid="stSidebar"]{ display:none!important; }
.login-page header[data-testid="stHeader"]{ display:none!important; }

/* ── sidebar ── */
section[data-testid="stSidebar"]{
  background:linear-gradient(180deg,#ffffff,#eef5ea); border-right:1px solid var(--line);
}
section[data-testid="stSidebar"] .stMarkdown h5{ color:var(--green-d); }

/* ── hero ── */
.ag-hero{
  position:relative; border-radius:20px; overflow:hidden;
  background:linear-gradient(135deg,#1b5e20 0%,#2e7d32 48%,#43a047 100%);
  color:#fff; padding:1.5rem 1.7rem; margin-bottom:.7rem;
}
.ag-hero::after{
  content:""; position:absolute; right:-50px; top:-60px; width:200px; height:200px;
  background:radial-gradient(circle, rgba(255,255,255,.14), transparent 70%);
}
.ag-hero h1{ color:#fff; font-size:2rem; margin:0; font-weight:800; }
.ag-hero p{ color:#e9f5ea; margin:.45rem 0 0; font-size:1.02rem; }
.ag-stats{ display:flex; gap:.5rem; margin-top:1rem; flex-wrap:wrap; }
.ag-stat{
  background:rgba(255,255,255,.16); border:1px solid rgba(255,255,255,.22);
  border-radius:10px; padding:.35rem .7rem; font-size:.78rem; color:#fff;
}

/* ── badges ── */
.ag-badge{
  display:inline-flex; align-items:center; gap:.3rem; padding:.22rem .62rem;
  border-radius:999px; font-size:.74rem; font-weight:700; margin:.14rem .3rem 0 0;
}
.ag-ok  { background:#d7f0d9; color:#1b5e20; }
.ag-warn{ background:#fff4d6; color:#7a5b00; }
.ag-role-admin { background:#e3f2fd; color:#0d47a1; }
.ag-role-viewer{ background:#f3e5f5; color:#6a1b9a; }

/* ── feature cards ── */
.ag-feature{
  background:var(--card); border:1px solid var(--line); border-radius:16px;
  padding:1.15rem 1.25rem; height:100%; margin-bottom:.4rem;
  transition:transform .16s ease, box-shadow .16s ease;
}
.ag-feature:hover{ transform:translateY(-3px); box-shadow:0 10px 24px rgba(27,94,32,.12); }
.ag-ico{
  width:44px; height:44px; border-radius:13px; font-size:1.35rem;
  display:flex; align-items:center; justify-content:center; margin-bottom:.7rem;
  background:linear-gradient(135deg,#e8f5e9,#c8e6c9);
}
.ag-ft{ font-weight:800; font-size:1.04rem; color:#1b5e20; }
.ag-fd{ color:var(--muted); font-size:.88rem; margin:.32rem 0 .6rem; line-height:1.45; }

/* ── result card ── */
.ag-result{
  background:linear-gradient(135deg,#eaf6ec,#f4faf0); border:1px solid #c8e6c9;
  border-radius:16px; padding:1.25rem 1.45rem; margin-top:.5rem;
}
.ag-big { font-size:1.7rem; font-weight:800; color:var(--green-d); line-height:1.2; }
.ag-conf{ font-weight:700; color:var(--green); margin-top:.25rem; }

/* ── confidence bars ── */
.ag-bars{ margin-top:.7rem; }
.ag-bar-row{
  display:grid; grid-template-columns:1.7fr 5fr .8fr;
  align-items:center; gap:.7rem; padding:.3rem 0;
}
.ag-bar-label{ font-size:.83rem; color:var(--ink); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.ag-bar-track{ background:#eef2ec; border-radius:999px; height:.72rem; overflow:hidden; }
.ag-bar-fill{
  height:100%; border-radius:999px;
  background:linear-gradient(90deg,#9ccc9e,#2e7d32); transition:width .7s ease;
}
.ag-bar-val{ font-size:.78rem; color:var(--muted); text-align:right; }

/* ── callout ── */
.ag-callout{
  border-left:4px solid var(--green); background:#f1f6ee;
  border-radius:0 12px 12px 0; padding:.75rem 1rem; color:#243027; margin-top:.6rem;
}

/* ── metrics / buttons / widgets ── */
[data-testid="stMetric"]{
  background:var(--card); border:1px solid var(--line);
  border-radius:13px; padding:.55rem .85rem; box-shadow:0 1px 2px rgba(0,0,0,.04);
}
[data-testid="stMetricValue"]{ color:var(--green); }
.stButton button{ border-radius:11px; font-weight:700; }
div[data-testid="stVerticalBlockBorderWrapper"]{
  border-radius:15px!important; border-color:var(--line)!important;
  box-shadow:0 1px 3px rgba(0,0,0,.05);
}
[data-testid="stFileUploaderDropzone"]{
  border:2px dashed #bfe0c2; background:#f3faf4; border-radius:14px;
}
[data-testid="stFileUploaderDropzone"]:hover{ border-color:var(--green); background:#eaf6ec; }

/* ── user mgmt table ── */
.user-row{
  display:grid; grid-template-columns:1fr 1fr 1fr auto;
  gap:.6rem; align-items:center; padding:.55rem .8rem;
  border-bottom:1px solid var(--line);
}
.user-row:last-child{ border-bottom:none; }
.user-row:nth-child(even){ background:#f8fbf7; }

/* ── footer ── */
.ag-foot{
  color:var(--muted); font-size:.78rem; margin-top:1.7rem;
  border-top:1px solid var(--line); padding-top:.75rem; line-height:1.5;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
#  AUTH HELPERS
# ═══════════════════════════════════════════════════════════════════
def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def load_users() -> dict:
    if USERS_FILE.exists():
        return json.loads(USERS_FILE.read_text())
    return {}


def save_users(users: dict):
    USERS_FILE.write_text(json.dumps(users, indent=2))


def verify(username: str, password: str):
    users = load_users()
    u = users.get(username)
    if u and u["password"] == _hash(password):
        return u
    return None


# ═══════════════════════════════════════════════════════════════════
#  LOGIN PAGE
# ═══════════════════════════════════════════════════════════════════
def show_login():
    # Hide sidebar completely on login screen via JS class injection
    st.markdown('<style>section[data-testid="stSidebar"]{display:none!important}'
                'header[data-testid="stHeader"]{display:none!important}</style>',
                unsafe_allow_html=True)

    # Centre the card using columns
    _, col, _ = st.columns([1, 1.1, 1])
    with col:
        st.markdown("""
        <div class="login-card">
          <div class="login-logo">
            <div class="login-logo-icon">🌱</div>
            <div class="login-logo-text">
              <h2>AgriSmart AI</h2>
              <p>Decision support for farms</p>
            </div>
          </div>
          <p class="login-title">Welcome back</p>
          <p class="login-sub">Sign in to access the platform</p>
        </div>
        """, unsafe_allow_html=True)

        # Error from previous attempt
        if st.session_state.get("login_error"):
            st.markdown(
                f'<div class="login-err">❌ &nbsp;{st.session_state.login_error}</div>',
                unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("👤  Username", placeholder="Enter your username")
            password = st.text_input("🔒  Password", type="password",
                                     placeholder="Enter your password")
            submitted = st.form_submit_button("Sign In →", type="primary",
                                              use_container_width=True)

        if submitted:
            if not username or not password:
                st.session_state.login_error = "Please enter both username and password."
                st.rerun()
            else:
                user = verify(username.strip(), password)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.username      = username.strip()
                    st.session_state.user_name     = user["name"]
                    st.session_state.user_role     = user["role"]
                    st.session_state.login_error   = ""
                    st.rerun()
                else:
                    st.session_state.login_error = "Invalid username or password."
                    st.rerun()

        st.markdown("""
        <div class="login-hint">
          <b>Demo credentials</b>
          <div class="login-cred">
            <span>admin / admin123</span>
            <span>farmer / farmer123</span>
            <span>demo / demo123</span>
          </div>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
#  HELPERS (shared across all app pages)
# ═══════════════════════════════════════════════════════════════════
def render(html):
    st.markdown(html, unsafe_allow_html=True)


def badge(label, kind):
    return f'<span class="ag-badge ag-{kind}">{label}</span>'


def conf_bars(items):
    rows = ""
    for label, p in items:
        pct = max(0.0, min(1.0, float(p))) * 100
        rows += (f'<div class="ag-bar-row">'
                 f'<div class="ag-bar-label">{label}</div>'
                 f'<div class="ag-bar-track">'
                 f'<div class="ag-bar-fill" style="width:{pct:.1f}%"></div></div>'
                 f'<div class="ag-bar-val">{pct:.1f}%</div></div>')
    return '<div class="ag-bars">' + rows + "</div>"


def pretty_disease(name):
    if "___" in name:
        plant, cond = name.split("___", 1)
        return f"{plant.replace('_',' ')} — {cond.replace('_',' ')}"
    return name.replace("_", " ")


def feature_card(icon, title, desc, ok):
    pill = badge("✓ Trained" if ok else "Not trained", "ok" if ok else "warn")
    return (f'<div class="ag-feature"><div class="ag-ico">{icon}</div>'
            f'<div class="ag-ft">{title}</div>'
            f'<div class="ag-fd">{desc}</div>{pill}</div>')


def statuses():
    return {
        "Crop Recommendation":    (MODELS / "crop_recommender.joblib").exists(),
        "Crop Yield Prediction":  (MODELS / "yield_regressor.joblib").exists(),
        "Plant Disease Detection":(MODELS / "disease_classifier.joblib").exists()
                                   and (MODELS / "disease_classes.json").exists(),
    }


@st.cache_resource
def load_model(file):
    p = MODELS / file
    return joblib.load(p) if p.exists() else None


@st.cache_resource
def load_disease():
    p  = MODELS / "disease_classifier.joblib"
    cp = MODELS / "disease_classes.json"
    if not p.exists() or not cp.exists():
        return None, None
    return joblib.load(p), json.loads(cp.read_text())


def load_report(name):
    p = REPORTS / name
    try:
        return json.loads(p.read_text()) if p.exists() else None
    except Exception:
        return None


def footer():
    render('<div class="ag-foot">🌱 AgriSmart AI — research prototype. Predictions are '
           "estimates, not agronomic guarantees. Always confirm decisions with local "
           "agronomy experts and field measurements.</div>")


# ═══════════════════════════════════════════════════════════════════
#  AUTH GATE
# ═══════════════════════════════════════════════════════════════════
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "login_error" not in st.session_state:
    st.session_state.login_error = ""

if not st.session_state.authenticated:
    show_login()
    st.stop()


# ═══════════════════════════════════════════════════════════════════
#  SIDEBAR  (only shown after login)
# ═══════════════════════════════════════════════════════════════════
STATUS = statuses()
role   = st.session_state.user_role

# branding
st.sidebar.markdown(
    '<div style="display:flex;align-items:center;gap:.6rem;padding:.2rem 0">'
    '<div style="width:40px;height:40px;border-radius:12px;display:flex;align-items:center;'
    'justify-content:center;font-size:1.3rem;background:linear-gradient(135deg,#2e7d32,#66bb6a)">🌱</div>'
    '<div><div style="font-weight:800;color:#1b5e20;font-size:1.12rem">AgriSmart AI</div>'
    '<div style="font-size:.72rem;color:#5f6f63">Decision support for farms</div></div></div>',
    unsafe_allow_html=True)

# logged-in user pill
role_kind = "role-admin" if role == "admin" else "role-viewer"
st.sidebar.markdown(
    f'<div style="margin:.5rem 0 .3rem">'
    f'<span style="font-size:.8rem;color:#5f6f63">Signed in as </span>'
    f'<b style="color:#1b5e20">{st.session_state.user_name}</b> &nbsp;'
    f'{badge(role.upper(), role_kind)}</div>',
    unsafe_allow_html=True)

st.sidebar.divider()

nav_options = ["Overview", "Crop Recommendation",
               "Crop Yield Prediction", "Plant Disease Detection", "Model Evaluation"]
if role == "admin":
    nav_options.append("User Management")

page = st.sidebar.radio("Navigate", nav_options)

st.sidebar.divider()
st.sidebar.markdown("##### Model status")
for name, ok in STATUS.items():
    st.sidebar.markdown(badge(("✓ " if ok else "○ ") + name, "ok" if ok else "warn"),
                        unsafe_allow_html=True)
st.sidebar.divider()
st.sidebar.caption("Research prototype · not a substitute for expert advice.")

# logout
if st.sidebar.button("🚪  Sign Out", use_container_width=True):
    for key in ["authenticated", "username", "user_name", "user_role", "login_error"]:
        st.session_state.pop(key, None)
    st.rerun()


# ═══════════════════════════════════════════════════════════════════
#  HERO BANNER
# ═══════════════════════════════════════════════════════════════════
trained = sum(STATUS.values())
render(
    '<div class="ag-hero"><h1>🌱 AgriSmart AI</h1>'
    "<p>Explainable ML decision support for sustainable agriculture — recommend crops, "
    "estimate yields and detect plant disease.</p>"
    f'<div class="ag-stats">'
    f'<span class="ag-stat">3 modules</span>'
    f'<span class="ag-stat">{trained}/3 models trained</span>'
    f'<span class="ag-stat">Hello, {st.session_state.user_name} 👋</span>'
    f'</div></div>'
)


# ═══════════════════════════════════════════════════════════════════
#  PAGE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════
def overview():
    st.subheader("Platform overview")
    st.caption("Three independently trained ML models for smarter farm decisions.")
    cols = st.columns(3)
    cards = [
        ("🌾","Crop Recommendation","Soil nutrients and climate → best crop to plant.","Crop Recommendation"),
        ("📈","Crop Yield Prediction","Region, crop, year and environment → estimated yield.","Crop Yield Prediction"),
        ("🍃","Plant Disease Detection","Upload a leaf image → predicted disease class.","Plant Disease Detection"),
    ]
    for col,(icon,title,desc,key) in zip(cols,cards):
        col.markdown(feature_card(icon,title,desc,STATUS[key]),unsafe_allow_html=True)
    st.write("")
    a,b,c = st.columns(3)
    a.metric("Applications",3)
    b.metric("Model types","Classical ML + Image")
    c.metric("Interface","Streamlit")
    render('<div class="ag-callout"><b>How it works:</b> each module is an independently '
           "trained ML model. Crop recommendation and yield estimation use scikit-learn on "
           "tabular data; disease detection classifies leaf images. Outputs are research-grade "
           "estimates — confirm with local experts before acting.</div>")


def crop_page():
    model = load_model("crop_recommender.joblib")
    st.subheader("🌾 Crop Recommendation")
    st.caption("Enter soil test results and local climate values to recommend a suitable crop.")
    if model is None:
        st.warning("Crop model not trained. Run: `python src/train_crop.py`"); return
    specs = [("N","Nitrogen",0,200,90),("P","Phosphorus",0,200,42),("K","Potassium",0,250,43),
             ("temperature","Temperature °C",-5,55,25),("humidity","Humidity %",0,100,80),
             ("ph","Soil pH",0,14,6.5),("rainfall","Rainfall mm",0,5000,100)]
    vals = {}
    with st.container(border=True):
        render('<div style="font-weight:700;color:#1b5e20;margin-bottom:.6rem">🧪 Soil &amp; climate inputs</div>')
        cols = st.columns(4)
        for i,(key,label,lo,hi,default) in enumerate(specs):
            with cols[i%4]:
                vals[key]=st.number_input(label,min_value=float(lo),max_value=float(hi),
                                          value=float(default),key=f"crop_{key}")
    if st.button("🌱 Recommend crop",type="primary"):
        x = pd.DataFrame([vals])
        pred = model.predict(x)[0]
        render(f'<div class="ag-result"><div class="ag-big">Recommended: {pred}</div>'
               "<div style='color:#5f6f63;margin:.35rem 0 0'>Best crop for this soil and climate profile.</div></div>")
        if hasattr(model,"predict_proba"):
            probs = model.predict_proba(x)[0]; idx = np.argsort(probs)[::-1][:5]
            render("<b>Top-5 model probabilities</b>")
            render(conf_bars([(model.classes_[i],probs[i]) for i in idx]))
            st.caption("Probabilities reflect model confidence, not guarantees of farm suitability.")
    with st.expander("About this model"):
        rep = load_report("crop_metrics.json")
        if rep: render(f"Selected model: <b>{rep.get('winner')}</b>"); st.json(rep.get("models",{}).get(rep.get("winner"),{}))
        else: st.caption("Report not generated.")


def yield_page():
    model = load_model("yield_regressor.joblib")
    st.subheader("📈 Crop Yield Prediction")
    st.caption("Estimate crop yield from region, crop, year and environmental variables.")
    if model is None:
        with st.container(border=True):
            st.warning("Yield model not trained.")
            st.markdown("1. Download [crop-yield-prediction-dataset](https://www.kaggle.com/datasets/patelris/crop-yield-prediction-dataset)")
            st.markdown("2. Place at `data/yield/crop_yield.csv`")
            st.markdown("3. Run `python src/train_yield.py`")
        return
    c1,c2 = st.columns(2)
    area = c1.text_input("Country / Area","India")
    crop = c2.text_input("Crop / Item","Wheat")
    c3,c4,c5 = st.columns(3)
    year = c3.number_input("Year",1961,2100,2010)
    rain = c4.number_input("Average annual rainfall (mm)",0.,10000.,1083.)
    pesticides = c5.number_input("Pesticides (tonnes)",0.,1e9,55000.)
    temp = st.number_input("Average temperature (°C)",-10.,60.,24.)
    if st.button("📈 Predict yield",type="primary"):
        row = pd.DataFrame([{"Area":area,"Item":crop,"Year":year,
                              "average_rain_fall_mm_per_year":rain,
                              "pesticides_tonnes":pesticides,"avg_temp":temp}])
        val = float(model.predict(row)[0])
        render(f'<div class="ag-result"><div class="ag-big">{val:,.2f} hg/ha</div>'
               "<div style='color:#5f6f63;margin:.3rem 0 0'>Estimated yield for the given inputs.</div></div>")
        st.caption("Predictions outside the model's observed geography/time range may be unreliable.")
    with st.expander("About this model"):
        rep = load_report("yield_metrics.json")
        if rep: render(f"Selected model: <b>{rep.get('winner')}</b>"); st.json(rep.get("models",{}).get(rep.get("winner"),{}))
        else: st.caption("Report not generated.")


def disease_page():
    model,classes = load_disease()
    st.subheader("🍃 Plant Disease Detection")
    st.caption("Upload a clear leaf photo to classify the disease (Tomato classes from PlantVillage).")
    if model is None:
        st.warning("Disease model not trained. Run: `python src/train_disease.py`"); return
    upload = st.file_uploader("Upload a clear leaf image",type=["jpg","jpeg","png"])
    if upload:
        image = Image.open(upload).convert("RGB")
        c1,c2 = st.columns([1,2])
        with c1: st.image(image,caption="Uploaded leaf",width="stretch")
        with c2:
            render('<div class="ag-callout"><b>Tips for a reliable prediction:</b>'
                   "<br>• Use a single, well-lit leaf on a plain background."
                   "<br>• Avoid blur and large background clutter."
                   "<br>• This model recognises Tomato leaf conditions only.</div>")
        if st.button("🔬 Analyze leaf",type="primary"):
            with st.spinner("Analyzing…"):
                probs = model.predict_proba(extract_features(image).reshape(1,-1))[0]
                idx = int(np.argmax(probs))
            render(f'<div class="ag-result"><div class="ag-big">{pretty_disease(classes[idx])}</div>'
                   f'<div class="ag-conf">Model confidence: {probs[idx]*100:.1f}%</div></div>')
            top = np.argsort(probs)[::-1][:5]
            render("<b>Top-5 predictions</b>")
            render(conf_bars([(pretty_disease(classes[i]),probs[i]) for i in top]))
            with st.expander("All classes & disclaimer"):
                render(" • ".join(pretty_disease(c) for c in classes))
                st.warning("Not a confirmed diagnosis or prescription. Confirm with an expert.")
    with st.expander("About this model"):
        rep = load_report("disease_metrics.json")
        if rep: render(f"Selected model: <b>{rep.get('winner')}</b> · classes: {len(rep.get('classes',[]))}")
        else: st.caption("Report not generated.")


def eval_page():
    st.subheader("📊 Model Evaluation")
    st.caption("Actual metrics recorded from completed training runs.")
    items = [("crop_metrics.json","Crop Recommendation"),
             ("yield_metrics.json","Crop Yield"),
             ("disease_metrics.json","Plant Disease")]
    summary_keys = ("cv_accuracy","cv_f1_macro","test_accuracy","test_f1_macro",
                    "MAE","RMSE","R2","WAPE_percent")
    for fn,label in items:
        rep = load_report(fn)
        with st.expander(f"{label} — {fn}",expanded=False):
            if rep is None: st.caption("Not generated yet."); continue
            winner = rep.get("winner")
            if winner: render(f"Selected model: <b>{winner}</b>")
            models = rep.get("models",{})
            rows = {n:{k:round(v,4) if isinstance(v,(int,float)) else v
                       for k,v in m.items() if k in summary_keys}
                    for n,m in models.items()}
            if rows: st.dataframe(pd.DataFrame(rows).T,width="stretch")
            st.json(rep)


# ═══════════════════════════════════════════════════════════════════
#  USER MANAGEMENT  (admin only)
# ═══════════════════════════════════════════════════════════════════
def user_management_page():
    st.subheader("👥 User Management")
    st.caption("Admin-only: add, remove or change passwords for platform users.")

    users = load_users()

    # ── current users table ──────────────────────────────────────
    with st.container(border=True):
        render('<div style="font-weight:700;color:#1b5e20;margin-bottom:.8rem">Current users</div>')
        render('<div class="user-row" style="font-weight:700;color:#5f6f63;font-size:.82rem">'
               '<div>USERNAME</div><div>NAME</div><div>ROLE</div><div>ACTION</div></div>')
        for uname, udata in list(users.items()):
            col1, col2, col3, col4 = st.columns([1,1,1,1])
            col1.markdown(f"**{uname}**")
            col2.write(udata["name"])
            col3.markdown(badge(udata["role"].upper(),
                                "role-admin" if udata["role"]=="admin" else "role-viewer"),
                          unsafe_allow_html=True)
            with col4:
                if uname != st.session_state.username:          # can't delete yourself
                    if st.button("🗑 Remove", key=f"del_{uname}",
                                 help=f"Delete user {uname}"):
                        users.pop(uname)
                        save_users(users)
                        st.success(f"User '{uname}' removed.")
                        st.rerun()
                else:
                    st.caption("(you)")

    st.write("")

    # ── add new user ─────────────────────────────────────────────
    with st.container(border=True):
        render('<div style="font-weight:700;color:#1b5e20;margin-bottom:.8rem">➕ Add new user</div>')
        c1,c2,c3,c4 = st.columns(4)
        new_user = c1.text_input("Username",    key="nu_user",  placeholder="e.g. john")
        new_name = c2.text_input("Full name",   key="nu_name",  placeholder="e.g. John Smith")
        new_pass = c3.text_input("Password",    key="nu_pass",  type="password", placeholder="Min 6 chars")
        new_role = c4.selectbox("Role",         key="nu_role",  options=["viewer","admin"])
        if st.button("Add user", type="primary"):
            if not new_user or not new_name or not new_pass:
                st.error("All fields are required.")
            elif len(new_pass) < 6:
                st.error("Password must be at least 6 characters.")
            elif new_user in users:
                st.error(f"Username '{new_user}' already exists.")
            else:
                users[new_user] = {"password": _hash(new_pass),
                                   "role": new_role, "name": new_name}
                save_users(users)
                st.success(f"User '{new_user}' added as {new_role}.")
                st.rerun()

    st.write("")

    # ── change password ──────────────────────────────────────────
    with st.container(border=True):
        render('<div style="font-weight:700;color:#1b5e20;margin-bottom:.8rem">🔑 Change password</div>')
        d1,d2,d3 = st.columns(3)
        cp_user  = d1.selectbox("User",        key="cp_user", options=list(users.keys()))
        cp_pass  = d2.text_input("New password",key="cp_pass", type="password", placeholder="Min 6 chars")
        cp_pass2 = d3.text_input("Confirm",     key="cp_pass2",type="password", placeholder="Repeat password")
        if st.button("Update password"):
            if not cp_pass:
                st.error("Enter a new password.")
            elif len(cp_pass) < 6:
                st.error("Password must be at least 6 characters.")
            elif cp_pass != cp_pass2:
                st.error("Passwords do not match.")
            else:
                users[cp_user]["password"] = _hash(cp_pass)
                save_users(users)
                st.success(f"Password updated for '{cp_user}'.")


# ═══════════════════════════════════════════════════════════════════
#  DISPATCH
# ═══════════════════════════════════════════════════════════════════
if page == "Overview":
    overview()
elif page == "Crop Recommendation":
    crop_page()
elif page == "Crop Yield Prediction":
    yield_page()
elif page == "Plant Disease Detection":
    disease_page()
elif page == "Model Evaluation":
    eval_page()
elif page == "User Management":
    if role == "admin":
        user_management_page()
    else:
        st.error("Access denied. Admin role required.")

footer()
