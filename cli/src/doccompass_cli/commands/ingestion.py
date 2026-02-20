import typer
import asyncio
from rich.console import Console
from rich.table import Table
from typing import Optional, List
from ..api import DocCompassClient

app = typer.Typer()
console = Console()

def get_client() -> DocCompassClient:
    return DocCompassClient()

def async_run(coro):
    return asyncio.run(coro)

@app.command()
def run(
    url: str = typer.Argument(..., help="The URL to start crawling from."),
    max_depth: Optional[int] = typer.Option(3, help="Maximum crawl depth."),
    include: Optional[List[str]] = typer.Option(None, help="URL patterns to include. (Can be provided multiple times)"),
    exclude: Optional[List[str]] = typer.Option(None, help="URL patterns to exclude. (Can be provided multiple times)")
):
    """Start a new ingestion job."""
    try:
        client = get_client()
        result = async_run(client.start_ingestion(url, max_depth, include, exclude))
        job_id = result.get("job_id") or result.get("id", "Unknown")
        console.print(f"[green]Successfully started ingestion job![/green] Job ID: {job_id}")
    except Exception as e:
        console.print(f"[red]Failed to start ingestion job: {e}[/red]")

@app.command()
def list(
    skip: int = typer.Option(0, help="Number of jobs to skip."),
    limit: int = typer.Option(100, help="Maximum number of jobs to return."),
    status: Optional[str] = typer.Option(None, help="Filter jobs by status.")
):
    """List ingestion jobs."""
    try:
        client = get_client()
        result = async_run(client.list_ingestion_jobs(skip, limit, status))
        jobs = result.get("items", []) if isinstance(result, dict) else result
        
        table = Table(title="Ingestion Jobs")
        table.add_column("Job ID", style="cyan", overflow="fold")
        table.add_column("Status", style="magenta")
        table.add_column("Progress", style="green")
        table.add_column("Pages Processed")
        
        for job in jobs:
            table.add_row(
                str(job.get("job_id") or job.get("id", "N/A")),
                str(job.get("status", "N/A")),
                f"{job.get('progress_percent', 0)}%",
                str(job.get("pages_processed", 0))
            )
        console.print(table)
    except Exception as e:
        console.print(f"[red]Failed to list ingestion jobs: {e}[/red]")

@app.command()
def status(id: str = typer.Argument(..., help="The ID of the ingestion job.")):
    """Get the status of an ingestion job."""
    try:
        client = get_client()
        job = async_run(client.get_ingestion_job(id))
        job_id = job.get('job_id') or job.get('id', 'Unknown')
        console.print(f"[bold cyan]Job ID:[/] {job_id}")
        console.print(f"[bold magenta]Status:[/] {job.get('status', 'Unknown')}")
        console.print(f"[bold green]Progress:[/] {job.get('progress_percent', 0)}%")
        console.print(f"[bold]Pages Processed:[/] {job.get('pages_processed', 0)}")
        if job.get("error_message"):
            console.print(f"[bold red]Error:[/] {job.get('error_message')}")
    except Exception as e:
        console.print(f"[red]Failed to get ingestion job status: {e}[/red]")

@app.command()
def stop(id: str = typer.Argument(..., help="The ID of the ingestion job to stop.")):
    """Stop an ingestion job."""
    try:
        client = get_client()
        async_run(client.stop_ingestion_job(id))
        console.print(f"[green]Successfully stopped ingestion job {id}[/green]")
    except Exception as e:
        console.print(f"[red]Failed to stop ingestion job: {e}[/red]")
