"""Data models for conversation API."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class RecommendationRequest(BaseModel):
    """Request model for recommendation endpoint."""
    message: str = Field(..., description="User's message or query")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID to continue a conversation")
    user_id: Optional[str] = Field(None, description="Optional user ID (uses demo user if not provided)")
    top_k: Optional[int] = Field(None, ge=1, le=50, description="Number of recommendations to return (default: 10)")
    model: Optional[str] = Field(None, description="LLM model to use (default: qwen3:latest)")
    algorithm: Optional[str] = Field(None, description="RecBole algorithm/checkpoint to use (e.g., 'LightGCN', 'BPR'). If not found, defaults to LightGCN")


class ProductRecommendation(BaseModel):
    """Model for a product recommendation."""
    item_id: str
    title: str
    description: Optional[str] = None
    rating: Optional[float] = None
    price: Optional[str] = None
    categories: Optional[str] = None
    main_category: Optional[str] = None
    image: Optional[str] = None
    score: float
    rank: int


class RecommendationResponse(BaseModel):
    """Response model for recommendation endpoint."""
    response: str = Field(..., description="AI-generated recommendation response")
    conversation_id: str = Field(..., description="Conversation ID for ongoing conversation")
    recommendations: List[ProductRecommendation] = Field(default_factory=list)
    raw_recommendations: List[Dict[str, Any]] = Field(default_factory=list, description="Raw recommendations from RecBole before LLM processing")
    debug: Dict[str, Any] = Field(default_factory=dict, description="Debug information about the recommendation process")
    user_id: Optional[str] = None
    success: bool = True
    error: Optional[str] = None


class BrowseRequest(BaseModel):
    """Request model for enhanced browse assistant endpoint."""
    message: str = Field(..., description="User's message or query")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID")
    user_id: Optional[str] = Field(None, description="Optional user ID")
    algorithm: Optional[str] = Field(None, description="RecBole algorithm to use")


class BrowseResponse(BaseModel):
    """Response model for enhanced browse assistant endpoint."""
    response: str = Field(..., description="AI-generated explanation or response")
    conversation_id: str
    products: List[ProductRecommendation] = Field(..., description="The narrowed/filtered products shown on the left")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Structured constraints extracted by AI")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata about the source of products (filtered, fallback, etc.)")
    success: bool = True
    error: Optional[str] = None


class ExtractRequest(BaseModel):
    message: str
    user_id: Optional[str] = None


class ExtractResponse(BaseModel):
    constraints: Dict[str, Any]
    intent: str
    success: bool = True


class FilterRequest(BaseModel):
    constraints: Dict[str, Any]
    user_id: Optional[str] = None
    algorithm: Optional[str] = None


class FilterResponse(BaseModel):
    products: List[ProductRecommendation]
    metadata: Dict[str, Any]
    success: bool = True


class RespondRequest(BaseModel):
    message: str
    conversation_id: str
    user_id: str
    product_details: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None


class RespondResponse(BaseModel):
    response: str
    conversation_id: str
    success: bool = True


class SelectItemRequest(BaseModel):
    item_id: str
    conversation_id: str
    user_id: str


class SelectItemResponse(BaseModel):
    success: bool = True


class FeedbackRequest(BaseModel):
    """Request model for item feedback (thumbs up/down)."""
    item_id: str
    conversation_id: str
    user_id: str
    feedback_type: str = Field(..., pattern="^(like|dislike)$")


class FeedbackResponse(BaseModel):
    """Response model for feedback submission."""
    success: bool = True
    message: str = "Feedback recorded"


class ExplainRequest(BaseModel):
    """Request model for explaining why a product was recommended."""
    item_id: str
    conversation_id: str
    user_id: str
    message: Optional[str] = "Why was this recommended?"


class ExplainResponse(BaseModel):
    """Response model for recommendation explanation."""
    explanation: str
    product_id: str
    attribute_scores: Optional[Dict[str, float]] = None
    success: bool = True

