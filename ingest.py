"""PDF ingestion pipeline for GNOSIS.

Scans data/reports/ for PDFs, chunks by page, embeds via OpenAI,
and stores in ChromaDB. Skips already-ingested documents.
"""

import hashlib
import json
import sys

import chromadb
import fitz  # PyMuPDF

from llama_index.embeddings.openai import OpenAIEmbedding

import config


def load_metadata() -> dict[str, dict]:
    """Load metadata.json and return a dict keyed by filename."""
    if not config.METADATA_PATH.exists():
        print(f"Warning: {config.METADATA_PATH} not found. All files will use default trust_tier=3.")
        return {}
    with open(config.METADATA_PATH, "r", encoding="utf-8") as f:
        entries = json.load(f)
    return {entry["filename"]: entry for entry in entries}


def file_hash(filepath) -> str:
    """Deterministic hash for a PDF file (used as dedup key)."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            h.update(block)
    return h.hexdigest()


def _parse_year(published: str) -> int:
    """Extract year integer from 'YYYY-QN' or 'YYYY' format. Returns 0 if unparseable."""
    try:
        return int(published.split("-")[0])
    except (ValueError, IndexError):
        return 0


def extract_pages(pdf_path) -> list[dict]:
    """Extract text from each page of a PDF using PyMuPDF."""
    pages = []
    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        text = doc[page_num].get_text()
        if text.strip():
            pages.append({"page": page_num + 1, "text": text})
    doc.close()
    return pages


def ingest(verbose: bool = True) -> dict:
    """Run the full ingestion pipeline. Returns summary stats."""
    metadata_map = load_metadata()

    # Init ChromaDB (persistent)
    client = chromadb.PersistentClient(path=config.CHROMA_DIR)
    collection = client.get_or_create_collection(
        name=config.COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    # Init embedding model
    embed_model = OpenAIEmbedding(
        model_name=config.EMBEDDING_MODEL,
        api_key=config.OPENAI_API_KEY,
    )

    # Gather PDFs
    pdf_files = sorted(config.DATA_DIR.rglob("*.pdf"))
    if not pdf_files:
        print("No PDFs found in", config.DATA_DIR)
        return {"documents": 0, "chunks": 0, "skipped": 0}

    # Check which files are already ingested (by content hash stored in metadata)
    existing_ids = set(collection.get()["ids"]) if collection.count() > 0 else set()

    docs_ingested = 0
    docs_skipped = 0
    total_chunks = 0

    for pdf_path in pdf_files:
        fname = pdf_path.name
        fhash = file_hash(pdf_path)
        # Chunk IDs follow pattern: <hash>_page_<N>
        # If first page already exists, skip the whole document
        if f"{fhash}_page_1" in existing_ids:
            if verbose:
                print(f"  Skipping (already ingested): {fname}")
            docs_skipped += 1
            continue

        if verbose:
            print(f"  Ingesting: {fname}")

        pages = extract_pages(pdf_path)
        if not pages:
            print(f"  Warning: no text extracted from {fname}")
            continue

        # Look up metadata
        meta = metadata_map.get(fname, {})
        trust_tier = meta.get("trust_tier", 3)
        provider = meta.get("provider", "Unknown")
        published = meta.get("published", "Unknown")
        topic_tags = meta.get("topic_tags", [])

        # Build chunk data
        ids = []
        documents = []
        metadatas = []

        for page in pages:
            chunk_id = f"{fhash}_page_{page['page']}"
            ids.append(chunk_id)
            documents.append(page["text"])
            metadatas.append({
                "filename": fname,
                "page": page["page"],
                "trust_tier": trust_tier,
                "provider": provider,
                "published": published,
                "published_year": _parse_year(published),
                "topic_tags": json.dumps(topic_tags),
                "file_hash": fhash,
            })

        # Embed all pages for this document in one batch
        texts = [p["text"] for p in pages]
        embeddings = embed_model.get_text_embedding_batch(texts)

        # Upsert into ChromaDB
        collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        docs_ingested += 1
        total_chunks += len(pages)
        if verbose:
            print(f"    -> {len(pages)} pages chunked and embedded")

    summary = {
        "documents": docs_ingested,
        "chunks": total_chunks,
        "skipped": docs_skipped,
    }

    if verbose:
        print("\n--- Ingestion Summary ---")
        print(f"  Documents ingested: {summary['documents']}")
        print(f"  Chunks created:     {summary['chunks']}")
        print(f"  Documents skipped:  {summary['skipped']}")
        print(f"  Total in corpus:    {collection.count()} chunks")

    return summary


def ingest_single(pdf_path, metadata_entry: dict, verbose: bool = True) -> int:
    """Ingest a single PDF with the given metadata. Returns number of chunks created."""
    client = chromadb.PersistentClient(path=config.CHROMA_DIR)
    collection = client.get_or_create_collection(
        name=config.COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    embed_model = OpenAIEmbedding(
        model_name=config.EMBEDDING_MODEL,
        api_key=config.OPENAI_API_KEY,
    )

    pages = extract_pages(pdf_path)
    if not pages:
        if verbose:
            print(f"  Warning: no text extracted from {pdf_path.name}")
        return 0

    fhash = file_hash(pdf_path)
    fname = pdf_path.name
    trust_tier = metadata_entry.get("trust_tier", 3)
    provider = metadata_entry.get("provider", "Unknown")
    published = metadata_entry.get("published", "Unknown")
    topic_tags = metadata_entry.get("topic_tags", [])

    ids = []
    documents = []
    metadatas = []

    for page in pages:
        chunk_id = f"{fhash}_page_{page['page']}"
        ids.append(chunk_id)
        documents.append(page["text"])
        metadatas.append({
            "filename": fname,
            "page": page["page"],
            "trust_tier": trust_tier,
            "provider": provider,
            "published": published,
            "published_year": _parse_year(published),
            "topic_tags": json.dumps(topic_tags),
            "file_hash": fhash,
        })

    texts = [p["text"] for p in pages]
    embeddings = embed_model.get_text_embedding_batch(texts)

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    if verbose:
        print(f"  Ingested {fname}: {len(pages)} chunks")

    return len(pages)


def remove_document(filename: str, verbose: bool = True) -> int:
    """Remove all ChromaDB chunks for a given filename. Returns number of chunks removed."""
    client = chromadb.PersistentClient(path=config.CHROMA_DIR)
    try:
        collection = client.get_collection(name=config.COLLECTION_NAME)
    except Exception:
        return 0

    # Find all chunk IDs for this filename
    results = collection.get(where={"filename": filename}, include=[])
    chunk_ids = results["ids"]

    if chunk_ids:
        collection.delete(ids=chunk_ids)
        if verbose:
            print(f"  Removed {len(chunk_ids)} chunks for {filename}")

    return len(chunk_ids)


def reingest_all(verbose: bool = True) -> dict:
    """Delete all chunks and re-ingest from scratch."""
    client = chromadb.PersistentClient(path=config.CHROMA_DIR)
    try:
        client.delete_collection(name=config.COLLECTION_NAME)
    except Exception:
        pass
    return ingest(verbose=verbose)


if __name__ == "__main__":
    ingest()
