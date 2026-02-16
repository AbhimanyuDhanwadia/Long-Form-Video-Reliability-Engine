"""
Configuration management for the Long-Form Video Reliability Engine.

This module handles all configuration settings, including environment
variables and API keys.
"""

import os
from typing import Optional


class Settings:
    """
    Global settings for the LFV-RE pipeline.
    
    Loads configuration from environment variables with sensible defaults.
    """
    
    def __init__(self):
        """Initialize settings from environment variables."""
        # Mock mode toggle
        self.USE_MOCK_GENERATION = os.getenv("USE_MOCK", "true").lower() == "true"
        
        # API Keys
        self.FLUX_API_KEY = os.getenv("FLUX_API_KEY", "")
        self.RUNWAY_API_KEY = os.getenv("RUNWAY_API_KEY", "")
        
        # API Endpoints
        self.FLUX_API_URL = os.getenv("FLUX_API_URL", "https://api.bfl.ml/v1/generate")
        self.RUNWAY_API_URL = os.getenv("RUNWAY_API_URL", "https://api.runwayml.com/v1/generate")
        
        # Retry settings
        # Retry settings
        self.MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
        self.SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.5"))
        
        # VLM Settings
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    
    def __repr__(self):
        """String representation of settings."""
        return (
            f"Settings(\n"
            f"  USE_MOCK_GENERATION={self.USE_MOCK_GENERATION},\n"
            f"  FLUX_API_KEY={'***' if self.FLUX_API_KEY else 'not set'},\n"
            f"  RUNWAY_API_KEY={'***' if self.RUNWAY_API_KEY else 'not set'},\n"
            f"  MAX_RETRIES={self.MAX_RETRIES},\n"
            f"  CRITIC_PASS_RATE={self.CRITIC_PASS_RATE}\n"
            f")"
        )


# Global settings instance
settings = Settings()
