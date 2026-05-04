"""Ollama LLM client integration."""
from typing import Optional, List, Dict
import httpx
from apps.config.Setting import settings
from apps.config.Tracing import get_logger

logger = get_logger(__name__)


class OllamaClient:
    """Client for interacting with Ollama LLM."""
    
    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = base_url or settings.ollama_base_url
        self.model = model or settings.ollama_model
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Generate text using Ollama (Async)."""
        try:
            # Separate Ollama 'options' from top-level parameters
            options = {}
            if "stop" in kwargs:
                options["stop"] = kwargs.pop("stop")
            if "temperature" in kwargs:
                options["temperature"] = kwargs.pop("temperature")
            if "top_p" in kwargs:
                options["top_p"] = kwargs.pop("top_p")
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                **kwargs
            }
            
            if options:
                payload["options"] = options
            
            if system_prompt:
                payload["system"] = system_prompt
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                return result.get("response", "")
        except Exception as e:
            logger.error(f"Error generating text with Ollama: {e}")
            raise
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Chat with Ollama using message format (Async)."""
        try:
            # Separate Ollama 'options' from top-level parameters
            options = {}
            if "stop" in kwargs:
                options["stop"] = kwargs.pop("stop")
            if "temperature" in kwargs:
                options["temperature"] = kwargs.pop("temperature")
            if "top_p" in kwargs:
                options["top_p"] = kwargs.pop("top_p")

            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                **kwargs
            }

            if options:
                payload["options"] = options
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                return result.get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"Error chatting with Ollama: {e}")
            raise


# Global Ollama client instance
ollama_client = OllamaClient(model="qwen3:latest")

