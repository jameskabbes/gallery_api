from arbor_imago.core import types

from pydantic import BaseModel
from typing import Optional


class GalleryExport(BaseModel):
    id: types.Gallery.id
    user_id: types.Gallery.user_id
    name: types.Gallery.name
    parent_id: types.Gallery.parent_id | None
    description: types.Gallery.description | None
    date: types.Gallery.date | None


class GalleryPublic(GalleryExport):
    pass


class GalleryPrivate(GalleryExport):
    visibility_level: types.Gallery.visibility_level


class GalleryImport(BaseModel):
    pass


class GalleryUpdate(GalleryImport):
    name: Optional[types.Gallery.name] = None
    user_id: Optional[types.Gallery.user_id] = None
    visibility_level: Optional[types.Gallery.visibility_level] = None
    parent_id: Optional[types.Gallery.parent_id] = None
    description: Optional[types.Gallery.description] = None
    date: Optional[types.Gallery.date] = None


class GalleryAdminUpdate(GalleryUpdate):
    pass


class _CreateBase(GalleryImport):
    name: types.Gallery.name
    visibility_level: types.Gallery.visibility_level
    description: Optional[types.Gallery.description] = None
    date: Optional[types.Gallery.date] = None


class GalleryCreate(_CreateBase):
    parent_id: types.Gallery.parent_id


class GalleryAdminCreate(_CreateBase):
    user_id: types.Gallery.user_id
    parent_id: Optional[types.Gallery.parent_id] = None


class GalleryAvailable(BaseModel):
    name: types.Gallery.name
    parent_id: Optional[types.Gallery.parent_id] = None
    date: Optional[types.Gallery.date] = None


class GalleryAdminAvailable(GalleryAvailable):
    user_id: types.User.id
