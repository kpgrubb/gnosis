"""Streamlit UI for GNOSIS research intelligence system."""

import json
import streamlit as st
import chromadb

import config
from auth import require_auth
from ingest import ingest
from particles import PARTICLE_HTML
from query import query

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="GNOSIS",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global theme CSS ─────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Dark base */
.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    background-color: #050508 !important;
    color: #e0e6ed !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stSidebar"] {
    background-color: #0a0a10 !important;
    border-right: 1px solid rgba(0,180,255,0.08) !important;
}
[data-testid="stSidebar"] * {
    color: #c0c8d4 !important;
    font-family: 'Inter', sans-serif !important;
}

/* Typography */
h1, h2, h3, h4, h5, h6, p, span, label, div {
    font-family: 'Inter', sans-serif !important;
}
h1 {
    color: #00d4ff !important;
    font-weight: 700 !important;
    text-shadow: 0 0 40px rgba(0,212,255,0.3) !important;
}
h2, h3 {
    color: #80e0ff !important;
    font-weight: 600 !important;
}

/* Inputs */
input, textarea, [data-testid="stTextInput"] input {
    background-color: #0d0d14 !important;
    border: 1px solid rgba(0,180,255,0.2) !important;
    color: #e0e6ed !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
}
input:focus, textarea:focus {
    border-color: #00d4ff !important;
    box-shadow: 0 0 15px rgba(0,212,255,0.15) !important;
}

