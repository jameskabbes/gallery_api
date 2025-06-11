from sqlmodel import select

from arbor_imago import custom_types
from arbor_imago.services import base
from arbor_imago.models.tables import GalleryPermission as GalleryPermissionTable
from arbor_imago.schemas import gallery_permission as gallery_permission_schema


class GalleryPermission(
        base.Service[
            GalleryPermissionTable,
            custom_types.GalleryPermission.id,
            gallery_permission_schema.GalleryPermissionAdminCreate,
            gallery_permission_schema.GalleryPermissionAdminUpdate,
            str
        ]):

    _MODEL = GalleryPermissionTable

    @classmethod
    def model_id(cls, inst):
        return custom_types.GalleryPermissionId(
            gallery_id=inst.gallery_id,
            user_id=inst.user_id,
        )

    @classmethod
    def _build_select_by_id(cls, id):
        return select(cls._MODEL).where(cls._MODEL.gallery_id == id.gallery_id, cls._MODEL.user_id == id.user_id)

    @classmethod
    async def _check_authorization_new(cls, params):

        if not params['admin']:
            if not params['authorized_user_id'] == params['create_model'].user_id:
                raise base.UnauthorizedError(
                    'Unauthorized to post gallery permission for another user'
                )

    @classmethod
    async def _check_authorization_existing(cls, params):

        if not params['admin']:
            if params['model_inst'].gallery.user_id != params['authorized_user_id']:
                authorized_user_gallery_permission = await cls.fetch_by_id_with_exception(
                    params['session'], params['id']
                )

                blocked_operations: set[base.CheckAuthorizationExistingOperation] = {
                    'delete', 'update'}

                if params['operation'] in blocked_operations:
                    if authorized_user_gallery_permission.user_id != params['authorized_user_id']:
                        raise base.UnauthorizedError(
                            'Unauthorized to {} gallery permission with id {}'.format(params['operation'], params['id']))

    @classmethod
    async def _check_validation_post(cls, params):

        id = custom_types.GalleryPermissionId(
            gallery_id=params['create_model'].gallery_id,
            user_id=params['create_model'].user_id
        )

        if await cls.fetch_by_id(params['session'], id):
            raise base.AlreadyExistsError(
                cls._MODEL, id
            )
