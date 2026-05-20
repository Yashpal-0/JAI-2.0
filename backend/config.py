import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from langsmith.integrations.openai_agents_sdk import OpenAIAgentsTracingProcessor

# Load environment variables
load_dotenv()

# Tenant/Domain Isolation Constants
# We enforce strict isolation between tenants so data won't leak between websites.
SUPPORTED_TENANTS = ["studio.zerostic.com", "pm.zerostic.com", "dev.zerostic.com"]

# 1. OpenRouter Client Integration
# This forces the OpenAI Agents SDK to use DeepSeek via OpenRouter instead of default OpenAI GPTs
custom_openrouter_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    default_headers={
        "HTTP-Referer": "https://zerostic.com",
        "X-Title": "Zerostic JAI 2.0",
    }
)

OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-v4-flash:free")

def get_trace_processors():
    """Returns LangSmith processors if tracing is enabled in env."""
    if os.getenv("LANGSMITH_TRACING") == "true":
        return [OpenAIAgentsTracingProcessor()]
    return []
