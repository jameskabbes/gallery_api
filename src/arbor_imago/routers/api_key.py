from arbor_imago import core
from arbor_imago.core import utils, config, types
from arbor_imago.models.tables import ApiKey as ApiKeyTable
from arbor_imago.services.models.api_key import ApiKey as ApiKeyService
from arbor_imago.schemas import api_key as api_key_schema, pagination as pagination_schema, api as api_schema, order_by as order_by_schema
from arbor_imago.routers import user as user_router, base
from arbor_imago.auth import utils as auth_utils

from fastapi import Depends, status, HTTPException, Query
from sqlmodel import select, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Annotated, cast, Literal


class _Base(
    base.ServiceRouter[
        ApiKeyTable,
        types.User.id,
        api_key_schema.ApiKeyAdminCreate,
        api_key_schema.ApiKeyAdminUpdate,
        types.ApiKey.order_by
    ],
):
    _PREFIX = '/api-keys'
    _TAG = 'API Key'
    _SERVICE = ApiKeyService

    @classmethod
    def order_by_depends(cls,
                         order_by: Annotated[list[types.ApiKey.order_by], base.ORDER_BY_QUERY] = [
                         ],
                         order_by_desc: Annotated[list[types.ApiKey.order_by], base.ORDER_BY_DESC_QUERY] = [
                         ]
                         ) -> list[order_by_schema.OrderBy[types.ApiKey.order_by]]:
        return base.order_by_depends_converter(order_by, order_by_desc)


PAGINATION = base.get_pagination()


class ApiKeyJWTResponse(BaseModel):
    jwt: types.JwtEncodedStr


class ApiKeyRouter(_Base):

    _ADMIN = False

    @classmethod
    async def list(
        cls,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency())],
        pagination: Annotated[pagination_schema.Pagination, Depends(PAGINATION)],
        order_bys: Annotated[list[order_by_schema.OrderBy[types.ApiKey.order_by]], Depends(
            _Base.order_by_depends)],
    ) -> list[api_key_schema.ApiKeyPrivate]:

        return [api_key_schema.ApiKeyPrivate.model_validate(api_key) for api_key in await cls._get_many({
            'authorization': authorization,
            'order_bys': order_bys,
            'pagination': pagination,
            'query': select(ApiKeyTable).where(ApiKeyTable.user_id == authorization._user_id)
        })]

    @classmethod
    async def by_id(
        cls,
        api_key_id: types.ApiKey.id,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency())]
    ) -> api_key_schema.ApiKeyPrivate:

        return api_key_schema.ApiKeyPrivate.model_validate(
            await cls._get({
                'authorization': authorization,
                'id': api_key_id,
            })
        )

    @classmethod
    async def create(
        cls,
        api_key_create: api_key_schema.ApiKeyCreate,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency())]
    ) -> api_key_schema.ApiKeyPrivate:

        return api_key_schema.ApiKeyPrivate.model_validate(
            await cls._post({
                'authorization': authorization,
                'create_model': api_key_schema.ApiKeyAdminCreate(
                    **api_key_create.model_dump(
                        exclude_unset=True),
                    user_id=cast(types.User.id, authorization._user_id)
                )
            })
        )

    @classmethod
    async def update(
        cls,
        api_key_id: types.ApiKey.id,
        api_key_update: api_key_schema.ApiKeyUpdate,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency())]
    ) -> api_key_schema.ApiKeyPrivate:

        return api_key_schema.ApiKeyPrivate.model_validate(
            await cls._patch({
                'authorization': authorization,
                'id': api_key_id,
                'update_model': api_key_schema.ApiKeyAdminUpdate(
                    **api_key_update.model_dump(exclude_unset=True))
            })
        )

    @classmethod
    async def delete(
        cls,
        api_key_id: types.ApiKey.id,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency())]
    ):

        return await cls._delete({
            'authorization': authorization,
            'id': api_key_id,
        })

    @classmethod
    async def jwt(
        cls,
        api_key_id: types.ApiKey.id,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency())]
    ) -> ApiKeyJWTResponse:

        api_key = await cls._get({
            'authorization': authorization,
            'id': api_key_id,
        })

        return ApiKeyJWTResponse(
            jwt=utils.jwt_encode(cast(dict, ApiKeyService.to_jwt_payload(api_key))))

    @classmethod
    async def check_availability(
        cls,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency())],
        api_key_available: api_key_schema.ApiKeyAvailable = Depends(),
    ) -> api_schema.IsAvailableResponse:
        async with core.ASYNC_SESSIONMAKER() as session:
            return api_schema.IsAvailableResponse(
                available=await ApiKeyService.is_available(
                    session, api_key_schema.ApiKeyAdminAvailable(
                        **api_key_available.model_dump(exclude_unset=True),
                        user_id=cast(types.User.id,
                                     authorization._user_id)
                    )
                )
            )

    @classmethod
    async def count(
        cls,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency())],
    ) -> int:
        async with core.ASYNC_SESSIONMAKER() as session:
            query = select(func.count()).select_from(ApiKeyTable).where(
                ApiKeyTable.user_id == authorization._user_id)
            return (await session.exec(query)).one()

    def _set_routes(self):

        self.router.get('/')(self.list)
        self.router.get('/{api_key_id}')(self.by_id)
        self.router.post('/')(self.create)
        self.router.patch('/{api_key_id}')(self.update)
        self.router.delete(
            '/{api_key_id}', status_code=status.HTTP_204_NO_CONTENT)(self.delete)
        self.router.get('/{api_key_id}/generate-jwt')(self.jwt)
        self.router.get('/details/available')(self.check_availability)
        self.router.get('/details/count')(self.count)


