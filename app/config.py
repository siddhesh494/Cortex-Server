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

    # RAG / embeddings (nomic-embed-text-v1.5 via fastembed — Groq does not
    # currently expose this model on all accounts)
    EMBEDDING_MODEL: str = "nomic-ai/nomic-embed-text-v1.5"
    EMBEDDING_DIMENSION: int = 768
    RAG_TOP_K: int = 5

    # Optional Hugging Face token for fastembed ONNX downloads (higher Hub rate limits)
    HF_TOKEN: str = ""

    # Pinecone
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX_NAME: str = "cortex-rag"
    PINECONE_CLOUD: str = "aws"
    PINECONE_REGION: str = "us-east-1"


settings = Settings()