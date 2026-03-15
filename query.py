"""RAG query pipeline for GNOSIS.

Accepts a plain-language query, retrieves relevant chunks from ChromaDB,
and synthesizes a cited answer via GPT-4o.
"""

import json

import chromadb
from openai import OpenAI

from llama_index.embeddings.openai import OpenAIEmbedding

import config

SYSTEM_PROMPT = (
    "You are a research analyst. Answer the user's question using ONLY the "
    "provided source excerpts. For every claim, cite the source filename and "
    "page number inline (e.g. [mckinsey-report.pdf, p.12]). If sources "
    "conflict, note the disagreement. If no sources are relevant, say so — "
    "do not speculate."
)


def _format_context(results: dict) -> str:
    """Format ChromaDB query results into a numbered context block."""
    lines = []
    for i, (doc, meta) in enumerate(
        zip(results["documents"][0], results["metadatas"][0]), 1
    ):
        lines.append(
            f"--- Source {i}: {meta['filename']}, Page {meta['page']} "
            f"(Trust Tier {meta['trust_tier']}) ---\n{doc}\n"
        )
    return "\n".join(lines)


def _dedupe_sources(metadatas: list[dict]) -> list[dict]:
    """Return deduplicated list of contributing reports with trust tiers."""
    seen = set()
    sources = []
    for meta in metadatas:
        fname = meta["filename"]
        if fname not in seen:
            seen.add(fname)
            sources.append({
                "filename": fname,
                "provider": meta.get("provider", "Unknown"),
                "trust_tier": meta["trust_tier"],
                "published": meta.get("published", "Unknown"),
                "topic_tags": json.loads(meta.get("topic_tags", "[]")),
            })
    return sources


def query(question: str, top_k: int = config.TOP_K) -> dict:
    """Run a RAG query. Returns {"answer": str, "sources": list[dict]}."""
    # Embed the question
    embed_model = OpenAIEmbedding(
        model_name=config.EMBEDDING_MODEL,
        api_key=config.OPENAI_API_KEY,
    )
    query_embedding = embed_model.get_query_embedding(question)

    # Retrieve from ChromaDB
    client = chromadb.PersistentClient(path=config.CHROMA_DIR)
    collection = client.get_collection(name=config.COLLECTION_NAME)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    if not results["documents"] or not results["documents"][0]:
        return {
            "answer": "No relevant sources found in the corpus.",
            "sources": [],
        }

    # Build context and call GPT-4o
    context = _format_context(results)
    llm = OpenAI(api_key=config.OPENAI_API_KEY)

    response = llm.chat.completions.create(
        model=config.LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"## Source Excerpts\n\n{context}\n\n"
                    f"## Question\n\n{question}"
                ),
            },
        ],
        temperature=0.2,
    )

    answer = response.choices[0].message.content
    sources = _dedupe_sources(results["metadatas"][0])

    return {"answer": answer, "sources": sources}


if __name__ == "__main__":
    import sys

    q = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What are the key findings?"
    result = query(q)
    print("\n=== Answer ===\n")
    print(result["answer"])
    print("\n=== Sources ===\n")
    for s in result["sources"]:
        print(f"  [{s['trust_tier']}] {s['filename']} — {s['provider']}")
