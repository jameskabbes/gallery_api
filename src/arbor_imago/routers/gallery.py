from fastapi import Depends, status, UploadFile, HTTPException
from sqlmodel import select
from typing import Annotated, cast
import shutil

from arbor_imago import config, custom_types
from arbor_imago.auth import utils as auth_utils
from arbor_imago.routers import base, user as user_router
from arbor_imago.models.tables import Gallery as GalleryTable, GalleryPermission as GalleryPermissionTable
from arbor_imago.services.gallery import Gallery as GalleryService
from arbor_imago.services.gallery_permission import GalleryPermission as GalleryPermissionService
from arbor_imago.schemas import gallery as gallery_schema, pagination as pagination_schema, api as api_schema, gallery_permission as gallery_permission_schema


class _Base(
    base.ServiceRouter[
        GalleryTable,
        custom_types.User.id,
        gallery_schema.GalleryAdminCreate,
        gallery_schema.GalleryAdminUpdate,
        str
    ],
):
    _PREFIX = '/galleries'
    _TAG = 'Gallery'
    _SERVICE = GalleryService


galleries_pagination = base.get_pagination()


# class UploadFileToGalleryResponse(BaseModel):
#     message: str


class GalleryRouter(_Base):
    _ADMIN = False

    @classmethod
    async def list(
        cls,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency())],
        pagination: pagination_schema.Pagination = Depends(
            galleries_pagination)

    ) -> list[gallery_schema.GalleryPrivate]:
        return [gallery_schema.GalleryPrivate.model_validate(gallery) for gallery in
                await cls._get_many({
                    'authorization': authorization,
                    'pagination': pagination,
                    'query': select(GalleryTable).where(GalleryTable.user_id == authorization._user_id)
                })
                ]

    @classmethod
    async def by_id(
        cls,
        gallery_id: custom_types.Gallery.id,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency(raise_exceptions=False))]
    ) -> gallery_schema.GalleryPublic:

        return gallery_schema.GalleryPublic.model_validate(await cls._get({
            'authorization': authorization,
            'id': gallery_id,
        }))

    @classmethod
    async def create(
        cls,
        gallery_create: gallery_schema.GalleryCreate,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency())]
    ) -> gallery_schema.GalleryPrivate:

        return gallery_schema.GalleryPrivate.model_validate(await cls._post({
            'authorization': authorization,
            'create_model': gallery_schema.GalleryAdminCreate(
                **gallery_create.model_dump(exclude_unset=True), user_id=cast(custom_types.User.id, authorization._user_id)),
        }))

    @classmethod
    async def update(
        cls,
        gallery_id: custom_types.Gallery.id,
        gallery_update: gallery_schema.GalleryUpdate,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency())]
    ) -> gallery_schema.GalleryPrivate:

        return gallery_schema.GalleryPrivate.model_validate(await cls._patch({
            'authorization': authorization,
            'id': gallery_id,
            'update_model': gallery_schema.GalleryAdminUpdate(
                **gallery_update.model_dump(exclude_unset=True)),
        }))

    @classmethod
    async def delete(
        cls,
        gallery_id: custom_types.Gallery.id,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency())]
    ):

        return await cls._delete({
            'authorization': authorization,
            'id': gallery_id,
        })

    @classmethod
    async def check_availability(
        cls,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency())],
        gallery_available: gallery_schema.GalleryAvailable = Depends(),
    ):

        async with config.ASYNC_SESSIONMAKER() as session:

            return api_schema.IsAvailableResponse(
                available=await GalleryService.is_available(
                    session=session,
                    gallery_available_admin=gallery_schema.GalleryAdminAvailable(
                        **gallery_available.model_dump(exclude_unset=True),
                        user_id=cast(custom_types.User.id,
                                     authorization._user_id)
                    )

                )
            )

    # @classmethod
    # async def get_galleries_by_user(
    #     cls,
    #     user_id: models.UserTypes.id,
    #     authorization: Annotated[auth_utils.GetAuthReturn, Depends(
    #         get_auth_from_token(raise_exceptions=False))],
    #     pagination: PaginationParams = Depends(get_pagination_params),
    # ) -> list[models.GalleryPublic]:

    #     async with c.AsyncSession() as session:
    #         galleries = session.exec(select(models.Gallery).where(
    #             models.Gallery.user_id == user_id).offset(pagination.offset).limit(pagination.limit)).all()
    #         return [models.GalleryPublic.model_validate(gallery) for gallery in galleries]

    @classmethod
    async def upload_file(
        cls,
        gallery_id: custom_types.Gallery.id,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency())],
        file: UploadFile
    ):

        async with config.ASYNC_SESSIONMAKER() as session:

            gallery = await GalleryService.fetch_by_id(session, gallery_id)
            if not gallery:
                raise base.NotFoundError(GalleryTable, gallery_id)

            if gallery.user.id != authorization._user_id:
                gallery_permission = await GalleryPermissionService.fetch_by_id(
                    session, custom_types.GalleryPermission.id(
                        gallery_id, cast(custom_types.User.id, authorization._user_id))
                )

                if gallery_permission is None:
                    if gallery.visibility_level == config.VISIBILITY_LEVEL_NAME_MAPPING['private']:
                        raise base.NotFoundError(GalleryTable, gallery_id)

                    if gallery.visibility_level == config.VISIBILITY_LEVEL_NAME_MAPPING['public']:
                        raise HTTPException(
                            status.HTTP_403_FORBIDDEN, detail='User lacks edit permission for this gallery')
                else:
                    if gallery_permission.permission_level < config.PERMISSION_LEVEL_NAME_MAPPING['editor']:
                        raise HTTPException(
                            status.HTTP_403_FORBIDDEN, detail='User does not have permission to add files to this gallery')

            file_path = (await GalleryService.get_dir(session, gallery, config.GALLERIES_DIR)).joinpath(file.filename or 'test.jpg')
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

    @classmethod
    async def sync(
        cls,
        gallery_id: custom_types.Gallery.id,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency())]
    ) -> api_schema.DetailOnlyResponse:
        async with config.ASYNC_SESSIONMAKER() as session:

            gallery = await cls._get({
                'authorization': authorization,
                'id': gallery_id,
            })
            dir = await GalleryService.get_dir(session, gallery, config.GALLERIES_DIR)

            # await gallery.sync_with_local(session, c, dir)
            return api_schema.DetailOnlyResponse(detail='Synced gallery')

    def _set_routes(self):

        self.router.get('/', tags=[user_router._Base._TAG])(self.list)
        self.router.get('/{gallery_id}/')(self.by_id)
        self.router.post('/')(self.create)
        self.router.patch('/{gallery_id}/')(self.update)
        self.router.delete(
            '/{gallery_id}/', status_code=status.HTTP_204_NO_CONTENT)(self.delete)
        self.router.get('/details/available/')(self.check_availability)

        # need to decide how to deal with gallery permissions and how to return
        # @self.router.get('/users/{user_id}/', tags=[models.User._ROUTER_TAG])(self.get_galleries_by_user)

        self.router.post("/{gallery_id}/upload/",
                         status_code=status.HTTP_201_CREATED)(self.upload_file)
        self.router.post('/{gallery_id}/sync/')(self.sync)


