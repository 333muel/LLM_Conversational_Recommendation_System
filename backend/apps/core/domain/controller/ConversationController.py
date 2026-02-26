"""API controller for conversation/recommendation endpoints."""
from fastapi import APIRouter, HTTPException
from apps.core.domain.model.ConversationModel import (
    RecommendationRequest, RecommendationResponse, 
    BrowseRequest, BrowseResponse,
    ExtractRequest, ExtractResponse,
    FilterRequest, FilterResponse,
    RespondRequest, RespondResponse
)
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
            - conversation_id: Optional conversation ID for multi-turn
            - user_id: Optional user ID (uses demo user if not provided)
            - top_k: Optional number of recommendations (default: 10)
            - model: Optional LLM model name (default: qwen3:latest)
            - algorithm: Optional RecBole algorithm name (e.g., 'LightGCN', 'BPR')
        
    Returns:
        Recommendation response with AI-generated text and product recommendations
    """
    try:
        logger.info(f"Received recommendation request: {request.message[:100]}")
        logger.info(f"Parameters: conv_id={request.conversation_id}, top_k={request.top_k}, algorithm={request.algorithm}, model={request.model}")
        
        # Get agent and process request
        agent = get_recommendation_agent()
        result = await agent.process_request(
            user_message=request.message,
            conversation_id=request.conversation_id,
            user_id=request.user_id,
            top_k=request.top_k,
            model=request.model,
            algorithm=request.algorithm
        )
        
        # Convert to response model
        response = RecommendationResponse(**result)
        
        logger.info(f"Recommendation generated successfully for conv {response.conversation_id}: {len(response.recommendations)} items")
        return response
        
    except Exception as e:
        logger.error(f"Error in recommendation endpoint: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/browse", response_model=BrowseResponse)
async def get_browse_discovery(request: BrowseRequest) -> BrowseResponse:
    """
    Enhanced browse discovery with AI query processing.
    """
    try:
        logger.info(f"Received browse request: {request.message[:100]}")
        
        agent = get_recommendation_agent()
        result = await agent.process_browse(
            user_message=request.message,
            conversation_id=request.conversation_id,
            user_id=request.user_id,
            algorithm=request.algorithm
        )
        
        return BrowseResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in browse endpoint: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract", response_model=ExtractResponse)
async def extract_constraints(request: ExtractRequest) -> ExtractResponse:
    """Extract structured constraints from user message."""
    try:
        agent = get_recommendation_agent()
        result = await agent.extract_constraints(request.message)
        return ExtractResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/filter", response_model=FilterResponse)
async def filter_products(request: FilterRequest) -> FilterResponse:
    """Filter products based on constraints."""
    try:
        agent = get_recommendation_agent()
        user_id = request.user_id or "AFNT6ZJCYQN3WDIKUSWHJDXNND2Q"
        result = await agent.filter_candidates(request.constraints, user_id, request.algorithm)
        return FilterResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/respond", response_model=RespondResponse)
async def generate_response(request: RespondRequest) -> RespondResponse:
    """Generate assistant response for given products."""
    try:
        agent = get_recommendation_agent()
        result = await agent.generate_assistant_response(
            user_message=request.message,
            conversation_id=request.conversation_id,
            user_id=request.user_id,
            product_details=request.product_details,
            metadata=request.metadata
        )
        return RespondResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

