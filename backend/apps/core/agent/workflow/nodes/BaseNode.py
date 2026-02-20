"""Base node class for LangGraph workflow."""
from abc import ABC, abstractmethod
from typing import Dict, Any
from apps.core.agent.workflow.state.RecommendationState import RecommendationState


class BaseNode(ABC):
    """Base class for workflow nodes."""
    
    @abstractmethod
    def execute(self, state: RecommendationState) -> Dict[str, Any]:
        """
        Execute the node logic.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state dictionary
        """
        pass

