from sqlmodel import select
from pydantic import BaseModel
import string
import secrets
import datetime as datetime_module

from arbor_imago import config, core_utils, custom_types
from arbor_imago.models.tables import OTP as OTPTable
from arbor_imago.schemas import otp as otp_schema, auth_credential as auth_credential_schema
from arbor_imago.services import auth_credential as auth_credential_service, base


class OTP(
        base.Service[
            OTPTable,
            custom_types.OTP.id,
            otp_schema.OTPAdminCreate,
            otp_schema.OTPAdminUpdate,
            str
        ],
        base.SimpleIdModelService[
            OTPTable,
            custom_types.OTP.id,
        ],
        auth_credential_service.Table[OTPTable],
):

    auth_type = auth_credential_schema.Type.OTP
    _MODEL = OTPTable

    @classmethod
    def model_inst_from_create_model(cls, create_model):

        return cls._MODEL(
            id=custom_types.OTP.id(core_utils.generate_uuid()),
            issued=datetime_module.datetime.now().astimezone(datetime_module.UTC),
            **create_model.model_dump()
        )

    @classmethod
    def generate_code(cls) -> custom_types.OTP.code:
        characters = string.digits
        return ''.join(secrets.choice(characters) for _ in range(config.OTP_LENGTH))

    @classmethod
    def hash_code(cls, code: custom_types.OTP.code) -> custom_types.OTP.hashed_code:
        return core_utils.hash_password(code)

    @classmethod
    def verify_code(cls, code: custom_types.OTP.code, hashed_code: custom_types.OTP.hashed_code) -> bool:
        return core_utils.verify_password(code, hashed_code)

    @classmethod
    def _build_select_by_id(cls, id):
        return select(cls._MODEL).where(cls._MODEL.id == id)
