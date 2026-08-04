from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str

    HOST: str
    PORT: int

    MONGO_URI: str
    DATABASE_NAME: str

    JWT_SECRET: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    LOG_LEVEL: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )
    GROQ_API_KEY: str
    TAVILY_API_KEY: str

    # Fallback / legacy single-model setting
    MODEL_NAME: str = "llama-3.1-8b-instant"

    # Per-agent models (override via .env to A/B test without code changes)
    TITLE_MODEL: str = "llama-3.1-8b-instant"
    DECISION_MODEL: str = "llama-3.1-8b-instant"
    SUMMARY_MODEL: str = "llama-3.3-70b-versatile"
    RESPONSE_MODEL: str = "llama-3.3-70b-versatile"


settings = Settings()