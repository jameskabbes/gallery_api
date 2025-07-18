import os
from typing import Annotated, Literal, Union, NamedTuple, TypeVar, NewType, Type, Any, Optional, TypedDict, NotRequired
from pydantic import EmailStr, StringConstraints, GetCoreSchemaHandler, BaseModel
from pydantic_core import core_schema
import re
import datetime as datetime_module
from pathlib import Path

PhoneNumber = str
Email = Annotated[EmailStr, StringConstraints(
    min_length=1, max_length=254)]
JwtEncodedStr = str
ISO8601DurationStr = Annotated[str, "ISO 8601 duration string"]


class PermissionLevel:
    id = int
    name = Literal['editor', 'viewer']


class VisibilityLevel:
    id = int
    name = Literal['public', 'private']


class Scope:
    id = int
    name = Literal['admin', 'users.read', 'users.write']


class UserRole:
    id = int
    name = Literal['admin', 'user']


UserId = str


class User:
    id = str
    email = Email
    phone_number = PhoneNumber

    password = Annotated[str, StringConstraints(
        min_length=1, max_length=64)]
    username = Annotated[str, StringConstraints(
        min_length=3, max_length=20, pattern=re.compile(r'^[a-zA-Z0-9_.-]+$'), to_lower=True)]
    hashed_password = str
    user_role_id = UserRole.id


timestamp = float


class AuthCredential:
    issued = Annotated[datetime_module.datetime,
                       'The datetime at which the auth credential was issued']
    issued_timestamp = Annotated[timestamp,
                                 'The datetime at which the auth credential was issued']
    expiry = Annotated[datetime_module.datetime,
                       'The datetime at which the auth credential will expire']
    expiry_timestamp = Annotated[timestamp,
                                 'The datetime at which the auth credential will expire']
    type = Literal['access_token', 'api_key', 'otp', 'sign_up']


OTPId = str


class OTP(AuthCredential):
    id = OTPId
    code = Annotated[str, StringConstraints(
        min_length=6, max_length=6, pattern=re.compile(r'^\d{' + str(6) + r'}$'))]
    hashed_code = str


UserAccessTokenId = str


class UserAccessToken(AuthCredential):
    id = UserAccessTokenId


ApiKeyId = str


class ApiKey(AuthCredential):
    id = ApiKeyId
    name = Annotated[str, StringConstraints(
        min_length=1, max_length=256)]
    order_by = Literal['issued', 'expiry', 'name']


class SignUp(AuthCredential):
    email = User.email


GalleryId = str


class Gallery:
    id = GalleryId
    user_id = User.id

    # name can't start with the `YYYY-MM-DD ` pattern
    name = Annotated[str, StringConstraints(
        min_length=1, max_length=256, pattern=re.compile(r'^(?!\d{4}-\d{2}-\d{2} ).*'))]
    visibility_level = VisibilityLevel.id
    parent_id = GalleryId
    description = Annotated[str, StringConstraints(
        min_length=0, max_length=20000)]
    date = datetime_module.date
    folder_name = str


class GalleryDateAndName(NamedTuple):
    date: datetime_module.date | None
    name: str


class _GalleryPermissionBase:
    gallery_id = Gallery.id
    user_id = User.id
    permission_level = PermissionLevel.id


class GalleryPermissionId(NamedTuple):
    gallery_id: GalleryId
    user_id: User.id


class GalleryPermission(_GalleryPermissionBase):
    id = GalleryPermissionId


class _ApiKeyScopeBase:
    api_key_id = ApiKey.id
    scope_id = Scope.id


class ApiKeyScopeId(NamedTuple):
    api_key_id: ApiKey.id
    scope_id: Scope.id


class ApiKeyScope(_ApiKeyScopeBase):
    id = ApiKeyScopeId


FileId = str


class File:
    id = FileId
    stem = str
    suffix = Annotated[str, StringConstraints(
        to_lower=True)]
    size = int
    gallery_id = Gallery.id


ImageVersionId = str


class ImageVersion:

    id = ImageVersionId
    gallery_id = Gallery.id
    base_name = Annotated[str, StringConstraints(
        # prohibit underscore
        min_length=1, max_length=240, pattern=re.compile(r'^(?!.*_).+$')
    )]
    version = Annotated[str, StringConstraints(
        # version cannot be exactly two digits
        pattern=re.compile(r'^(?!\d{2}$).+$'))]
    parent_id = ImageVersionId
    datetime = datetime_module.datetime
    description = Annotated[str, StringConstraints(
        min_length=0, max_length=20000)]
    aspect_ratio = float
    average_color = str


class ImageFileMetadata:
    file_id = File.id
    version_id = ImageVersion.id
    scale = int


SimpleId = UserId | OTPId | UserAccessTokenId | ApiKeyId | GalleryId | FileId | ImageVersionId
Id = SimpleId | GalleryPermissionId | ApiKeyScopeId

TSimpleId = TypeVar('TSimpleId', bound=SimpleId)
TSimpleId_co = TypeVar('TSimpleId_co', bound=SimpleId, covariant=True)
TSimpleId_contra = TypeVar(
    'TSimpleId_contra', bound=SimpleId, contravariant=True)

