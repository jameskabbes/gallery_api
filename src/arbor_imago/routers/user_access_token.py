from fastapi import Depends, status, Response
from sqlmodel import select, func
from typing import Annotated, cast, Literal

from arbor_imago import config, custom_types
from arbor_imago.models.tables import UserAccessToken as UserAccessTokenTable
from arbor_imago.services.user_access_token import UserAccessToken as UserAccessTokenService
from arbor_imago.schemas import user_access_token as user_access_token_schema, pagination as pagination_schema, api as api_schema
from arbor_imago.routers import user as user_router, base
from arbor_imago.auth import utils as auth_utils


def user_access_token_pagination(
    pagination: Annotated[pagination_schema.Pagination, Depends(
        base.get_pagination(default_limit=50, max_limit=500))]
):
    return pagination


class _Base(
    base.ServiceRouter[
        UserAccessTokenTable,
        custom_types.UserAccessToken.id,
        user_access_token_schema.UserAccessTokenAdminCreate,
        user_access_token_schema.UserAccessTokenAdminUpdate,
        str
    ]
):

    _PREFIX = '/user-access-tokens'
    _TAG = 'User Access Token'
    _SERVICE = UserAccessTokenService


class UserAccessTokenRouter(_Base):

    _ADMIN = False

    @classmethod
    async def list(
        cls,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency())],
        pagination: pagination_schema.Pagination = Depends(
            user_access_token_pagination)

    ) -> list[UserAccessTokenTable]:

        return list(await cls._get_many({
            'authorization': authorization,
            'pagination': pagination,
            'query': select(UserAccessTokenTable).where(
                UserAccessTokenTable.user_id == authorization._user_id)
        }))

    @classmethod
    async def by_id(
        cls,
        user_access_token_id: custom_types.UserAccessToken.id,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency())]
    ) -> UserAccessTokenTable:

        return await cls._get({
            'authorization': authorization,
            'id': user_access_token_id,
        })

    @classmethod
    async def delete(
        cls,
        response: Response,
        user_access_token_id: custom_types.UserAccessToken.id,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency())]
    ):

        if isinstance(authorization.auth_credential, UserAccessTokenTable):
            if authorization.auth_credential.id == user_access_token_id:
                response.headers[config.HEADER_KEYS['auth_logout']] = 'true'
                auth_utils.delete_access_token_cookie(response)

        return await cls._delete({
            'authorization': authorization,
            'id': user_access_token_id,
        })

    @classmethod
    async def count(
        cls,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency())],
    ) -> int:
        async with config.ASYNC_SESSIONMAKER() as session:
            query = select(func.count()).select_from(UserAccessTokenTable).where(
                UserAccessTokenTable.user_id == authorization._user_id)
            return (await session.exec(query)).one()

    def _set_routes(self):

        self.router.get('/', tags=[user_router._Base._TAG])(self.list)
        self.router.get('/{user_access_token_id}/')(self.by_id)
        self.router.delete('/{user_access_token_id}/',
                           status_code=status.HTTP_204_NO_CONTENT)(self.delete)
        self.router.get('/details/count/')(self.count)


class UserAccessTokenAdminRouter(_Base):

    _ADMIN = True

    @classmethod
    async def list_by_user(
        cls,
        user_id: custom_types.User.id,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency(required_scopes={'admin'}))],
        pagination: pagination_schema.Pagination = Depends(
            user_access_token_pagination)
    ) -> list[UserAccessTokenTable]:

        return list(await cls._get_many({
            'authorization': authorization,
            'pagination': pagination,
            'query': select(UserAccessTokenTable).where(
                UserAccessTokenTable.user_id == user_id)

        }))

    @classmethod
    async def by_id(
        cls,
        user_access_token_id: custom_types.UserAccessToken.id,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency(required_scopes={'admin'}))]
    ) -> UserAccessTokenTable:

        return await cls._get({
            'authorization': authorization,
            'id': user_access_token_id,
        })

    @classmethod
    async def create(
        cls,
        user_access_token_create_admin: user_access_token_schema.UserAccessTokenAdminCreate,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency(required_scopes={'admin'}))]
    ) -> UserAccessTokenTable:

        return await cls._post({
            'authorization': authorization,
            'create_model': user_access_token_create_admin,
        })

    @classmethod
    async def delete(
        cls,
        response: Response,
        user_access_token_id: custom_types.UserAccessToken.id,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency(required_scopes={'admin'}))]
    ):

        if isinstance(authorization.auth_credential, UserAccessTokenTable):
            if authorization.auth_credential.id == user_access_token_id:
                response.headers[config.HEADER_KEYS['auth_logout']] = 'true'
                auth_utils.delete_access_token_cookie(response)

        return await cls._delete({
            'authorization': authorization,
            'id': user_access_token_id,
        })

    def _set_routes(self):

        self.router.get(
            '/users/{user_id}/', tags=[user_router._Base._TAG])(self.list_by_user)
        self.router.get('/{user_access_token_id}/')(self.by_id)
        self.router.post('/')(self.create)
        self.router.delete('/{user_access_token_id}/',
                           status_code=status.HTTP_204_NO_CONTENT)(self.delete)
