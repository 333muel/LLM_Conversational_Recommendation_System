import json
from typing import Dict, Any, Optional
from apps.config.Setting import settings
from apps.config.Tracing import get_logger

logger = get_logger(__name__)

class QueryProcessor:
    """Utility to translate natural language queries into structured constraints."""
    
    SYSTEM_PROMPT = """You are a query parsing assistant for a beauty e-commerce store. 
Your task is to extract structured constraints from a user's natural language request.

IMPORTANT - Typo correction: If the user's text contains likely typos in brand names, ingredients, or product terms, correct them to the standard spelling in your output. Use your knowledge of common beauty brands and skincare terms. The corrected form will be used for database search, so accuracy matters.

Output ONLY a valid JSON object with the following optional keys:
- "category": (string) The specific product category (e.g., "Serums", "Cleansers", "Makeup", "Face", "Makeup, Face, Concealers & Neutralizers"). Use the most specific category mentioned.
- "max_price": (float) Maximum budget if mentioned.
- "min_rating": (float) Minimum rating if mentioned.
- "keywords": (list of strings) Key features, ingredients, or brand names mentioned (e.g., "fragrance-free", "sensitive skin", "vitamin c", "CeraVe", "Neutrogena").
- "intent": (string) Short summary of what the user is looking for.
- "regenerate": (boolean) True if the user wants different/new recommendations (e.g., "regenerate", "show me different products", "something else", "more options", "other options").

If a constraint is not mentioned, do not include it in the JSON.
Example: "Find me a serum for sensitive skin under $30"
Output: {"category": "Serums", "max_price": 30.0, "keywords": ["sensitive skin"], "intent": "sensitive skin serum"}

Example: "Show me some best rated cleansers"
Output: {"category": "Cleansers", "min_rating": 4.5, "intent": "highly rated cleansers"}

Example: "I want CeraVa moisturizer" (user likely meant CeraVe)
Output: {"keywords": ["CeraVe"], "category": "Moisturizers", "intent": "CeraVe moisturizer"}

Example: "Regenerate" or "Show me different products"
Output: {"regenerate": true, "intent": "regenerate recommendations"}

Return ONLY the JSON object. Do not include any other text."""

    def __init__(self, model: Optional[str] = None, provider: Optional[str] = "ollama"):
        self._model = model
        self._provider = provider

    async def process(self, user_message: str) -> Dict[str, Any]:
        """Process user message into structured constraints."""
        try:
            logger.info(f"Processing query for constraints: {user_message} using {self._provider}")
            from apps.core.llm import get_llm_client
            client = get_llm_client(provider=self._provider, model=self._model)
            
            response = await client.generate(
                prompt=f"User request: \"{user_message}\"",
                system_prompt=self.SYSTEM_PROMPT
            )
            
            # Clean response to ensure it's just JSON
            cleaned_response = response.strip()
            if "```json" in cleaned_response:
                cleaned_response = cleaned_response.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned_response:
                cleaned_response = cleaned_response.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            constraints = json.loads(cleaned_response)
            logger.info(f"Extracted constraints: {constraints}")
            return constraints
            
        except Exception as e:
            logger.error(f"Error processing query with LLM: {e}")
            # Return empty constraints on error
            return {"intent": "general discovery"}
