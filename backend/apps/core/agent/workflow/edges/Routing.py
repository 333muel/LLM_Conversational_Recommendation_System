"""Routing logic for workflow edges."""
from typing import Literal
from apps.core.agent.workflow.state.RecommendationState import RecommendationState


def route_after_recommend(state: RecommendationState) -> Literal["generate_response"]:
    """Route after recommendation node."""
    # Always go to generate response after recommendations
    return "generate_response"


def route_after_generate(state: RecommendationState) -> Literal["end"]:
    """Route after generate response node."""
    # End the workflow
    return "end"

