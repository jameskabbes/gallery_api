from pydantic import BaseModel
from typing import Optional
from arbor_imago.core import types


class GalleryPermissionExport(BaseModel):

    gallery_id: types.GalleryPermission.gallery_id
    user_id: types.GalleryPermission.user_id
    permission_level: types.GalleryPermission.permission_level


class GalleryPermissionPublic(GalleryPermissionExport):
    pass


class Private(GalleryPermissionExport):
    pass


class GalleryPermissionImport(BaseModel):
    pass


class GalleryPermissionAdminUpdate(GalleryPermissionImport):
    permission_level: Optional[types.GalleryPermission.permission_level] = None


class GalleryPermissionAdminCreate(GalleryPermissionImport):
    gallery_id: types.GalleryPermission.gallery_id
    user_id: types.GalleryPermission.user_id
    permission_level: types.GalleryPermission.permission_level
