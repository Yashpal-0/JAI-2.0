import os
import tempfile
import pytest
from langchain_core.documents import Document


def test_query_docs_returns_string_when_no_db():
    from rag.pipeline import query_docs
    result = query_docs.invoke(
        {"question": "What is Zerostic?"},
        config={"configurable": {"chroma_dir": "/tmp/nonexistent_chroma_xyz"}},
    )
    assert "No documentation indexed" in result


def test_query_docs_returns_results_when_db_exists(tmp_path):
    from langchain_chroma import Chroma
    from langchain_huggingface import HuggingFaceEmbeddings

    chroma_dir = str(tmp_path / "chroma_db")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    docs = [
        Document(
            page_content="Zerostic is a decentralized marketplace platform.",
            metadata={"source": "test.md", "title": "Overview"},
        ),
    ]
    Chroma.from_documents(docs, embeddings, persist_directory=chroma_dir)

    from rag.pipeline import query_docs
    result = query_docs.invoke(
        {"question": "What is Zerostic?"},
        config={"configurable": {"chroma_dir": chroma_dir}},
    )
    assert "Zerostic" in result
    assert isinstance(result, str)
