from pydantic import BaseModel, Field
from typing import Optional
from arbor_imago import custom_types


class ImageFileMetadataExport:
    file_id: custom_types.ImageFileMetadata.file_id
    version_id: custom_types.ImageFileMetadata.version_id
    scale: custom_types.ImageFileMetadata.scale | None


class ImageFileMetadataImport(BaseModel):
    pass


class ImageFileMetadataUpdate(ImageFileMetadataImport):
    file_id: custom_types.ImageFileMetadata.file_id


class ImageFileMetadataAdminUpdate(ImageFileMetadataUpdate):
    pass


class ImageFileMetadataCreate(ImageFileMetadataImport):
    file_id: custom_types.ImageFileMetadata.file_id
    version_id: custom_types.ImageFileMetadata.version_id
    scale: Optional[custom_types.ImageFileMetadata.scale] = Field(
        default=None, ge=1, le=99)


class ImageFileMetadataAdminCreate(ImageFileMetadataCreate):
    pass
