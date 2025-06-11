from pydantic import BaseModel
from typing import Optional
from arbor_imago import custom_types


class GalleryPermissionExport(BaseModel):

    gallery_id: custom_types.GalleryPermission.gallery_id
    user_id: custom_types.GalleryPermission.user_id
    permission_level: custom_types.GalleryPermission.permission_level


class GalleryPermissionPublic(GalleryPermissionExport):
    pass


class Private(GalleryPermissionExport):
    pass


class GalleryPermissionImport(BaseModel):
    pass


class GalleryPermissionAdminUpdate(GalleryPermissionImport):
    permission_level: Optional[custom_types.GalleryPermission.permission_level] = None


class GalleryPermissionAdminCreate(GalleryPermissionImport):
    gallery_id: custom_types.GalleryPermission.gallery_id
    user_id: custom_types.GalleryPermission.user_id
    permission_level: custom_types.GalleryPermission.permission_level