class ApiKeyAdminRouter(_Base):

    _ADMIN = True

    @classmethod
    async def list_by_user(
        cls,
        user_id: types.User.id,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency(required_scopes={'admin'}))],
        pagination: Annotated[pagination_schema.Pagination, Depends(PAGINATION)],
        order_bys: Annotated[list[order_by_schema.OrderBy[types.ApiKey.order_by]], Depends(
            _Base.order_by_depends)]

    ) -> list[api_key_schema.ApiKeyPrivate]:

        return [api_key_schema.ApiKeyPrivate.model_validate(api_key) for api_key in await cls._get_many(
            {
                'authorization': authorization,
                'order_bys': order_bys,
                'pagination': pagination,
                'query': select(ApiKeyTable).where(ApiKeyTable.user_id == authorization._user_id)})]

    @classmethod
    async def by_id(
        cls,
        api_key_id: types.ApiKey.id,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency(required_scopes={'admin'}))]
    ) -> api_key_schema.ApiKeyPrivate:

        return api_key_schema.ApiKeyPrivate.model_validate(
            await cls._get({
                'authorization': authorization,
                'id': api_key_id,
            })
        )

    @classmethod
    async def create(
        cls,
        api_key_create_admin: api_key_schema.ApiKeyAdminCreate,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency(required_scopes={'admin'}))]
    ) -> api_key_schema.ApiKeyPrivate:

        return api_key_schema.ApiKeyPrivate.model_validate(
            await cls._post({
                'authorization': authorization,
                'create_model': api_key_create_admin
            })
        )

    @classmethod
    async def update(
        cls,
        api_key_id: types.ApiKey.id,
        api_key_update_admin: api_key_schema.ApiKeyAdminUpdate,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency(required_scopes={'admin'}))]
    ) -> api_key_schema.ApiKeyPrivate:

        return api_key_schema.ApiKeyPrivate.model_validate(
            await
            cls._patch({
                'authorization': authorization,
                'id': api_key_id,
                'update_model': api_key_update_admin
            })
        )

    @classmethod
    async def delete(
        cls,
        api_key_id: types.ApiKey.id,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency(required_scopes={'admin'}))]
    ):

        return await cls._delete({
            'authorization': authorization,
            'id': api_key_id,
        })

    @classmethod
    async def check_availability(
        cls,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency(required_scopes={'admin'}))],
        api_key_available_admin: api_key_schema.ApiKeyAdminAvailable = Depends(),
    ):

        async with core.ASYNC_SESSIONMAKER() as session:
            return api_schema.IsAvailableResponse(
                available=await ApiKeyService.is_available(
                    session, api_key_available_admin
                )
            )

    def _set_routes(self):

        self.router.get(
            '/users/{user_id}/', tags=[user_router._Base._TAG])(self.list_by_user)
        self.router.get('/{api_key_id}')(self.by_id)
        self.router.post('/')(self.create)
        self.router.patch('/{api_key_id}')(self.update)
        self.router.delete(
            '/{api_key_id}', status_code=status.HTTP_204_NO_CONTENT)(self.delete)
        self.router.get('/details/available')(self.check_availability)
