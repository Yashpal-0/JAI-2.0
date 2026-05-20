import os
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

DEFAULT_CHROMA_DIR = os.path.join(os.path.dirname(__file__), "../../chroma_db")


@tool
def query_docs(question: str, config: RunnableConfig) -> str:
    """Search the Zerostic documentation for relevant information about the platform, features, and workflows."""
    cfg = config.get("configurable") or {}
    chroma_dir = cfg.get("chroma_dir", DEFAULT_CHROMA_DIR)

    if not os.path.exists(chroma_dir):
        return "No documentation indexed. Run backend/rag/ingest.py first."

    try:
        from langchain_chroma import Chroma
        from langchain_huggingface import HuggingFaceEmbeddings

        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vectorstore = Chroma(persist_directory=chroma_dir, embedding_function=embeddings)
        docs = vectorstore.similarity_search(question, k=4)
    except Exception as e:
        return f"RAG retrieval error: {str(e)}"

    if not docs:
        return "No relevant documentation found for this query."

    return "\n\n".join([
        f"[{doc.metadata.get('source', 'unknown')} — {doc.metadata.get('title', 'Section')}]\n{doc.page_content}"
        for doc in docs
    ])
