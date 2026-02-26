import json
import os
from datetime import datetime
from typing import Any, Dict
from pathlib import Path
from apps.config.Tracing import get_logger

logger = get_logger(__name__)


class ConversationLogger:
    """Utility to log full conversation interactions to the filesystem."""
    
    @staticmethod
    def log_interaction(interaction_data: Dict[str, Any]) -> None:
        """
        Log a single interaction (input and output) to a JSON file.
        
        Args:
            interaction_data: Dictionary containing all relevant interaction details
        """
        try:
            # Get conversation ID
            conversation_id = interaction_data.get("conversation_id", "unknown")
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
            
            # Define log directory: backend/logs/conversations
            # Current file is in backend/apps/core/agent/workflow/utils/
            # Path to logs: backend/logs/
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent.parent.parent.parent
            log_dir = project_root / "logs" / "conversations"
            
            # Ensure log directory exists
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Create unique filename
            filename = f"conv_{conversation_id}_{timestamp}.json"
            file_path = log_dir / filename
            
            # Save interaction data as JSON
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(interaction_data, f, indent=4, ensure_ascii=False)
            
            logger.info(f"Interaction logged to filesystem: {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to log interaction to filesystem: {e}")
