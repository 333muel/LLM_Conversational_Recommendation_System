"""Node for generating recommendations using RecBole."""
import anyio
from typing import Dict, Any, List, Optional
from apps.core.agent.workflow.nodes.BaseNode import BaseNode
from apps.core.agent.workflow.state.RecommendationState import RecommendationState
from apps.core.agent.workflow.tools.RecBoleModel import get_recbole_engine
from apps.core.agent.workflow.utils.QueryProcessor import QueryProcessor
from apps.database.Mongo import ProductRepository
from apps.config.Setting import settings
from apps.config.Tracing import get_logger

logger = get_logger(__name__)


class RecommendItemNode(BaseNode):
    """Node that generates recommendations using RecBole model.
    
    When the user provides refinement constraints (e.g., brand name like "CeraVe",
    category, keywords), filters RecBole candidates to match those constraints.
    """

    def _has_refinement_constraints(self, constraints: Dict[str, Any]) -> bool:
        """Check if constraints indicate a refinement request (brand, category, keywords)."""
        return bool(
            constraints.get("keywords")
            or constraints.get("category")
        )

    def _filter_by_constraints(
        self,
        raw_recommendations: List[Dict[str, Any]],
        constraints: Dict[str, Any],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """Filter RecBole recommendations by extracted constraints."""
        candidate_asins = [r["item_id"] for r in raw_recommendations]
        rec_map = {r["item_id"]: r for r in raw_recommendations}

        matching = ProductRepository.filter_products(
            product_ids=candidate_asins,
            category=constraints.get("category"),
            max_price=constraints.get("max_price"),
            min_rating=constraints.get("min_rating"),
            keywords=constraints.get("keywords"),
        )

        if len(matching) >= 3:
            # Use filtered results, preserve RecBole order among matches
            filtered = []
            for p in matching:
                asin = p.get("asin")
                if asin in rec_map:
                    filtered.append(rec_map[asin])
                else:
                    filtered.append({"item_id": asin, "score": 0.0, "rank": len(filtered) + 1})
            return filtered[:top_k]

        # Fallback: search entire DB when few matches in RecBole candidates
        if constraints.get("keywords") or constraints.get("category"):
            logger.info("Few matches in RecBole candidates, searching entire DB.")
            db_results = ProductRepository.filter_products(
                product_ids=None,
                category=constraints.get("category"),
                max_price=constraints.get("max_price"),
                min_rating=constraints.get("min_rating"),
                keywords=constraints.get("keywords"),
            )
            if db_results:
                return [
                    {"item_id": p.get("asin"), "score": 0.0, "rank": i + 1}
                    for i, p in enumerate(db_results[:top_k])
                ]

        # Last resort: return unfiltered (better than empty)
        logger.info("No constraint matches, using unfiltered RecBole recommendations.")
        return raw_recommendations[:top_k]

    async def execute(self, state: RecommendationState) -> Dict[str, Any]:
        """Generate recommendations for the user, optionally filtered by constraints."""
        try:
            user_id = state.get("user_id")
            if not user_id:
                logger.warning("No user_id in state, using default demo user")
                user_id = "AFNT6ZJCYQN3WDIKUSWHJDXNND2Q"

            top_k = state.get("top_k") or settings.recommendation_top_k
            algorithm = state.get("algorithm")
            user_message = state.get("user_message", "")
            llm_provider = state.get("llm_provider", "ollama")

            logger.info(f"Generating recommendations for user: {user_id}, algorithm: {algorithm}, top_k: {top_k}")

            engine = get_recbole_engine(algorithm=algorithm)
            context_k = max(top_k, settings.recommendation_context_k)

            recommendations = await anyio.to_thread.run_sync(
                lambda: engine.recommend(
                    user_id=user_id,
                    top_k=context_k,
                    filter_interacted=True,
                )
            )

            logger.info(f"Generated {len(recommendations)} raw recommendations from RecBole")

            # Extract constraints and filter when user refines (e.g., "Yes CeraVe")
            processor = QueryProcessor(provider=llm_provider)
            constraints = await processor.process(user_message)

            if self._has_refinement_constraints(constraints):
                logger.info(f"Applying constraint filter: {constraints}")
                recommendations = self._filter_by_constraints(
                    recommendations, constraints, top_k
                )
                logger.info(f"After constraint filter: {len(recommendations)} recommendations")
            else:
                recommendations = recommendations[:top_k]

            return {
                "raw_recommendations": recommendations,
                "user_id": user_id,
                "constraints": constraints,
            }

        except Exception as e:
            logger.error(f"Error in RecommendItem node: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "raw_recommendations": [],
                "user_id": state.get("user_id", "AFNT6ZJCYQN3WDIKUSWHJDXNND2Q"),
                "constraints": None,
            }


# Node instance
recommend_item_node = RecommendItemNode()

