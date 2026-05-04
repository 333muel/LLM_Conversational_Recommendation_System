"""State management for recommendation workflow."""
from typing import List, Dict, Optional, TypedDict, Annotated, Any
from langgraph.graph.message import add_messages


class RecommendationState(TypedDict):
    """State for the recommendation workflow."""
    # User input
    user_message: str
    
    # Processed query constraints
    constraints: Optional[Dict[str, Any]]
    
    # User ID for recommendations (demo user)
    user_id: Optional[str]
    
    # Request parameters
    top_k: Optional[int]
    algorithm: Optional[str]
    model: Optional[str]
    llm_provider: Optional[str]
    
    # Raw recommendations from RecBole (candidates)
    raw_recommendations: List[Dict[str, any]]
    
    # Product details for recommended items
    product_details: List[Dict[str, any]]
    
    # Metadata about product sourcing
    product_metadata: Optional[Dict[str, Any]]
    
    # Mode flag: 'recbole' or 'baseline'
    mode: Optional[str]
    
    # Exclude these item IDs (e.g. when user asks to regenerate/different products)
    exclude_item_ids: Optional[List[str]]
    
    # Final AI-generated recommendation response
    final_response: Optional[str]
    
    # 1-based indices of products the LLM highlighted in its response
    highlighted_indices: Optional[List[int]]
    
    # Messages for LLM conversation
    messages: Annotated[List[Dict], add_messages]

