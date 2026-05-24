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


def load_all_docs(docs_dir: str):
    from langchain_community.document_loaders import TextLoader
    from langchain_core.documents import Document

    docs_path = Path(docs_dir)
    all_docs = []

    for file in sorted(docs_path.rglob("*")):
        if not file.is_file() or file.suffix not in SUPPORTED_EXTENSIONS:
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


def ingest_local_files(docs_dir: str = "docs", chroma_dir: str = "chroma_db") -> None:
    """
    Embed all local docs into Chroma, replacing previously ingested local chunks.
    Safe to call on every startup — idempotent via metadata filter deletion.
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_chroma import Chroma
    from rag.pipeline import reset_retriever

    docs_path = Path(docs_dir)
    if not docs_path.exists():
        print(f"[ingest_local] Docs directory not found: {docs_dir}")
        return

    raw_docs = load_all_docs(docs_dir)
    if not raw_docs:
        print("[ingest_local] No supported files found.")
        return

    # Tag all local chunks so we can delete and replace on next startup
    for doc in raw_docs:
        doc.metadata["local"] = True

    splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150)
    chunks = splitter.split_documents(raw_docs)

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    chroma_path = Path(chroma_dir)

    if chroma_path.exists():
        vs = Chroma(persist_directory=chroma_dir, embedding_function=embeddings)
        existing = vs.get(where={"local": True})
        if existing["ids"]:
            vs.delete(ids=existing["ids"])
        vs.add_documents(chunks)
    else:
        Chroma.from_documents(chunks, embeddings, persist_directory=chroma_dir)

    reset_retriever()
    print(f"[ingest_local] {len(chunks)} local chunks → {chroma_dir}")


def main():
    parser = argparse.ArgumentParser(description="Ingest Zerostic docs into Chroma vectorstore.")
    parser.add_argument("--docs-dir", default="docs", help="Path to docs directory (default: docs)")
    parser.add_argument("--chroma-dir", default="chroma_db", help="Path to persist Chroma DB (default: chroma_db)")
    args = parser.parse_args()
    ingest(docs_dir=args.docs_dir, chroma_dir=args.chroma_dir)


if __name__ == "__main__":
    main()
