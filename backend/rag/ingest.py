#!/usr/bin/env python3
"""
CLI to chunk and embed all markdown docs into a Chroma vectorstore.

Usage (run from backend/):
    python rag/ingest.py
    python rag/ingest.py --docs-dir docs --chroma-dir chroma_db
"""
import argparse
from pathlib import Path


def ingest(docs_dir: str = "docs", chroma_dir: str = "chroma_db") -> None:
    from langchain_community.document_loaders import DirectoryLoader, TextLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_chroma import Chroma

    docs_path = Path(docs_dir)
    if not docs_path.exists():
        print(f"[ERROR] Docs directory not found: {docs_dir}")
        return

    print(f"[INFO] Loading markdown files from {docs_dir}...")
    loader = DirectoryLoader(
        docs_dir,
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        show_progress=True,
    )
    raw_docs = loader.load()

    if not raw_docs:
        print("[WARNING] No markdown files found.")
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


def main():
    parser = argparse.ArgumentParser(description="Ingest Zerostic docs into Chroma vectorstore.")
    parser.add_argument("--docs-dir", default="docs", help="Path to markdown docs directory (default: docs)")
    parser.add_argument("--chroma-dir", default="chroma_db", help="Path to persist Chroma DB (default: chroma_db)")
    args = parser.parse_args()
    ingest(docs_dir=args.docs_dir, chroma_dir=args.chroma_dir)


if __name__ == "__main__":
    main()
