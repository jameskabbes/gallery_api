from typing import Any
from sqlmodel import select
from pydantic import BaseModel
import datetime as datetime_module

from arbor_imago import config, core_utils, custom_types
from arbor_imago.models.tables import UserAccessToken as UserAccessTokenTable
from arbor_imago.schemas import user_access_token as user_access_token_schema, auth_credential as auth_credential_schema
from arbor_imago.services import auth_credential as auth_credential_service, base, user as user_service


class UserAccessToken(
    base.Service[
        UserAccessTokenTable,
        custom_types.UserAccessToken.id,
        user_access_token_schema.UserAccessTokenAdminCreate,
        user_access_token_schema.UserAccessTokenAdminUpdate,
        str
    ],
    base.SimpleIdModelService[
        UserAccessTokenTable,
        custom_types.UserAccessToken.id,
    ],
    auth_credential_service.JwtIO[
        UserAccessTokenTable,
        custom_types.UserAccessToken.id,
    ],
    auth_credential_service.Table[
        UserAccessTokenTable,
    ],
    auth_credential_service.JwtAndSimpleIdTable[
        UserAccessTokenTable,
        custom_types.UserAccessToken.id,
    ]
):

    auth_type = auth_credential_schema.Type.ACCESS_TOKEN
    _MODEL = UserAccessTokenTable

    @classmethod
    def model_inst_from_create_model(cls, create_model):

        return cls._MODEL(
            id=custom_types.UserAccessToken.id(core_utils.generate_uuid()),
            issued=datetime_module.datetime.now().astimezone(datetime_module.UTC),
            **create_model.model_dump(exclude_unset=True, exclude_defaults=True, exclude_none=True)
        )

    @classmethod
    async def _check_authorization_new(cls, params):

        if not params['admin']:
            if params['authorized_user_id'] != params['create_model'].user_id:
                raise base.UnauthorizedError(
                    'Unauthorized to post access token for another user'
                )

    @classmethod
    async def _check_authorization_existing(cls, params):
        if not params['admin']:
            if params['model_inst'].user_id != params['authorized_user_id']:
                raise base.NotFoundError(
                    UserAccessTokenTable, params['model_inst'].id)

    @classmethod
    async def get_scope_ids(cls, session, inst):
        return list(config.USER_ROLE_ID_SCOPE_IDS[(await user_service.User.fetch_by_id_with_exception(
            session,
            inst.user_id
        )).user_role_id
        ])
