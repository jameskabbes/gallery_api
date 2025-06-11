from enum import Enum
from sqlmodel import SQLModel
from typing import TypedDict, Generic, TypeVar
from arbor_imago import custom_types


TSub = TypeVar('TSub')


class Type(Enum):
    ACCESS_TOKEN = 'access_token'
    API_KEY = 'api_key'
    OTP = 'otp'
    SIGN_UP = 'sign_up'


class JwtPayload(Generic[TSub], TypedDict):
    sub: TSub
    exp: custom_types.AuthCredential.expiry_timestamp
    iat: custom_types.AuthCredential.issued_timestamp
    type: custom_types.AuthCredential.type
