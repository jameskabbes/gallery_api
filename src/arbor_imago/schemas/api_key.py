from pydantic import BaseModel
from typing import Optional

from arbor_imago import custom_types
from arbor_imago.schemas import auth_credential as auth_credential_schema


class ApiKeyAvailable(BaseModel):
    name: custom_types.ApiKey.name


class ApiKeyAdminAvailable(ApiKeyAvailable):
    user_id: custom_types.User.id


class ApiKeyImport(BaseModel):
    pass


class ApiKeyUpdate(ApiKeyImport):
    name: Optional[custom_types.ApiKey.name] = None
    expiry: custom_types.AuthCredential.expiry | None = None


class ApiKeyAdminUpdate(ApiKeyUpdate, BaseModel):
    pass


class ApiKeyCreate(ApiKeyImport):
    name: custom_types.ApiKey.name
    expiry: custom_types.AuthCredential.expiry


class ApiKeyAdminCreate(ApiKeyCreate, BaseModel):
    user_id: custom_types.User.id


class ApiKeyExport(BaseModel):
    id: custom_types.ApiKey.id
    user_id: custom_types.User.id
    name: custom_types.ApiKey.name
    issued: custom_types.ApiKey.issued
    expiry: custom_types.ApiKey.expiry


class ApiKeyPublic(ApiKeyExport):
    pass


class ApiKeyPrivate(ApiKeyExport):
    pass
