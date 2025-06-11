from pydantic import BaseModel, Field
from typing import Optional
from arbor_imago import custom_types


class ImageVersionExport(BaseModel):
    id: custom_types.ImageVersion.id
    base_name: custom_types.ImageVersion.base_name | None
    parent_id: custom_types.ImageVersion.parent_id | None
    version: custom_types.ImageVersion.version | None
    datetime: custom_types.ImageVersion.datetime | None
    description: custom_types.ImageVersion.description | None
    aspect_ratio: custom_types.ImageVersion.aspect_ratio | None
    average_color: custom_types.ImageVersion.average_color | None


class ImageVersionImport(BaseModel):
    base_name: Optional[custom_types.ImageVersion.base_name] = None
    parent_id: Optional[custom_types.ImageVersion.parent_id] = None
    version: Optional[custom_types.ImageVersion.version] = None
    datetime: Optional[custom_types.ImageVersion.datetime] = None
    description: Optional[custom_types.ImageVersion.description] = None


class ImageVersionUpdate(ImageVersionImport):
    id: custom_types.ImageVersion.id


class ImageVersionAdminUpdate(ImageVersionUpdate):
    pass


class ImageVersionCreate(ImageVersionImport):
    pass


class ImageVersionAdminCreate(ImageVersionCreate):
    gallery_id: custom_types.ImageVersion.gallery_id
    aspect_ratio: Optional[custom_types.ImageVersion.aspect_ratio] = None
    average_color: Optional[custom_types.ImageVersion.average_color] = None
