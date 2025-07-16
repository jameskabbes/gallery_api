from arbor_imago.core import types

from pydantic import BaseModel, Field
from typing import Optional


class ImageFileMetadataExport:
    file_id: types.ImageFileMetadata.file_id
    version_id: types.ImageFileMetadata.version_id
    scale: types.ImageFileMetadata.scale | None


class ImageFileMetadataImport(BaseModel):
    pass


class ImageFileMetadataUpdate(ImageFileMetadataImport):
    file_id: types.ImageFileMetadata.file_id


class ImageFileMetadataAdminUpdate(ImageFileMetadataUpdate):
    pass


class ImageFileMetadataCreate(ImageFileMetadataImport):
    file_id: types.ImageFileMetadata.file_id
    version_id: types.ImageFileMetadata.version_id
    scale: Optional[types.ImageFileMetadata.scale] = Field(
        default=None, ge=1, le=99)


class ImageFileMetadataAdminCreate(ImageFileMetadataCreate):
    pass
