"""Data models for conversation API."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class RecommendationRequest(BaseModel):
    """Request model for recommendation endpoint."""
    message: str = Field(..., description="User's message or query")
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
    score: float
    rank: int


class RecommendationResponse(BaseModel):
    """Response model for recommendation endpoint."""
    response: str = Field(..., description="AI-generated recommendation response")
    recommendations: List[ProductRecommendation] = Field(default_factory=list)
    raw_recommendations: List[Dict[str, Any]] = Field(default_factory=list, description="Raw recommendations from RecBole before LLM processing")
    debug: Dict[str, Any] = Field(default_factory=dict, description="Debug information about the recommendation process")
    user_id: Optional[str] = None
    success: bool = True
    error: Optional[str] = None

