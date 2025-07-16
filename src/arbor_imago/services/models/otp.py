from sqlmodel import select
from pydantic import BaseModel
import string
import secrets
import datetime as datetime_module

from arbor_imago import utils
from arbor_imago.core import config, types
from arbor_imago.models.tables import OTP as OTPTable
from arbor_imago.schemas import otp as otp_schema, auth_credential as auth_credential_schema
from arbor_imago.services.models import auth_credential as auth_credential_service, base


class OTP(
        base.Service[
            OTPTable,
            types.OTP.id,
            otp_schema.OTPAdminCreate,
            otp_schema.OTPAdminUpdate,
            str
        ],
        base.SimpleIdModelService[
            OTPTable,
            types.OTP.id,
        ],
        auth_credential_service.Table[OTPTable],
):

    auth_type = auth_credential_schema.Type.OTP
    _MODEL = OTPTable

    @classmethod
    def model_inst_from_create_model(cls, create_model):

        return cls._MODEL(
            id=types.OTP.id(utils.generate_uuid()),
            issued=datetime_module.datetime.now().astimezone(datetime_module.UTC),
            **create_model.model_dump()
        )

    @classmethod
    def generate_code(cls) -> types.OTP.code:
        characters = string.digits
        return ''.join(secrets.choice(characters) for _ in range(config.OTP_LENGTH))

    @classmethod
    def hash_code(cls, code: types.OTP.code) -> types.OTP.hashed_code:
        return utils.hash_password(code)

    @classmethod
    def verify_code(cls, code: types.OTP.code, hashed_code: types.OTP.hashed_code) -> bool:
        return utils.verify_password(code, hashed_code)

    @classmethod
    def _build_select_by_id(cls, id):
        return select(cls._MODEL).where(cls._MODEL.id == id)
