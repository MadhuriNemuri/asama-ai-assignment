import os
from pydantic import BaseModel

class Settings(BaseModel):
    APP_NAME: str = "B2B AI Agent Social Network"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./agent_network.db")
    
    # Security
    HMAC_SECRET_KEY: str = os.getenv("HMAC_SECRET_KEY", "b2b-agent-platform-secret-key-2026")
    
    # Relevance Routing Parameters
    STAGE2_TOP_K: int = 50
    STAGE3_RERANK_THRESHOLD: float = 0.75
    
    # Feedback Loop Parameters
    LEARNING_RATE_POSITIVE: float = 0.10
    LEARNING_RATE_NEGATIVE: float = 0.05
    
    # Vector dimensionality
    EMBEDDING_DIM: int = 384

settings = Settings()
