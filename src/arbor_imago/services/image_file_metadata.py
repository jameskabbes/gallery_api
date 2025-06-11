from sqlmodel import select
from typing import ClassVar
import re

from arbor_imago import custom_types
from arbor_imago.services import base
from arbor_imago.models.tables import ImageFileMetadata as ImageFileMetadataTable
from arbor_imago.schemas import image_file_metadata as image_file_metadata_schema


class ImageFileMetadata(
        base.Service[
            ImageFileMetadataTable,
            custom_types.ImageFileMetadata.file_id,
            image_file_metadata_schema.ImageFileMetadataAdminCreate,
            image_file_metadata_schema.ImageFileMetadataAdminUpdate,
            str
        ]):

    _MODEL = ImageFileMetadataTable

    SUFFIXES: ClassVar[set[str]] = {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}

    @classmethod
    def model_id(cls, inst):
        return inst.file_id

    @classmethod
    def _build_select_by_id(cls, id):
        return select(cls._MODEL).where(cls._MODEL.file_id == id)

    @classmethod
    def parse_file_stem(cls, file_stem: str) -> tuple[custom_types.ImageVersion.base_name, custom_types.ImageVersion.version | None, custom_types.ImageFileMetadata.scale | None]:

        scale = None
        if match := re.search(r'_(\d{2})$', file_stem):
            scale = int(match.group(1))
            file_stem = file_stem[:match.start()]

        version = None
        if match := re.search(r'_(.+)$', file_stem):
            version = match.group(1)
            file_stem = file_stem[:match.start()]

        return file_stem, version, scale
