import subprocess
import sys
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table

console = Console()

app = typer.Typer(
    name="pubmed",
    help="A CLI tool to interact with PubMed articles database.",
    add_completion=False,
    rich_markup_mode="rich"
)

db_app = typer.Typer(
    help="Database management commands.",
    rich_markup_mode="rich"
)

app.add_typer(db_app, name="db")

@db_app.command("init")
def init_db(
    skip_create: bool = typer.Option(
        False, "--skip-create", help="Skip creating the database."
        )
    ):
    from pubmed_app.config import settings, logger
    from pubmed_app.database.connection import create_database_if_not_exists,run_schema,verify_tables

    console.print(f"[bold green]Initializing database:[/bold green] {settings.DB_NAME}")

    schema_path = Path(__file__).parent.parent / "database" / "schema.sql"

    if not schema_path.exists():
        console.print(f"[bold red]Schema file not found:[/bold red] {schema_path}")
        raise typer.Exit(code=1)
    
    try:
        if not skip_create:
            console.print("[bold blue]Creating database if not exists...[/bold blue]")
            created = create_database_if_not_exists()
            if created:
                console.print(f"[bold green]Database {settings.DB_NAME} created successfully.[/bold green]")
            else:
                console.print(f"[bold yellow]Database {settings.DB_NAME} already exists.[/bold yellow]")

        console.print("[bold blue]Running database schema...[/bold blue]")
        run_schema(schema_path=schema_path)
        console.print("[bold green]Database schema executed successfully.[/bold green]")

        console.print("[bold blue]Verifying database tables...[/bold blue]")
        table_status = verify_tables()

        for table, exists in table_status.items():
            if exists:
                console.print(f"[bold green]Table exists:[/bold green] {table}")
            else:
                console.print(f"[bold red]Table missing:[/bold red] {table}")
        
        if all(table_status.values()):
            console.print("[bold green]Database initialization completed successfully.[/bold green]")
        else:
            console.print("[bold red]Database initialization failed. Some tables are missing.[/bold red]")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        console.print(f"[bold red]Error initializing database:[/bold red] {e}")
        raise typer.Exit(code=1)

@app.command()
def etl(
    topic: str = typer.Option(
        ...,
        "--topic", "-t",
        help="The search term/topic to fetch articles from PubMed."
        ),
    max_results: int =typer.Option(
        100,
        "--max-results", "-m",
        help="Maximum number of articles to fetch."
        ),
    debug: bool = typer.Option(
        False,
        "--debug", "-d",
        help="Enable debug logging."
        )
    ):
    from pubmed_app.config import settings, logger
    from pubmed_app.etl import etl_pipeline
    if debug:
        import logging
        logging.getLogger('pubmed_app_logger').setLevel(logging.DEBUG)
    console.print(f"[bold green]Starting ETL pipeline for topic:[/bold green] {topic}")
    console.print(f"[bold green]Maximum results to fetch:[/bold green] {max_results}")

    try:
        pipeline = etl_pipeline.ETLPipeline(
            email=settings.PUBMED_EMAIL,
            api_key=settings.PUBMED_API_KEY
        )
        stats = pipeline.run(search_term=topic, retmax=max_results)
        console.print(f"[bold green]ETL pipeline completed with stats:[/bold green] {stats}")
    except Exception as e:
        logger.error(f"Error running ETL pipeline: {e}")
        console.print(f"[bold red]Error running ETL pipeline:[/bold red] {e}")
        raise typer.Exit(code=1)