"""
Main entry point for the Search & Solve CLI application.
"""

import asyncio

import typer
from typing_extensions import Annotated

from src.core.config import settings
from src.core.logging_setup import log
from src.scraping.search import SearchApp
from src.utils.proxy_handler import build_rated_proxy_pool


# Create a Typer app instance
cli = typer.Typer(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)


@cli.command()
def start(
    ctx: typer.Context,
    query: Annotated[
        str,
        typer.Option("--query", "-q", prompt="Please enter your search query"),
    ],
    engine: Annotated[
        str,
        typer.Option(
            "--engine", "-e", prompt="Which search engine would you like to use?"
        ),
    ],
):
    """
    Starts the interactive search and parse process.
    """

    async def main_async_logic():
        log.info("Application starting...")

        proxy_pool = []
        if settings.USE_FREE_PROXIES:
            proxy_pool = await build_rated_proxy_pool()
            if not proxy_pool:
                log.error("Could not build a valid proxy pool. Exiting.")
                raise typer.Exit(code=1)

        app = SearchApp(query=query, engine_key=engine.lower(), proxy_pool=proxy_pool)
        await app.run()

    try:
        if engine.lower() not in settings.SEARCH_ENGINES:
            log.error(
                f"Invalid engine '{engine}'. Please choose from: {list(settings.SEARCH_ENGINES.keys())}"
            )
            raise typer.Exit(code=1)

        asyncio.run(main_async_logic())
    except KeyboardInterrupt:
        log.info("\nProcess interrupted by user. Shutting down.")
    except Exception as e:
        log.critical(f"An unexpected critical error occurred: {e}", exc_info=True)


if __name__ == "__main__":
    cli()
