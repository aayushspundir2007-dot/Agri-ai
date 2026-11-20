"""AgriSmart AI v2 — Streamlit UI (calls FastAPI backend)."""
import hashlib
import io
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

API = st.secrets.get("API_URL", "http://localhost:8000") if hasattr(st, "secrets") else "http://localhost:8000"
try:
    import os
    API = os.environ.get("STREAMLIT_API_URL", API)
except Exception:
    pass

st.set_page_config(page_title="AgriSmart AI v2", page_icon="🌱",
                   layout="wide", initial_sidebar_state="expanded")

# ═══════════════════════════════════════
#  CSS
# ═══════════════════════════════════════
st.markdown("""
<style>
:root{--green:#2e7d32;--green-d:#1b5e20;--green-l:#66bb6a;
  --bg:#f6f9f4;--card:#fff;--line:#e3e8e0;--ink:#1f2d27;--muted:#5f6f63;}
.stApp{background:var(--bg);}
h1,h2,h3,h4{color:var(--ink)!important;}
.ag-hero{background:linear-gradient(135deg,#1b5e20,#2e7d32,#43a047);
  color:#fff;border-radius:20px;padding:1.4rem 1.7rem;margin-bottom:.8rem;position:relative;overflow:hidden;}
.ag-hero h1{color:#fff;font-size:1.9rem;font-weight:800;margin:0;}
.ag-hero p{color:#e9f5ea;margin:.4rem 0 0;font-size:.98rem;}
.ag-stats{display:flex;gap:.5rem;margin-top:.9rem;flex-wrap:wrap;}
.ag-stat{background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.25);
  border-radius:10px;padding:.3rem .7rem;font-size:.78rem;color:#fff;}
.ag-result{background:linear-gradient(135deg,#eaf6ec,#f4faf0);border:1px solid #c8e6c9;
  border-radius:16px;padding:1.2rem 1.4rem;margin-top:.6rem;}
.ag-big{font-size:1.65rem;font-weight:800;color:var(--green-d);}
.ag-conf{font-weight:700;color:var(--green);margin-top:.2rem;}
.ag-badge{display:inline-flex;align-items:center;gap:.3rem;padding:.2rem .6rem;
  border-radius:999px;font-size:.74rem;font-weight:700;}
.ag-ok{background:#d7f0d9;color:#1b5e20;}
.ag-warn{background:#fff4d6;color:#7a5b00;}
.ag-callout{border-left:4px solid var(--green);background:#f1f6ee;
  border-radius:0 12px 12px 0;padding:.7rem 1rem;color:var(--ink);margin:.6rem 0;}
.ag-foot{color:var(--muted);font-size:.78rem;margin-top:1.6rem;
  border-top:1px solid var(--line);padding-top:.7rem;}
[data-testid="stMetric"]{background:#fff;border:1px solid var(--line);
  border-radius:13px;padding:.5rem .85rem;box-shadow:0 1px 2px rgba(0,0,0,.04);}
[data-testid="stMetricValue"]{color:var(--green);}
.stButton button{border-radius:11px;font-weight:700;}
/* login */
.login-wrap{display:flex;align-items:center;justify-content:center;min-height:60vh;}
.login-card{background:#fff;border-radius:24px;padding:2.4rem 2.2rem 1.8rem;
  box-shadow:0 20px 50px rgba(0,0,0,.14);width:100%;max-width:400px;}
</style>
""", unsafe_allow_html=True)

def r(html): st.markdown(html, unsafe_allow_html=True)

