from fastapi import Depends, status, Query, HTTPException
from sqlmodel import select, func
from pydantic import BaseModel
from collections.abc import Sequence
from typing import Annotated, cast, Optional

from arbor_imago import custom_types, config
from arbor_imago.routers import user as user_router, api_key as api_key_router, gallery as gallery_router, base, user_access_token as user_access_token_router
from arbor_imago.schemas import api_key as api_key_schema, pagination as pagination_schema, api as api_schema, order_by as order_by_schema, user as user_schema, user_access_token as user_access_token_schema, gallery as gallery_schema, api_key_scope as api_key_scope_schema
from arbor_imago.models.tables import ApiKey as ApiKeyTable, UserAccessToken as UserAccessTokenTable, Gallery as GalleryTable
from arbor_imago.services import api_key as api_key_service, user_access_token as user_access_token_service, gallery as gallery_service
from arbor_imago.auth import utils as auth_utils


class ProfilePageResponse(auth_utils.GetUserSessionInfoNestedReturn):
    user: user_schema.UserPrivate | None = None


class HomePageResponse(auth_utils.GetUserSessionInfoNestedReturn):
    pass


class SettingsPageResponse(auth_utils.GetUserSessionInfoNestedReturn):
    pass


class SettingsApiKeysPageResponse(auth_utils.GetUserSessionInfoNestedReturn):
    api_key_count: int
    api_keys: list[api_key_schema.ApiKeyPrivate]
    api_key_scopes: dict[custom_types.ApiKey.id,
                         list[custom_types.Scope.id]]


class SettingsUserAccessTokensPageResponse(auth_utils.GetUserSessionInfoNestedReturn):
    user_access_token_count: int
    user_access_tokens: list[UserAccessTokenTable]


class StylesPageResponse(auth_utils.GetUserSessionInfoNestedReturn):
    pass


class GalleryPageResponse(auth_utils.GetUserSessionInfoNestedReturn):
    gallery: gallery_schema.GalleryPublic
    parents: list[gallery_schema.GalleryPublic]
    children: list[gallery_schema.GalleryPublic]


class _Base(base.Router):
    _PREFIX = '/pages'
    _TAG = 'Page'


class PagesRouter(_Base):
    _ADMIN = False

    @classmethod
    async def profile(
        cls,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency())]
    ) -> ProfilePageResponse:
        return ProfilePageResponse(
            **auth_utils.get_user_session_info(authorization).model_dump()
        )

    @classmethod
    async def home(
        cls,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency(raise_exceptions=False))]
    ) -> HomePageResponse:
        return HomePageResponse(
            **auth_utils.get_user_session_info(authorization).model_dump()
        )

    @classmethod
    async def settings(
        cls,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency(raise_exceptions=False))]
    ) -> SettingsPageResponse:
        return SettingsPageResponse(
            **auth_utils.get_user_session_info(authorization).model_dump()
        )

    @classmethod
    async def settings_api_keys(
        cls,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(auth_utils.make_get_auth_dependency())],
        pagination: pagination_schema.Pagination = Depends(
            api_key_router.PAGINATION),
        order_by: list[order_by_schema.OrderBy[custom_types.ApiKey.order_by]] = Depends(
            api_key_router._Base.order_by_depends
        )
    ) -> SettingsApiKeysPageResponse:
        api_keys = await api_key_router.ApiKeyRouter.list(authorization, pagination, order_by)

        async with config.ASYNC_SESSIONMAKER() as session:
            api_key_scopes = await api_key_service.ApiKey.get_scope_ids_by_api_key_ids(
                session=session,
                api_key_ids=[api_key.id for api_key in api_keys]
            )

        return SettingsApiKeysPageResponse(
            **auth_utils.get_user_session_info(authorization).model_dump(),
            api_key_count=await api_key_router.ApiKeyRouter.count(authorization),
            api_keys=api_keys,
            api_key_scopes=api_key_scopes
        )

    @classmethod
    async def settings_user_access_tokens(
        cls,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(auth_utils.make_get_auth_dependency())],
        pagination: pagination_schema.Pagination = Depends(
            user_access_token_router.user_access_token_pagination)
    ) -> SettingsUserAccessTokensPageResponse:
        return SettingsUserAccessTokensPageResponse(
            **auth_utils.get_user_session_info(authorization).model_dump(),
            user_access_token_count=await user_access_token_router.UserAccessTokenRouter.count(authorization),
            user_access_tokens=await user_access_token_router.UserAccessTokenRouter.list(
                authorization, pagination)
        )

    @classmethod
    async def styles(
        cls,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency(raise_exceptions=False))]
    ) -> StylesPageResponse:
        return StylesPageResponse(
            **auth_utils.get_user_session_info(authorization).model_dump()
        )

    @classmethod
    async def gallery(
        cls,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency())],
        gallery_id: custom_types.Gallery.id | None = Query(None),
    ) -> GalleryPageResponse:

        # if gallery_id is None, get the root gallery for the user, then find that gallery
        if gallery_id is None:
            async with config.ASYNC_SESSIONMAKER() as session:
                root_gallery = await gallery_service.Gallery.get_root_gallery(session, cast(custom_types.User.id, authorization._user_id))
                if root_gallery is None:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail='Root gallery could not be found. This is a server error.'
                    )
                gallery_id = gallery_service.Gallery.model_id(root_gallery)

        # refetch the root gallery to utilize the Router handlings of authorization and exceptions
        gallery = gallery_router.GalleryRouter.by_id(
            gallery_id=gallery_id,
            authorization=authorization,
        )

        return GalleryPageResponse(
            **auth_utils.get_user_session_info(authorization).model_dump(),
            gallery=gallery_schema.GalleryPublic.model_validate(gallery),
            parents=[],
            children=[]
            # parents=[gallery_schema.GalleryPublic.model_validate(
            #     parent) for parent in await GalleryService.get_parents(session, gallery)],
            # children=[gallery_schema.GalleryPublic.model_validate(
            #     child) for child in gallery.children]
        )

    def _set_routes(self):
        self.router.get(
            '/profile', tags=[user_router._Base._TAG])(self.profile)
        self.router.get('/home')(self.home)
        self.router.get('/settings')(self.settings)
        self.router.get('/settings/api-keys',
                        tags=[api_key_router._Base._TAG])(self.settings_api_keys)
        self.router.get('/settings/user-access-tokens',
                        tags=[user_access_token_router._Base._TAG])(self.settings_user_access_tokens)
        self.router.get('/styles')(self.styles)
        self.router.get('/galleries',
                        tags=[gallery_router._Base._TAG])(self.gallery)


class PagesAdminRouter(_Base):
    _ADMIN = True

    def _set_routes(self):
        pass
