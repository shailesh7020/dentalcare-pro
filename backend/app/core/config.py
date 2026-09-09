import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import AliasChoices, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", populate_by_name=True
    )

    environment: Literal["development", "test", "staging", "production"] = "development"
    database_url: str = Field(validation_alias=AliasChoices("DATABASE_URL"))
    secret_key: SecretStr = Field(validation_alias=AliasChoices("SECRET_KEY"))
    jwt_secret: SecretStr = Field(validation_alias=AliasChoices("JWT_SECRET", "JWT_SECRET_KEY"))
    jwt_algorithm: Literal["HS256", "HS384", "HS512"] = Field(
        validation_alias=AliasChoices("JWT_ALGORITHM")
    )
    access_token_expire_minutes: int = Field(
        ge=1, le=60, validation_alias=AliasChoices("ACCESS_TOKEN_EXPIRE_MINUTES")
    )
    refresh_token_expire_days: int = Field(
        ge=1, le=90, validation_alias=AliasChoices("REFRESH_TOKEN_EXPIRE_DAYS")
    )
    redis_url: str = Field(validation_alias=AliasChoices("REDIS_URL"))
    cors_origins: Annotated[list[str], NoDecode] = Field(
        validation_alias=AliasChoices("CORS_ORIGINS")
    )
    storage_backend: Literal["local", "s3"] = Field(
        default="local", validation_alias=AliasChoices("STORAGE_BACKEND")
    )
    storage_local_path: Path = Field(
        default=Path("./storage"), validation_alias=AliasChoices("STORAGE_LOCAL_PATH")
    )
    login_rate_limit: int = Field(
        default=5, ge=1, le=100, validation_alias=AliasChoices("LOGIN_RATE_LIMIT")
    )
    refresh_rate_limit: int = Field(
        default=15, ge=1, le=100, validation_alias=AliasChoices("REFRESH_RATE_LIMIT")
    )
    rate_limit_window_seconds: int = Field(
        default=60, ge=1, le=3600, validation_alias=AliasChoices("RATE_LIMIT_WINDOW_SECONDS")
    )

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        if not value.startswith(("postgres://", "postgresql://", "postgresql+asyncpg://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection URL")
        return value

    @field_validator("secret_key", "jwt_secret")
    @classmethod
    def validate_secret_length(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < 32:
            raise ValueError("must contain at least 32 characters")
        return value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            value_str = value.strip()
            if value_str.startswith("[") and value_str.endswith("]"):
                try:
                    parsed = json.loads(value_str)
                    if isinstance(parsed, list):
                        return [str(origin).strip().rstrip("/") for origin in parsed if str(origin).strip()]
                except (json.JSONDecodeError, TypeError, ValueError):
                    logger.debug("Failed to parse CORS_ORIGINS as JSON array, falling back to comma split")
            return [origin.strip().strip("'\"[]").rstrip("/") for origin in value_str.split(",") if origin.strip().strip("'\"[]")]
        if isinstance(value, list):
            return [str(origin).strip().rstrip("/") for origin in value if str(origin).strip()]
        return value

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if not self.cors_origins:
            raise ValueError("CORS_ORIGINS must contain at least one origin")
        if self.environment == "production" and "*" in self.cors_origins:
            raise ValueError("CORS_ORIGINS cannot contain '*' in production")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return self.cors_origins


@lru_cache
def get_settings() -> Settings:
    return Settings()
