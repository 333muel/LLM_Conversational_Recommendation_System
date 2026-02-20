"""Node for generating recommendations using RecBole."""
from typing import Dict, Any
from apps.core.agent.workflow.nodes.BaseNode import BaseNode
from apps.core.agent.workflow.state.RecommendationState import RecommendationState
from apps.core.agent.workflow.tools.RecBoleModel import get_recbole_engine
from apps.config.Setting import settings
from apps.config.Tracing import get_logger

logger = get_logger(__name__)


class RecommendItemNode(BaseNode):
    """Node that generates recommendations using RecBole model."""
    
    def execute(self, state: RecommendationState) -> Dict[str, Any]:
        """Generate recommendations for the user."""
        try:
            user_id = state.get("user_id")
            if not user_id:
                logger.warning("No user_id in state, using default demo user")
                # Use a demo user ID from the dataset
                user_id = "AFNT6ZJCYQN3WDIKUSWHJDXNND2Q"
            
            # Get parameters from state
            top_k = state.get("top_k")
            algorithm = state.get("algorithm")
            
            # Use provided top_k or default
            if top_k is None:
                top_k = settings.recommendation_top_k
            
            logger.info(f"Generating recommendations for user: {user_id}, algorithm: {algorithm}, top_k: {top_k}")
            
            # Get RecBole engine for the specified algorithm
            engine = get_recbole_engine(algorithm=algorithm)
            
            # Generate recommendations
            # Use context_k to get more items for LLM context, but we'll return top_k
            context_k = max(top_k, settings.recommendation_context_k)
            recommendations = engine.recommend(
                user_id=user_id,
                top_k=context_k,  # Get more items for LLM context
                filter_interacted=True
            )
            
            logger.info(f"Generated {len(recommendations)} recommendations")
            
            return {
                "raw_recommendations": recommendations,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error in RecommendItem node: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Return valid state fields only (no "error" field)
            return {
                "raw_recommendations": [],
                "user_id": state.get("user_id", "AFNT6ZJCYQN3WDIKUSWHJDXNND2Q")
            }


# Node instance
recommend_item_node = RecommendItemNode()

