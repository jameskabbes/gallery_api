from sqlmodel.ext.asyncio.session import AsyncSession as SQLMAsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, async_sessionmaker
from arbor_imago.core import config

DB_ASYNC_ENGINE = create_async_engine(
    config.DB['URL'],
)

ASYNC_SESSIONMAKER = async_sessionmaker(
    bind=DB_ASYNC_ENGINE,
    class_=SQLMAsyncSession,
    expire_on_commit=False
)
