from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- API Keys (set whichever provider you use) ---
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None

    # --- Model names — change these to switch providers ---
    # Anthropic examples : "claude-sonnet-4-6"  /  "claude-haiku-4-5-20251001"
    # Gemini examples     : "gemini/gemini-1.5-pro"  /  "gemini/gemini-2.0-flash"
    broker_model: str = "claude-sonnet-4-6"
    aggregator_model: str = "claude-sonnet-4-6"
    scorer_model: str = "claude-haiku-4-5-20251001"

    # --- Optional infrastructure ---
    redis_url: Optional[str] = None
    database_url: Optional[str] = None

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
