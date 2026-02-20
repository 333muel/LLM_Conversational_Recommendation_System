"""API controller for conversation/recommendation endpoints."""
from fastapi import APIRouter, HTTPException
from apps.core.domain.model.ConversationModel import RecommendationRequest, RecommendationResponse
from apps.core.agent.AgentResponse import get_recommendation_agent
from apps.config.Tracing import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/conversation", tags=["conversation"])


@router.post("/recommend", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest) -> RecommendationResponse:
    """
    Get product recommendations based on user message.
    
    Args:
        request: Recommendation request with user message and optional parameters:
            - message: User's query
            - user_id: Optional user ID (uses demo user if not provided)
            - top_k: Optional number of recommendations (default: 10)
            - model: Optional LLM model name (default: qwen3:latest)
            - algorithm: Optional RecBole algorithm name (e.g., 'LightGCN', 'BPR')
        
    Returns:
        Recommendation response with AI-generated text and product recommendations
    """
    try:
        logger.info(f"Received recommendation request: {request.message[:100]}")
        logger.info(f"Parameters: top_k={request.top_k}, algorithm={request.algorithm}, model={request.model}")
        
        # Get agent and process request
        agent = get_recommendation_agent()
        result = agent.process_request(
            user_message=request.message,
            user_id=request.user_id,
            top_k=request.top_k,
            model=request.model,
            algorithm=request.algorithm
        )
        
        # Convert to response model
        response = RecommendationResponse(**result)
        
        logger.info(f"Recommendation generated successfully: {len(response.recommendations)} items")
        return response
        
    except Exception as e:
        logger.error(f"Error in recommendation endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

