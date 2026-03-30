"""Node for generating final AI response."""
from typing import Dict, Any, List, Optional
from apps.core.agent.workflow.nodes.BaseNode import BaseNode
from apps.core.agent.workflow.state.RecommendationState import RecommendationState
from apps.database.Mongo import ProductRepository
from apps.config.Tracing import get_logger

logger = get_logger(__name__)


class GenerateResponseNode(BaseNode):
    """Node that generates final AI response based on recommendations."""
    
    def _get_product_details(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get product details for recommended items."""
        product_details = []
        
        for rec in recommendations:
            item_id = rec.get("item_id")
            if item_id:
                product = ProductRepository.get_product_by_id(item_id)
                if product:
                    product_details.append({
                        "item_id": item_id,
                        "title": product.get("product_title", ""),
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
                    # Item not in MongoDB catalog — skip it entirely rather than
                    # returning a placeholder that misleads the user or LLM
                    logger.debug(f"Item {item_id} not found in MongoDB catalog, skipping")
        
        return product_details
    
    def _create_recommendation_prompt(
        self,
        user_message: str,
        product_details: List[Dict[str, Any]],
        top_n: int = 10,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create prompt for LLM to generate recommendation response."""
        from apps.config.Setting import settings
        
        # Build info about product sourcing
        source_info = ""
        if metadata:
            source = metadata.get("source", "recommendation")
            matched = metadata.get("matched_count", 0)
            if source == "mixed_db_fallback":
                source_info = f"\nNote for Assistant: We couldn't find enough items in the user's personalized recommendations that match their specific filter. I have supplemented the results with top-rated items from the entire store database."
            elif matched > 0:
                source_info = f"\nNote for Assistant: I found {matched} products from the user's personalized recommendations that match their request."
            else:
                source_info = f"\nNote for Assistant: None of the user's usual personalized recommendations matched this query, so I am showing their top general recommendations."

        # Separate top items (to highlight) from context items
        top_items = product_details[:top_n]
        context_items = product_details[top_n:] if len(product_details) > top_n else []
        
        # Build text for top recommendations
        top_products_text = ""
        for i, product in enumerate(top_items, 1):
            asin = product.get("item_id", "")
            top_products_text += f"\n{i}. [ASIN {asin}] {product.get('title', 'Unknown Product')}"
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
        
        # Build context summary if there are additional items
        context_summary = ""
        if context_items:
            categories = {}
            for product in context_items:
                cat = product.get('categories', '').split(';')[0] if product.get('categories') else 'Other'
                categories[cat] = categories.get(cat, 0) + 1
            
            context_summary = f"\n\nAdditional context: I also found {len(context_items)} more products in categories like: {', '.join(list(categories.keys())[:5])}. "
            context_summary += "You can mention these categories if relevant to the user's request, but focus on the top recommendations above."
        
        prompt = f"""You are a helpful recommendation assistant. A user has asked: "{user_message}"

Based on the user's request, I have found the following top recommended products (ranked by relevance):

{top_products_text}{context_summary}

CRITICAL RULES (strictly enforced):
1. Only mention products from the numbered list above. Copy each **bold** product name EXACTLY as shown (you may shorten very long titles with "..." but do NOT substitute different brands or products). Never invent or name products not in this list.
2. NEVER state, estimate, or invent a price. If the product shows "(not listed — do NOT state a price)", omit any price claim entirely for that product. Only quote a price when it is explicitly shown in the list above.

Please provide a VERY SHORT, friendly response (maximum 60 words total) that:
1. Acknowledges the request in one sentence.
2. Lists 2-3 top picks using bullet points (•) with ONE key point each.
3. Use **bold** for product names exactly as in the list. Keep each bullet to one short line.
4. No long paragraphs. Be conversational but scannable.

Example format:
• **Exact Title From List** – key benefit
• **Exact Title From List** – key benefit

Be brief and focused. Do not repeat full product details from the list."""

        return prompt
    
    async def execute(self, state: RecommendationState) -> Dict[str, Any]:
        """Generate final AI response."""
        try:
            user_message = state.get("user_message", "")
            raw_recommendations = state.get("raw_recommendations", [])
            messages = state.get("messages", [])
            
            # Get product details for all recommendations
            # If product_details are already provided (e.g. by BrowseItemNode), use them
            product_details = state.get("product_details", [])
            if not product_details and raw_recommendations:
                product_details = self._get_product_details(raw_recommendations)
            
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
            
            # Get parameters from state
            top_k = state.get("top_k")
            model = state.get("model")
            
            # Use provided top_k or default
            from apps.config.Setting import settings
            if top_k is None:
                top_k = settings.recommendation_top_k
            
            # Generate context from recommendations for the AI
            recommendations_context = self._create_recommendation_prompt(
                user_message, 
                product_details,
                top_n=top_k,
                metadata=state.get("product_metadata")
            )
            
            # Prepare chat messages
            chat_messages = []
            
            # Add a system prompt with context about the recommendations
            chat_messages.append({
                "role": "system",
                "content": f"You are a helpful and friendly recommendation assistant. {recommendations_context}"
            })
            
            # Add conversation history
            # Filter out any existing system messages from history if we want to use our new one
            for msg in messages:
                if msg.get("role") != "system":
                    chat_messages.append(msg)
            
            # Generate response using LLM - use provider-specific model (state "model" may be wrong if from different provider)
            llm_provider = state.get("llm_provider", "ollama")
            if llm_provider == "dashscope":
                llm_model = model if model and ":" not in model else settings.dashscope_model  # ":" indicates Ollama tag
            else:
                llm_model = model or settings.ollama_model
            logger.info(f"Generating AI response using provider: {llm_provider}, model: {llm_model}")
            
            from apps.core.llm import get_llm_client
            client = get_llm_client(provider=llm_provider, model=llm_model)
            
            # Recommendation blurbs are short and conversational — no benefit from
            # extended chain-of-thought on thinking models.
            response = await client.chat(messages=chat_messages, enable_thinking=False)
            
            logger.info("AI response generated successfully")
            
            # Return top_k product details
            top_product_details = product_details[:top_k]
            
            # The agent will handle updating the message history
            return {
                "final_response": response,
                "product_details": top_product_details,
                "raw_recommendations": raw_recommendations,
                "messages": [{"role": "assistant", "content": response}]
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


# Node instance
generate_response_node = GenerateResponseNode()

