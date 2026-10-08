import json
import os
from functools import cached_property,lru_cache

from pydantic import Field, HttpUrl, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class BaseConfigSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="allow",
    )

class DatabaseSettings(BaseConfigSettings):
    user: str = Field(...,alias="POSTGRES_USER")
    password: str = Field(...,alias="POSTGRES_PASSWORD")
    server: str = Field("db",alias="POSTGRES_SERVER")
    port: int = Field(5432,alias="POSTGRES_PORT", ge=1, le=65535)
    db_name: str = Field("app_db",alias="POSTGRES_DB")

    @computed_field
    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.server}:{self.port}/{self.db_name}"

    @computed_field
    @property
    def async_url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.server}:{self.port}/{self.db_name}"


class Settings(BaseConfigSettings):
    database: DatabaseSettings = Field(default_factory=DatabaseSettings) #type: ignore

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()