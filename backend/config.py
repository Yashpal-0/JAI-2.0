import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

SUPPORTED_TENANTS = ["studio.zerostic.com", "pm.zerostic.com", "dev.zerostic.com"]
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")


def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=OPENROUTER_MODEL,
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        openai_api_base="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://zerostic.com",
            "X-Title": "Zerostic JAI 2.0",
        },
    )
