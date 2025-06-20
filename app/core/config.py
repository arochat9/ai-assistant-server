import os
from typing import Optional
from urllib.parse import urlparse

from dotenv import dotenv_values, load_dotenv
from pydantic_settings import BaseSettings

config = dotenv_values(".env")  # returns dict of key-value pairs
# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "AI Assistant Server"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    PORT: int = 8000

    # Database settings
    temp_db_url: Optional[str] = os.getenv("DATABASE_URL")
    if temp_db_url is None:
        raise ValueError("DATABASE_URL environment variable is not defined")
    DATABASE_URL: str = temp_db_url
    # temp_parsed_url: ParseResult = urlparse(temp_db_url)
    # ASYNC_DATABASE_URL: str = f"postgresql+asyncpg://{temp_parsed_url.username}:{temp_parsed_url.password}@{temp_parsed_url.hostname}{temp_parsed_url.path}?ssl=require"
    # SYNC_DATABASE_URL: str = f"postgresql+psycopg2://{temp_parsed_url.username}:{temp_parsed_url.password}@{temp_parsed_url.hostname}{temp_parsed_url.path}?ssl=require"

    # Agent settings
    DEBOUNCE_SECONDS: int = 60
    MAX_CONCURRENT_AGENTS: int = 1

    # APM settings
    ENABLE_APM: bool = True
    APM_SERVICE_NAME: str = "ai-assistant-server"

    class Config:
        env_file = ".env"

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        parsed = urlparse(self.DATABASE_URL)
        return f"postgresql+asyncpg://{parsed.username}:{parsed.password}@{parsed.hostname}{parsed.path}?ssl=require"

    @property
    def SYNC_DATABASE_URL(self) -> str:
        parsed = urlparse(self.DATABASE_URL)
        return f"postgresql+psycopg2://{parsed.username}:{parsed.password}@{parsed.hostname}{parsed.path}?ssl=require"


settings = Settings()
