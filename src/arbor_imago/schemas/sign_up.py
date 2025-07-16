from sqlmodel import Field
from pydantic import BaseModel
from arbor_imago.core import types


class SignUpAdminCreate(BaseModel):
    email: types.SignUp.email
    expiry: types.AuthCredential.expiry
