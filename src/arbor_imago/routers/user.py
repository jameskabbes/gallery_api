from fastapi import Depends, status
from sqlmodel import select
from typing import Annotated, cast, Type
from collections.abc import Sequence

from arbor_imago import config, custom_types
from arbor_imago.auth import utils as auth_utils
from arbor_imago.routers import base
from arbor_imago.models.tables import User as UserTable
from arbor_imago.services.user import User as UserService, base as base_service
from arbor_imago.schemas import user as user_schema, pagination as pagination_schema, api as api_schema, order_by as order_by_schema


PAGINATION_DEPENDS = base.get_pagination()


class _Base(
    base.ServiceRouter[
        UserTable,
        custom_types.User.id,
        user_schema.UserAdminCreate,
        user_schema.UserAdminUpdate,
        str
    ],
):
    _PREFIX = '/users'
    _TAG = 'User'
    _SERVICE = UserService
    _ID_PARAM_NAME = 'user_id'


class UserRouter(_Base):

    _ADMIN = False

    @classmethod
    async def list(
        cls,
        pagination: Annotated[pagination_schema.Pagination, Depends(
            base.get_pagination())],
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency(raise_exceptions=False))]
    ) -> Sequence[user_schema.UserPublic]:
        return [user_schema.UserPublic.model_validate(user) for user in await cls._get_many({
            'authorization': authorization,
            'pagination': pagination,
            # these are public users
            'query': select(UserTable).where(UserTable.username != None)
        })]

    @classmethod
    async def get_me(
        cls,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency(raise_exceptions=True))]
    ) -> user_schema.UserPrivate:
        user = await cls._get({'authorization': authorization, 'id': cast(
            custom_types.User.id, authorization._user_id)})
        return user_schema.UserPrivate.model_validate(user)

    @classmethod
    async def update_me(
        cls,
        user_update: user_schema.UserUpdate,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency(raise_exceptions=True))]
    ) -> user_schema.UserPrivate:
        user = await cls._patch({
            'authorization': authorization,
            'id': cast(custom_types.User.id, authorization._user_id),
            'update_model': user_schema.UserAdminUpdate(**user_update.model_dump(exclude_unset=True)),
        })
        return user_schema.UserPrivate.model_validate(user)

    @classmethod
    async def by_id(
        cls,
        user_id: custom_types.User.id,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency(raise_exceptions=False))]
    ) -> user_schema.UserPublic:
        user = await cls._get({
            'authorization': authorization,
            'id': user_id,
        })
        return user_schema.UserPublic.model_validate(user)

    @classmethod
    async def delete_me(
        cls,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency(raise_exceptions=True))]
    ):
        await cls._delete({
            'authorization': authorization,
            'id': cast(custom_types.User.id, authorization._user_id),
        })

    @classmethod
    async def check_username_availability(cls, username: custom_types.User.username):
        async with config.ASYNC_SESSIONMAKER() as session:
            return api_schema.IsAvailableResponse(
                available=not await UserService.is_username_available(session, username))

    def _set_routes(self):

        self.router.get('/')(self.list)
        self.router.get('/me/')(self.get_me)
        self.router.get('/{user_id}/')(self.by_id)
        self.router.patch('/me/')(self.update_me)
        self.router.delete(
            '/me/', status_code=status.HTTP_204_NO_CONTENT)(self.delete_me)
        self.router.get(
            '/available/username/{username}/')(self.check_username_availability)


class UserAdminRouter(_Base):

    _ADMIN = True

    @classmethod
    async def list(
        cls,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency(required_scopes={'admin'}))],
        pagination: Annotated[pagination_schema.Pagination, Depends(
            base.get_pagination())]
    ) -> list[user_schema.UserPrivate]:

        return [
            user_schema.UserPrivate.model_validate(user) for user in await cls._get_many({
                'authorization': authorization,
                'pagination': pagination,
            })]

    @classmethod
    async def by_id(
        cls,
        user_id: custom_types.User.id,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency(required_scopes={'admin'}))]
    ) -> user_schema.UserPrivate:
        return user_schema.UserPrivate.model_validate(
            await cls._get({
                'authorization': authorization,
                'id': user_id,
            })
        )

    @classmethod
    async def create(
        cls,
        user_create_admin: user_schema.UserAdminCreate,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency(required_scopes={'admin'}))]
    ) -> user_schema.UserPrivate:

        return user_schema.UserPrivate.model_validate(await cls._post({
            'authorization': authorization,
            'create_model': user_create_admin,
        })
        )

    @classmethod
    async def update(
        cls,
        user_id: custom_types.User.id,
        user_update_admin: user_schema.UserAdminUpdate,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency(required_scopes={'admin'}))]
    ) -> user_schema.UserPrivate:

        return user_schema.UserPrivate.model_validate(await cls._patch({
            'authorization': authorization,
            'id': user_id,
            'update_model': user_update_admin,
        }))

    @classmethod
    async def delete(
        cls,
        user_id: custom_types.User.id,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency(required_scopes={'admin'}))]
    ):
        return await cls._delete({
            'authorization': authorization,
            'id': user_id,
        })

    def _set_routes(self):
        self.router.get('/')(self.list)
        self.router.get('/{user_id}/')(self.by_id)
        self.router.post('/')(self.create)
        self.router.patch('/{user_id}/')(self.update)
        self.router.delete(
            '/{user_id}/', status_code=status.HTTP_204_NO_CONTENT)(self.delete)
