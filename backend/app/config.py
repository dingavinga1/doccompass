from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "documentation-mcp-backend"
    app_env: str = "development"
    app_port: int = 8000

    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")
    postgres_connection_string: str = Field(
        default="postgresql://user:password@db:5432/docmcp",
        alias="POSTGRES_CONNECTION_STRING",
    )
    mcp_server_token: str = Field(default="super-secret-token", alias="MCP_SERVER_TOKEN")


settings = Settings()
