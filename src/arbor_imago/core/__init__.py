import arbor_imago
from arbor_imago.core import config

from sqlmodel.ext.asyncio.session import AsyncSession as SQLMAsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, async_sessionmaker
import logging

DB_ASYNC_ENGINE = create_async_engine(
    config.DB['URL']
)

ASYNC_SESSIONMAKER = async_sessionmaker(
    bind=DB_ASYNC_ENGINE,
    class_=SQLMAsyncSession,
    expire_on_commit=False
)

LOGGER = logging.getLogger(arbor_imago.__name__)
if 'level' in config.LOGGER:
    logging.basicConfig(level=config.LOGGER['level'])

LOGGER.debug(f'Config initialized with ENV: {config.ENV}')

if config.BACKEND_CONFIG_PATH is not None and not config.BACKEND_CONFIG_PATH.exists():
    LOGGER.warning(
        f'Supplied BACKEND_CONFIG_PATH {config.BACKEND_CONFIG_PATH} does not exist.')

if config.SHARED_CONFIG_PATH is not None and not config.SHARED_CONFIG_PATH.exists():
    LOGGER.warning(
        f'Supplied SHARED_CONFIG_PATH {config.SHARED_CONFIG_PATH} does not exist.'
    )
