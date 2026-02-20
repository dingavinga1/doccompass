from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from doccompass_cli.main import app
import builtins

runner = CliRunner()

@patch('doccompass_cli.commands.ingestion.async_run')
@patch('doccompass_cli.commands.ingestion.get_client')
def test_ingestion_list(mock_get_client, mock_async_run):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    
    mock_async_run.return_value = {
        "items": [
            {
                "id": "123",
                "status": "COMPLETED",
                "progress_percent": 100,
                "created_at": "2026-02-20"
            }
        ]
    }
    
    result = runner.invoke(app, ["ingestion", "list"])
    assert result.exit_code == 0
    assert "123" in result.stdout
    assert "COMPLETED" in result.stdout

@patch('doccompass_cli.commands.ingestion.async_run')
@patch('doccompass_cli.commands.ingestion.get_client')
def test_ingestion_run(mock_get_client, mock_async_run):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    
    mock_async_run.return_value = {"id": "456"}
    
    result = runner.invoke(app, ["ingestion", "run", "https://example.com", "--max-depth", "5"])
    assert result.exit_code == 0
    assert "Successfully started ingestion job!" in result.stdout
    assert "456" in result.stdout

@patch('doccompass_cli.commands.docs.async_run')
@patch('doccompass_cli.commands.docs.get_client')
def test_docs_list(mock_get_client, mock_async_run):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    
    mock_async_run.return_value = {
        "items": [
            {
                "id": "doc_1",
                "url": "https://fastapi.tiangolo.com",
                "section_count": 50
            }
        ]
    }
    
    result = runner.invoke(app, ["docs", "list"])
    assert result.exit_code == 0
    assert "doc_1" in result.stdout
    assert "fastapi" in result.stdout

@patch('doccompass_cli.commands.docs.async_run')
@patch('doccompass_cli.commands.docs.get_client')
def test_docs_search(mock_get_client, mock_async_run):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    
    mock_async_run.return_value = {
        "items": [
            {
                "title": "Async Endpoints",
                "path": "/tutorial/async",
                "score": 0.99,
                "summary": "This is how you do async."
            }
        ]
    }
    
    result = runner.invoke(app, ["docs", "search", "doc_1", "async"])
    assert result.exit_code == 0
    assert "Async Endpoints" in result.stdout
    assert "This is how you do async" in result.stdout
    
@patch('doccompass_cli.main.save_config')
@patch('doccompass_cli.main.load_config')
def test_config(mock_load, mock_save):
    mock_load.return_value = {}
    
    result = runner.invoke(app, ["config", "--set-backend-url", "http://test:8000"])
    assert result.exit_code == 0
    assert "Successfully linking to backend URL: http://test:8000" in result.stdout
    mock_save.assert_called_once_with({"backend_url": "http://test:8000"})
