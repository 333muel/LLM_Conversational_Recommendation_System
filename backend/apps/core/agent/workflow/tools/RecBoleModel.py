"""RecBole model loader and recommendation engine."""
import os
import torch
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
from recbole.config import Config
from recbole.data import create_dataset, data_preparation
from recbole.utils import init_logger, init_seed, get_model
from recbole.trainer import Trainer
from apps.config.Setting import settings
from apps.config.Tracing import get_logger
from apps.core.agent.workflow.utils.CheckpointFinder import CheckpointFinder

logger = get_logger(__name__)


class RecBoleRecommendationEngine:
    """RecBole model loader and recommendation engine."""
    
    def __init__(self, algorithm: Optional[str] = None):
        self.model = None
        self.dataset = None
        self.config = None
        self.train_data = None
        self.valid_data = None
        self.test_data = None
        self.trainer = None
        self.algorithm = algorithm or settings.recbole_model_name
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the trained RecBole model."""
        try:
            logger.info(f"Loading RecBole model (algorithm: {self.algorithm})...")
            
            # Get absolute paths - adjust paths relative to project root
            # __file__ is: ai-chain/apps/core/agent/workflow/tools/RecBoleModel.py
            # We need to go up 7 levels to get to "FYP Recbole" root
            current_file = Path(__file__).resolve()
            # Go up: tools -> workflow -> agent -> core -> apps -> ai-chain -> FYP Recbole
            project_root = current_file.parent.parent.parent.parent.parent.parent.parent
            
            # Find checkpoint for the algorithm
            checkpoint_relative = CheckpointFinder.find_checkpoint(self.algorithm)
            checkpoint_path = project_root / checkpoint_relative
            
            # Build paths relative to project root
            dataset_path = project_root / settings.recbole_dataset_path
            
            # Convert to strings for RecBole
            dataset_path_str = str(dataset_path)
            checkpoint_path_str = str(checkpoint_path)
            
            if not dataset_path.exists():
                raise FileNotFoundError(f"Dataset path not found: {dataset_path_str}")
            if not checkpoint_path.exists():
                raise FileNotFoundError(f"Checkpoint path not found: {checkpoint_path_str}")
            
            # Create config - must match training.yaml exactly
            # RecBole expects:
            # - dataset name to match the .inter file prefix (amazon_sentiment_200k)
            # - data_path to point to the parent directory containing the dataset folder
            # - The dataset folder should be named after the dataset
            config_dict = {
                "model": self.algorithm,  # Use the algorithm name
                "dataset": "amazon_sentiment_200k",  # Match the .inter file prefix
                "data_path": str(dataset_path.parent),  # Parent directory containing dataset folder (data/)
                "checkpoint_dir": str(checkpoint_path.parent),  # Directory containing checkpoint (checkpoints/)
                # Match training.yaml exactly
                "field_separator": "\t",
                "seq_separator": " ",
                "USER_ID_FIELD": "user_id",
                "ITEM_ID_FIELD": "item_id",
                "RATING_FIELD": "rating",
                "NEG_PREFIX": "neg_",
                "LABEL_FIELD": "label",
                "load_col": {
                    "inter": ["user_id", "item_id", "rating"]  # No timestamp in training config
                },
                # Data filtering - must match training.yaml
                "val_interval": {
                    "rating": "[1,inf)"
                },
                "unused_col": {
                    "inter": ["rating"]
                },
                "user_inter_num_interval": "[5,inf)",  # Users with at least 5 interactions
                "item_inter_num_interval": "[5,inf)",  # Items with at least 5 interactions
                # Model config
                "embedding_size": 64,
            }
            
            self.config = Config(
                model=self.algorithm,
                dataset="amazon_sentiment_200k",
                config_dict=config_dict
            )
            
            # Create dataset
            self.dataset = create_dataset(self.config)
            logger.info(f"Dataset loaded: {self.dataset}")
            
            # Prepare data
            self.train_data, self.valid_data, self.test_data = data_preparation(
                self.config, self.dataset
            )
            
            # Initialize model
            self.model = get_model(self.config["model"])(self.config, self.train_data.dataset).to(
                self.config["device"]
            )
            
            # Load checkpoint
            checkpoint = torch.load(checkpoint_path_str, map_location=self.config["device"], weights_only=False)
            
            # RecBole checkpoints can have different structures
            if "state_dict" in checkpoint:
                # Standard RecBole checkpoint format
                self.model.load_state_dict(checkpoint["state_dict"])
            elif "model_state_dict" in checkpoint:
                # Alternative format
                self.model.load_state_dict(checkpoint["model_state_dict"])
            else:
                # Try loading directly if it's just the state dict
                self.model.load_state_dict(checkpoint)
            self.model.eval()
            
            # Create trainer for prediction
            self.trainer = Trainer(self.config, self.model)
            
            logger.info("RecBole model loaded successfully!")
            
        except Exception as e:
            logger.error(f"Error loading RecBole model: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def recommend(
        self,
        user_id: str,
        top_k: int = 10,
        filter_interacted: bool = True
    ) -> List[Dict[str, any]]:
        """
        Generate recommendations for a user.
        
        Args:
            user_id: User ID from the dataset
            top_k: Number of recommendations to return
            filter_interacted: Whether to filter out items the user has already interacted with
        
        Returns:
            List of recommended items with scores
        """
        try:
            # RecBole dataset structure:
            # - field2token_id["user_id"] maps user_id string -> internal_id (use this for lookup)
            # - field2id_token["user_id"] is np.ndarray: index -> token (no .index() on numpy!)
            # - Internal IDs are 1-indexed (1, 2, 3, ...)
            field2id_token = self.dataset.field2id_token
            field2token_id = self.dataset.field2token_id
            
            # Look up user_id via field2token_id (token string -> internal id)
            # Do NOT use field2id_token.index() - it's a numpy array, has no .index() method
            token_to_id = field2token_id.get("user_id") if field2token_id else None
            if isinstance(token_to_id, dict):
                user_token = token_to_id.get(user_id)
            else:
                user_token = None
            
            if user_token is None:
                logger.warning(f"User ID {user_id} not found in filtered dataset, using first available user")
                # Get first user from filtered dataset (token 1, skip token 0 which is padding)
                user_id_list = field2id_token["user_id"]
                if len(user_id_list) > 1:
                    user_id = user_id_list[1]  # Get the actual user_id string
                    user_token = 1
                    logger.info(f"Using user_id: {user_id} (token: {user_token})")
                else:
                    logger.error("No users found in dataset")
                    return []
            
            # user_token from field2token_id is already the internal ID (1-indexed)
            user_id_internal = user_token
            
            logger.info(f"User mapping: user_id={user_id}, token={user_token}, internal_id={user_id_internal}")
            
            # Get user interactions if filtering
            interacted_items = set()
            if filter_interacted:
                try:
                    user_interactions = self.train_data.dataset.inter_feat[
                        self.train_data.dataset.inter_feat["user_id"] == user_id_internal
                    ]
                    if len(user_interactions) > 0:
                        interacted_items = set(user_interactions["item_id"].tolist())
                    logger.info(f"User {user_id} has {len(interacted_items)} interacted items")
                except Exception as e:
                    logger.warning(f"Could not get user interactions: {e}")
            
            # Use RecBole's prediction method
            logger.info(f"Generating recommendations for user_id_internal: {user_id_internal}, item_num: {self.dataset.item_num}")
            
            # Create a test dataset with just this user
            from recbole.data import dataset
            import pandas as pd
            
            # Get all items (excluding interacted ones if filtering)
            all_item_ids = list(range(1, self.dataset.item_num + 1))
            if filter_interacted and interacted_items:
                all_item_ids = [item_id for item_id in all_item_ids if item_id not in interacted_items]
            
            # Create interaction pairs: (user_id, item_id)
            test_data = pd.DataFrame({
                'user_id': [user_id_internal] * len(all_item_ids),
                'item_id': all_item_ids
            })
            
            # Use model's predict method
            # Note: RecBole uses 1-indexed internal IDs, but PyTorch embeddings are 0-indexed
            # So we need to subtract 1 when accessing embeddings
            with torch.no_grad():
                # Convert to 0-indexed for embedding lookup
                user_tensor = torch.tensor([user_id_internal - 1], device=self.config["device"])
                # all_item_ids are already 1-indexed, convert to 0-indexed
                item_tensor = torch.tensor([item_id - 1 for item_id in all_item_ids], device=self.config["device"])
                
                # Get embeddings
                user_emb = self.model.user_embedding(user_tensor)  # Shape: [1, emb_dim]
                item_emb = self.model.item_embedding(item_tensor)   # Shape: [num_items, emb_dim]
                
                # Calculate scores: user_emb @ item_emb^T = [1, emb_dim] @ [emb_dim, num_items] = [1, num_items]
                scores = torch.matmul(user_emb, item_emb.t()).squeeze(0)  # Shape: [num_items]
                
                logger.info(f"Computed scores for {len(scores)} items, shape: {scores.shape}")
                
                # Get top-k
                top_k_actual = min(top_k, len(scores))
                top_scores, top_indices = torch.topk(scores, top_k_actual)
                
                # Convert indices back to item IDs
                top_item_ids = [all_item_ids[int(idx.item())] for idx in top_indices]
                
                logger.info(f"Top {len(top_item_ids)} items selected")
                
                # Convert internal item IDs to original item_id strings
                # field2id_token["item_id"] is a list where index=token, value=item_id string
                recommendations = []
                item_id_list = self.dataset.field2id_token["item_id"]
                
                for rank, (item_id_internal, score) in enumerate(zip(top_item_ids, top_scores.cpu().tolist()), 1):
                    try:
                        # item_id_internal is 1-indexed, so use it directly as token index
                        # But we need to make sure it's within bounds
                        if 1 <= item_id_internal < len(item_id_list):
                            item_id = item_id_list[item_id_internal]
                        else:
                            logger.warning(f"Item internal ID {item_id_internal} out of range (max: {len(item_id_list)-1})")
                            continue
                        
                        recommendations.append({
                            "item_id": str(item_id),
                            "score": float(score),
                            "rank": rank
                        })
                    except Exception as e:
                        logger.warning(f"Error converting item {item_id_internal}: {e}")
                        continue
                
                logger.info(f"Successfully generated {len(recommendations)} recommendations")
                if len(recommendations) == 0:
                    logger.error("No recommendations generated! Check logs above for errors.")
                return recommendations
                
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            import traceback
            error_trace = traceback.format_exc()
            logger.error(error_trace)
            # Return empty list - this will be handled by GenerateResponse node
            return []


# Global RecBole engine instances (keyed by algorithm)
recbole_engines: Dict[str, RecBoleRecommendationEngine] = {}


def get_recbole_engine(algorithm: Optional[str] = None) -> RecBoleRecommendationEngine:
    """
    Get or create RecBole engine instance for the specified algorithm.
    
    Args:
        algorithm: Algorithm name (e.g., 'LightGCN', 'BPR'). If None, uses default.
    
    Returns:
        RecBoleRecommendationEngine instance
    """
    global recbole_engines
    
    # Normalize algorithm name
    algorithm_key = algorithm or settings.recbole_model_name
    
    # Check if we already have an engine for this algorithm
    if algorithm_key not in recbole_engines:
        logger.info(f"Creating new RecBole engine for algorithm: {algorithm_key}")
        recbole_engines[algorithm_key] = RecBoleRecommendationEngine(algorithm=algorithm_key)
    
    return recbole_engines[algorithm_key]

