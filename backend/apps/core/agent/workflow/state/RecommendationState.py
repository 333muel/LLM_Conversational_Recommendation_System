"""State management for recommendation workflow."""
from typing import List, Dict, Optional, TypedDict, Annotated
from langgraph.graph.message import add_messages


class RecommendationState(TypedDict):
    """State for the recommendation workflow."""
    # User input
    user_message: str
    
    # Processed query
    query: Optional[str]
    
    # User ID for recommendations (demo user)
    user_id: Optional[str]
    
    # Request parameters
    top_k: Optional[int]
    algorithm: Optional[str]
    model: Optional[str]
    
    # Raw recommendations from RecBole
    raw_recommendations: List[Dict[str, any]]
    
    # Product details for recommended items
    product_details: List[Dict[str, any]]
    
    # Final AI-generated recommendation response
    final_response: Optional[str]
    
    # Messages for LLM conversation
    messages: Annotated[List[Dict], add_messages]

