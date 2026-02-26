import anyio
from typing import Dict, Any, List
from apps.core.agent.workflow.nodes.BaseNode import BaseNode
from apps.core.agent.workflow.state.RecommendationState import RecommendationState
from apps.core.agent.workflow.tools.RecBoleModel import get_recbole_engine
from apps.core.agent.workflow.utils.QueryProcessor import QueryProcessor
from apps.database.Mongo import ProductRepository
from apps.config.Setting import settings
from apps.config.Tracing import get_logger

logger = get_logger(__name__)

class BrowseItemNode(BaseNode):
    """Enhanced node for discovery-based browsing with AI query processing."""
    
    def __init__(self):
        self.query_processor = QueryProcessor()

    async def execute(self, state: RecommendationState) -> Dict[str, Any]:
        """Execute the enhanced discovery logic."""
        try:
            user_id = state.get("user_id") or "AFNT6ZJCYQN3WDIKUSWHJDXNND2Q"
            user_message = state.get("user_message", "")
            algorithm = state.get("algorithm")
            
            # Fast Path: If query is empty or just generic recommendation request, skip AI processing
            is_generic = not user_message or user_message.lower().strip() in ["show me some recommendations", "recommend some products", "browse"]
            
            if is_generic:
                # ... existing logic ...
                logger.info("Generic request detected, skipping AI query processing.")
                engine = get_recbole_engine(algorithm=algorithm)
                # Run sync in thread to avoid blocking loop
                candidates = await anyio.to_thread.run_sync(
                    engine.recommend, user_id, 20
                )
                candidate_asins = [c["item_id"] for c in candidates]
                products = ProductRepository.get_products_by_ids(candidate_asins)
                
                # Format products
                formatted_products = []
                for p in products:
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
                    "constraints": {},
                    "product_metadata": {"source": "recbole_default"},
                    "user_id": user_id,
                    "final_response": "I've picked out some top recommendations from across our beauty collection just for you! Have a look through these curated picks, and let me know if you're looking for something more specific like a particular category or price range."
                }

            # 1. AI Query Processing
            constraints = await self.query_processor.process(user_message)
            
            # 2. Get large candidate set from RecBole (Top 100)
            engine = get_recbole_engine(algorithm=algorithm)
            candidates = await anyio.to_thread.run_sync(
                engine.recommend, user_id, 100
            )
            candidate_asins = [c["item_id"] for c in candidates]
            
            # 3. Filter candidates based on constraints
            matching_products = ProductRepository.filter_products(
                product_ids=candidate_asins,
                category=constraints.get("category"),
                max_price=constraints.get("max_price"),
                min_rating=constraints.get("min_rating"),
                keywords=constraints.get("keywords")
            )
            
            # 4. Narrowing and Fallback Logic
            final_products = []
            metadata = {
                "matched_count": len(matching_products),
                "source": "recbole_filtered",
                "constraints_applied": constraints
            }
            
            # If we found matches, take them (up to 20)
            final_products = matching_products[:20]
            
            # Fallback 1: If matches < 5 and we have a category, search the whole DB
            if len(final_products) < 5 and constraints.get("category"):
                logger.info(f"Fewer than 5 matches for category {constraints.get('category')}, searching entire DB.")
                db_fallback = ProductRepository.get_top_rated_by_category(
                    constraints["category"], 
                    limit=10
                )
                # Add unique fallback products
                existing_asins = {p["asin"] for p in final_products}
                added_from_db = 0
                for p in db_fallback:
                    if p["asin"] not in existing_asins:
                        final_products.append(p)
                        existing_asins.add(p["asin"])
                        added_from_db += 1
                metadata["added_from_db_fallback"] = added_from_db
                metadata["source"] = "mixed_db_fallback"

            # Fallback 2: If we still have less than 20, fill with top RecBole recommendations (unfiltered)
            if len(final_products) < 20:
                logger.info(f"Still fewer than 20 products ({len(final_products)}), filling with top recommendations.")
                existing_asins = {p["asin"] for p in final_products}
                
                # Fetch full details for the top recommendations to fill up
                full_candidates = ProductRepository.get_products_by_ids(candidate_asins[:50])
                # Map back to preserve order from RecBole
                candidate_map = {p["asin"]: p for p in full_candidates}
                
                added_from_rec = 0
                for asin in candidate_asins:
                    if asin not in existing_asins and asin in candidate_map:
                        final_products.append(candidate_map[asin])
                        existing_asins.add(asin)
                        added_from_rec += 1
                    if len(final_products) >= 20:
                        break
                metadata["added_from_recbole_unfiltered"] = added_from_rec

            # Transform to unified format for state
            # Map MongoDB document to the format used in product_details
            formatted_products = []
            for p in final_products:
                formatted_products.append({
                    "item_id": p.get("asin"),
                    "title": p.get("product_title", "Unknown"),
                    "description": p.get("product_description", ""),
                    "rating": p.get("product_avg_rating"),
                    "price": p.get("product_price", ""),
                    "categories": p.get("product_categories", ""),
                    "main_category": p.get("product_main_category", ""),
                    "image": p.get("product_image_url", ""),
                    "score": 0.0, # Will be filled if needed, or ignored by LLM
                    "rank": 0
                })

            return {
                "product_details": formatted_products,
                "constraints": constraints,
                "product_metadata": metadata,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error in BrowseItem node: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "product_details": [],
                "constraints": {},
                "product_metadata": {"error": str(e)}
            }

browse_item_node = BrowseItemNode()
