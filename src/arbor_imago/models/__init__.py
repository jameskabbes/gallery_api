from sqlmodel import SQLModel
from typing import Protocol, TypeVar, Generic

from arbor_imago import custom_types
from arbor_imago.models.tables import User, UserAccessToken, OTP, ApiKey, ApiKeyScope, Gallery, GalleryPermission, File, ImageVersion, ImageFileMetadata
from arbor_imago.models.models import SignUp

ModelSimple = User | UserAccessToken | OTP | ApiKey | Gallery | File | ImageVersion
Model = ModelSimple | ApiKeyScope | GalleryPermission | ImageFileMetadata | SignUp


TModel = TypeVar('TModel', bound=Model)
TModel_co = TypeVar('TModel_co', bound=Model, covariant=True)
TModel_contra = TypeVar('TModel_contra', bound=Model, contravariant=True)

TSimpleModel = TypeVar('TSimpleModel', bound=ModelSimple)
TSimpleModel_co = TypeVar(
    'TSimpleModel_co', bound=ModelSimple, covariant=True)
TSimpleModel_contra = TypeVar(
    'TSimpleModel_contra', bound=ModelSimple, contravariant=True)


class HasSimpleId(Generic[custom_types.TSimpleId], Protocol):
    id: custom_types.TSimpleId
