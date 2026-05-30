"""
vector_store.py — ChromaDB-backed vector store for resume ingestion & retrieval.

Responsibilities:
 • Extract text from PDF and DOCX files.
 • Chunk extracted text into manageable segments.
 • Store chunks in a local ChromaDB collection with metadata.
 • Perform similarity search against stored resume chunks.
"""

import os
import re
import logging
from typing import List, Dict, Any

from django.conf import settings

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Text extraction helpers
# ──────────────────────────────────────────────────────────────────────────────

def extract_text_from_pdf(file_path: str) -> str:
    """Extract all text from a PDF file using PyPDF2."""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n".join(pages)
    except Exception as exc:
        logger.error("Failed to extract text from PDF %s: %s", file_path, exc)
        return ""


def extract_text_from_docx(file_path: str) -> str:
    """Extract all text from a DOCX file using python-docx."""
    try:
        from docx import Document
        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)
    except Exception as exc:
        logger.error("Failed to extract text from DOCX %s: %s", file_path, exc)
        return ""


def extract_text(file_path: str) -> str:
    """Route to the correct extractor based on file extension."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext in (".docx", ".doc"):
        return extract_text_from_docx(file_path)
    else:
        # Fallback: attempt to read as plain text
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
                return fh.read()
        except Exception as exc:
            logger.error("Cannot read file %s: %s", file_path, exc)
            return ""


def extract_email_from_text(text: str) -> str:
    """Try to find the first email address in a block of text."""
    match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    return match.group(0) if match else ""


def extract_name_from_text(text: str) -> str:
    """
    Heuristic: treat the first non-empty line of the resume as the candidate name.
    Falls back to 'Unknown Candidate'.
    """
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped and len(stripped) < 80 and not stripped.startswith("http"):
            # Skip lines that look like email / phone
            if "@" not in stripped and not re.match(r"^[\d\s\-\+\(\)]+$", stripped):
                return stripped
    return "Unknown Candidate"


# ──────────────────────────────────────────────────────────────────────────────
# ChromaDB client singleton
# ──────────────────────────────────────────────────────────────────────────────

_chroma_client = None


def get_chroma_client() -> chromadb.ClientAPI:
    """Return a persistent ChromaDB client (singleton)."""
    global _chroma_client
    if _chroma_client is None:
        persist_dir = getattr(settings, "CHROMA_PERSIST_DIR", "./chroma_db")
        os.makedirs(persist_dir, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=persist_dir)
    return _chroma_client


def get_collection(collection_name: str | None = None):
    """Get or create a ChromaDB collection."""
    name = collection_name or getattr(
        settings, "CHROMA_COLLECTION_NAME", "hr_resumes"
    )
    client = get_chroma_client()
    return client.get_or_create_collection(name=name)


# ──────────────────────────────────────────────────────────────────────────────
# Ingestion
# ──────────────────────────────────────────────────────────────────────────────

def add_documents(
    file_paths: List[str],
    collection_name: str | None = None,
    job_id: str = "",
) -> List[Dict[str, Any]]:
    """
    Extract text from files, chunk them, and upsert into ChromaDB.

    Returns a list of dicts: [{filename, full_text, email, name, num_chunks}, ...]
    """
    collection = get_collection(collection_name)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    results = []
    for file_path in file_paths:
        filename = os.path.basename(file_path)
        full_text = extract_text(file_path)
        if not full_text.strip():
            logger.warning("No text extracted from %s — skipping.", filename)
            continue

        email = extract_email_from_text(full_text)
        name = extract_name_from_text(full_text)
        chunks = splitter.split_text(full_text)

        ids = []
        documents = []
        metadatas = []
        for idx, chunk in enumerate(chunks):
            chunk_id = f"{job_id}_{filename}_{idx}"
            ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append({
                "source_file": filename,
                "candidate_name": name,
                "candidate_email": email,
                "job_id": job_id,
                "chunk_index": idx,
            })

        if ids:
            collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

        results.append({
            "filename": filename,
            "full_text": full_text,
            "email": email,
            "name": name,
            "num_chunks": len(chunks),
        })
        logger.info(
            "Ingested %s: %d chunks, email=%s, name=%s",
            filename, len(chunks), email or "(none)", name,
        )

    return results


# ──────────────────────────────────────────────────────────────────────────────
# Retrieval
# ──────────────────────────────────────────────────────────────────────────────

def similarity_search(
    query: str,
    n_results: int = 20,
    collection_name: str | None = None,
    job_id: str = "",
) -> List[Dict[str, Any]]:
    """
    Query ChromaDB for the most relevant resume chunks.

    Returns a list of dicts with keys: document, metadata, distance.
    """
    collection = get_collection(collection_name)

    where_filter = {"job_id": job_id} if job_id else None
    try:
        query_result = collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter,
        )
    except Exception as exc:
        logger.error("ChromaDB query failed: %s", exc)
        return []

    results = []
    if query_result and query_result.get("documents"):
        docs = query_result["documents"][0]
        metas = query_result["metadatas"][0] if query_result.get("metadatas") else [{}] * len(docs)
        dists = query_result["distances"][0] if query_result.get("distances") else [0.0] * len(docs)
        for doc, meta, dist in zip(docs, metas, dists):
            results.append({"document": doc, "metadata": meta, "distance": dist})

    return results
