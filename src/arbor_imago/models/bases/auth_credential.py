from sqlmodel import SQLModel
from pydantic import field_serializer, field_validator, ValidationInfo
import datetime as datetime_module

from arbor_imago.core import types
from arbor_imago.models.custom_field_types import timestamp


class AuthCredentialBase(SQLModel):
    issued: types.AuthCredential.issued
    expiry: types.AuthCredential.expiry

    @field_validator('expiry', 'issued')
    @classmethod
    def validate_datetime(cls, v: types.AuthCredential.expiry | types.AuthCredential.issued, info: ValidationInfo) -> types.AuthCredential.expiry | types.AuthCredential.issued:
        return timestamp.validate_and_normalize_datetime(v, info)

    @field_serializer('expiry', 'issued')
    @classmethod
    def serialize_datetime(cls, v: types.AuthCredential.expiry | types.AuthCredential.issued) -> types.AuthCredential.expiry | types.AuthCredential.issued:
        return v.astimezone(datetime_module.timezone.utc)
