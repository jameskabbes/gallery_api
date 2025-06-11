from sqlmodel.ext.asyncio.session import AsyncSession as SQLMAsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, async_sessionmaker
import json
from pathlib import Path
import os
import typing
from typing import TypedDict, NotRequired, Literal
import yaml
from dotenv import dotenv_values
import datetime as datetime_module
import isodate
from platformdirs import user_config_dir
import warnings
import secrets
from arbor_imago import custom_types, core_utils
import arbor_imago

ARBOR_IMAGO_DIR = Path(__file__).parent  # /gallery/backend/src/arbor_imago/
EXAMPLES_DIR = ARBOR_IMAGO_DIR / 'examples'
EXAMPLE_CONFIG_DIR = EXAMPLES_DIR / 'config'

EXAMPLE_BACKEND_SECRETS_CONFIG_PATH = EXAMPLE_CONFIG_DIR / 'backend_secrets.env'
EXAMPLE_BACKEND_CONFIG_PATH = EXAMPLE_CONFIG_DIR / 'backend.yaml'
EXAMPLE_SHARED_CONFIG_PATH = EXAMPLE_CONFIG_DIR / 'shared.yaml'

SRC_DIR = ARBOR_IMAGO_DIR.parent
BACKEND_DIR = SRC_DIR.parent
REPO_DIR = BACKEND_DIR.parent


# POSSIBLE ENVIRONMENT VARIABLES

# Priority 1. These three paths are explicit paths set to config files
_backend_secrets_config_path = os.getenv('BACKEND_SECRETS_CONFIG_PATH', None)
_backend_config_path = os.getenv('BACKEND_CONFIG_PATH', None)
_shared_config_path = os.getenv('SHARED_CONFIG_PATH', None)

# also included is 'FRONTEND_CONFIG_PATH', which is not used in the backend

# Priority 2. This specifies the config directory, names of config files are fixed
_config_env_dir = os.getenv('CONFIG_ENV_DIR', None)

# Priority 3. This specifies the name of the config folder, parent direct is the user config dir
_app_env = os.getenv('APP_ENV', None)


def convert_env_path_to_absolute(root_dir: Path, a: str) -> Path:
    """process a relative path sent to an environment variable"""
    A = Path(a)
    if A.is_absolute():
        return A
    else:
        return (root_dir / A).resolve()


def process_explicit_config_path(config_path: str | None) -> Path | None:
    """process an explicit config path sent to an environment variable"""

    if config_path is None:
        return None
    else:
        path = convert_env_path_to_absolute(Path.cwd(), config_path)

        # if the user specifies an exist path, we need to ensure it exists. Do NOT generate a new one
        if not path.exists():
            raise FileNotFoundError(
                'Config path {} does not exist. Please create it or specify a different one.'.format(path))

        return path


BACKEND_SECRETS_CONFIG_PATH = process_explicit_config_path(
    _backend_secrets_config_path)
BACKEND_CONFIG_PATH = process_explicit_config_path(_backend_config_path)
SHARED_CONFIG_PATH = process_explicit_config_path(_shared_config_path)