# ═══════════════════════════════════════
#  API helpers
# ═══════════════════════════════════════
def api_post(path, data=None, files=None, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        resp = requests.post(f"{API}{path}", json=data, files=files,
                             headers=headers, timeout=15)
        return resp
    except requests.exceptions.ConnectionError:
        return None

def api_get(path, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        return requests.get(f"{API}{path}", headers=headers, timeout=10)
    except requests.exceptions.ConnectionError:
        return None

def api_online():
    r = api_get("/api/health")
    return r is not None and r.status_code == 200

# ═══════════════════════════════════════
#  Session init
# ═══════════════════════════════════════
for k, v in [("authenticated", False), ("token", None), ("username", None),
              ("user_name", None), ("user_role", None), ("login_error", ""),
              ("history", []), ("dark_mode", False)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ═══════════════════════════════════════
#  LOGIN
# ═══════════════════════════════════════
def show_login():
    st.markdown('<style>section[data-testid="stSidebar"]{display:none!important}'
                'header[data-testid="stHeader"]{display:none!important}</style>',
                unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.1, 1])
    with col:
        r("""<div class="login-card">
          <div style="display:flex;align-items:center;gap:.7rem;margin-bottom:1.4rem;justify-content:center">
            <div style="width:50px;height:50px;border-radius:14px;background:linear-gradient(135deg,#2e7d32,#66bb6a);
              display:flex;align-items:center;justify-content:center;font-size:1.5rem">🌱</div>
            <div><div style="font-weight:800;color:#1b5e20;font-size:1.3rem">AgriSmart AI</div>
            <div style="font-size:.78rem;color:#5f6f63">v2.0 · Decision support for farms</div></div>
          </div>
          <p style="text-align:center;font-weight:700;font-size:1.1rem;margin-bottom:.2rem">Welcome back</p>
          <p style="text-align:center;color:#5f6f63;font-size:.87rem;margin-bottom:1.2rem">Sign in to access the platform</p>
        </div>""")

        online = api_online()
        if not online:
            st.warning("⚠️ API server offline. Start it with: `python -m uvicorn app.main:app --port 8000`")

        if st.session_state.login_error:
            r(f'<div style="background:#fdecea;border:1px solid #f5c6cb;border-radius:10px;'
              f'padding:.6rem 1rem;color:#c0392b;font-size:.88rem;margin-bottom:.7rem">'
              f'❌ {st.session_state.login_error}</div>')

        with st.form("login_form"):
            username = st.text_input("👤 Username", placeholder="Enter your username")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Sign In →", type="primary", use_container_width=True)

        if submitted:
            if not username or not password:
                st.session_state.login_error = "Please enter both username and password."
                st.rerun()
            else:
                resp = api_post("/api/auth/login",
                                data={"username": username.strip(), "password": password})
                if resp is None:
                    st.session_state.login_error = "Cannot reach API server. Is it running?"
                elif resp.status_code == 200:
                    d = resp.json()
                    st.session_state.update({
                        "authenticated": True, "token": d["access_token"],
                        "username": username.strip(), "user_name": d["name"],
                        "user_role": d["role"], "login_error": "",
                    })
                    st.rerun()
                else:
                    st.session_state.login_error = "Invalid username or password."
                    st.rerun()

        r("""<div style="background:#f1f8e9;border:1px solid #c8e6c9;border-radius:10px;
          padding:.65rem .9rem;color:#2e7d32;font-size:.82rem;margin-top:.9rem">
          <b style="display:block;margin-bottom:.3rem;color:#1b5e20">Demo credentials</b>
          <span style="font-family:monospace;background:#e8f5e9;padding:.15rem .5rem;border-radius:6px;margin-right:.4rem">admin / admin123</span>
          <span style="font-family:monospace;background:#e8f5e9;padding:.15rem .5rem;border-radius:6px;margin-right:.4rem">farmer / farmer123</span>
          <span style="font-family:monospace;background:#e8f5e9;padding:.15rem .5rem;border-radius:6px">demo / demo123</span>
        </div>""")

# ═══════════════════════════════════════
#  AUTH GATE
# ═══════════════════════════════════════
if not st.session_state.authenticated:
    show_login()
    st.stop()

token = st.session_state.token
role  = st.session_state.user_role

# ═══════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════
st.sidebar.markdown(
    f'<div style="display:flex;align-items:center;gap:.6rem;padding:.2rem 0">'
    f'<div style="width:40px;height:40px;border-radius:12px;background:linear-gradient(135deg,#2e7d32,#66bb6a);'
    f'display:flex;align-items:center;justify-content:center;font-size:1.3rem">🌱</div>'
    f'<div><div style="font-weight:800;color:#1b5e20;font-size:1.1rem">AgriSmart AI</div>'
    f'<div style="font-size:.7rem;color:#5f6f63">v2.0 · Decision support</div></div></div>',
    unsafe_allow_html=True)

role_col = "#0d47a1" if role == "admin" else "#6a1b9a"
role_bg  = "#e3f2fd" if role == "admin" else "#f3e5f5"
st.sidebar.markdown(
    f'<div style="margin:.5rem 0 .3rem;font-size:.82rem;color:#5f6f63">Signed in as '
    f'<b style="color:#1b5e20">{st.session_state.user_name}</b> &nbsp;'
    f'<span style="background:{role_bg};color:{role_col};border-radius:999px;'
    f'padding:.15rem .55rem;font-size:.72rem;font-weight:700">{role.upper()}</span></div>',
    unsafe_allow_html=True)

st.sidebar.divider()

nav_opts = ["Overview","Crop Recommendation","Crop Yield Prediction",
            "Plant Disease Detection","Model Evaluation","Analytics & Drift"]
if role == "admin":
    nav_opts.append("User Management")

page = st.sidebar.radio("Navigate", nav_opts)

# API status indicator
health = api_get("/api/health")
api_ok = health is not None and health.status_code == 200
st.sidebar.divider()
st.sidebar.markdown(
    f'<span class="ag-badge {"ag-ok" if api_ok else "ag-warn"}">'
    f'{"✓ API online" if api_ok else "○ API offline"}</span>',
    unsafe_allow_html=True)

if api_ok:
    hdata = health.json()
    for mod, ok in hdata.get("models_loaded",{}).items():
        st.sidebar.markdown(
            f'<span class="ag-badge {"ag-ok" if ok else "ag-warn"}">'
            f'{"✓" if ok else "○"} {mod.capitalize()}</span>',
            unsafe_allow_html=True)

st.sidebar.divider()
st.sidebar.caption("Research prototype · not agronomic advice.")
if st.sidebar.button("🚪 Sign Out", use_container_width=True):
    for k in ["authenticated","token","username","user_name","user_role","login_error","history"]:
        st.session_state.pop(k, None)
    st.rerun()

# ═══════════════════════════════════════
#  HERO
# ═══════════════════════════════════════
trained = sum(hdata.get("models_loaded",{}).values()) if api_ok else 0
r(f'<div class="ag-hero"><h1>🌱 AgriSmart AI</h1>'
  f'<p>Explainable ML decision support — crop recommendation, yield estimation &amp; disease detection.</p>'
  f'<div class="ag-stats"><span class="ag-stat">3 modules</span>'
  f'<span class="ag-stat">{trained}/3 models loaded</span>'
  f'<span class="ag-stat">Hello, {st.session_state.user_name} 👋</span>'
  f'<span class="ag-stat">{"🟢 API online" if api_ok else "🔴 API offline"}</span>'
  f'</div></div>')

def add_history(module, inputs, result):
    st.session_state.history.insert(0, {
        "time": datetime.now().strftime("%H:%M:%S"),
        "module": module, "inputs": str(inputs)[:60], "result": str(result)[:80]
    })
    st.session_state.history = st.session_state.history[:10]

def show_history():
    if st.session_state.history:
        with st.expander("📋 Prediction history (this session)", expanded=False):
            df = pd.DataFrame(st.session_state.history)
            st.dataframe(df, use_container_width=True, hide_index=True)
            csv = df.to_csv(index=False)
            st.download_button("⬇️ Download CSV", csv, "predictions.csv",
                               "text/csv", use_container_width=True)

# ═══════════════════════════════════════
#  PAGES
# ═══════════════════════════════════════
if page == "Overview":
    st.subheader("Platform overview")
    st.caption("Three independently trained ML models for smarter farm decisions.")
    c1, c2, c3 = st.columns(3)
    for col, icon, title, desc, mod in [
        (c1,"🌾","Crop Recommendation","Soil & climate → best crop to plant.","crop"),
        (c2,"📈","Crop Yield Prediction","Region, year & env → estimated yield.","yield"),
        (c3,"🍃","Disease Detection","Leaf image → disease class.","disease"),
    ]:
        ok = hdata.get("models_loaded",{}).get(mod, False) if api_ok else False
        with col:
            with st.container(border=True):
                st.markdown(f"#### {icon} {title}")
                st.caption(desc)
                r(f'<span class="ag-badge {"ag-ok" if ok else "ag-warn"}">{"✓ Trained" if ok else "Not loaded"}</span>')
    st.write("")
    a, b, c = st.columns(3)
    a.metric("Applications", 3)
    b.metric("API version", "v2.0")
    c.metric("Uptime (s)", hdata.get("uptime_seconds","—") if api_ok else "—")
    r('<div class="ag-callout"><b>v2.0:</b> now backed by a FastAPI REST API with JWT auth. '
      'All predictions are made via <code>/api/predict/*</code> endpoints.</div>')

elif page == "Crop Recommendation":
    st.subheader("🌾 Crop Recommendation")
    st.caption("Soil nutrients and climate → best crop to plant.")
    specs = [("N","Nitrogen",0,200,90),("P","Phosphorus",0,200,42),("K","Potassium",0,250,43),
             ("temperature","Temperature °C",-5,55,25),("humidity","Humidity %",0,100,80),
             ("ph","Soil pH",0,14,6.5),("rainfall","Rainfall mm",0,5000,100)]
    vals = {}
    with st.container(border=True):
        r('<div style="font-weight:700;color:#1b5e20;margin-bottom:.6rem">🧪 Soil &amp; climate inputs</div>')
        cols = st.columns(4)
        for i,(key,label,lo,hi,default) in enumerate(specs):
            with cols[i%4]:
                vals[key] = st.number_input(label, min_value=float(lo), max_value=float(hi),
                                             value=float(default), key=f"crop_{key}")

    # Gauge chart for soil health
    with st.expander("🌡️ Soil health gauge", expanded=False):
        ph_val = vals["ph"]
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=ph_val,
            title={"text": "Soil pH", "font": {"size": 16}},
            gauge={"axis": {"range":[0,14]},
                   "steps":[{"range":[0,5.5],"color":"#ffcdd2"},
                             {"range":[5.5,7.5],"color":"#c8e6c9"},
                             {"range":[7.5,14],"color":"#fff9c4"}],
                   "bar":{"color":"#2e7d32"}}))
        fig.update_layout(height=250, margin=dict(t=30,b=10,l=10,r=10))
        st.plotly_chart(fig, use_container_width=True)

    if st.button("🌱 Recommend Crop", type="primary"):
        with st.spinner("Calling API…"):
            resp = api_post("/api/predict/crop", data=vals, token=token)
        if resp is None:
            st.error("API offline. Start with: `python -m uvicorn app.main:app --port 8000`")
        elif resp.status_code == 200:
            d = resp.json()
            r(f'<div class="ag-result"><div class="ag-big">Recommended: {d["crop"]}</div>'
              f'<div style="color:#5f6f63;margin:.3rem 0 0">Best crop for this soil and climate profile.</div></div>')
            if d.get("probabilities"):
                probs = d["probabilities"]
                fig = px.bar(x=list(probs.keys()), y=list(probs.values()),
                             labels={"x":"Crop","y":"Probability"},
                             color_discrete_sequence=["#2e7d32"])
                fig.update_layout(title="Top-5 Crop Probabilities",
                                  height=300, margin=dict(t=40,b=20,l=10,r=10))
                st.plotly_chart(fig, use_container_width=True)
            add_history("Crop", vals, d["crop"])
        else:
            st.error(f"API error {resp.status_code}: {resp.text}")
    show_history()

