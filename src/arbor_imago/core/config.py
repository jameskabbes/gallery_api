from arbor_imago import utils
from arbor_imago.core import types
import arbor_imago

from pathlib import Path
import os
import typing
import yaml
from dotenv import dotenv_values
import isodate
from platformdirs import user_config_dir
import warnings

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


def convert_env_path_to_absolute(root_dir: Path, a: str | os.PathLike[str]) -> Path:
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
                EXAMPLE_BACKEND_SECRETS_CONFIG_PATH.read_text().format(JWT_SECRET_KEY=utils.generate_jwt_secret_key()))

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


# generate these files if they do not exist
# read in the shared config file

with SHARED_CONFIG_PATH.open('r') as f:
    _SHARED_CONFIG: types.SharedConfig = yaml.safe_load(f)


# info from shared constants constants
BACKEND_URL = _SHARED_CONFIG['BACKEND_URL']
FRONTEND_URL = _SHARED_CONFIG['FRONTEND_URL']
AUTH_KEY = _SHARED_CONFIG['AUTH_KEY']
HEADER_KEYS = _SHARED_CONFIG['HEADER_KEYS']
FRONTEND_ROUTES = _SHARED_CONFIG['FRONTEND_ROUTES']

SCOPE_NAME_MAPPING = _SHARED_CONFIG['SCOPE_NAME_MAPPING']
SCOPE_ID_MAPPING = {
    SCOPE_NAME_MAPPING[scope_name]: scope_name for scope_name in SCOPE_NAME_MAPPING
}

VISIBILITY_LEVEL_NAME_MAPPING = _SHARED_CONFIG['VISIBILITY_LEVEL_NAME_MAPPING']
PERMISSION_LEVEL_NAME_MAPPING = _SHARED_CONFIG['PERMISSION_LEVEL_NAME_MAPPING']

USER_ROLE_NAME_MAPPING = _SHARED_CONFIG['USER_ROLE_NAME_MAPPING']

USER_ROLE_ID_SCOPE_IDS = {
    USER_ROLE_NAME_MAPPING[user_role_name]: set([
        SCOPE_NAME_MAPPING[scope_name] for scope_name in _SHARED_CONFIG['USER_ROLE_SCOPES'][user_role_name]
    ]) for user_role_name in USER_ROLE_NAME_MAPPING
}

GOOGLE_CLIENT_ID = _SHARED_CONFIG['GOOGLE_CLIENT_ID']
OTP_LENGTH = _SHARED_CONFIG['OTP_LENGTH']

# Backend Config


with BACKEND_CONFIG_PATH.open('r') as f:
    _BACKEND_CONFIG: types.BackendConfig = yaml.safe_load(f)


DB = _BACKEND_CONFIG['DB']

MEDIA_DIR = convert_env_path_to_absolute(
    BACKEND_DIR, _BACKEND_CONFIG['MEDIA_DIR'])

GALLERIES_DIR = MEDIA_DIR / 'galleries'
UVICORN = _BACKEND_CONFIG['UVICORN']


AUTH: types.AuthConfig = {
    'credential_lifespans': {
        key: isodate.parse_duration(value) for key, value in _BACKEND_CONFIG['AUTH']['credential_lifespans'].items()
    }
}

OPENAPI_SCHEMA_PATHS: dict[types.OpenAPISchemaKeys, Path] = {
    d: convert_env_path_to_absolute(
        Path.cwd(), _BACKEND_CONFIG['OPENAPI_SCHEMA_PATHS'][d]) for d in _BACKEND_CONFIG['OPENAPI_SCHEMA_PATHS']
}


ACCESS_TOKEN_COOKIE = _BACKEND_CONFIG['ACCESS_TOKEN_COOKIE']


BACKEND_SECRETS = typing.cast(
    types.BackendSecrets, dotenv_values(BACKEND_SECRETS_CONFIG_PATH))
