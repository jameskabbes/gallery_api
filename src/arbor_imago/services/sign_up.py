import datetime as datetime_module

from arbor_imago import custom_types
from arbor_imago.models.models import SignUp as SignUpModel
from arbor_imago.schemas import sign_up as sign_up_schema, auth_credential as auth_credential_schema
from arbor_imago.services import auth_credential as auth_credential_service


class SignUp(
    auth_credential_service.JwtIO[
        SignUpModel, custom_types.SignUp.email],
    auth_credential_service.JwtNotTable[
        SignUpModel, custom_types.SignUp.email, sign_up_schema.SignUpAdminCreate],
):

    auth_type = auth_credential_schema.Type.SIGN_UP
    _MODEL = SignUpModel

    @classmethod
    def _model_sub(cls, inst):
        return inst.email

    @classmethod
    def model_inst_from_create_model(cls, create_model):
        """Create a new instance of the model from the create model (TCreateModel), don't overwrite this method"""

        return cls._MODEL(
            issued=datetime_module.datetime.now().astimezone(datetime_module.UTC),
            **create_model.model_dump()
        )

    @classmethod
    def model_inst_from_jwt_payload(cls, payload):
        return cls._MODEL(
            issued=datetime_module.datetime.fromtimestamp(
                payload['iat']).astimezone(datetime_module.UTC),
            expiry=datetime_module.datetime.fromtimestamp(
                payload['exp']).astimezone(datetime_module.UTC),
            email=payload['sub'],
        )
