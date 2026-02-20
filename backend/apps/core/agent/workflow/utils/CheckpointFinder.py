"""Utility to find RecBole checkpoints by algorithm name."""
import os
from pathlib import Path
from typing import Optional
from apps.config.Setting import settings
from apps.config.Tracing import get_logger

logger = get_logger(__name__)


class CheckpointFinder:
    """Finds checkpoints by algorithm name."""
    
    @staticmethod
    def find_checkpoint(algorithm: Optional[str] = None) -> str:
        """
        Find checkpoint file for given algorithm.
        
        Args:
            algorithm: Algorithm name (e.g., 'LightGCN', 'BPR'). If None, uses default.
        
        Returns:
            Path to checkpoint file (relative to project root)
        """
        # Get project root
        # __file__ is: ai-chain/apps/core/agent/workflow/utils/CheckpointFinder.py
        # Go up: utils -> workflow -> agent -> core -> apps -> ai-chain -> FYP Recbole
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent.parent.parent.parent.parent
        checkpoints_dir = project_root / "checkpoints"
        
        if not checkpoints_dir.exists():
            logger.warning(f"Checkpoints directory not found: {checkpoints_dir}")
            return settings.recbole_model_checkpoint
        
        # Default algorithm
        if not algorithm:
            algorithm = "LightGCN"
        
        # Look for checkpoint starting with algorithm name
        algorithm_prefix = f"{algorithm}-"
        matching_checkpoints = []
        
        for checkpoint_file in checkpoints_dir.glob("*.pth"):
            if checkpoint_file.name.startswith(algorithm_prefix):
                matching_checkpoints.append(checkpoint_file)
        
        if matching_checkpoints:
            # Sort by modification time, get most recent
            matching_checkpoints.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            selected_checkpoint = matching_checkpoints[0]
            relative_path = selected_checkpoint.relative_to(project_root)
            logger.info(f"Found checkpoint for {algorithm}: {relative_path}")
            return str(relative_path)
        else:
            # Fallback to LightGCN
            logger.warning(f"No checkpoint found for algorithm '{algorithm}', using LightGCN")
            lightgcn_checkpoints = list(checkpoints_dir.glob("LightGCN-*.pth"))
            if lightgcn_checkpoints:
                lightgcn_checkpoints.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                selected_checkpoint = lightgcn_checkpoints[0]
                relative_path = selected_checkpoint.relative_to(project_root)
                logger.info(f"Using LightGCN checkpoint: {relative_path}")
                return str(relative_path)
            else:
                # Use default from settings
                logger.warning(f"No LightGCN checkpoint found, using default: {settings.recbole_model_checkpoint}")
                return settings.recbole_model_checkpoint
    
    @staticmethod
    def list_available_algorithms() -> list[str]:
        """
        List all available algorithms based on checkpoint files.
        
        Returns:
            List of algorithm names
        """
        # Get project root (same as find_checkpoint)
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent.parent.parent.parent.parent
        checkpoints_dir = project_root / "checkpoints"
        
        if not checkpoints_dir.exists():
            return []
        
        algorithms = set()
        for checkpoint_file in checkpoints_dir.glob("*.pth"):
            # Extract algorithm name (everything before first '-')
            parts = checkpoint_file.stem.split('-', 1)
            if len(parts) > 0:
                algorithms.add(parts[0])
        
        return sorted(list(algorithms))

