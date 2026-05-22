import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

SUPPORTED_TENANTS = ["zerostic.com"]
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")

# LangSmith tracing — auto-activates when LANGSMITH_API_KEY is set in .env
# Env vars read by LangChain/LangSmith SDK automatically:
#   LANGSMITH_TRACING=true
#   LANGSMITH_API_KEY=<key>
#   LANGSMITH_PROJECT=JAI-2.0
#   LANGSMITH_ENDPOINT=https://api.smith.langchain.com


def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=OPENROUTER_MODEL,
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        streaming=True,  # enables token-level streaming + LangSmith trace detail
        default_headers={
            "HTTP-Referer": "https://zerostic.com",
            "X-Title": "Zerostic JAI 2.0",
        },
    )