class GalleryAdminRouter(_Base):
    _ADMIN = True

    @classmethod
    async def by_id(
        cls,
        gallery_id: custom_types.Gallery.id,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency(required_scopes={'admin'}))]
    ) -> gallery_schema.GalleryPrivate:
        return gallery_schema.GalleryPrivate.model_validate(
            await cls._get({
                'authorization': authorization,
                'id': gallery_id,
            })
        )

    @classmethod
    async def create(
        cls,
        gallery_create_admin: gallery_schema.GalleryAdminCreate,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency(required_scopes={'admin'}))]
    ) -> gallery_schema.GalleryPrivate:
        return gallery_schema.GalleryPrivate.model_validate(
            await cls._post({
                'authorization': authorization,
                'create_model': gallery_create_admin
            })
        )

    @classmethod
    async def update(
        cls,
        gallery_id: custom_types.Gallery.id,
        gallery_update_admin: gallery_schema.GalleryAdminUpdate,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency(required_scopes={'admin'}))]
    ) -> gallery_schema.GalleryPrivate:

        return gallery_schema.GalleryPrivate.model_validate(
            await cls._patch({
                'authorization': authorization,
                'id': gallery_id,
                'update_model': gallery_update_admin
            })
        )

    @classmethod
    async def delete(
        cls,
        gallery_id: custom_types.Gallery.id,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency(required_scopes={'admin'}))]
    ):
        return await cls._delete({
            'authorization': authorization,
            'id': gallery_id,
        })

    @classmethod
    async def check_availability(
        cls,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency(required_scopes={'admin'}))],
        gallery_available_admin: gallery_schema.GalleryAdminAvailable = Depends(),
    ):

        async with config.ASYNC_SESSIONMAKER() as session:
            return api_schema.IsAvailableResponse(
                available=await GalleryService.is_available(
                    session=session,
                    gallery_available_admin=gallery_schema.GalleryAdminAvailable(
                        **gallery_available_admin.model_dump(exclude_unset=True),
                        user_id=cast(custom_types.User.id,
                                     authorization._user_id)
                    )
                )
            )

    @classmethod
    async def list_by_user(
        cls,
        user_id: custom_types.User.id,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency(required_scopes={'admin'}))],
        pagination: pagination_schema.Pagination = Depends(
            galleries_pagination)
    ) -> list[gallery_schema.GalleryPrivate]:

        return [gallery_schema.GalleryPrivate.model_validate(gallery) for gallery in
                await cls._get_many({
                    'authorization': authorization,
                    'query': select(GalleryTable).where(
                        GalleryTable.user_id == user_id),
                    'pagination': pagination
                })]

    def _set_routes(self):

        self.router.get('/{gallery_id}/')(self.by_id)
        self.router.post('/')(self.create)
        self.router.patch('/{gallery_id}/')(self.update)
        self.router.delete(
            '/{gallery_id}/', status_code=status.HTTP_204_NO_CONTENT)(self.delete)
        self.router.get('/details/available/')(self.check_availability)
        self.router.get('/users/{user_id}')(self.list_by_user)
