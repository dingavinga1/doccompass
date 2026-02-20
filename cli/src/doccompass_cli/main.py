import typer
from rich.console import Console
from .commands import ingestion, docs
from .config import save_config, load_config

app = typer.Typer(help="DocCompass CLI - Manage documentation and ingestion jobs.")
console = Console()

app.add_typer(ingestion.app, name="ingestion", help="Manage ingestion jobs.")
app.add_typer(docs.app, name="docs", help="Browse and search documentation.")

@app.command()
def config(
    backend_url: str = typer.Option(..., "--set-backend-url", help="Set the permanent backend URL for the CLI.")
):
    """Configure CLI settings."""
    config_data = load_config()
    config_data["backend_url"] = backend_url
    save_config(config_data)
    console.print(f"[green]Successfully linking to backend URL: {backend_url}[/green]")

if __name__ == "__main__":
    app()
