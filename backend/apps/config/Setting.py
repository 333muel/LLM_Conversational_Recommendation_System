"""Application settings and configuration management."""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # MongoDB Configuration
    mongodb_url: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    mongodb_database: str = os.getenv("MONGODB_DATABASE", "recommendation_db")
    
    # RecBole Configuration
    recbole_dataset_path: str = os.getenv("RECBOLE_DATASET_PATH", "data/amazon_sentiment_200k")
    recbole_model_checkpoint: str = os.getenv("RECBOLE_MODEL_CHECKPOINT", "checkpoints/LightGCN-Nov-09-2025_21-24-15.pth")
    recbole_model_name: str = os.getenv("RECBOLE_MODEL_NAME", "LightGCN")
    
    # LLM Configuration (Ollama)
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen3:latest")
    
    # LLM Configuration (DashScope / Qwen)
    # API keys differ by region. Use China URL for China keys, International for Singapore/US keys.
    # China: https://dashscope.aliyuncs.com/compatible-mode/v1
    # Singapore: https://dashscope-intl.aliyuncs.com/compatible-mode/v1
    # US: https://dashscope-us.aliyuncs.com/compatible-mode/v1
    dashscope_api_key: str = os.getenv("DASHSCOPE_API_KEY", "")
    dashscope_base_url: str = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")
    dashscope_model: str = os.getenv("DASHSCOPE_MODEL", "qwen3.5-35b-a3b")
    
    # API Configuration
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    api_debug: bool = os.getenv("API_DEBUG", "False").lower() == "true"
    
    # Recommendation Configuration
    recommendation_top_k: int = int(os.getenv("RECOMMENDATION_TOP_K", "10"))  # Items to return to user
    recommendation_context_k: int = int(os.getenv("RECOMMENDATION_CONTEXT_K", "20"))  # Items to provide to LLM for context
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

