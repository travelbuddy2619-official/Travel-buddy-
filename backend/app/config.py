from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application configuration loaded from environment."""

    port: int = Field(8000, alias="PORT")
    groq_api_key: str = Field(..., alias="GROQ_API_KEY")
    maptiler_api_key: str = Field(..., alias="MAPTILER_API_KEY")
    openweather_api_key: str = Field(..., alias="OPENWEATHER_API_KEY")
    serper_api_key: str = Field(..., alias="SERPER_API_KEY")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache
def get_settings() -> "Settings":
    return Settings()