from sqlmodel import SQLModel
from pydantic import field_serializer, field_validator, ValidationInfo
import datetime as datetime_module

from arbor_imago import custom_types
from arbor_imago.models.custom_field_types import timestamp


class AuthCredentialBase(SQLModel):
    issued: custom_types.AuthCredential.issued
    expiry: custom_types.AuthCredential.expiry

    @field_validator('expiry', 'issued')
    @classmethod
    def validate_datetime(cls, v: custom_types.AuthCredential.expiry | custom_types.AuthCredential.issued, info: ValidationInfo) -> custom_types.AuthCredential.expiry | custom_types.AuthCredential.issued:
        return timestamp.validate_and_normalize_datetime(v, info)

    @field_serializer('expiry', 'issued')
    @classmethod
    def serialize_datetime(cls, v: custom_types.AuthCredential.expiry | custom_types.AuthCredential.issued) -> custom_types.AuthCredential.expiry | custom_types.AuthCredential.issued:
        return v.astimezone(datetime_module.timezone.utc)
