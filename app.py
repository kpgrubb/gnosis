"""Streamlit UI for GNOSIS research intelligence system."""

import json
from datetime import datetime
from pathlib import Path

import bcrypt
import streamlit as st
import streamlit.components.v1 as components
import chromadb

import config
from auth import require_auth
from ingest import ingest, ingest_single, remove_document, reingest_all
from particles import PARTICLE_HTML
from query import query, discover

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="GNOSIS",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
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

/* Hide Streamlit branding (keep sidebar toggle visible) */
footer, [data-testid="stToolbar"] { display: none !important; }

/* Force sidebar always visible */
[data-testid="stSidebar"] {
    min-width: 280px !important;
    width: 280px !important;
    transform: none !important;
    visibility: visible !important;
    position: relative !important;
}
[data-testid="stSidebarCollapsedControl"] { display: none !important; }
section[data-testid="stSidebar"] > div { overflow-y: auto !important; }

/* Particle iframe — full screen behind content */
/* Multiple selectors for cross-version Streamlit compatibility */
[data-testid="stCustomComponentV1"] iframe,
[data-testid="stHtml"] iframe,
iframe[title*="components.v1.html"],
iframe[title*="streamlit_components"] {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    z-index: 0 !important;
    pointer-events: none !important;
    border: none !important;
}
/* Hide the 1px wrapper so it doesn't take layout space */
[data-testid="stCustomComponentV1"],
[data-testid="stHtml"] {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 0 !important;
    height: 0 !important;
    overflow: visible !important;
    z-index: 0 !important;
    pointer-events: none !important;
}

