from sqlmodel import select

from arbor_imago import custom_types
from arbor_imago.services import base
from arbor_imago.models.tables import ImageVersion as ImageVersionTable
from arbor_imago.schemas import file as file_schema


class ImageVersion(
        base.Service[
            ImageVersionTable,
            custom_types.ImageVersion.id,
            file_schema.FileAdminCreate,
            file_schema.FileAdminUpdate,
            str
        ],

        base.SimpleIdModelService[
            ImageVersionTable,
            custom_types.ImageVersion.id,
        ],

):

    _MODEL = ImageVersionTable

    # @model_validator(mode='after')
    # def validate_model(self, info: ValidationInfo) -> None:
    #     if self.base_name is None and self.parent_id is None:
    #         raise ValueError('Unnamed versions must have a parent_id')

    # @field_validator('datetime')
    # @classmethod
    # def validate_datetime(cls, value: datetime_module.datetime, info: ValidationInfo) -> datetime_module.datetime:
    #     return validate_and_normalize_datetime(value, info)

    # @field_serializer('datetime')
    # def serialize_datetime(value: datetime_module.datetime) -> datetime_module.datetime:
    #     return value.replace(tzinfo=datetime_module.timezone.utc)

    # async def get_root_base_name(self) -> types.ImageVersion.base_name:
    #     if self.base_name is not None:
    #         return self.base_name
    #     else:
    #         if self.parent_id is not None:
    #             return (await self.parent.get_root_base_name())
    #         else:
    #             raise ValueError('Unnamed versions must have a parent_id')
