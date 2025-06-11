from sqlmodel import Field, Relationship, select, SQLModel
from typing import TYPE_CHECKING, TypedDict, Optional, ClassVar, Annotated, Type

from arbor_imago import custom_types
from arbor_imago.models.tables import ApiKeyScope as ApiKeyScopeTable, ApiKey as ApiKeyTable
from arbor_imago.services import api_key as api_key_service, base
from arbor_imago.schemas import api_key_scope as api_key_scope_schema


class ApiKeyScope(base.Service[
    ApiKeyScopeTable,
    custom_types.ApiKeyScope.id,
    api_key_scope_schema.ApiKeyScopeAdminCreate,
    api_key_scope_schema.ApiKeyScopeAdminUpdate,
    str
]):

    _MODEL = ApiKeyScopeTable

    @classmethod
    def model_id(cls, inst: ApiKeyScopeTable):
        return custom_types.ApiKeyScopeId(
            api_key_id=inst.api_key_id,
            scope_id=inst.scope_id,
        )

    @classmethod
    def _build_select_by_id(cls, id):
        return select(cls._MODEL).where(cls._MODEL.api_key_id == id.api_key_id, cls._MODEL.scope_id == id.scope_id)

    @classmethod
    async def _check_authorization_new(cls, params):

        api_key = await api_key_service.ApiKey.fetch_by_id_with_exception(
            params['session'],
            params['create_model'].api_key_id
        )

        if not params['admin']:
            # if user is not admin, check if the api key belongs to the user
            if api_key.user_id != params['authorized_user_id']:
                raise base.NotFoundError(
                    ApiKeyTable, params['create_model'].api_key_id)

    @classmethod
    async def _check_authorization_existing(cls, params):

        if not params['admin']:
            # if user is not admin, check if the api key belongs to the user
            if params['model_inst'].api_key.user_id != params['authorized_user_id']:
                raise base.NotFoundError(
                    ApiKeyTable, params['model_inst'].api_key_id)

    @classmethod
    async def _check_validation_post(cls, params):

        id = custom_types.ApiKeyScopeId(
            api_key_id=params['create_model'].api_key_id,
            scope_id=params['create_model'].scope_id
        )

        if await cls.fetch_by_id(params['session'], id):
            raise base.AlreadyExistsError(
                cls._MODEL, id)
