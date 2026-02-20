"""API controller for algorithm-related endpoints."""
from fastapi import APIRouter
from apps.core.agent.workflow.utils.CheckpointFinder import CheckpointFinder
from apps.config.Tracing import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/algorithms", tags=["algorithms"])


@router.get("/available")
async def get_available_algorithms():
    """
    Get list of available algorithms based on checkpoint files.
    
    Returns:
        List of available algorithm names
    """
    try:
        algorithms = CheckpointFinder.list_available_algorithms()
        return {
            "algorithms": algorithms,
            "count": len(algorithms)
        }
    except Exception as e:
        logger.error(f"Error listing algorithms: {e}")
        return {
            "algorithms": [],
            "count": 0,
            "error": str(e)
        }

