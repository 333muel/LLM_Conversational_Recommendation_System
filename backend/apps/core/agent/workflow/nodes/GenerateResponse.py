"""Node for generating final AI response."""
import re
from typing import Dict, Any, List, Optional
from apps.core.agent.workflow.nodes.BaseNode import BaseNode
from apps.core.agent.workflow.state.RecommendationState import RecommendationState
from apps.database.Mongo import ProductRepository
from apps.config.Tracing import get_logger

logger = get_logger(__name__)


class GenerateResponseNode(BaseNode):
    """Node that generates final AI response based on recommendations."""
    
    def _get_product_details(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get product details for recommended items.

        Deduplicates by normalised product title so that variant ASINs for the
        same product (e.g. different pack sizes or duplicate catalogue entries)
        are not surfaced as separate recommendations.  The highest-ranked item
        for each unique title is kept.
        """
        product_details = []
        seen_titles: set = set()

        for rec in recommendations:
            item_id = rec.get("item_id")
            if item_id:
                product = ProductRepository.get_product_by_id(item_id)
                if product:
                    raw_title: str = product.get("product_title", "")
                    normalised_title = " ".join(raw_title.lower().split())
                    if normalised_title in seen_titles:
                        logger.debug(
                            f"Skipping duplicate title for item {item_id}: '{raw_title}'"
                        )
                        continue
                    seen_titles.add(normalised_title)
                    product_details.append({
                        "item_id": item_id,
                        "title": raw_title,
                        "description": product.get("product_description", ""),
                        "rating": product.get("product_avg_rating"),
                        "price": product.get("product_price", ""),
                        "categories": product.get("product_categories", ""),
                        "main_category": product.get("product_main_category", ""),
                        "image": product.get("product_image_url", ""),
                        "score": rec.get("score", 0.0),
                        "rank": rec.get("rank", 0)
                    })
                else:
                    logger.debug(f"Item {item_id} not found in MongoDB catalog, skipping")

        return product_details
    
    def _deduplicate_by_title(self, product_details: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove entries that share the same normalised product title.

        Keeps the first (highest-ranked) occurrence.  Used when product_details
        are already formatted and injected into state, bypassing _get_product_details.
        """
        seen_titles: set = set()
        deduplicated = []
        for product in product_details:
            raw_title: str = product.get("title", "")
            normalised_title = " ".join(raw_title.lower().split())
            if normalised_title in seen_titles:
                logger.debug(
                    f"Skipping duplicate title for item {product.get('item_id')}: '{raw_title}'"
                )
                continue
            seen_titles.add(normalised_title)
            deduplicated.append(product)
        return deduplicated

    def _sanitize_response(self, text: str) -> str:
        """Sanitize response to prevent system prompt leakage."""
        keywords = [
            "RecBole", "LangGraph", "MongoDB", "DashScope", "Ollama", 
            "system prompt", "internal instruction", "workflow node",
            "GenerateResponseNode", "RecommendItemNode"
        ]
        text_lower = text.lower()
        for kw in keywords:
            if kw.lower() in text_lower:
                logger.warning(f"Response flagged for architectural keyword leakage: {kw}")
                return (
                    "I've found some great recommendations for you, but I encountered "
                    "a safety filter while formatting the response. Please try asking "
                    "about specific products or categories again!"
                )
        return text

    @staticmethod
    def _short_name(title: str) -> str:
        """Create a concise display name from a verbose Amazon product title."""
        if not title:
            return "Unknown Product"
        for sep in (" - ", " | ", " – "):
            parts = title.split(sep)
            if len(parts) >= 2:
                short = parts[0].strip()
                if len(short) < 15 and len(parts) > 1:
                    short = f"{parts[0].strip()} {parts[1].strip()}"
                return short[:55]
        if "," in title:
            short = title.split(",")[0].strip()
            if len(short) > 10:
                return short[:55]
        return title[:55]

    def _create_recommendation_prompt(
        self,
        product_details: List[Dict[str, Any]],
        top_n: int = 10,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create prompt for LLM to generate recommendation response.
        
        Note: user_message is NOT concatenated here to mitigate prompt injection.
        It is passed as a distinct HumanMessage in the chat history.
        """
        top_items = product_details[:top_n]
        context_items = product_details[top_n:] if len(product_details) > top_n else []
        
        top_products_text = ""
        for i, product in enumerate(top_items, 1):
            short = self._short_name(product.get("title", "Unknown Product"))
            top_products_text += f"\n{i}. **{short}**"
            if product.get('description'):
                top_products_text += f"\n   Description: {product.get('description', '')[:200]}"
            if product.get('rating'):
                top_products_text += f"\n   Rating: {product.get('rating')}/5.0"
            price_val = product.get('price', '').strip() if product.get('price') else ''
            if price_val:
                top_products_text += f"\n   Price: {price_val}"
            else:
                top_products_text += f"\n   Price: (not listed — do NOT state a price)"
            if product.get('categories'):
                top_products_text += f"\n   Category: {product.get('categories', '').split(';')[0]}"
            top_products_text += "\n"
            
        context_summary = ""
        if context_items:
            categories = {}
            for product in context_items:
                cat = product.get('categories', '').split(';')[0] if product.get('categories') else 'Other'
                categories[cat] = categories.get(cat, 0) + 1
            
            context_summary = f"\n\nAdditional context: I also found {len(context_items)} more products in categories like: {', '.join(list(categories.keys())[:5])}. "
            context_summary += "You can mention these categories if relevant to the user's request, but focus on the top recommendations above."
        
        prompt = f"""You are a helpful recommendation assistant for a beauty e-commerce store.

Based on the products provided below (and the user's latest query provided as a separate message), 
generate a concise, friendly response.

### PRODUCT DATA (DELIMITED) ###
{top_products_text}{context_summary}
### END PRODUCT DATA ###

CRITICAL RULES (strictly enforced):
1. Only mention products from the numbered list above using the **bold short name** shown.
2. NEVER state, estimate, or invent a price. If the product shows "(not listed — do NOT state a price)", omit any price claim.
3. If you do not find suitable products in the list, state that you couldn't find matches.

Please provide a VERY SHORT, friendly response (maximum 60 words total) that:
1. Acknowledges the request in one sentence.
2. Lists 2-3 top picks using bullet points (•) with **bold name** and ONE key point each.
3. Keep each bullet to one short line. Be conversational but scannable.
4. On the VERY LAST line, output EXACTLY: HIGHLIGHTED: X, Y (the product numbers you featured, comma-separated). This line is mandatory.

[STOP_SEQUENCE: User:]"""

        return prompt
    
    async def execute(self, state: RecommendationState) -> Dict[str, Any]:
        """Generate final AI response."""
        try:
            user_message = state.get("user_message", "")
            raw_recommendations = state.get("raw_recommendations", [])
            messages = state.get("messages", [])
            
            product_details = state.get("product_details", [])
            if not product_details and raw_recommendations:
                product_details = self._get_product_details(raw_recommendations)
            else:
                product_details = self._deduplicate_by_title(product_details)

            logger.info(f"Retrieved details for {len(product_details)} products")

            if not product_details:
                msg = (
                    "I couldn't find products that match your request right now. "
                    "Try relaxing the price, category, or keywords—or browse again in a moment."
                )
                return {
                    "final_response": msg,
                    "product_details": [],
                    "raw_recommendations": raw_recommendations,
                    "messages": [{"role": "assistant", "content": msg}],
                }
            
            top_k = state.get("top_k")
            model = state.get("model")
            
            from apps.config.Setting import settings
            if top_k is None:
                top_k = settings.recommendation_top_k
            
            recommendations_context = self._create_recommendation_prompt(
                product_details,
                top_n=top_k,
                metadata=state.get("product_metadata")
            )
            
            chat_messages = []
            
            chat_messages.append({
                "role": "system",
                "content": f"You are a helpful and friendly recommendation assistant. {recommendations_context}"
            })
            
            for msg in messages:
                if msg.get("role") != "system":
                    chat_messages.append(msg)
            
            llm_provider = state.get("llm_provider", "ollama")
            if llm_provider == "dashscope":
                llm_model = model if model and ":" not in model else settings.dashscope_model
            else:
                llm_model = model or settings.ollama_model
            logger.info(f"Generating AI response using provider: {llm_provider}, model: {llm_model}")
            
            from apps.core.llm import get_llm_client
            client = get_llm_client(provider=llm_provider, model=llm_model)
            
            response = await client.chat(
                messages=chat_messages, 
                enable_thinking=False,
                stop=["User:", "Human:", "System:"]
            )
            
            highlighted_indices: List[int] = []
            hi_match = re.search(r"HIGHLIGHTED:\s*([\d,\s]+)", response, re.IGNORECASE)
            if hi_match:
                highlighted_indices = [
                    int(x.strip()) for x in hi_match.group(1).split(",") if x.strip().isdigit()
                ]
                response = re.sub(r"\n?\s*HIGHLIGHTED:\s*[\d,\s]+\s*$", "", response, flags=re.IGNORECASE).strip()
                
            response = self._sanitize_response(response)
            
            logger.info(f"AI response generated successfully (highlighted: {highlighted_indices})")
            
            top_product_details = product_details[:top_k]
            if highlighted_indices:
                idx_set = set(highlighted_indices)
                highlighted = [p for i, p in enumerate(top_product_details, 1) if i in idx_set]
                rest = [p for i, p in enumerate(top_product_details, 1) if i not in idx_set]
                top_product_details = highlighted + rest
            
            return {
                "final_response": response,
                "product_details": top_product_details,
                "raw_recommendations": raw_recommendations,
                "messages": [{"role": "assistant", "content": response}],
                "highlighted_indices": highlighted_indices,
            }
            
        except Exception as e:
            logger.error(f"Error in GenerateResponse node: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "final_response": f"I encountered an error while generating recommendations: {str(e)}",
                "product_details": [],
                "raw_recommendations": state.get("raw_recommendations", [])
            }

generate_response_node = GenerateResponseNode()

