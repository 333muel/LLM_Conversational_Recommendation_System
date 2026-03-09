"""Routing logic for workflow edges."""
from typing import Literal
from apps.core.agent.workflow.state.RecommendationState import RecommendationState


def route_after_recommend(state: RecommendationState) -> Literal["generate_response"]:
    """Route after recommendation node."""
    # Always go to generate response after recommendations
    return "generate_response"


def route_after_generate(state: RecommendationState) -> Literal["update_user_profile"]:
    """Route after generate response node."""
    # Go to update user profile node after generating response
    return "update_user_profile"