if BACKEND_SECRETS_CONFIG_PATH is None or BACKEND_CONFIG_PATH is None or SHARED_CONFIG_PATH is None:

    if _config_env_dir is not None:
        CONFIG_ENV_DIR = convert_env_path_to_absolute(
            Path.cwd(), _config_env_dir)
    else:
        # this is going to reference the USER_CONFIG_DIR
        USER_CONFIG_DIR = Path(user_config_dir(
            arbor_imago.__name__, appauthor=False))

        if not USER_CONFIG_DIR.exists():
            warnings.warn(
                'Config dir {} does not exist. Creating a new one.'.format(USER_CONFIG_DIR))
            USER_CONFIG_DIR.mkdir()

        if _app_env is not None:
            CONFIG_ENV_DIR = USER_CONFIG_DIR / _app_env
        else:
            CONFIG_ENV_DIR = USER_CONFIG_DIR / 'dev'
            warnings.warn(
                'Environment variables APP_ENV and CONFIG_ENV_DIR are not set. Defaulting to builtin dev environment located at {}.'.format(CONFIG_ENV_DIR))

    if not CONFIG_ENV_DIR.exists():
        CONFIG_ENV_DIR.mkdir()
        warnings.warn(
            'Config env dir {} does not exist. Creating a new one.'.format(CONFIG_ENV_DIR))

    if BACKEND_SECRETS_CONFIG_PATH is None:
        BACKEND_SECRETS_CONFIG_PATH = CONFIG_ENV_DIR / \
            EXAMPLE_BACKEND_SECRETS_CONFIG_PATH.name
        if not BACKEND_SECRETS_CONFIG_PATH.exists():
            warnings.warn(
                'Backend secrets file {} does not exist. Creating a new one.'.format(BACKEND_SECRETS_CONFIG_PATH))
            BACKEND_SECRETS_CONFIG_PATH.write_text(
                EXAMPLE_BACKEND_SECRETS_CONFIG_PATH.read_text().format(JWT_SECRET_KEY=core_utils.generate_jwt_secret_key()))

    if BACKEND_CONFIG_PATH is None:
        BACKEND_CONFIG_PATH = CONFIG_ENV_DIR / EXAMPLE_BACKEND_CONFIG_PATH.name
        if not BACKEND_CONFIG_PATH.exists():
            warnings.warn(
                'Backend config file {} does not exist. Creating a new one.'.format(BACKEND_CONFIG_PATH))
            BACKEND_CONFIG_PATH.write_text(
                EXAMPLE_BACKEND_CONFIG_PATH.read_text())

    if SHARED_CONFIG_PATH is None:
        SHARED_CONFIG_PATH = CONFIG_ENV_DIR / EXAMPLE_SHARED_CONFIG_PATH.name
        if not SHARED_CONFIG_PATH.exists():
            warnings.warn(
                'Shared config file {} does not exist. Creating a new one.'.format(SHARED_CONFIG_PATH))
            SHARED_CONFIG_PATH.write_text(
                EXAMPLE_SHARED_CONFIG_PATH.read_text())


# Shared config

class SharedConfig(TypedDict):
    BACKEND_URL: str
    FRONTEND_URL: str
    AUTH_KEY: str
    HEADER_KEYS: dict[str, str]
    FRONTEND_ROUTES: dict[str, str]
    SCOPE_NAME_MAPPING: dict[custom_types.Scope.name, custom_types.Scope.id]
    VISIBILITY_LEVEL_NAME_MAPPING: dict[custom_types.VisibilityLevel.name,
                                        custom_types.VisibilityLevel.id]
    PERMISSION_LEVEL_NAME_MAPPING: dict[custom_types.PermissionLevel.name,
                                        custom_types.PermissionLevel.id]
    USER_ROLE_NAME_MAPPING: dict[custom_types.UserRole.name,
                                 custom_types.UserRole.id]
    USER_ROLE_SCOPES: dict[custom_types.UserRole.name,
                           list[custom_types.Scope.name]]
    OTP_LENGTH: int
    GOOGLE_CLIENT_ID: str


# generate these files if they do not exist

# read in the shared config file

with SHARED_CONFIG_PATH.open('r') as f:
    _SHARED_CONFIG: SharedConfig = yaml.safe_load(f)


# info from shared constants constants
BACKEND_URL: str = _SHARED_CONFIG['BACKEND_URL']
FRONTEND_URL: str = _SHARED_CONFIG['FRONTEND_URL']
AUTH_KEY: str = _SHARED_CONFIG['AUTH_KEY']
HEADER_KEYS: dict[str, str] = _SHARED_CONFIG['HEADER_KEYS']
FRONTEND_ROUTES: dict[str, str] = _SHARED_CONFIG['FRONTEND_ROUTES']

SCOPE_NAME_MAPPING: dict[custom_types.Scope.name,
                         custom_types.Scope.id] = _SHARED_CONFIG['SCOPE_NAME_MAPPING']
