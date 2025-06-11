from pydantic import BaseModel, Field
from typing import Optional
from arbor_imago import custom_types, config
from arbor_imago.schemas import FromAttributes


class UserImport(BaseModel):
    phone_number: Optional[custom_types.User.phone_number] = None
    username: Optional[custom_types.User.username] = None
    password: Optional[custom_types.User.password] = None


class UserUpdate(UserImport):
    email: Optional[custom_types.User.email] = None


class UserAdminUpdate(UserUpdate):
    user_role_id: Optional[custom_types.User.user_role_id] = None


class UserCreate(UserImport):
    email: custom_types.User.email


class UserAdminCreate(UserCreate):
    user_role_id: custom_types.User.user_role_id = config.USER_ROLE_NAME_MAPPING['user']


class UserExport(FromAttributes):
    id: custom_types.User.id
    username: Optional[custom_types.User.username] = None


class UserPublic(UserExport):
    pass


class UserPrivate(UserExport):
    email: custom_types.User.email
    user_role_id: custom_types.User.user_role_id
