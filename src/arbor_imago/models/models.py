from sqlmodel import Field

from arbor_imago.models.bases.auth_credential import AuthCredentialBase
from arbor_imago.core import types


class SignUp(AuthCredentialBase):
    email: types.User.email = Field()
