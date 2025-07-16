from enum import Enum
from sqlmodel import SQLModel
from typing import TypedDict, Generic, TypeVar
from arbor_imago.core import types


TSub = TypeVar('TSub')


class Type(Enum):
    ACCESS_TOKEN = 'access_token'
    API_KEY = 'api_key'
    OTP = 'otp'
    SIGN_UP = 'sign_up'


class JwtPayload(Generic[TSub], TypedDict):
    sub: TSub
    exp: types.AuthCredential.expiry_timestamp
    iat: types.AuthCredential.issued_timestamp
    type: types.AuthCredential.type
