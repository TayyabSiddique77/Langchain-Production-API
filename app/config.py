from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

class Settings(BaseSettings):
    """
    Application settings
    """

    # LLM Configuration

    groq_api_key : str
    google_api_key: str
    primary_model: str = 'openai/gpt-oss-120b'
    fallback_model: str = 'gemini-3.8-flash'

    # LangSmith
    langchain_tracing_v2: bool = True
    langchain_api_key: str = ""
    langchain_project: str = 'production-api'

    # Application
    app_env: str = 'development'
    log_level: str = 'INFO'
    rate_limit: str = '20/minute'
    cache_ttl_seconds: int = 300
    max_retries: int = 3

    model_config = {'env_file':'.env', 'extra':'ignore'}

    @property
    def is_production(self)->bool:
        return self.app_env == 'production'

@lru_cache
def get_settings()->Settings:
    """Cached settigs instance - loaded once, reused everywhere"""
    return Settings()

