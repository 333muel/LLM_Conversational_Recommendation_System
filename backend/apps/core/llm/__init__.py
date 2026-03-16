"""LLM package."""
from typing import Optional, List, Dict, Any
from .Ollama import OllamaClient
from .DashScope import DashScopeClient
from apps.config.Setting import settings

def get_llm_client(provider: Optional[str] = "ollama", model: Optional[str] = None):
    """Factory function to get appropriate LLM client."""
    if provider == "dashscope":
        return DashScopeClient(model=model or settings.dashscope_model)
    else:
        # Default to Ollama
        return OllamaClient(model=model or settings.ollama_model)
