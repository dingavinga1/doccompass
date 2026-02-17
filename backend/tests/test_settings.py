from app.config import Settings


def test_settings_reads_env(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/1")
    monkeypatch.setenv("POSTGRES_CONNECTION_STRING", "postgresql://a:b@localhost:5432/c")
    monkeypatch.setenv("MCP_SERVER_TOKEN", "token")

    cfg = Settings()

    assert cfg.redis_url == "redis://localhost:6379/1"
    assert cfg.postgres_connection_string == "postgresql://a:b@localhost:5432/c"
    assert cfg.mcp_server_token == "token"
