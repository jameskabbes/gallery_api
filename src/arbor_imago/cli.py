from arbor_imago import core, app
from arbor_imago.core import config

import typer
import asyncio
import json
from sqlmodel import SQLModel

cli = typer.Typer()


@cli.command()
def runserver():
    app.run()


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
        json.dumps(app.app.openapi()))


@cli.command()
def export_shared_config():
    """Export shared configuration to a file."""

    config.export_shared_config()


if __name__ == "__main__":
    cli()