SCOPE_ID_MAPPING: dict[custom_types.Scope.id, custom_types.Scope.name] = {
    SCOPE_NAME_MAPPING[scope_name]: scope_name for scope_name in SCOPE_NAME_MAPPING
}

VISIBILITY_LEVEL_NAME_MAPPING: dict[custom_types.VisibilityLevel.name,
                                    custom_types.VisibilityLevel.id] = _SHARED_CONFIG['VISIBILITY_LEVEL_NAME_MAPPING']


PERMISSION_LEVEL_NAME_MAPPING: dict[custom_types.PermissionLevel.name,
                                    custom_types.PermissionLevel.id] = _SHARED_CONFIG['PERMISSION_LEVEL_NAME_MAPPING']

USER_ROLE_NAME_MAPPING: dict[custom_types.UserRole.name,
                             custom_types.UserRole.id] = _SHARED_CONFIG['USER_ROLE_NAME_MAPPING']

USER_ROLE_ID_SCOPE_IDS: dict[custom_types.UserRole.id,
                             set[custom_types.Scope.id]] = {
    USER_ROLE_NAME_MAPPING[user_role_name]: set([
        SCOPE_NAME_MAPPING[scope_name] for scope_name in _SHARED_CONFIG['USER_ROLE_SCOPES'][user_role_name]
    ]) for user_role_name in USER_ROLE_NAME_MAPPING
}

GOOGLE_CLIENT_ID = _SHARED_CONFIG['GOOGLE_CLIENT_ID']
OTP_LENGTH: int = _SHARED_CONFIG['OTP_LENGTH']

# Backend Config


class DbEnv(TypedDict):
    URL: str


CredentialNames = typing.Literal['access_token',
                                 'magic_link', 'request_sign_up', 'otp']


class AuthEnv(TypedDict):
    credential_lifespans: dict[CredentialNames,
                               custom_types.ISO8601DurationStr]


class AccessTokenCookie(TypedDict):
    key: str
    secure: NotRequired[bool]
    httponly: NotRequired[bool]
    samesite: NotRequired[Literal['lax', 'strict', 'none']]


class BackendConfig(TypedDict):
    UVICORN: dict
    DB: DbEnv
    MEDIA_DIR: str
    GOOGLE_CLIENT_PATH: str
    AUTH: AuthEnv
    OPENAPI_SCHEMA_PATH: str
    ACCESS_TOKEN_COOKIE: AccessTokenCookie


with BACKEND_CONFIG_PATH.open('r') as f:
    _BACKEND_CONFIG: BackendConfig = yaml.safe_load(f)


DB_ASYNC_ENGINE = create_async_engine(_BACKEND_CONFIG['DB']['URL'])
ASYNC_SESSIONMAKER = async_sessionmaker(
    bind=DB_ASYNC_ENGINE,
    class_=SQLMAsyncSession,
    expire_on_commit=False
)

MEDIA_DIR = convert_env_path_to_absolute(
    BACKEND_DIR, _BACKEND_CONFIG['MEDIA_DIR'])

GALLERIES_DIR = MEDIA_DIR / 'galleries'
UVICORN = _BACKEND_CONFIG['UVICORN']


class AuthConfig(TypedDict):
    credential_lifespans: dict[CredentialNames, datetime_module.timedelta]


AUTH: AuthConfig = {
    'credential_lifespans': {
        key: isodate.parse_duration(value) for key, value in _BACKEND_CONFIG['AUTH']['credential_lifespans'].items()
    }
}

OPENAPI_SCHEMA_PATH = convert_env_path_to_absolute(
    Path.cwd(), _BACKEND_CONFIG['OPENAPI_SCHEMA_PATH'])

ACCESS_TOKEN_COOKIE: AccessTokenCookie = _BACKEND_CONFIG['ACCESS_TOKEN_COOKIE']


class BackendSecrets(TypedDict):
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str


BACKEND_SECRETS = typing.cast(
    BackendSecrets, dotenv_values(BACKEND_SECRETS_CONFIG_PATH))
