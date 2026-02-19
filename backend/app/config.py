from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "documentation-mcp-backend"
    app_env: str = "development"
    app_port: int = 8000

    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")
    postgres_connection_string: str = Field(
        default="postgresql+psycopg://user:password@db:5432/docmcp",
        alias="POSTGRES_CONNECTION_STRING",
    )
    mcp_server_token: str = Field(default="super-secret-token", alias="MCP_SERVER_TOKEN")
    mcp_rate_limit_window_seconds: int = Field(default=60, alias="MCP_RATE_LIMIT_WINDOW_SECONDS")
    mcp_rate_limit_max_requests: int = Field(default=120, alias="MCP_RATE_LIMIT_MAX_REQUESTS")
    store_raw_pages: bool = Field(default=False, alias="STORE_RAW_PAGES")

    # Embedding settings (Phase 8)
    embedding_model: str = Field(default="bedrock:amazon.titan-embed-text-v2:0", alias="EMBEDDING_MODEL")
    embedding_dimension: int = Field(default=1024, alias="EMBEDDING_DIMENSION")
    embedding_batch_size: int = Field(default=64, alias="EMBEDDING_BATCH_SIZE")
    embedding_max_retries: int = Field(default=3, alias="EMBEDDING_MAX_RETRIES")
    embedding_token_limit: int = Field(default=8192, alias="EMBEDDING_TOKEN_LIMIT")
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")


settings = Settings()
