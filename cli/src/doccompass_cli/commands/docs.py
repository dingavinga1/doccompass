import typer
import asyncio
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich.markdown import Markdown
from typing import Optional
from ..api import DocCompassClient

app = typer.Typer()
console = Console()

def get_client() -> DocCompassClient:
    return DocCompassClient()

def async_run(coro):
    return asyncio.run(coro)

@app.command()
def list(
    skip: int = typer.Option(0, help="Number of items to skip."),
    limit: int = typer.Option(100, help="Maximum number of items to return.")
):
    """List available documentation."""
    try:
        client = get_client()
        result = async_run(client.list_documentation(skip, limit))
        items = result.get("items", []) if isinstance(result, dict) else result
        
        table = Table(title="Documentations")
        table.add_column("ID", style="cyan", overflow="fold")
        table.add_column("URL", style="blue", overflow="fold")
        table.add_column("Sections", style="magenta")
        
        for item in items:
            table.add_row(
                str(item.get("id")),
                str(item.get("url")),
                str(item.get("section_count", "N/A"))
            )
        console.print(table)
    except Exception as e:
        console.print(f"[red]Failed to list documentations: {e}[/red]")

@app.command()
def tree(id: str = typer.Argument(..., help="The Documentation ID.")):
    """View the topic tree of a documentation set."""
    try:
        client = get_client()
        data = async_run(client.get_documentation_tree(id))
        
        def build_tree(node_data, tree_node):
            for child in node_data.get("children", []):
                child_node = tree_node.add(f"[blue]{child.get('title', 'Unknown')}[/] ([cyan]{child.get('path', '/')}[/])")
                build_tree(child, child_node)
                
        root_tree = Tree(f"Documentation {id}")
        roots = data.get("roots", []) if isinstance(data, dict) else (data if isinstance(data, type([])) else [data])
        for item in roots:
            node = root_tree.add(f"[bold blue]{item.get('title', 'Root')}[/] ([cyan]{item.get('path', '/')}[/])")
            build_tree(item, node)
            
        console.print(root_tree)
    except Exception as e:
        console.print(f"[red]Failed to get documentation tree: {e}[/red]")

@app.command()
def search(
    id: str = typer.Argument(..., help="The Documentation ID."),
    query: str = typer.Argument(..., help="The search query.")
):
    """Search within a documentation set."""
    try:
        client = get_client()
        results = async_run(client.search_documentation(id, query))
        items = results.get("items", []) if isinstance(results, dict) else results
        
        if not items:
            console.print("[yellow]No results found.[/yellow]")
            return
            
        for i, item in enumerate(items, 1):
            console.print(f"[bold cyan]{i}. {item.get('title', 'Untitled')}[/] ([blue]{item.get('path')}[/])")
            console.print(f"   Score: {item.get('score', 0):.4f}")
            console.print(f"   [dim]{item.get('summary', '')[:200]}...[/dim]\n")
    except Exception as e:
        console.print(f"[red]Failed to search documentation: {e}[/red]")

@app.command()
def content(
    id: str = typer.Argument(..., help="The Documentation ID."),
    path: str = typer.Argument(..., help="The exact path of the section.")
):
    """Get the markdown content for a specific documentation section."""
    try:
        client = get_client()
        result = async_run(client.get_section_content(id, path))
        content_text = result.get("content", "")
        if not content_text:
            console.print("[yellow]Empty content or section not found.[/yellow]")
            return
            
        console.print(Markdown(content_text))
    except Exception as e:
        console.print(f"[red]Failed to get section content: {e}[/red]")
