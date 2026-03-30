import json
import re
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
- "clear_constraints": (boolean) True if the user wants to remove all active filters and see everything (e.g., "show all", "reset filters", "any price", "no filters", "remove constraints", "all products").

If a constraint is not mentioned, do not include it in the JSON.
Example: "Find me a serum for sensitive skin under $30"
Output: {"category": "Serums", "max_price": 30.0, "keywords": ["sensitive skin"], "intent": "sensitive skin serum"}

Example: "Show me some best rated cleansers"
Output: {"category": "Cleansers", "min_rating": 4.5, "intent": "highly rated cleansers"}

Example: "I want CeraVa moisturizer" (user likely meant CeraVe)
Output: {"keywords": ["CeraVe"], "category": "Moisturizers", "intent": "CeraVe moisturizer"}

Example: "Regenerate" or "Show me different products"
Output: {"regenerate": true, "intent": "regenerate recommendations"}

Example: "cheaper" or "lower price" (no dollar amount)
Output: {"max_price": 15.0, "intent": "more affordable options"}

Example: "under $16" or "price below $16" (even with typos like $16d)
Output: {"max_price": 16.0, "intent": "budget under $16"}

Return ONLY the JSON object. Do not include any other text."""

    @staticmethod
    def _normalize_constraints(user_message: str, constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Post-process LLM output: fix typos, infer price from text, default 'cheaper' to a budget."""
        text = user_message or ""
        low = text.lower()

        # Recover max_price from noisy text (e.g. "under $16d be", "$16d")
        if constraints.get("max_price") is None:
            for pattern in (
                r"(?:under|below|less than|max(?:imum)?)\s*\$?\s*(\d+(?:\.\d+)?)\s*d?\b",
                r"\$\s*(\d+(?:\.\d+)?)\s*d\b",
            ):
                m = re.search(pattern, low, re.IGNORECASE)
                if m:
                    try:
                        constraints["max_price"] = float(m.group(1))
                        logger.info(f"Inferred max_price from text: {constraints['max_price']}")
                        break
                    except ValueError:
                        pass

        # "Cheaper" / budget with no explicit number → default cap so filtering applies
        if constraints.get("max_price") is None and not re.search(r"\$\s*\d+", text):
            if any(
                w in low
                for w in ("cheaper", "lower price", "more affordable", "budget friendly", "less expensive")
            ):
                constraints.setdefault("max_price", 15.0)
                logger.info("Applied default max_price=15 for budget/cheaper request without explicit amount")

        return constraints

    def __init__(self, model: Optional[str] = None, provider: Optional[str] = "ollama"):
        self._model = model
        self._provider = provider

    async def process(self, user_message: str) -> Dict[str, Any]:
        """Process user message into structured constraints.
        
        Uses the fast utility model (e.g. qwen-turbo) rather than the main
        model — constraint extraction is simple JSON pattern-matching and does
        not benefit from chain-of-thought reasoning.
        """
        try:
            logger.info(f"Processing query for constraints: {user_message} using {self._provider}")
            from apps.core.llm import get_llm_client
            from apps.config.Setting import settings

            # Use the dedicated fast model for this utility task
            fast_model = (
                self._model
                or (settings.dashscope_fast_model if self._provider == "dashscope" else None)
            )
            client = get_llm_client(provider=self._provider, model=fast_model)
            
            response = await client.generate(
                prompt=f"User request: \"{user_message}\"",
                system_prompt=self.SYSTEM_PROMPT,
                # Disable chain-of-thought on thinking models — not needed for JSON extraction
                enable_thinking=False
            )
            
            # Clean response to ensure it's just JSON
            cleaned_response = response.strip()
            if "```json" in cleaned_response:
                cleaned_response = cleaned_response.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned_response:
                cleaned_response = cleaned_response.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            constraints = json.loads(cleaned_response)
            constraints = self._normalize_constraints(user_message, constraints)
            logger.info(f"Extracted constraints: {constraints}")
            return constraints
            
        except Exception as e:
            logger.error(f"Error processing query with LLM: {e}")
            # Return empty constraints on error
            return {"intent": "general discovery"}
