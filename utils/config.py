"""
Configuration management for the VC Sourcing Agent.
"""
import os
from typing import Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    """Application settings."""
    
    # LinkedIn Configuration
    LINKEDIN_EMAIL: Optional[str] = None
    LINKEDIN_PASSWORD: Optional[str] = None
    LINKEDIN_SESSION_COOKIES: Optional[str] = None
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = None
    CRUNCHBASE_API_KEY: Optional[str] = None
    
    # Database
    DATABASE_URL: str = "sqlite:///vc_sourcing.db"
    
    # Scraping Settings
    SCRAPING_DELAY: float = 2.0  # seconds between requests
    MAX_RETRIES: int = 3
    REQUEST_TIMEOUT: int = 30
    
    # Model Settings
    FIT_MODEL_PATH: str = "models/fit_model.pkl"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # Search Criteria
    DEFAULT_STAGES: list = ["pre-seed", "seed", "series-a"]
    DEFAULT_LOCATIONS: list = ["San Francisco", "New York", "Austin", "Boston"]
    DEFAULT_INDUSTRIES: list = [
        "Technology", "Software", "Fintech", "Healthtech", 
        "E-commerce", "AI/ML", "SaaS", "Mobile"
    ]
    
    # Rate Limiting
    REQUESTS_PER_MINUTE: int = 20
    REQUESTS_PER_HOUR: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get application settings."""
    return settings 