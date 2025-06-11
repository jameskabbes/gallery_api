from pydantic import BaseModel
from typing import Optional
from arbor_imago import custom_types


class FileExport(BaseModel):
    id: custom_types.File.id
    stem: custom_types.File.stem
    suffix: custom_types.File.suffix | None
    size: custom_types.File.size


class FileImport(BaseModel):
    pass


class FileUpdate(FileImport):
    stem: Optional[custom_types.File.stem] = None
    gallery_id: Optional[custom_types.File.gallery_id] = None


class FileAdminUpdate(FileUpdate):
    pass


class FileCreate(FileImport):
    stem: custom_types.File.stem
    suffix: custom_types.File.suffix | None
    gallery_id: custom_types.File.gallery_id
    size: custom_types.File.size | None


class FileAdminCreate(FileCreate):
    pass
