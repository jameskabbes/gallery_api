from arbor_imago.core import types

from pydantic import BaseModel


class OTPAdminUpdate(BaseModel):
    pass


class OTPAdminCreate(BaseModel):
    user_id: types.User.id
    hashed_code: types.OTP.hashed_code
    expiry: types.AuthCredential.expiry
