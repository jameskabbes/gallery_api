from arbor_imago import core
from arbor_imago.app import app as fastapi_app
from arbor_imago.core import config

import typer
import asyncio
import json
from sqlmodel import SQLModel
import uvicorn

cli = typer.Typer()


@cli.command()
def runserver():
    uvicorn.run("arbor_imago.app:app", **config.UVICORN)


@cli.command()
def create_tables():
    """Create all database tables."""
    async def _main():
        async with core.DB_ASYNC_ENGINE.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    print("Creating tables...")
    asyncio.run(_main())


@cli.command()
def export_api_schema():
    """Export OpenAPI schema to file."""

    print('Exporting OpenAPI schema...')
    config.OPENAPI_SCHEMA_PATHS['gallery'].write_text(
        json.dumps(fastapi_app.openapi()))


if __name__ == "__main__":
    cli()
