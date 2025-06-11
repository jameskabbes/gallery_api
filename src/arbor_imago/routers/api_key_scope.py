from fastapi import Depends, status
from typing import Annotated

from arbor_imago import custom_types
from arbor_imago.routers import base
from arbor_imago.models.tables import ApiKeyScope as ApiKeyScopeTable
from arbor_imago.services.api_key_scope import ApiKeyScope as ApiKeyScopeService
from arbor_imago.schemas import api_key_scope as api_key_scope_schema
from arbor_imago.auth import utils as auth_utils


class _Base(
    base.ServiceRouter[
        ApiKeyScopeTable,
        custom_types.ApiKeyScope.id,
        api_key_scope_schema.ApiKeyScopeAdminCreate,
        api_key_scope_schema.ApiKeyScopeAdminUpdate,
        str
    ],
):
    _PREFIX = '/api-key-scopes'
    _TAG = 'API Key Scope'
    _SERVICE = ApiKeyScopeService


class ApiKeyScopeRouter(_Base):

    _ADMIN = False

    @classmethod
    async def add_scope_to_api_key(
        cls,
        api_key_id: custom_types.ApiKey.id,
        scope_id: custom_types.Scope.id,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency())]
    ) -> None:
        api_key_scope = await cls._post({
            'authorization': authorization,
            'create_model': api_key_scope_schema.ApiKeyScopeAdminCreate(
                api_key_id=api_key_id, scope_id=scope_id),
        })

    @classmethod
    async def remove_scope_from_api_key(
        cls,
        api_key_id: custom_types.ApiKey.id,
        scope_id: custom_types.Scope.id,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency())]
    ) -> None:
        await cls._delete({
            'authorization': authorization,
            'id': custom_types.ApiKeyScope.id(
                api_key_id=api_key_id, scope_id=scope_id),
        })

    def _set_routes(self):

        self.router.post(
            '/api-keys/{api_key_id}/scopes/{scope_id}/')(self.add_scope_to_api_key)
        self.router.delete('/api-keys/{api_key_id}/scopes/{scope_id}/',
                           status_code=status.HTTP_204_NO_CONTENT)(self.remove_scope_from_api_key)


class ApiKeyScopeAdminRouter(_Base):

    _ADMIN = True

    @classmethod
    async def add_scope_to_api_key(
        cls,
        api_key_id: custom_types.ApiKey.id,
        scope_id: custom_types.Scope.id,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency(required_scopes={'admin'}))]
    ) -> None:
        api_key_scope = await cls._post({
            'authorization': authorization,
            'create_model': api_key_scope_schema.ApiKeyScopeAdminCreate(
                api_key_id=api_key_id, scope_id=scope_id),
        })

    @classmethod
    async def remove_scope_from_api_key(
        cls,
        api_key_id: custom_types.ApiKey.id,
        scope_id: custom_types.Scope.id,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency(required_scopes={'admin'}))]
    ) -> None:
        await cls._delete({
            'authorization': authorization,
            'id': custom_types.ApiKeyScope.id(
                api_key_id=api_key_id, scope_id=scope_id),
        })

    def _set_routes(self):

        self.router.post(
            '/api-keys/{api_key_id}/scopes/{scope_id}/')(self.add_scope_to_api_key)
        self.router.delete('/api-keys/{api_key_id}/scopes/{scope_id}/',
                           status_code=status.HTTP_204_NO_CONTENT)(self.remove_scope_from_api_key)
