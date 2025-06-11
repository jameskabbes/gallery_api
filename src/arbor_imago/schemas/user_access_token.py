from pydantic import BaseModel
from arbor_imago import custom_types
from arbor_imago.schemas import FromAttributes


class UserAccessTokenAdminUpdate(BaseModel):
    expiry: custom_types.AuthCredential.expiry


class UserAccessTokenAdminCreate(BaseModel):
    expiry: custom_types.AuthCredential.expiry
    user_id: custom_types.User.id


class UserAccessTokenExport(FromAttributes):
    pass


class UserAccessTokenPublic(UserAccessTokenExport):
    id: custom_types.UserAccessToken.id
    expiry: custom_types.AuthCredential.expiry


class UserAccessTokenPrivate(UserAccessTokenExport):
    id: custom_types.UserAccessToken.id
    expiry: custom_types.AuthCredential.expiry
    user_id: custom_types.User.id
