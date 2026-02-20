"""Agent response handling."""
from typing import Dict, Any, Optional
from apps.core.agent.workflow.graph.RecommendationGraph import get_recommendation_graph
from apps.core.agent.workflow.state.RecommendationState import RecommendationState
from apps.config.Tracing import get_logger
from apps.config.Setting import settings

logger = get_logger(__name__)


class RecommendationAgent:
    """Main agent for handling recommendation requests."""
    
    def __init__(self):
        self.graph = get_recommendation_graph()
    
    def process_request(
        self,
        user_message: str,
        user_id: Optional[str] = None,
        top_k: Optional[int] = None,
        model: Optional[str] = None,
        algorithm: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user recommendation request.
        
        Args:
            user_message: User's message/query
            user_id: Optional user ID (will use demo user if not provided)
        
        Returns:
            Dictionary with recommendation response and metadata
        """
        try:
            # Use demo user if not provided
            if not user_id:
                user_id = "AFNT6ZJCYQN3WDIKUSWHJDXNND2Q"  # Demo user from dataset
            
            # Store request parameters in state for nodes to use
            initial_state: RecommendationState = {
                "user_message": user_message,
                "query": None,
                "user_id": user_id,
                "top_k": top_k,
                "algorithm": algorithm,
                "model": model,
                "raw_recommendations": [],
                "product_details": [],
                "final_response": None,
                "messages": []
            }
            
            # Store custom parameters (we'll pass these through state or use them directly)
            # For now, we'll modify the workflow to accept these parameters
            # Note: We need to update nodes to use these parameters
            
            # Run workflow
            logger.info(f"Processing recommendation request for user: {user_id}, top_k={top_k}, algorithm={algorithm}, model={model}")
            result = self.graph.invoke(initial_state)
            
            # Extract results
            raw_recs = result.get("raw_recommendations", [])
            product_details = result.get("product_details", [])
            
            # Debug info
            debug_info = {
                "raw_recommendations_count": len(raw_recs),
                "product_details_count": len(product_details),
                "has_final_response": result.get("final_response") is not None,
                "algorithm_used": algorithm or "LightGCN",
                "model_used": model or settings.ollama_model
            }
            
            # Return top_k recommendations (not all context items)
            requested_top_k = top_k or settings.recommendation_top_k
            top_recommendations = product_details[:requested_top_k]
            
            return {
                "response": result.get("final_response", "No response generated"),
                "recommendations": top_recommendations,  # Return top_k items
                "raw_recommendations": raw_recs[:requested_top_k] if raw_recs else [],
                "user_id": result.get("user_id"),
                "success": len(raw_recs) > 0,
                "debug": debug_info
            }
            
        except Exception as e:
            logger.error(f"Error processing recommendation request: {e}")
            return {
                "response": f"I encountered an error: {str(e)}",
                "recommendations": [],
                "success": False,
                "error": str(e)
            }


# Global agent instance
recommendation_agent: Optional[RecommendationAgent] = None


def get_recommendation_agent() -> RecommendationAgent:
    """Get or create recommendation agent instance."""
    global recommendation_agent
    if recommendation_agent is None:
        recommendation_agent = RecommendationAgent()
    return recommendation_agent

