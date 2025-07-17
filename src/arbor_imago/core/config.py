from arbor_imago import utils
from arbor_imago.core import types
import arbor_imago

from pathlib import Path
import os
from dotenv import dotenv_values, load_dotenv
import isodate
from platformdirs import user_config_dir
import warnings
import datetime

# /gallery/gallery_api/src/arbor_imago/
ARBOR_IMAGO_DIR = Path(__file__).parent

SRC_DIR = ARBOR_IMAGO_DIR.parent
BACKEND_DIR = SRC_DIR.parent
REPO_DIR = BACKEND_DIR.parent

USER_CONFIG_DIR = Path(user_config_dir(
    arbor_imago.__name__, appauthor=False))

_env_var_mapping: dict[str, types.EnvVar] = {
    'env': 'ARBOR_IMAGO_ENV',
    'config_dir': 'ARBOR_IMAGO_CONFIG_DIR',
    'env_path': 'ARBOR_IMAGO_ENV_PATH',
    'backend_config_path': 'ARBOR_IMAGO_BACKEND_CONFIG_PATH',
    'shared_config_path': 'ARBOR_IMAGO_SHARED_CONFIG_PATH',
    'jwt_secret_key': 'ARBOR_IMAGO_JWT_SECRET_KEY'
}

# ENV
env_env = os.getenv(_env_var_mapping['env'])
ENV = env_env if env_env else 'local'

# CONFIG_DIR
env_config_dir = os.getenv(_env_var_mapping['config_dir'])
if env_config_dir is None:
    CONFIG_DIR = USER_CONFIG_DIR / ENV
else:
    CONFIG_DIR = utils.resolve_path(Path.cwd(), env_config_dir)


# ENV_PATH
env_env_path = os.getenv(_env_var_mapping['env_path'])
ENV_PATH = None
if env_env_path is not None:
    ENV_PATH = utils.resolve_path(Path.cwd(), env_env_path)
else:
    ENV_PATH = CONFIG_DIR / '.env'

load_dotenv(ENV_PATH)
_dotenv_values = dotenv_values(ENV_PATH)

if _env_var_mapping['env'] in _dotenv_values and _dotenv_values[_env_var_mapping['env']] != ENV:
    raise ValueError(
        f'ENV in .env file ({_dotenv_values["ENV"]}) does not match ENV environment variable ({ENV}). '
        'Please ensure they are consistent.'
    )
if _env_var_mapping['env_path'] in _dotenv_values:
    raise ValueError(
        f'ENV_PATH in .env file ({_dotenv_values["ENV_PATH"]}) is not supported. '
        'Please remove it from the .env file.'
    )


env_backend_config_path = os.getenv(_env_var_mapping['backend_config_path'])
BACKEND_CONFIG_PATH = utils.resolve_path(
    Path.cwd(), env_backend_config_path
) if env_backend_config_path else None

env_shared_config_path = os.getenv(_env_var_mapping['shared_config_path'])
SHARED_CONFIG_PATH = utils.resolve_path(
    Path.cwd(), env_shared_config_path
) if env_shared_config_path else None


# Backend Config
_backend_config: types.BackendConfig = {}

if BACKEND_CONFIG_PATH is not None:
    if BACKEND_CONFIG_PATH.exists():
        _backend_config.update(utils.load_dict_from_file(BACKEND_CONFIG_PATH))


DB = _backend_config.get('DB', {
    'URL': 'sqlite+aiosqlite:///./data/gallery.db'
})


# uvicorn
UVICORN: types.UvicornConfig = {}
if ENV == 'local':
    UVICORN['reload'] = True

UVICORN.update(_backend_config.get('UVICORN', {}))


# Media Dir
_media_dir = _backend_config.get('MEDIA_DIR')

if _media_dir is None:
    MEDIA_DIR = Path.cwd() / 'media'
else:
    MEDIA_DIR = utils.resolve_path(
        Path.cwd(), _media_dir)


GALLERIES_DIR = MEDIA_DIR / 'galleries'

# Auth
_auth: types.AuthTextConfig = {}
_auth.update(_backend_config.get('AUTH', {}))

_auth_credential_lifespans: types.CredentialLifespans = {
    'access_token': datetime.timedelta(days=7),
    'magic_link': datetime.timedelta(minutes=10),
    'request_sign_up': datetime.timedelta(hours=1),
    'otp': datetime.timedelta(minutes=10)
}

_auth_credential_lifespans.update(
    {
        key: isodate.parse_duration(value) for key, value in _auth.get('credential_lifespans', {}).items()
    }
)

_jwt_algorithm = _auth.get('jwt_algorithm', 'HS256')
_jwt_secret_key = os.getenv('JWT_SECRET_KEY')

