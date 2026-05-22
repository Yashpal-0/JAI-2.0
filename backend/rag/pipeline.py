from pathlib import Path
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

_CHROMA_DIR = str(Path(__file__).parent.parent / "chroma_db")
_LOW_SIMILARITY_THRESHOLD = 1.2  # L2 distance; higher = less similar
_retriever = None
_vectorstore = None


def reset_retriever() -> None:
    """Force the next get_shared_retriever() call to reload Chroma from disk."""
    global _retriever, _vectorstore
    _retriever = None
    _vectorstore = None


def get_shared_retriever():
    """Lazy-load and cache the Chroma retriever for the process lifetime."""
    global _retriever, _vectorstore
    if _retriever is not None:
        return _retriever
    chroma_path = Path(_CHROMA_DIR)
    if not chroma_path.exists():
        return None
    try:
        from langchain_chroma import Chroma
        from langchain_huggingface import HuggingFaceEmbeddings
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        _vectorstore = Chroma(persist_directory=_CHROMA_DIR, embedding_function=embeddings)
        _retriever = _vectorstore.as_retriever(search_kwargs={"k": 4})
        return _retriever
    except Exception:
        return None


def build_rag_context(query: str) -> str:
    """
    Retrieve top-k chunks for query and format as injected context.
    Returns empty string if vectorstore missing or all chunks score poorly
    (low similarity = skip RAG rather than hallucinate around it).
    """
    global _vectorstore
    # Ensure retriever is initialized so _vectorstore is set
    if get_shared_retriever() is None:
        return ""
    try:
        results = _vectorstore.similarity_search_with_score(query, k=4)
        if not results:
            return ""
        # Filter out low-confidence chunks (L2 distance above threshold = irrelevant)
        confident = [(doc, score) for doc, score in results if score <= _LOW_SIMILARITY_THRESHOLD]
        if not confident:
            return ""
        chunks = "\n\n---\n\n".join(doc.page_content for doc, _ in confident)
        return f"KNOWLEDGE BASE CONTEXT (use this to answer — do not fabricate beyond this):\n\n{chunks}"
    except Exception:
        return ""


@tool
def query_docs(question: str, config: RunnableConfig) -> str:
    """Search the Zerostic documentation for relevant information about the platform, features, and workflows."""
    cfg = config.get("configurable") or {}
    override_dir = cfg.get("chroma_dir")

    if override_dir and override_dir != _CHROMA_DIR:
        # Test or custom path — create one-off retriever, don't pollute singleton
        from pathlib import Path as _Path
        if not _Path(override_dir).exists():
            return "No documentation indexed. Run backend/rag/ingest.py first."
        try:
            from langchain_chroma import Chroma
            from langchain_huggingface import HuggingFaceEmbeddings
            embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            vs = Chroma(persist_directory=override_dir, embedding_function=embeddings)
            docs = vs.similarity_search(question, k=4)
        except Exception as e:
            return f"RAG retrieval error: {str(e)}"
    else:
        retriever = get_shared_retriever()
        if retriever is None:
            return "No documentation indexed. Run backend/rag/ingest.py first."
        try:
            docs = retriever.invoke(question)
        except Exception as e:
            return f"RAG retrieval error: {str(e)}"

    if not docs:
        return "No relevant documentation found for this query."
    return "\n\n".join(
        f"[{doc.metadata.get('source', 'unknown')}]\n{doc.page_content}"
        for doc in docs
    )