/* Ensure main content sits above the particle iframe */
[data-testid="stMain"],
[data-testid="stAppViewContainer"] > section > div,
[data-testid="stSidebar"] {
    position: relative;
    z-index: 1;
}
</style>
""", unsafe_allow_html=True)

# ── Particle background ─────────────────────────────────────────────────────
# components.html renders an iframe where JS actually executes.
# The CSS above repositions the iframe to cover the full viewport.

components.html(PARTICLE_HTML, height=1)

# ── Auth gate ────────────────────────────────────────────────────────────────

require_auth()

# ── Auto-ingest on first load ────────────────────────────────────────────────

if "ingested" not in st.session_state:
    with st.spinner("Building corpus index..."):
        ingest(verbose=False)
    st.session_state["ingested"] = True

if "history" not in st.session_state:
    st.session_state["history"] = []

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

    # Session history
    st.markdown(
        "<p style='font-size:0.75rem;color:#556;text-transform:uppercase;"
        "letter-spacing:1px'>Session History</p>",
        unsafe_allow_html=True,
    )
    if st.session_state["history"]:
        for idx, entry in enumerate(st.session_state["history"]):
            q_label = entry["question"][:50] + ("..." if len(entry["question"]) > 50 else "")
            with st.expander(f"Q: {q_label}", expanded=False):
                st.markdown(entry["answer"])
                if entry["sources"]:
                    st.caption(
                        "Sources: " + ", ".join(s["filename"] for s in entry["sources"])
                    )
    else:
        st.caption("No queries yet this session.")

    st.divider()

    # Admin gate
    if config.ADMIN_PASSWORD_HASH:
        st.markdown(
            "<p style='font-size:0.75rem;color:#556;text-transform:uppercase;"
            "letter-spacing:1px'>Admin</p>",
            unsafe_allow_html=True,
        )
        if st.session_state.get("admin_unlocked"):
            st.success("Admin unlocked", icon="🔓")
            if st.button("Lock Admin", use_container_width=True):
                st.session_state["admin_unlocked"] = False
                st.rerun()
        else:
            admin_pw = st.text_input("Admin password", type="password", key="admin_pw_input")
            if st.button("Unlock", use_container_width=True, key="admin_unlock_btn"):
                if admin_pw and bcrypt.checkpw(
                    admin_pw.encode("utf-8"),
                    config.ADMIN_PASSWORD_HASH.encode("utf-8"),
                ):
                    st.session_state["admin_unlocked"] = True
                    st.rerun()
                else:
                    st.error("Wrong password.")

        st.divider()

    if st.button("Logout", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state["username"] = None
        st.session_state["admin_unlocked"] = False
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

# Corpus report listing — button toggle instead of expander
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    report_count = len(_meta_list)
    if st.button(
        f"{'▾' if st.session_state.get('show_corpus') else '▸'} "
        f"Corpus: {report_count} report{'s' if report_count != 1 else ''} indexed",
        use_container_width=True,
    ):
        st.session_state["show_corpus"] = not st.session_state.get("show_corpus", False)
        st.rerun()

    if st.session_state.get("show_corpus"):
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

# Filters
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    if st.button(
        f"{'▾' if st.session_state.get('show_filters') else '▸'} Filters",
        use_container_width=True,
        key="toggle_filters",
    ):
        st.session_state["show_filters"] = not st.session_state.get("show_filters", False)
        st.rerun()

    if st.session_state.get("show_filters"):
        fcol1, fcol2 = st.columns(2)
        with fcol1:
            st.markdown(
                "<p style='font-size:0.78rem;color:#667;margin-bottom:4px'>Trust Tier</p>",
                unsafe_allow_html=True,
            )
            tier1 = st.checkbox("Tier 1 — Verified", value=True, key="ft1")
            tier2 = st.checkbox("Tier 2 — Credible", value=True, key="ft2")
            tier3 = st.checkbox("Tier 3 — Caveat", value=True, key="ft3")
        with fcol2:
            st.markdown(
                "<p style='font-size:0.78rem;color:#667;margin-bottom:4px'>Date Range</p>",
                unsafe_allow_html=True,
            )
            year_from = st.number_input("From year", min_value=2000, max_value=2030, value=2020, key="yr_from")
            year_to = st.number_input("To year", min_value=2000, max_value=2030, value=2026, key="yr_to")
    else:
        tier1 = tier2 = tier3 = True
        year_from = 2020
        year_to = 2026

# Mode toggle + Query input
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    mode = st.radio("Mode", ["Synthesize", "Discover"], horizontal=True,
                    key="query_mode", label_visibility="collapsed")

    question = st.text_input(
        "Research query",
        placeholder="e.g. What are the top risks to global banking in 2025?",
        label_visibility="collapsed",
    )

    # Build filter params
    selected_tiers = [t for t, checked in [(1, tier1), (2, tier2), (3, tier3)] if checked]

    btn_label = "⟐  Query Corpus" if mode == "Synthesize" else "⟐  Discover Reports"
    if st.button(btn_label, type="primary", use_container_width=True) and question:
        if not selected_tiers:
            st.warning("Select at least one trust tier.")
            st.stop()
        if year_from > year_to:
            st.warning("'From year' must be less than or equal to 'To year'.")
            st.stop()

        if mode == "Synthesize":
            # ── Synthesize mode ──────────────────────────────────────
            with st.spinner("Retrieving sources and synthesizing answer..."):
                try:
                    result = query(question, trust_tiers=selected_tiers,
                                   year_from=year_from, year_to=year_to)
                except Exception as e:
                    st.error(f"Query failed: {e}")
                    st.stop()

            st.session_state["history"].insert(0, {
                "question": question,
                "answer": result["answer"],
                "sources": result["sources"],
                "timestamp": datetime.now().isoformat(),
            })

            st.markdown("---")
            st.markdown(
                "<h3 style='font-size:1.1rem;margin-bottom:0.5rem'>Analysis</h3>",
                unsafe_allow_html=True,
            )
            st.markdown(result["answer"])

            # Confidence indicator
            chunk_metas = result.get("chunk_metadatas", [])
            if chunk_metas:
                tiers = [m["trust_tier"] for m in chunk_metas]
                total = len(tiers)
                tier3_count = tiers.count(3)
                if tier3_count > total * 0.5:
                    conf_color, conf_bg = "#ff1744", "rgba(255,23,68,0.08)"
                    conf_label, conf_detail = "LOW CONFIDENCE", f"{tier3_count}/{total} sources are Tier 3"
                elif tier3_count == 0:
                    conf_color, conf_bg = "#00e676", "rgba(0,230,118,0.08)"
                    conf_label, conf_detail = "HIGH CONFIDENCE", "All sources are Tier 1-2"
                else:
                    conf_color, conf_bg = "#ffab00", "rgba(255,171,0,0.08)"
                    conf_label, conf_detail = "MODERATE CONFIDENCE", f"{total - tier3_count}/{total} sources are Tier 1-2"
                st.markdown(
                    f"<div style='padding:10px 16px;margin:12px 0;border-left:3px solid {conf_color};"
                    f"background:{conf_bg};border-radius:4px'>"
                    f"<span style='color:{conf_color};font-weight:600;font-size:0.8rem;"
                    f"letter-spacing:1px'>{conf_label}</span>"
                    f"<span style='color:#667;font-size:0.75rem;margin-left:12px'>{conf_detail}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            if result["sources"]:
                st.markdown(
                    "<p style='color:#556;font-size:0.8rem;margin-top:1.5rem;"
                    "text-transform:uppercase;letter-spacing:1px'>Sources Used</p>",
                    unsafe_allow_html=True,
                )
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

        else:
            # ── Discover mode ────────────────────────────────────────
            with st.spinner("Discovering relevant reports..."):
                try:
                    reports = discover(question, trust_tiers=selected_tiers,
                                       year_from=year_from, year_to=year_to)
                except Exception as e:
                    st.error(f"Discovery failed: {e}")
                    st.stop()

            if not reports:
                st.info("No matching reports found.")
            else:
                st.markdown("---")
                st.markdown(
                    "<h3 style='font-size:1.1rem;margin-bottom:0.5rem'>Discovered Reports</h3>",
                    unsafe_allow_html=True,
                )
                for rpt in reports:
                    tier = rpt["trust_tier"]
                    color = {1: "#00e676", 2: "#ffab00"}.get(tier, "#ff1744")
                    badge = {1: "TIER 1", 2: "TIER 2"}.get(tier, "TIER 3")
                    tags = ", ".join(rpt["topic_tags"]) if rpt["topic_tags"] else ""
                    st.markdown(
                        f"<div style='padding:14px;margin:10px 0;border-left:3px solid {color};"
                        f"background:rgba(255,255,255,0.02);border-radius:4px'>"
                        f"<span style='color:#556;font-size:0.7rem'>#{rpt['rank']}</span> "
                        f"<strong style='color:#e0e6ed'>{rpt['filename']}</strong>"
                        f" &nbsp;<span style='font-size:0.65rem;padding:2px 6px;"
                        f"background:{color}20;color:{color};border-radius:10px;"
                        f"font-weight:600'>{badge}</span><br/>"
                        f"<span style='color:#667;font-size:0.78rem'>"
                        f"{rpt['provider']} &middot; {rpt['published']}"
                        f"{(' &middot; ' + tags) if tags else ''}</span><br/>"
                        f"<span style='color:#aab;font-size:0.85rem;margin-top:6px;"
                        f"display:block'>{rpt['abstract']}</span></div>",
                        unsafe_allow_html=True,
                    )
                    # Download button
                    pdf_path = config.DATA_DIR / rpt["filename"]
                    if pdf_path.exists():
                        with open(pdf_path, "rb") as f:
                            st.download_button(
                                f"Download {rpt['filename']}",
                                f.read(),
                                file_name=rpt["filename"],
                                mime="application/pdf",
                                key=f"dl_{rpt['rank']}",
                            )

# ── Admin Panel ─────────────────────────────────────────────────────────────

if st.session_state.get("admin_unlocked"):
    st.markdown("---")
    st.markdown(
        "<h2 style='text-align:center;font-size:1.4rem;margin-top:2rem'>Admin Panel</h2>",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        # ── Corpus table ──────────────────────────────────────────
        st.markdown("### Corpus")
        if _meta_list:
            table_data = [
                {
                    "Filename": r["filename"],
                    "Provider": r.get("provider", "—"),
                    "Tier": r.get("trust_tier", 3),
                    "Published": r.get("published", "—"),
                    "Tags": ", ".join(r.get("topic_tags", [])),
                }
                for r in _meta_list
            ]
            st.dataframe(table_data, use_container_width=True, hide_index=True)
        else:
            st.info("No reports in corpus.")

        st.markdown("---")

        # ── Add Report ────────────────────────────────────────────
        st.markdown("### Add Report")
        with st.form("add_report_form", clear_on_submit=True):
            uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
            ar_provider = st.text_input("Provider", placeholder="e.g. McKinsey & Company")
            ar_tier = st.selectbox("Trust Tier", [1, 2, 3], index=1)
            ar_published = st.text_input("Published", placeholder="e.g. 2025-Q1")
            ar_tags = st.text_input("Topic tags (comma-separated)", placeholder="e.g. banking, AI, strategy")
            add_submitted = st.form_submit_button("Add Report", use_container_width=True)

        if add_submitted and uploaded_file:
            # Save PDF to data/reports/
            save_path = config.DATA_DIR / uploaded_file.name
            save_path.write_bytes(uploaded_file.getvalue())

            # Build metadata entry
            tag_list = [t.strip() for t in ar_tags.split(",") if t.strip()] if ar_tags else []
            new_entry = {
                "filename": uploaded_file.name,
                "provider": ar_provider or "Unknown",
                "trust_tier": ar_tier,
                "published": ar_published or "Unknown",
                "topic_tags": tag_list,
            }

            # Append to metadata.json
            meta_list = []
            if config.METADATA_PATH.exists():
                with open(config.METADATA_PATH, "r", encoding="utf-8") as f:
                    meta_list = json.load(f)
            meta_list.append(new_entry)
            with open(config.METADATA_PATH, "w", encoding="utf-8") as f:
                json.dump(meta_list, f, indent=2)

            # Ingest into ChromaDB
            with st.spinner(f"Ingesting {uploaded_file.name}..."):
                chunks = ingest_single(save_path, new_entry, verbose=False)

            st.success(f"Added {uploaded_file.name} ({chunks} chunks)")
            st.rerun()
        elif add_submitted and not uploaded_file:
            st.warning("Please upload a PDF file.")

        st.markdown("---")

        # ── Remove Report ─────────────────────────────────────────
        st.markdown("### Remove Report")
        if _meta_list:
            filenames = [r["filename"] for r in _meta_list]
            remove_file = st.selectbox("Select report to remove", filenames, key="remove_select")
            if st.button("Remove Report", type="primary", key="remove_btn"):
                # Remove from ChromaDB
                with st.spinner(f"Removing {remove_file}..."):
                    removed = remove_document(remove_file, verbose=False)

                # Remove PDF file
                pdf_to_remove = config.DATA_DIR / remove_file
                if pdf_to_remove.exists():
                    pdf_to_remove.unlink()

                # Update metadata.json
                meta_list = []
                if config.METADATA_PATH.exists():
                    with open(config.METADATA_PATH, "r", encoding="utf-8") as f:
                        meta_list = json.load(f)
                meta_list = [m for m in meta_list if m["filename"] != remove_file]
                with open(config.METADATA_PATH, "w", encoding="utf-8") as f:
                    json.dump(meta_list, f, indent=2)

                st.success(f"Removed {remove_file} ({removed} chunks deleted)")
                st.rerun()
        else:
            st.info("No reports to remove.")

        st.markdown("---")

        # ── Re-ingest All ─────────────────────────────────────────
        st.markdown("### Re-ingest Corpus")
        st.caption("Deletes all chunks and re-ingests every PDF from scratch. Use after metadata changes.")
        if st.button("Re-ingest All", type="primary", key="reingest_btn"):
            with st.spinner("Re-ingesting entire corpus..."):
                summary = reingest_all(verbose=False)
            st.success(
                f"Re-ingestion complete: {summary['documents']} documents, "
                f"{summary['chunks']} chunks"
            )
