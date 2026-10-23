from functools import lru_cache

from typing import List, Optional

from pydantic import Field, field_validator

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    model_config = SettingsConfigDict(

        env_file=".env",

        env_file_encoding="utf-8",

        case_sensitive=True,

        extra="ignore",

    )

    APP_NAME: str = "Digital Twin PK Backend"

    APP_VERSION: str = "1.1.0"

    ENVIRONMENT: str = Field(default="development")

    DEBUG: bool = False

    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "sqlite:////tmp/digital_twin.db"

    DB_POOL_SIZE: int = 5

    DB_MAX_OVERFLOW: int = 10

    DB_POOL_RECYCLE: int = 1800

    REDIS_URL: Optional[str] = None

    SECRET_KEY: str = Field(default="INSECURE-dev-key-change-in-production", min_length=16)

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    CORS_ORIGINS: str = "*"

    ENABLE_DOCS: bool = True

    LOG_LEVEL: str = "INFO"

    API_KEYS: str = ""

    RATE_LIMIT_PER_MINUTE: int = 60

    ALLOW_DEMO_FALLBACK: bool = True

    REQUIRE_POSTGRES_IN_PROD: bool = True

    REQUIRE_API_KEYS_IN_PROD: bool = True

    @field_validator("ENVIRONMENT")

    @classmethod

    def normalize_env(cls, v: str) -> str:

        v = v.lower().strip()

        if v not in ("development", "staging", "production"):

            return "development"

        return v

    @property

    def is_production(self) -> bool:

        return self.ENVIRONMENT == "production"

    @property

    def cors_origins_list(self) -> List[str]:

        if self.CORS_ORIGINS.strip() == "*":

            return ["*"]

        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property

    def docs_url(self) -> Optional[str]:

        if self.is_production and not self.ENABLE_DOCS:

            return None

        return "/docs"

    @property

    def redoc_url(self) -> Optional[str]:

        if self.is_production and not self.ENABLE_DOCS:

            return None

        return "/redoc"

    @property

    def api_keys_list(self) -> List[str]:

        return [k.strip() for k in self.API_KEYS.split(",") if k.strip()]

@lru_cache()

def get_settings() -> Settings:

    s = Settings()

    if s.is_production:

        if (

            not s.SECRET_KEY

            or s.SECRET_KEY.startswith("INSECURE")

            or s.SECRET_KEY.startswith("change-me")

        ):

            raise RuntimeError("Set a strong SECRET_KEY when ENVIRONMENT=production")

        if s.REQUIRE_POSTGRES_IN_PROD and not s.DATABASE_URL.startswith("postgresql"):

            raise RuntimeError("Production requires postgresql DATABASE_URL")

        if s.REQUIRE_API_KEYS_IN_PROD and not s.api_keys_list:

            raise RuntimeError("Production requires API_KEYS (comma-separated)")

        if s.CORS_ORIGINS.strip() == "*":

            raise RuntimeError("Production forbids CORS_ORIGINS=* — set explicit origins")

        if s.ALLOW_DEMO_FALLBACK:

            raise RuntimeError("Set ALLOW_DEMO_FALLBACK=false in production")

    return s

