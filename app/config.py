import asyncio
from cachetools import TTLCache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    openai_api_key: str
    fast_model: str = "gpt-4o-mini"
    smart_model: str = "gpt-4o"
    ct_base_url: str = "https://clinicaltrials.gov/api/v2"
    ct_page_size: int = 100
    cache_ttl: int = 3600
    cache_maxsize: int = 256
    max_pages: int = 20


settings = Settings()

_study_cache: TTLCache = TTLCache(
    maxsize=settings.cache_maxsize,
    ttl=settings.cache_ttl,
)
_cache_lock: asyncio.Lock = asyncio.Lock()
