from pydantic import BaseModel
from typing import Optional
from arbor_imago.core import types


class FileExport(BaseModel):
    id: types.File.id
    stem: types.File.stem
    suffix: types.File.suffix | None
    size: types.File.size


class FileImport(BaseModel):
    pass


class FileUpdate(FileImport):
    stem: Optional[types.File.stem] = None
    gallery_id: Optional[types.File.gallery_id] = None


class FileAdminUpdate(FileUpdate):
    pass


class FileCreate(FileImport):
    stem: types.File.stem
    suffix: types.File.suffix | None
    gallery_id: types.File.gallery_id
    size: types.File.size | None


class FileAdminCreate(FileCreate):
    pass
