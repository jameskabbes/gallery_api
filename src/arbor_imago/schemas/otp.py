from pydantic import BaseModel
from typing import Optional

from arbor_imago import custom_types
from arbor_imago.schemas import auth_credential as auth_credential_schema


class OTPAdminUpdate(BaseModel):
    pass


class OTPAdminCreate(BaseModel):
    user_id: custom_types.User.id
    hashed_code: custom_types.OTP.hashed_code
    expiry: custom_types.AuthCredential.expiry
