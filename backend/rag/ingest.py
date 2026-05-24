#!/usr/bin/env python3
"""
CLI to chunk and embed all docs into a Chroma vectorstore.
Supports: .md, .txt, .json, .jsonl

Usage (run from backend/):
    python rag/ingest.py
    python rag/ingest.py --docs-dir docs --chroma-dir chroma_db
"""
import argparse
import json
from pathlib import Path


SUPPORTED_EXTENSIONS = {".md", ".txt", ".json", ".jsonl"}

# Fix: docs/jai/ contains the JAI system prompt and behavioral guide — internal
# config that must NOT be embedded into the vectorstore. RAG retrieving prompt
# fragments (e.g. "NEVER quote specific pricing") as if they were factual KB
# content pollutes retrieval and can trigger the system_prompt_leak output guard.
EXCLUDED_DIRS = {"jai"}


def load_all_docs(docs_dir: str):
    from langchain_community.document_loaders import TextLoader
    from langchain_core.documents import Document

    docs_path = Path(docs_dir)
    all_docs = []

    for file in sorted(docs_path.rglob("*")):
        if not file.is_file() or file.suffix not in SUPPORTED_EXTENSIONS:
            continue

        # Skip any file whose path passes through an excluded directory
        relative_parts = file.relative_to(docs_path).parts
        if any(part in EXCLUDED_DIRS for part in relative_parts):
            print(f"  Skipping (excluded dir) {file.relative_to(docs_path)}")
            continue

        print(f"  Loading {file.relative_to(docs_path)} ...")

        if file.suffix == ".jsonl":
            # One Document per line
            with open(file, encoding="utf-8") as f:
                for i, line in enumerate(f):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        content = json.dumps(obj, ensure_ascii=False)
                    except json.JSONDecodeError:
                        content = line
                    all_docs.append(Document(
                        page_content=content,
                        metadata={"source": str(file), "line": i},
                    ))
        else:
            # .md / .txt / .json — load as plain text
            loader = TextLoader(str(file), encoding="utf-8")
            all_docs.extend(loader.load())

    return all_docs


def ingest(docs_dir: str = "docs", chroma_dir: str = "chroma_db") -> None:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_chroma import Chroma

    docs_path = Path(docs_dir)
    if not docs_path.exists():
        print(f"[ERROR] Docs directory not found: {docs_dir}")
        return

    print(f"[INFO] Loading documents from {docs_dir} ...")
    raw_docs = load_all_docs(docs_dir)

    if not raw_docs:
        print("[WARNING] No supported files found.")
        return

    print(f"[INFO] Loaded {len(raw_docs)} documents. Splitting into chunks...")
    splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150)
    chunks = splitter.split_documents(raw_docs)
    print(f"[INFO] Created {len(chunks)} chunks.")

    print("[INFO] Loading embedding model (all-MiniLM-L6-v2)...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    print(f"[INFO] Embedding and persisting to {chroma_dir}...")
    Chroma.from_documents(chunks, embeddings, persist_directory=chroma_dir)
    print(f"[SUCCESS] Ingested {len(chunks)} chunks from {len(raw_docs)} documents into {chroma_dir}.")


def ingest_from_pages(docs: list, chroma_dir: str = "chroma_db") -> None:
    """
    Embed a list of LangChain Documents into Chroma, replacing any previously
    scraped content.

    docs: list[Document] — as returned by rag.crawler.fetch_zerostic_pages()
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_chroma import Chroma

    docs = [d for d in docs if d.page_content]
    if not docs:
        return

    splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150)
    chunks = splitter.split_documents(docs)

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    chroma_path = Path(chroma_dir)

    if chroma_path.exists():
        vs = Chroma(persist_directory=chroma_dir, embedding_function=embeddings)
        # Remove old web-scraped chunks before adding fresh ones
        existing = vs.get(where={"web_scraped": True})
        if existing["ids"]:
            vs.delete(ids=existing["ids"])
        vs.add_documents(chunks)
    else:
        Chroma.from_documents(chunks, embeddings, persist_directory=chroma_dir)

    print(f"[ingest] {len(chunks)} web chunks → {chroma_dir}")


def main():
    parser = argparse.ArgumentParser(description="Ingest Zerostic docs into Chroma vectorstore.")
    parser.add_argument("--docs-dir", default="docs", help="Path to docs directory (default: docs)")
    parser.add_argument("--chroma-dir", default="chroma_db", help="Path to persist Chroma DB (default: chroma_db)")
    args = parser.parse_args()
    ingest(docs_dir=args.docs_dir, chroma_dir=args.chroma_dir)


if __name__ == "__main__":
    main()