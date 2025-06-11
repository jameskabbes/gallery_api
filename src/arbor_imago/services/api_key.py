from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
import datetime as datetime_module
from typing import cast

from arbor_imago import custom_types, core_utils
from arbor_imago.models.tables import ApiKey as ApiKeyTable
from arbor_imago.schemas import api_key as api_key_schema, auth_credential as auth_credential_schema
from arbor_imago.services import auth_credential as auth_credential_service, base


class ApiKey(
        base.Service[
            ApiKeyTable,
            custom_types.ApiKey.id,
            api_key_schema.ApiKeyAdminCreate,
            api_key_schema.ApiKeyAdminUpdate,
            custom_types.ApiKey.order_by
        ],
        base.SimpleIdModelService[ApiKeyTable, custom_types.ApiKey.id],
        auth_credential_service.JwtIO[ApiKeyTable, custom_types.ApiKey.id],
        auth_credential_service.Table[ApiKeyTable],
        auth_credential_service.JwtAndSimpleIdTable[ApiKeyTable,
                                                    custom_types.ApiKey.id],
):

    auth_type = auth_credential_schema.Type.API_KEY
    _MODEL = ApiKeyTable

    @classmethod
    def model_inst_from_create_model(cls, create_model):

        return cls._MODEL(
            id=custom_types.ApiKey.id(core_utils.generate_uuid()),
            issued=datetime_module.datetime.now().astimezone(datetime_module.UTC),
            **create_model.model_dump()
        )

    @classmethod
    async def get_scope_ids(cls, session, inst):
        return [api_key_scope.scope_id for api_key_scope in inst.api_key_scopes]

    @classmethod
    async def is_available(cls, session: AsyncSession, api_key_available_admin: api_key_schema.ApiKeyAdminAvailable) -> bool:
        return (await session.exec(select(cls).where(
            api_key_schema.ApiKeyAdminAvailable.name == api_key_available_admin.name,
            api_key_schema.ApiKeyAdminAvailable.user_id == api_key_available_admin.user_id
        ))).one_or_none() is not None

    @classmethod
    async def _check_authorization_new(cls, params):
        if not params['admin']:
            if params['authorized_user_id'] != params['create_model'].user_id:
                raise base.UnauthorizedError(
                    'Unauthorized to post API Key for another user'
                )

    @classmethod
    async def _check_authorization_existing(cls, params):

        if not params['admin']:
            if params['model_inst'].user_id != params['authorized_user_id']:
                raise base.NotFoundError(
                    ApiKeyTable, params['id']
                )

    @classmethod
    async def _check_validation_post(cls, params):
        if not await cls.is_available(params['session'], api_key_schema.ApiKeyAdminAvailable(
            **params['create_model'].model_dump(exclude_unset=True), user_id=cast(custom_types.User.id, params['authorized_user_id']),
        )):
            raise base.NotAvailableError(
                'Cannot create API Key {} for user {}, not available'.format(
                    str(params['create_model']), params['authorized_user_id']
                )
            )

    @classmethod
    async def _check_validation_patch(cls, params):
        if 'name' in params['update_model'].model_fields_set:
            if not await cls.is_available(params['session'], api_key_schema.ApiKeyAdminAvailable(
                    name=cast(custom_types.ApiKey.name, params['update_model'].name), user_id=cast(custom_types.User.id, params['authorized_user_id']))):
                raise base.NotAvailableError(
                    'Cannot update API Key {} for user {}, not available'.format(
                        str(params['update_model']
                            ), params['authorized_user_id']
                    )
                )
