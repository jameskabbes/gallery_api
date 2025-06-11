from pydantic import BaseModel
from typing import Optional

from arbor_imago import custom_types
from arbor_imago.services import base as base_service


class GalleryExport(BaseModel):
    id: custom_types.Gallery.id
    user_id: custom_types.Gallery.user_id
    name: custom_types.Gallery.name
    parent_id: custom_types.Gallery.parent_id | None
    description: custom_types.Gallery.description | None
    date: custom_types.Gallery.date | None


class GalleryPublic(GalleryExport):
    pass


class GalleryPrivate(GalleryExport):
    visibility_level: custom_types.Gallery.visibility_level


class GalleryImport(BaseModel):
    pass


class GalleryUpdate(GalleryImport):
    name: Optional[custom_types.Gallery.name] = None
    user_id: Optional[custom_types.Gallery.user_id] = None
    visibility_level: Optional[custom_types.Gallery.visibility_level] = None
    parent_id: Optional[custom_types.Gallery.parent_id] = None
    description: Optional[custom_types.Gallery.description] = None
    date: Optional[custom_types.Gallery.date] = None


class GalleryAdminUpdate(GalleryUpdate):
    pass


class _CreateBase(GalleryImport):
    name: custom_types.Gallery.name
    visibility_level: custom_types.Gallery.visibility_level
    description: Optional[custom_types.Gallery.description] = None
    date: Optional[custom_types.Gallery.date] = None


class GalleryCreate(_CreateBase):
    parent_id: custom_types.Gallery.parent_id


class GalleryAdminCreate(_CreateBase):
    user_id: custom_types.Gallery.user_id
    parent_id: Optional[custom_types.Gallery.parent_id] = None


class GalleryAvailable(BaseModel):
    name: custom_types.Gallery.name
    parent_id: Optional[custom_types.Gallery.parent_id] = None
    date: Optional[custom_types.Gallery.date] = None


class GalleryAdminAvailable(GalleryAvailable):
    user_id: custom_types.User.id
