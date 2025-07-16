from pydantic import BaseModel
from arbor_imago.core import types
from arbor_imago.schemas import FromAttributes


class UserAccessTokenAdminUpdate(BaseModel):
    expiry: types.AuthCredential.expiry


class UserAccessTokenAdminCreate(BaseModel):
    expiry: types.AuthCredential.expiry
    user_id: types.User.id


class UserAccessTokenExport(FromAttributes):
    pass


class UserAccessTokenPublic(UserAccessTokenExport):
    id: types.UserAccessToken.id
    expiry: types.AuthCredential.expiry


class UserAccessTokenPrivate(UserAccessTokenExport):
    id: types.UserAccessToken.id
    expiry: types.AuthCredential.expiry
    user_id: types.User.id
