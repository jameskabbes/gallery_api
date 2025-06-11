from sqlmodel import Field

from arbor_imago.models.bases.auth_credential import AuthCredentialBase
from arbor_imago import custom_types


class SignUp(AuthCredentialBase):
    email: custom_types.User.email = Field()