TId = TypeVar('TId', bound=Id)
TId_co = TypeVar('TId_co', bound=Id, covariant=True)
TId_contra = TypeVar('TId_contra', bound=Id, contravariant=True)


class NotNullable:
    def __get_pydantic_core_schema__(self, source: Type[Any], handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        schema = handler(source)
        assert schema["type"] == "nullable"
        return schema["schema"]


T = TypeVar("T")
Omissible = Annotated[Optional[T], NotNullable()]

HeaderKeys = dict[str, str]
FrontendRoutes = dict[str, str]
ScopeNameMapping = dict[Scope.name, Scope.id]
ScopeIdMapping = dict[Scope.id, Scope.name]
VisibilityLevelNameMapping = dict[VisibilityLevel.name, VisibilityLevel.id]
PermissionLevelNameMapping = dict[PermissionLevel.name, PermissionLevel.id]
UserRoleNameMapping = dict[UserRole.name, UserRole.id]
UserRoleNameScopeNamesSet = dict[UserRole.name, set[Scope.name]]
UserRoleNameScopeNamesList = dict[UserRole.name, list[Scope.name]]
UserRoleIdScopeIdsSet = dict[UserRole.id, set[Scope.id]]
UserRoleIdScopeIdsList = dict[UserRole.id, list[Scope.id]]


class SharedConfigFromFile(TypedDict, total=False):
    BACKEND_URL: str
    FRONTEND_URL: str
    AUTH_KEY: str
    HEADER_KEYS: HeaderKeys
    FRONTEND_ROUTES: FrontendRoutes
    SCOPE_NAME_MAPPING: ScopeNameMapping
    VISIBILITY_LEVEL_NAME_MAPPING: VisibilityLevelNameMapping
    PERMISSION_LEVEL_NAME_MAPPING: PermissionLevelNameMapping
    USER_ROLE_NAME_MAPPING: UserRoleNameMapping
    USER_ROLE_NAME_SCOPE_NAMES: UserRoleNameScopeNamesList
    OTP_LENGTH: int
    GOOGLE_CLIENT_ID: str


class GeneratedSharedConfig(TypedDict):
    ENV: str
    BACKEND_URL: str
    FRONTEND_URL: str
    AUTH_KEY: str
    HEADER_KEYS: HeaderKeys
    FRONTEND_ROUTES: FrontendRoutes
    SCOPE_NAME_MAPPING: ScopeNameMapping
    VISIBILITY_LEVEL_NAME_MAPPING: VisibilityLevelNameMapping
    PERMISSION_LEVEL_NAME_MAPPING: PermissionLevelNameMapping
    USER_ROLE_NAME_MAPPING: UserRoleNameMapping
    USER_ROLE_SCOPES: UserRoleNameScopeNamesList
    OTP_LENGTH: int
    GOOGLE_CLIENT_ID: str


class UvicornConfig(TypedDict):
    run_kwargs: dict
    use_string_import: NotRequired[bool]


class UvicornConfigFromFile(TypedDict, total=False):
    run_kwargs: dict
    use_string_import: bool


class DbConfigFromFile(TypedDict, total=False):
    URL: str


class DbConfig(TypedDict):
    URL: str


CredentialNames = Literal['access_token',
                          'magic_link', 'request_sign_up', 'otp']


CredentialLifespans = dict[CredentialNames, datetime_module.timedelta]


class AuthConfig(TypedDict):
    credential_lifespans: CredentialLifespans
    jwt_algorithm: str
    jwt_secret_key: str


class AuthConfigFromFile(TypedDict, total=False):
    credential_lifespans: dict[CredentialNames,
                               ISO8601DurationStr]
    jwt_algorithm: str


class AccessTokenCookieConfig(TypedDict):
    key: str
    secure: NotRequired[bool]
    httponly: NotRequired[bool]
    samesite: NotRequired[Literal['lax', 'strict', 'none']]


class AccessTokenCookieConfigFromFile(TypedDict, total=False):
    key: str
    secure: bool
    httponly: bool
    samesite: Literal['lax', 'strict', 'none']


class LoggerConfig(TypedDict, total=False):
    level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']


OpenAPISchemaKeys = Literal['gallery']
OpenAPISchemaPaths = dict[OpenAPISchemaKeys, Path]


class BackendConfigFromFile(TypedDict, total=False):
    UVICORN: UvicornConfigFromFile
    DB: DbConfigFromFile
    MEDIA_DIR: str
    GOOGLE_CLIENT_PATH: str
    AUTH: AuthConfigFromFile
    OPENAPI_SCHEMA_PATHS: dict[OpenAPISchemaKeys, os.PathLike[str] | str]
    ACCESS_TOKEN_COOKIE: AccessTokenCookieConfigFromFile


EnvVar = Literal[
    'ARBOR_IMAGO_ENV',
    'ARBOR_IMAGO_CONFIG_DIR',
    'ARBOR_IMAGO_ENV_PATH',
    'ARBOR_IMAGO_BACKEND_CONFIG_PATH',
    'ARBOR_IMAGO_SHARED_CONFIG_PATH',
    'ARBOR_IMAGO_GENERATED_SHARED_CONFIG_PATH',
    'ARBOR_IMAGO_JWT_SECRET_KEY'
]
