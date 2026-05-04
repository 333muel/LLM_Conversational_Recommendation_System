"""Node for direct MongoDB product search (Baseline without RecBole)."""
from typing import Dict, Any, List, Optional
from apps.core.agent.workflow.nodes.BaseNode import BaseNode
from apps.core.agent.workflow.state.RecommendationState import RecommendationState
from apps.core.agent.workflow.utils.QueryProcessor import QueryProcessor
from apps.database.Mongo import ProductRepository
from apps.config.Tracing import get_logger

logger = get_logger(__name__)

class BaselineSearchNode(BaseNode):
    """Node that searches products directly from MongoDB based on AI intent extraction."""
    
    def __init__(self, provider: Optional[str] = "ollama"):
        self._provider = provider

    async def execute(self, state: RecommendationState) -> Dict[str, Any]:
        """Search MongoDB directly using extracted constraints."""
        try:
            user_message = state.get("user_message", "")
            llm_provider = state.get("llm_provider", self._provider)
            
            processor = QueryProcessor(provider=llm_provider)
            constraints = await processor.process(user_message)
            
            limit = 20
            
            if not constraints or not any(constraints.values()):
                logger.info("No constraints found for baseline search, fetching top rated.")
                products = ProductRepository.get_top_rated_by_category("beauty", limit=limit)
            else:
                logger.info(f"Baseline search with constraints: {constraints}")
                category = constraints.get("category", "beauty")
                
                products = ProductRepository.filter_products(
                    product_ids=None,
                    category=category,
                    max_price=constraints.get("max_price"),
                    min_rating=constraints.get("min_rating"),
                    keywords=constraints.get("keywords")
                )
                
                if len(products) < 5:
                    fallback = ProductRepository.get_top_rated_by_category(category, limit=limit)
                    existing_asins = {p["asin"] for p in products}
                    for p in fallback:
                        if p["asin"] not in existing_asins:
                            products.append(p)
                        if len(products) >= limit:
                            break

            formatted_products = []
            seen_titles: set = set()
            for p in products[:limit]:
                raw_title: str = p.get("product_title", "Unknown")
                normalised_title = " ".join(raw_title.lower().split())
                if normalised_title in seen_titles:
                    logger.debug(
                        f"Skipping duplicate title for item {p.get('asin')}: '{raw_title}'"
                    )
                    continue
                seen_titles.add(normalised_title)
                formatted_products.append({
                    "item_id": p.get("asin"),
                    "title": raw_title,
                    "description": p.get("product_description", ""),
                    "rating": p.get("product_avg_rating"),
                    "price": p.get("product_price", ""),
                    "categories": p.get("product_categories", ""),
                    "main_category": p.get("product_main_category", ""),
                    "image": p.get("product_image_url", ""),
                    "score": 0.0,
                    "rank": 0
                })

            return {
                "product_details": formatted_products,
                "constraints": constraints,
                "product_metadata": {"source": "baseline_mongodb"},
                "raw_recommendations": []
            }
            
        except Exception as e:
            logger.error(f"Error in BaselineSearchNode: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "product_details": [],
                "constraints": {},
                "product_metadata": {"error": str(e)}
            }

baseline_search_node = BaselineSearchNode()
