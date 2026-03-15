import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Streamlit Cloud injects secrets into st.secrets, not env vars.
# Bridge them so the rest of the app can use os.environ uniformly.
try:
    import streamlit as st
    if "OPENAI_API_KEY" in st.secrets:
        os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
except Exception:
    pass

# Paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data" / "reports"
METADATA_PATH = DATA_DIR / "metadata.json"
CHROMA_DIR = str(PROJECT_ROOT / "db")

# OpenAI
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4o"

# RAG
CHUNK_OVERLAP = 0  # page-level chunks, no overlap needed
TOP_K = 8

# ChromaDB
COLLECTION_NAME = "gnosis_reports"
