import typer
import asyncio
import json
from sqlmodel import SQLModel
import uvicorn
from arbor_imago import models, config
from arbor_imago.app import app as fastapi_app

cli = typer.Typer()


@cli.command()
def runserver():
    uvicorn.run("arbor_imago.app:app", **config.UVICORN)


@cli.command()
def create_tables():
    """Create all database tables."""
    async def _main():
        async with config.DB_ASYNC_ENGINE.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    print("Creating tables...")
    asyncio.run(_main())


@cli.command()
def export_openapi():
    """Export OpenAPI schema to file."""

    print('Exporting OpenAPI schema...')
    config.OPENAPI_SCHEMA_PATH.write_text(json.dumps(fastapi_app.openapi()))


if __name__ == "__main__":
    cli()
