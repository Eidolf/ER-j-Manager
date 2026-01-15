
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "JDownloader 2 Manager"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "changethis-in-production-to-a-secure-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # JDownloader Configuration
    USE_MOCK_API: bool = False
    JD_API_URL: str = "http://127.0.0.1:3128"
    
    # CORS
    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Logging
    LOG_LEVEL: str = "INFO"
    
    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")

settings = Settings()
