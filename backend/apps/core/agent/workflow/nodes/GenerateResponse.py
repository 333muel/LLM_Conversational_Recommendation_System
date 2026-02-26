"""Node for generating final AI response."""
from typing import Dict, Any, List, Optional
from apps.core.agent.workflow.nodes.BaseNode import BaseNode
from apps.core.agent.workflow.state.RecommendationState import RecommendationState
from apps.core.llm.Ollama import ollama_client
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
                    # Product not found in DB, use minimal info
                    product_details.append({
                        "item_id": item_id,
                        "title": f"Product {item_id}",
                        "description": "",
                        "rating": 0.0,
                        "price": "",
                        "categories": "",
                        "main_category": "",
                        "image": "",
                        "score": rec.get("score", 0.0),
                        "rank": rec.get("rank", 0)
                    })
        
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
            top_products_text += f"\n{i}. {product.get('title', 'Unknown Product')}"
            if product.get('description'):
                top_products_text += f"\n   Description: {product.get('description', '')[:200]}"
            if product.get('rating'):
                top_products_text += f"\n   Rating: {product.get('rating')}/5.0"
            if product.get('price'):
                top_products_text += f"\n   Price: {product.get('price')}"
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

Please provide a natural, helpful response to the user that:
1. Acknowledges their request and shows you understand what they're looking for
2. Presents the top 3 recommended products in a friendly, conversational way
3. Highlights key features, benefits, or unique selling points of the top recommendations
4. Groups products by category when relevant to make it easier to understand
5. Mentions price and rating when they add value to the recommendation
6. Keeps the response concise but informative (aim for 3-5 sentences per product mentioned)
7. If the user's request doesn't perfectly match the products, acknowledge this but explain why these recommendations might still be useful

Format your response as a natural conversation, not a bullet list. Make it engaging and helpful. Focus on the top-ranked products but use the additional context to provide better insights."""

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
            
            # Generate response using Ollama chat
            llm_model = model or settings.ollama_model
            logger.info(f"Generating AI response using model: {llm_model}")
            
            from apps.core.llm.Ollama import OllamaClient
            client = OllamaClient(model=llm_model)
            
            response = await client.chat(messages=chat_messages)
            
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

