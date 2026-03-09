"""Node for direct MongoDB product search (Baseline without RecBole)."""
from typing import Dict, Any, List
from apps.core.agent.workflow.nodes.BaseNode import BaseNode
from apps.core.agent.workflow.state.RecommendationState import RecommendationState
from apps.core.agent.workflow.utils.QueryProcessor import QueryProcessor
from apps.database.Mongo import ProductRepository
from apps.config.Tracing import get_logger

logger = get_logger(__name__)

class BaselineSearchNode(BaseNode):
    """Node that searches products directly from MongoDB based on AI intent extraction."""
    
    def __init__(self):
        self.query_processor = QueryProcessor()

    async def execute(self, state: RecommendationState) -> Dict[str, Any]:
        """Search MongoDB directly using extracted constraints."""
        try:
            user_message = state.get("user_message", "")
            
            # 1. AI Query Processing to get constraints
            constraints = await self.query_processor.process(user_message)
            
            # 2. Search MongoDB directly (no RecBole candidate set)
            # Use filter_products but with an empty product_ids list to search entire DB
            # We'll use a larger limit for the baseline search
            limit = 20
            
            # If no constraints, just get top rated products
            if not constraints or not any(constraints.values()):
                logger.info("No constraints found for baseline search, fetching top rated.")
                products = ProductRepository.get_top_rated_by_category("beauty", limit=limit)
            else:
                logger.info(f"Baseline search with constraints: {constraints}")
                # Use category search as base if available
                category = constraints.get("category", "beauty")
                
                # We'll use filter_products with product_ids=None to indicate full DB search
                # Need to update filter_products to handle product_ids=None
                products = ProductRepository.filter_products(
                    product_ids=None,
                    category=category,
                    max_price=constraints.get("max_price"),
                    min_rating=constraints.get("min_rating"),
                    keywords=constraints.get("keywords")
                )
                
                # If still too few, supplement with category top rated
                if len(products) < 5:
                    fallback = ProductRepository.get_top_rated_by_category(category, limit=limit)
                    existing_asins = {p["asin"] for p in products}
                    for p in fallback:
                        if p["asin"] not in existing_asins:
                            products.append(p)
                        if len(products) >= limit:
                            break

            # 3. Format results
            formatted_products = []
            for p in products[:limit]:
                formatted_products.append({
                    "item_id": p.get("asin"),
                    "title": p.get("product_title", "Unknown"),
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
                "raw_recommendations": [] # No RecBole here
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