elif page == "Crop Yield Prediction":
    st.subheader("📈 Crop Yield Prediction")
    st.caption("Region, crop, year and environment → estimated yield (hg/ha).")
    c1, c2 = st.columns(2)
    area = c1.text_input("Country / Area", "India")
    item = c2.text_input("Crop / Item", "Wheat")
    c3, c4, c5 = st.columns(3)
    year        = c3.number_input("Year", 1961, 2100, 2010)
    rainfall    = c4.number_input("Avg annual rainfall (mm)", 0.0, 10000.0, 1083.0)
    pesticides  = c5.number_input("Pesticides (tonnes)", 0.0, 1e9, 55000.0)
    temperature = st.number_input("Average temperature (°C)", -10.0, 60.0, 24.0)

    if st.button("📈 Predict Yield", type="primary"):
        payload = {"area": area, "item": item, "year": int(year),
                   "rainfall": rainfall, "pesticides": pesticides,
                   "temperature": temperature}
        with st.spinner("Calling API…"):
            resp = api_post("/api/predict/yield", data=payload, token=token)
        if resp is None:
            st.error("API offline.")
        elif resp.status_code == 200:
            d = resp.json()
            val = d["yield_hgha"]
            r(f'<div class="ag-result"><div class="ag-big">{val:,.2f} hg/ha</div>'
              f'<div style="color:#5f6f63;margin:.3rem 0 0">Estimated yield for {item} in {area}, {year}.</div></div>')

            # Historical comparison bar
            hist_avg = {"Wheat":28000,"Rice, paddy":35000,"Maize":40000,
                        "Potatoes":180000,"Soybeans":25000}
            avg = hist_avg.get(item, 30000)
            fig = px.bar(x=["Predicted", "Dataset average"],
                         y=[val, avg], color=["Predicted","Average"],
                         color_discrete_map={"Predicted":"#2e7d32","Average":"#90a4ae"},
                         labels={"x":"","y":"hg/ha"})
            fig.update_layout(title="Predicted vs Dataset Average",
                              height=280, margin=dict(t=40,b=10,l=10,r=10), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            add_history("Yield", f"{area}/{item}/{year}", f"{val:,.0f} hg/ha")
        else:
            st.error(f"API error {resp.status_code}: {resp.text}")
    show_history()

elif page == "Plant Disease Detection":
    st.subheader("🍃 Plant Disease Detection")
    st.caption("Upload a clear leaf photo (Tomato classes from PlantVillage).")
    upload = st.file_uploader("Upload leaf image", type=["jpg","jpeg","png"])
    if upload:
        image = Image.open(upload).convert("RGB")
        c1, c2 = st.columns([1,2])
        with c1:
            st.image(image, caption="Uploaded leaf", use_container_width=True)
        with c2:
            r('<div class="ag-callout"><b>Tips:</b> single well-lit leaf, plain background, '
              'no blur. Tomato classes only.</div>')
        if st.button("🔬 Analyze Leaf", type="primary"):
            buf = io.BytesIO(); image.save(buf, format="JPEG"); buf.seek(0)
            with st.spinner("Analyzing…"):
                resp = api_post("/api/predict/disease",
                                files={"file": ("leaf.jpg", buf, "image/jpeg")}, token=token)
            if resp is None:
                st.error("API offline.")
            elif resp.status_code == 200:
                d = resp.json()
                pretty = d["predicted_class"].replace("___"," — ").replace("_"," ")
                r(f'<div class="ag-result"><div class="ag-big">{pretty}</div>'
                  f'<div class="ag-conf">Model confidence: {d["confidence"]*100:.1f}%</div></div>')

                # Radar chart for top-5
                if d.get("top5"):
                    labels = [k.replace("Tomato___","").replace("_"," ") for k in d["top5"]]
                    values = list(d["top5"].values())
                    fig = go.Figure(go.Scatterpolar(
                        r=values + [values[0]], theta=labels + [labels[0]],
                        fill="toself", fillcolor="rgba(46,125,50,.15)",
                        line=dict(color="#2e7d32")))
                    fig.update_layout(polar=dict(radialaxis=dict(range=[0,1])),
                                      title="Top-5 Confidence Radar",
                                      height=350, margin=dict(t=50,b=10,l=40,r=40))
                    st.plotly_chart(fig, use_container_width=True)
                add_history("Disease", upload.name, pretty)
            else:
                st.error(f"API error {resp.status_code}: {resp.text}")
    show_history()

elif page == "Model Evaluation":
    st.subheader("📊 Model Evaluation")
    st.caption("Actual metrics from completed training runs.")
    if api_ok:
        resp = api_get("/api/metrics", token=token)
        metrics_data = resp.json() if resp and resp.status_code == 200 else {}
    else:
        metrics_data = {}
        st.warning("API offline — showing cached data.")
        import json as _json
        from app.core.config import settings
        for n in ["crop_metrics.json","yield_metrics.json","disease_metrics.json"]:
            p = settings.REPORTS_DIR / n
            if p.exists():
                metrics_data[n] = _json.loads(p.read_text())

    summary = [
        ("Crop Recommendation","RandomForest","Test F1-macro","0.9932","Test acc 0.9932"),
        ("Crop Yield","ExtraTrees","R²","0.9555","WAPE 11.46%"),
        ("Plant Disease","HistGradientBoosting","Test accuracy","0.8750","F1-macro 0.8751"),
    ]
    df_sum = pd.DataFrame(summary, columns=["Module","Model","Metric","Value","Secondary"])
    st.dataframe(df_sum, use_container_width=True, hide_index=True)

    # Interactive Plotly metric comparison
    fig = px.bar(df_sum, x="Module", y="Value", color="Model",
                 color_discrete_sequence=["#2e7d32","#43a047","#66bb6a"],
                 labels={"Value":"Score"}, text="Value")
    fig.update_layout(title="Model Performance Comparison",
                      height=320, margin=dict(t=40,b=10))
    st.plotly_chart(fig, use_container_width=True)

    for fn, label in [("crop_metrics.json","Crop"),
                      ("yield_metrics.json","Yield"),
                      ("disease_metrics.json","Disease")]:
        with st.expander(f"{label} — {fn}"):
            if fn in metrics_data:
                st.json(metrics_data[fn])
            else:
                st.caption("Not available.")

elif page == "Analytics & Drift":
    st.subheader("📡 Analytics & Model Drift")
    st.caption("Live prediction statistics from the running API.")
    if api_ok:
        resp = api_get("/api/analytics", token=token)
        if resp and resp.status_code == 200:
            data = resp.json()
            c1,c2,c3 = st.columns(3)
            totals = data.get("total_predictions",{})
            c1.metric("Crop predictions",   totals.get("crop",0))
            c2.metric("Yield predictions",  totals.get("yield",0))
            c3.metric("Disease predictions",totals.get("disease",0))
            st.metric("API uptime (s)", data.get("uptime_seconds",0))

            if data.get("top5_crops"):
                fig = px.bar(x=list(data["top5_crops"].keys()),
                             y=list(data["top5_crops"].values()),
                             labels={"x":"Crop","y":"Count"},
                             color_discrete_sequence=["#2e7d32"])
                fig.update_layout(title="Most Recommended Crops",
                                  height=300, margin=dict(t=40,b=10))
                st.plotly_chart(fig, use_container_width=True)

            avg_conf = data.get("average_confidence",{})
            if any(v for v in avg_conf.values()):
                fig2 = px.bar(x=[k for k,v in avg_conf.items() if v],
                              y=[v for v in avg_conf.values() if v],
                              labels={"x":"Module","y":"Avg confidence"},
                              color_discrete_sequence=["#43a047"])
                fig2.update_layout(title="Average Model Confidence",
                                   yaxis_range=[0,1],height=280,margin=dict(t=40,b=10))
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No analytics data yet — make some predictions first.")
    else:
        st.error("API offline.")

elif page == "User Management" and role == "admin":
    st.subheader("👥 User Management")
    st.caption("Admin only — add, remove or change passwords.")
    if api_ok:
        resp = api_get("/api/users", token=token)
        if resp and resp.status_code == 200:
            users = resp.json()
            with st.container(border=True):
                r('<div style="font-weight:700;color:#1b5e20;margin-bottom:.7rem">Current users</div>')
                for u in users:
                    col1,col2,col3,col4 = st.columns([1,1,1,1])
                    col1.markdown(f"**{u['username']}**")
                    col2.write(u["name"])
                    rc = "#0d47a1" if u["role"]=="admin" else "#6a1b9a"
                    rb = "#e3f2fd" if u["role"]=="admin" else "#f3e5f5"
                    col3.markdown(f'<span style="background:{rb};color:{rc};border-radius:999px;'
                                  f'padding:.15rem .55rem;font-size:.72rem;font-weight:700">'
                                  f'{u["role"].upper()}</span>', unsafe_allow_html=True)
                    with col4:
                        if u["username"] != st.session_state.username:
                            if st.button("🗑", key=f"del_{u['username']}"):
                                dr = requests.delete(f"{API}/api/users/{u['username']}",
                                                     headers={"Authorization":f"Bearer {token}"})
                                if dr.status_code == 204:
                                    st.success(f"Removed {u['username']}")
                                    st.rerun()
                        else:
                            st.caption("(you)")

        with st.container(border=True):
            r('<div style="font-weight:700;color:#1b5e20;margin-bottom:.7rem">➕ Add new user</div>')
            c1,c2,c3,c4 = st.columns(4)
            nu = c1.text_input("Username", key="nu_u")
            nn = c2.text_input("Full name", key="nu_n")
            np_ = c3.text_input("Password", type="password", key="nu_p")
            nr = c4.selectbox("Role", ["viewer","admin"], key="nu_r")
            if st.button("Add user", type="primary"):
                r2 = api_post("/api/users",
                              data={"username":nu,"name":nn,"password":np_,"role":nr},
                              token=token)
                if r2 and r2.status_code == 201:
                    st.success(f"User '{nu}' added.")
                    st.rerun()
                elif r2:
                    st.error(r2.json().get("detail","Error"))
    else:
        st.error("API offline.")

r('<div class="ag-foot">🌱 AgriSmart AI v2.0 — research prototype. '
  'Predictions are estimates, not agronomic guarantees.</div>')