/* Holographic buttons */
.stButton > button {
    background: linear-gradient(135deg, #0a1628 0%, #0d2847 50%, #0a1628 100%) !important;
    border: 1px solid rgba(0,212,255,0.3) !important;
    color: #00d4ff !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    letter-spacing: 0.5px !important;
    border-radius: 8px !important;
    padding: 0.6rem 1.5rem !important;
    transition: all 0.3s ease !important;
    text-shadow: 0 0 10px rgba(0,212,255,0.3) !important;
    position: relative !important;
    overflow: hidden !important;
}
.stButton > button:hover {
    border-color: #00d4ff !important;
    box-shadow: 0 0 25px rgba(0,212,255,0.2), inset 0 0 25px rgba(0,212,255,0.05) !important;
    background: linear-gradient(135deg, #0d2040 0%, #103050 50%, #0d2040 100%) !important;
    color: #ffffff !important;
}
.stButton > button:active {
    box-shadow: 0 0 40px rgba(0,212,255,0.3), inset 0 0 40px rgba(0,212,255,0.1) !important;
}

/* Primary button variant */
[data-testid="stFormSubmitButton"] button,
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #002a4a 0%, #004080 50%, #002a4a 100%) !important;
    border: 1px solid rgba(0,212,255,0.5) !important;
}

/* Metrics */
[data-testid="stMetric"] {
    background: rgba(0,180,255,0.04) !important;
    border: 1px solid rgba(0,180,255,0.1) !important;
    border-radius: 8px !important;
    padding: 12px !important;
}
[data-testid="stMetricValue"] {
    color: #00d4ff !important;
    font-weight: 600 !important;
}
[data-testid="stMetricLabel"] {
    color: #667788 !important;
    text-transform: uppercase !important;
    font-size: 0.7rem !important;
    letter-spacing: 1px !important;
}

/* Expander */
[data-testid="stExpander"] {
    background-color: rgba(0,180,255,0.03) !important;
    border: 1px solid rgba(0,180,255,0.1) !important;
    border-radius: 8px !important;
}
[data-testid="stExpander"] summary {
    color: #c0c8d4 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
    gap: 0.5rem !important;
}
[data-testid="stExpander"] summary span {
    color: #c0c8d4 !important;
}
[data-testid="stExpander"] summary svg {
    color: #00d4ff !important;
    flex-shrink: 0 !important;
}

/* Divider */
hr {
    border-color: rgba(0,180,255,0.1) !important;
}

/* Alerts / toast */
.stAlert {
    background-color: rgba(0,180,255,0.05) !important;
    border: 1px solid rgba(0,180,255,0.15) !important;
    border-radius: 8px !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #050508; }
::-webkit-scrollbar-thumb { background: rgba(0,180,255,0.2); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(0,180,255,0.4); }

/* Hide Streamlit branding */
#MainMenu, footer, [data-testid="stToolbar"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ── Particle background ─────────────────────────────────────────────────────

st.markdown(PARTICLE_HTML, unsafe_allow_html=True)

# ── Auth gate ────────────────────────────────────────────────────────────────

require_auth()

# ── Auto-ingest on first load ────────────────────────────────────────────────

if "ingested" not in st.session_state:
    with st.spinner("Building corpus index..."):
        ingest(verbose=False)
    st.session_state["ingested"] = True

# ── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        "<h2 style='margin:0;font-size:1.3rem'>◉ GNOSIS</h2>"
        "<p style='margin:0 0 1rem 0;font-size:0.75rem;color:#556;'>"
        "Personal Research Intelligence</p>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"<p style='font-size:0.75rem;color:#445'>Logged in as "
        f"<span style='color:#00d4ff'>{st.session_state.get('username','—')}"
        f"</span></p>",
        unsafe_allow_html=True,
    )

    st.divider()

    # Corpus stats
    try:
        client = chromadb.PersistentClient(path=config.CHROMA_DIR)
        collection = client.get_or_create_collection(name=config.COLLECTION_NAME)
        chunk_count = collection.count()
        if chunk_count > 0:
            all_meta = collection.get(include=["metadatas"])["metadatas"]
            doc_count = len({m["filename"] for m in all_meta})
        else:
            doc_count = 0
        st.metric("Documents in corpus", doc_count)
        st.metric("Total chunks", chunk_count)
    except Exception:
        st.metric("Documents in corpus", 0)
        st.metric("Total chunks", 0)

    st.divider()

    if st.button("Logout", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state["username"] = None
        st.rerun()

# ── Main area ────────────────────────────────────────────────────────────────

# Load corpus metadata for the report count / listing
_meta_list = []
if config.METADATA_PATH.exists():
    with open(config.METADATA_PATH, "r", encoding="utf-8") as _mf:
        _meta_list = json.load(_mf)

st.markdown(
    "<h1 style='text-align:center;font-size:2.5rem;margin-top:2rem'>GNOSIS</h1>"
    "<p style='text-align:center;color:#556;font-size:0.95rem;margin-bottom:0.8rem'>"
    "Ask a question. Get cited answers from your research corpus.</p>",
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    with st.expander(
        f"Corpus: {len(_meta_list)} report{'s' if len(_meta_list) != 1 else ''} indexed",
        expanded=False,
    ):
        for rpt in _meta_list:
            tier = rpt.get("trust_tier", 3)
            if tier == 1:
                color, badge = "#00e676", "TIER 1"
            elif tier == 2:
                color, badge = "#ffab00", "TIER 2"
            else:
                color, badge = "#ff1744", "TIER 3"
            tags = ", ".join(rpt.get("topic_tags", []))
            st.markdown(
                f"<div style='padding:8px 12px;margin:6px 0;"
                f"border-left:3px solid {color};"
                f"background:rgba(255,255,255,0.02);border-radius:4px'>"
                f"<strong style='color:#e0e6ed'>{rpt['filename']}</strong>"
                f" &nbsp;<span style='font-size:0.65rem;padding:2px 6px;"
                f"background:{color}20;color:{color};border-radius:10px;"
                f"font-weight:600'>{badge}</span><br/>"
                f"<span style='color:#667;font-size:0.78rem'>"
                f"{rpt.get('provider','—')} · {rpt.get('published','—')}"
                f"{(' · ' + tags) if tags else ''}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    question = st.text_input(
        "Research query",
        placeholder="e.g. What are the top risks to global banking in 2025?",
        label_visibility="collapsed",
    )

    if st.button("⟐  Query Corpus", type="primary", use_container_width=True) and question:
        with st.spinner("Retrieving sources and synthesizing answer..."):
            try:
                result = query(question)
            except Exception as e:
                st.error(f"Query failed: {e}")
                st.stop()

        st.markdown("---")
        st.markdown(
            "<h3 style='font-size:1.1rem;margin-bottom:0.5rem'>Analysis</h3>",
            unsafe_allow_html=True,
        )
        st.markdown(result["answer"])

        if result["sources"]:
            with st.expander("Sources Used", expanded=True):
                for src in result["sources"]:
                    tier = src["trust_tier"]
                    if tier == 1:
                        color, label = "#00e676", "TIER 1 — VERIFIED"
                    elif tier == 2:
                        color, label = "#ffab00", "TIER 2 — CREDIBLE"
                    else:
                        color, label = "#ff1744", "TIER 3 — CAVEAT"

                    tags = ", ".join(src["topic_tags"]) if src["topic_tags"] else "—"
                    st.markdown(
                        f"<div style='padding:10px 14px;margin:8px 0;"
                        f"border-left:3px solid {color};"
                        f"background:rgba(255,255,255,0.02);border-radius:4px'>"
                        f"<strong style='color:#e0e6ed'>{src['filename']}</strong>"
                        f" &nbsp;<span style='font-size:0.7rem;padding:2px 8px;"
                        f"background:{color}20;color:{color};border-radius:10px;"
                        f"font-weight:600;letter-spacing:0.5px'>{label}</span><br/>"
                        f"<span style='color:#667;font-size:0.8rem'>"
                        f"{src['provider']} · {src['published']} · {tags}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
