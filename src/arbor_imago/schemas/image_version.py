from arbor_imago.core import types

from pydantic import BaseModel, Field
from typing import Optional


class ImageVersionExport(BaseModel):
    id: types.ImageVersion.id
    base_name: types.ImageVersion.base_name | None
    parent_id: types.ImageVersion.parent_id | None
    version: types.ImageVersion.version | None
    datetime: types.ImageVersion.datetime | None
    description: types.ImageVersion.description | None
    aspect_ratio: types.ImageVersion.aspect_ratio | None
    average_color: types.ImageVersion.average_color | None


class ImageVersionImport(BaseModel):
    base_name: Optional[types.ImageVersion.base_name] = None
    parent_id: Optional[types.ImageVersion.parent_id] = None
    version: Optional[types.ImageVersion.version] = None
    datetime: Optional[types.ImageVersion.datetime] = None
    description: Optional[types.ImageVersion.description] = None


class ImageVersionUpdate(ImageVersionImport):
    id: types.ImageVersion.id


class ImageVersionAdminUpdate(ImageVersionUpdate):
    pass


class ImageVersionCreate(ImageVersionImport):
    pass


class ImageVersionAdminCreate(ImageVersionCreate):
    gallery_id: types.ImageVersion.gallery_id
    aspect_ratio: Optional[types.ImageVersion.aspect_ratio] = None
    average_color: Optional[types.ImageVersion.average_color] = None
