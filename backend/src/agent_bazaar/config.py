from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- API Keys (set whichever provider you use) ---
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None

    # --- Model names — change these to switch providers ---
    # Anthropic : "claude-sonnet-4-6"          / "claude-haiku-4-5-20251001"
    # Gemini    : "gemini/gemini-2.0-flash"     / "gemini/gemini-2.0-flash-lite"
    broker_model: str = "gemini/gemini-2.5-flash"
    aggregator_model: str = "gemini/gemini-2.5-flash"
    scorer_model: str = "gemini/gemini-2.5-flash-lite"

    # --- Specialist agent models (fast = bidding/cheap, thorough = quality execution) ---
    specialist_fast_model: str = "gemini/gemini-2.5-flash-lite"
    specialist_thorough_model: str = "gemini/gemini-2.5-flash"

    # --- Fallback model (used when primary model returns 503/429 after retries) ---
    fallback_model: str = "gemini/gemini-2.0-flash"

    # --- Optional infrastructure ---
    redis_url: Optional[str] = None
    database_url: Optional[str] = None

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
