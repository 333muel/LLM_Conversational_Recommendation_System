"""LangGraph workflow for recommendation system."""
from langgraph.graph import StateGraph, END
from apps.core.agent.workflow.state.RecommendationState import RecommendationState
from apps.core.agent.workflow.nodes.RecommendItem import recommend_item_node
from apps.core.agent.workflow.nodes.BrowseItem import browse_item_node
from apps.core.agent.workflow.nodes.GenerateResponse import generate_response_node
from apps.core.agent.workflow.edges.Routing import route_after_recommend, route_after_generate
from apps.config.Tracing import get_logger

logger = get_logger(__name__)


def create_recommendation_graph() -> StateGraph:
    """Create the recommendation workflow graph."""
    workflow = StateGraph(RecommendationState)
    
    # Add nodes
    workflow.add_node("recommend_item", recommend_item_node.execute)
    workflow.add_node("generate_response", generate_response_node.execute)
    
    # Set entry point
    workflow.set_entry_point("recommend_item")
    
    # Add edges
    workflow.add_conditional_edges(
        "recommend_item",
        route_after_recommend,
        {
            "generate_response": "generate_response"
        }
    )
    
    workflow.add_conditional_edges(
        "generate_response",
        route_after_generate,
        {
            "end": END
        }
    )
    
    return workflow.compile()


def create_browse_graph() -> StateGraph:
    """Create the enhanced browse discovery workflow graph."""
    workflow = StateGraph(RecommendationState)
    
    # Add nodes
    workflow.add_node("browse_item", browse_item_node.execute)
    workflow.add_node("generate_response", generate_response_node.execute)
    
    # Set entry point
    workflow.set_entry_point("browse_item")
    
    # Add edges
    workflow.add_conditional_edges(
        "browse_item",
        lambda x: "generate_response",
        {
            "generate_response": "generate_response"
        }
    )
    
    workflow.add_conditional_edges(
        "generate_response",
        route_after_generate,
        {
            "end": END
        }
    )
    
    return workflow.compile()


# Global graph instances
recommendation_graph = None
browse_graph = None


def get_recommendation_graph():
    """Get or create recommendation graph instance."""
    global recommendation_graph
    if recommendation_graph is None:
        recommendation_graph = create_recommendation_graph()
    return recommendation_graph


def get_browse_graph():
    """Get or create browse graph instance."""
    global browse_graph
    if browse_graph is None:
        browse_graph = create_browse_graph()
    return browse_graph