if _jwt_secret_key is None:
    raise ValueError(
        'JWT_SECRET_KEY must be set as an environment variable.')


AUTH: types.AuthConfig = {
    'credential_lifespans': _auth_credential_lifespans,
    'jwt_algorithm': _jwt_algorithm,
    'jwt_secret_key': _jwt_secret_key
}


# OpenAPI Schema Paths
OPENAPI_SCHEMA_PATHS: types.OpenAPISchemaPaths = {
    'gallery': Path.cwd().parent / 'gallery_api_schema.json'
}

_openapi_schema_paths = _backend_config.get('OPENAPI_SCHEMA_PATHS', {})

OPENAPI_SCHEMA_PATHS.update({
    key: utils.resolve_path(
        Path.cwd(), _openapi_schema_paths[key]) for key in _openapi_schema_paths
})

# access_token_cookie
ACCESS_TOKEN_COOKIE: types.AccessTokenCookieConfig = {
    'key': 'access_token',
    'secure': True,
    'httponly': True,
    'samesite': 'lax'
}
_access_token_cookie = _backend_config.get('ACCESS_TOKEN_COOKIE', {})
ACCESS_TOKEN_COOKIE.update(_access_token_cookie)

LOGGER: types.LoggerConfig = {
    'level': 'DEBUG' if ENV == 'local' else 'INFO',
}

_shared_config: types.SharedConfig = {}

if SHARED_CONFIG_PATH is not None:
    if SHARED_CONFIG_PATH.exists():
        _shared_config.update(utils.load_dict_from_file(SHARED_CONFIG_PATH))


# info from shared constants constants
BACKEND_URL = _shared_config.get(
    'BACKEND_URL', 'http://localhost:' + str(UVICORN.get('port', 8000)))
FRONTEND_URL = _shared_config.get(
    'FRONTEND_URL', 'http://localhost:3000')
AUTH_KEY = _shared_config.get('AUTH_KEY', 'auth')


HEADER_KEYS: types.HeaderKeys = {
    'auth_logout': 'x-auth-logout'
}
HEADER_KEYS.update(_shared_config.get('HEADER_KEYS', {}))

FRONTEND_ROUTES: types.FrontendRoutes = {
    'verify_email': '/welcome',
    'verify_magic_link': '/verify-magic-link',
    'galleries': '/galleries',
}
FRONTEND_ROUTES.update(_shared_config.get('FRONTEND_ROUTES', {}))

SCOPE_NAME_MAPPING: types.ScopeNameMapping = {
    'admin': 1,
    'users.read': 2,
    'users.write': 3,
}

SCOPE_ID_MAPPING: types.ScopeIdMapping = {
    SCOPE_NAME_MAPPING[scope_name]: scope_name for scope_name in SCOPE_NAME_MAPPING
}

VISIBILITY_LEVEL_NAME_MAPPING: types.VisibilityLevelNameMapping = {
    'public': 1,
    'private': 2,
}
VISIBILITY_LEVEL_NAME_MAPPING.update(
    _shared_config.get('VISIBILITY_LEVEL_NAME_MAPPING', {})
)

PERMISSION_LEVEL_NAME_MAPPING: types.PermissionLevelNameMapping = {
    'editor': 2,
    'viewer': 1,
}
PERMISSION_LEVEL_NAME_MAPPING.update(
    _shared_config.get('PERMISSION_LEVEL_NAME_MAPPING', {})
)

USER_ROLE_NAME_MAPPING: types.UserRoleNameMapping = {
    'admin': 1,
    'user': 2,
}
USER_ROLE_NAME_MAPPING.update(
    _shared_config.get('USER_ROLE_NAME_MAPPING', {}))

USER_ROLE_NAME_SCOPE_NAMES: types.UserRoleNameScopeNamesSet = {
    'admin': {'admin', 'users.read', 'users.write'},
    'user': {'users.read', 'users.write'},
}
USER_ROLE_NAME_SCOPE_NAMES.update(
    {key: set(value) for key, value in _shared_config.get(
        'USER_ROLE_NAME_SCOPE_NAMES', {}).items()}
)

USER_ROLE_ID_SCOPE_IDS: types.UserRoleIdScopeIds = {
    USER_ROLE_NAME_MAPPING[user_role_name]: set([
        SCOPE_NAME_MAPPING[scope_name] for scope_name in USER_ROLE_NAME_SCOPE_NAMES[user_role_name]
    ]) for user_role_name in USER_ROLE_NAME_MAPPING
}

GOOGLE_CLIENT_ID = _shared_config.get(
    'GOOGLE_CLIENT_ID', 'abcdef.apps.googleusercontent.com')
OTP_LENGTH = _shared_config.get('OTP_LENGTH', 6)
