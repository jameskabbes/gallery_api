from sqlmodel import select

from arbor_imago.core import types
from arbor_imago.models.tables import File as FileTable
from arbor_imago.schemas import file as file_schema
from arbor_imago.services.models import base


class File(
        base.Service[
            FileTable,
            types.File.id,
            file_schema.FileAdminCreate,
            file_schema.FileAdminUpdate,
            str
        ],
        base.SimpleIdModelService[
            FileTable,
            types.File.id,
        ],
):
    _MODEL = FileTable

    @classmethod
    def model_name(cls, inst: FileTable) -> str:
        return inst.stem + ('' if inst.suffix is None else inst.suffix)
