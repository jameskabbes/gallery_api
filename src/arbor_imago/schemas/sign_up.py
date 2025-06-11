from sqlmodel import Field
from pydantic import BaseModel
from arbor_imago import custom_types


class SignUpAdminCreate(BaseModel):
    email: custom_types.SignUp.email
    expiry: custom_types.AuthCredential.expiry
