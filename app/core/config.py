import json
import os
from functools import cached_property,lru_cache

from pydantic import Field, HttpUrl, computed_field, field_validator, List
from pydantic_settings import BaseSettings, SettingsConfigDict

class BaseConfigSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="allow",
    )

class AppSettings(BaseConfigSettings):
    project_name: str = Field("Project", alias= "PROJECT_NAME")
    project_version: str = Field("0.1.0", alias= "PROJECT_VERSION")



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


class CorsSettings(BaseConfigSettings):
    origins: List[str] = Field(default_factory=list, alias="CORS_ORIGINS")
    methods: List[str] = Field(
        default=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )
    headers: List[str] = Field(default=["*"])
    credentials: bool = Field(True)
    max_age: int = Field(600, ge=0)



class Settings(BaseConfigSettings):
    app: AppSettings = Field(default_factory=AppSettings) #type: ignore
    database: DatabaseSettings = Field(default_factory=DatabaseSettings) #type: ignore
    cors: CorsSettings = Field(default_factory=CorsSettings) #type: ignore

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()