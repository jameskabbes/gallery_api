from arbor_imago import utils
from arbor_imago.core import types
from arbor_imago.models.tables import ApiKey as ApiKeyTable, ApiKeyScope as ApiKeyScopeTable
from arbor_imago.schemas import api_key as api_key_schema, auth_credential as auth_credential_schema
from arbor_imago.services.models import auth_credential as auth_credential_service, base

from sqlmodel import select, col
from sqlmodel.ext.asyncio.session import AsyncSession
import datetime as datetime_module
from typing import cast
from collections.abc import Sequence


class ApiKey(
        base.Service[
            ApiKeyTable,
            types.ApiKey.id,
            api_key_schema.ApiKeyAdminCreate,
            api_key_schema.ApiKeyAdminUpdate,
            types.ApiKey.order_by
        ],
        base.SimpleIdModelService[ApiKeyTable, types.ApiKey.id],
        auth_credential_service.JwtIO[ApiKeyTable, types.ApiKey.id],
        auth_credential_service.Table[ApiKeyTable],
        auth_credential_service.JwtAndSimpleIdTable[ApiKeyTable,
                                                    types.ApiKey.id],
):

    auth_type = auth_credential_schema.Type.API_KEY
    _MODEL = ApiKeyTable

    @classmethod
    def model_inst_from_create_model(cls, create_model):

        return cls._MODEL(
            id=types.ApiKey.id(utils.generate_uuid()),
            issued=datetime_module.datetime.now().astimezone(datetime_module.UTC),
            **create_model.model_dump()
        )

    @classmethod
    async def get_scope_ids_by_api_key_ids(cls, session: AsyncSession, api_key_ids: Sequence[types.ApiKey.id]) -> dict[types.ApiKey.id, list[types.Scope.id]]:
        api_key_scopes = (await session.exec(select(ApiKeyScopeTable).where(col(ApiKeyScopeTable.api_key_id).in_(api_key_ids)))).all()

        d: dict[types.ApiKey.id, list[types.Scope.id]] = {}
        for api_key_scope in api_key_scopes:
            if api_key_scope.api_key_id not in d:
                d[api_key_scope.api_key_id] = []
            d[api_key_scope.api_key_id].append(api_key_scope.scope_id)
        return d

    @classmethod
    async def get_scope_ids(cls, session, inst):
        return [api_key_scope.scope_id for api_key_scope in inst.api_key_scopes]

    @classmethod
    async def is_available(cls, session: AsyncSession, api_key_available_admin: api_key_schema.ApiKeyAdminAvailable) -> bool:
        return (await session.exec(select(cls._MODEL).where(
            cls._MODEL.name == api_key_available_admin.name,
            cls._MODEL.user_id == cast(types.User.id, api_key_available_admin.user_id
                                       )))).one_or_none() is None

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
            **params['create_model'].model_dump(exclude_unset=True),
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
                    name=cast(types.ApiKey.name, params['update_model'].name), user_id=cast(types.User.id, params['authorized_user_id']))):
                raise base.NotAvailableError(
                    'Cannot update API Key {} for user {}, not available'.format(
                        str(params['update_model']
                            ), params['authorized_user_id']
                    )
                )
