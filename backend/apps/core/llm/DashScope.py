"""DashScope (OpenAI-compatible) LLM client integration."""
from typing import Optional, List, Dict, Any
import httpx
import json
from apps.config.Setting import settings
from apps.config.Tracing import get_logger

logger = get_logger(__name__)


class DashScopeClient:
    """Client for interacting with DashScope (Qwen) LLM via OpenAI-compatible API."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.dashscope_api_key
        self.base_url = base_url or settings.dashscope_base_url
        self.model = model or settings.dashscope_model
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None, enable_thinking: Optional[bool] = None, **kwargs) -> str:
        """Generate text using DashScope (Async)."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        return await self.chat(messages, enable_thinking=enable_thinking, **kwargs)
    
    async def chat(self, messages: List[Dict[str, str]], enable_thinking: Optional[bool] = None, **kwargs) -> str:
        """Chat with DashScope using message format (Async).
        
        Pass enable_thinking=False to skip the chain-of-thought step on Qwen3
        thinking models. This cuts latency from ~60-90 s down to ~2-5 s for
        simple tasks while keeping the same model weights.
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                **kwargs
            }
            # Qwen3 thinking models honour this flag to skip the CoT step
            if enable_thinking is not None:
                payload["enable_thinking"] = enable_thinking
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                choices = result.get("choices", [])
                if not choices:
                    return ""
                
                message = choices[0].get("message", {})
                
                # Handle reasoning_content if present (for deep thinking models)
                reasoning = message.get("reasoning_content", "")
                content = message.get("content", "")
                
                if reasoning:
                    logger.info(f"DashScope Thinking: {reasoning[:100]}...")
                    # Optionally combine or just return content. 
                    # Usually we want the final content, but let's keep it simple for now.
                
                return content
        except Exception as e:
            logger.error(f"Error chatting with DashScope: {e}")
            raise


# Global DashScope client instance
dashscope_client = DashScopeClient()
