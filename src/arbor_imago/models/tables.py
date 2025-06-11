from sqlmodel import Field, Relationship, SQLModel, PrimaryKeyConstraint, Column
from pydantic import field_serializer, field_validator, ValidationInfo
from typing import Optional, Protocol
import datetime as datetime_module

from arbor_imago import custom_types
from arbor_imago.models.custom_field_types import timestamp
from arbor_imago.models.bases.auth_credential import AuthCredentialBase


class User(SQLModel, table=True):

    __tablename__ = 'user'  # type: ignore

    id: custom_types.User.id = Field(
        primary_key=True, index=True, unique=True, const=True)
    email: custom_types.User.email = Field(index=True, unique=True, nullable=False)
    phone_number: Optional[custom_types.User.phone_number] = Field(
        index=True, unique=True, nullable=True, default=None)
    username: Optional[custom_types.User.username] = Field(
        index=True, unique=True, nullable=True, default=None)
    hashed_password: Optional[custom_types.User.hashed_password] = Field(
        nullable=True, default=None)
    user_role_id: custom_types.User.user_role_id = Field(nullable=False)

    api_keys: list['ApiKey'] = Relationship(
        back_populates='user', cascade_delete=True)
    user_access_tokens: list['UserAccessToken'] = Relationship(
        back_populates='user', cascade_delete=True)
    galleries: list['Gallery'] = Relationship(
        back_populates='user', cascade_delete=True)
    gallery_permissions: list['GalleryPermission'] = Relationship(
        back_populates='user', cascade_delete=True)
    otp: 'OTP' = Relationship(
        back_populates='user', cascade_delete=True)


class _AuthCredentialTableBase(AuthCredentialBase):

    user_id: custom_types.User.id = Field(
        index=True, foreign_key=str(User.__tablename__) + '.id', const=True, ondelete='CASCADE')


class UserAccessToken(_AuthCredentialTableBase, table=True):

    __tablename__ = 'user_access_token'  # type: ignore

    id: custom_types.UserAccessToken.id = Field(
        primary_key=True, index=True, unique=True, const=True)

    issued: custom_types.AuthCredential.issued = Field(
        const=True, sa_column=Column(timestamp.Timestamp))
    expiry: custom_types.AuthCredential.expiry = Field(
        sa_column=Column(timestamp.Timestamp))

    user: 'User' = Relationship(back_populates='user_access_tokens')


class OTP(_AuthCredentialTableBase, table=True):

    __tablename__ = 'otp'  # type: ignore

    id: custom_types.OTP.id = Field(
        primary_key=True, index=False, unique=True, const=True)

    issued: custom_types.AuthCredential.issued = Field(
        const=True, sa_column=Column(timestamp.Timestamp))
    expiry: custom_types.AuthCredential.expiry = Field(
        sa_column=Column(timestamp.Timestamp))

    hashed_code: custom_types.OTP.hashed_code = Field()
    user: 'User' = Relationship(
        back_populates='otp')


class ApiKey(_AuthCredentialTableBase, table=True):

    __tablename__ = 'api_key'  # type: ignore

    id: custom_types.ApiKey.id = Field(
        primary_key=True, index=True, unique=True, const=True)

    issued: custom_types.AuthCredential.issued = Field(
        const=True, sa_column=Column(timestamp.Timestamp))
    expiry: custom_types.AuthCredential.expiry = Field(
        sa_column=Column(timestamp.Timestamp))

    name: custom_types.ApiKey.name = Field()
    user: 'User' = Relationship(back_populates='api_keys')
    api_key_scopes: list['ApiKeyScope'] = Relationship(
        back_populates='api_key', cascade_delete=True)


class ApiKeyScope(SQLModel, table=True):

    __tablename__ = 'api_key_scope'  # type: ignore

    api_key_id: custom_types.ApiKeyScope.api_key_id = Field(
        primary_key=True, index=True, const=True, foreign_key=str(ApiKey.__tablename__) + '.id', ondelete='CASCADE')
    scope_id: custom_types.ApiKeyScope.scope_id = Field(
        primary_key=True, index=True, const=True)

    __table_args__ = (
        PrimaryKeyConstraint('api_key_id', 'scope_id'),
    )

    api_key: 'ApiKey' = Relationship(back_populates='api_key_scopes')


class Gallery(SQLModel, table=True):

    __tablename__ = 'gallery'  # type: ignore

    id: custom_types.ApiKey.id = Field(
        primary_key=True, index=True, unique=True, const=True)
    name: custom_types.Gallery.name = Field()
    test: str = Field()
    user_id: custom_types.Gallery.user_id = Field(
        index=True, foreign_key=str(User.__tablename__) + '.id', ondelete='CASCADE')

    visibility_level: custom_types.Gallery.visibility_level = Field()
    parent_id: custom_types.Gallery.parent_id = Field(nullable=True, index=True,
                                               foreign_key='gallery.id', ondelete='CASCADE')
    description: custom_types.Gallery.description = Field(nullable=True)
    date: custom_types.Gallery.date = Field(nullable=True)

    user: 'User' = Relationship(back_populates='galleries')
    parent: Optional['Gallery'] = Relationship(
        back_populates='children', sa_relationship_kwargs={'remote_side': 'Gallery.id'})
    children: list['Gallery'] = Relationship(
        back_populates='parent', cascade_delete=True)
    gallery_permissions: list['GalleryPermission'] = Relationship(
        back_populates='gallery', cascade_delete=True)
    files: list['File'] = Relationship(
        back_populates='gallery', cascade_delete=True)
    image_versions: list['ImageVersion'] = Relationship(
        back_populates='gallery', cascade_delete=True)


class GalleryPermission(SQLModel,  table=True):

    __tablename__ = 'gallery_permission'  # type: ignore

    gallery_id: custom_types.GalleryPermission.gallery_id = Field(
        primary_key=True, index=True, foreign_key=str(Gallery.__tablename__) + '.id', ondelete='CASCADE')
    user_id: custom_types.GalleryPermission.user_id = Field(
        primary_key=True, index=True, foreign_key=str(User.__tablename__) + '.id', ondelete='CASCADE')

    __table_args__ = (
        PrimaryKeyConstraint('gallery_id', 'user_id'),
    )

    permission_level: custom_types.GalleryPermission.permission_level = Field()

    gallery: 'Gallery' = Relationship(
        back_populates='gallery_permissions')
    user: 'User' = Relationship(
        back_populates='gallery_permissions')


class File(SQLModel, table=True):

    __tablename__ = 'file'  # type: ignore

    id: custom_types.File.id = Field(
        primary_key=True, index=True, unique=True, const=True)
    stem: custom_types.File.stem = Field()
    suffix: custom_types.File.suffix = Field(nullable=True)
    gallery_id: custom_types.File.gallery_id = Field(
        index=True, foreign_key=str(Gallery.__tablename__) + '.id', ondelete='CASCADE')
    size: custom_types.File.size = Field(nullable=True)

    gallery: 'Gallery' = Relationship(back_populates='files')
    image_file_metadata: Optional['ImageFileMetadata'] = Relationship(
        back_populates='file', cascade_delete=True)


class ImageVersion(SQLModel, table=True):

    __tablename__ = 'image_version'  # type: ignore

    id: custom_types.ImageVersion.id = Field(
        primary_key=True, index=True, unique=True, const=True)
    base_name: custom_types.ImageVersion.base_name = Field(
        nullable=True, index=True)
    parent_id: custom_types.ImageVersion.parent_id = Field(
        nullable=True, index=True, foreign_key='image_version.id', ondelete='SET NULL')

    # BW, Edit1, etc. Original version is null
    version: custom_types.ImageVersion.version = Field(nullable=True)
    gallery_id: custom_types.ImageVersion.gallery_id = Field(
        index=True, foreign_key=str(Gallery.__tablename__) + '.id', ondelete='CASCADE')
    datetime: custom_types.ImageVersion.datetime = Field(nullable=True)
    description: custom_types.ImageVersion.description = Field(nullable=True)
    aspect_ratio: custom_types.ImageVersion.aspect_ratio = Field(nullable=True)
    average_color: custom_types.ImageVersion.average_color = Field(
        nullable=True)

    parent: Optional['ImageVersion'] = Relationship(
        back_populates='children', sa_relationship_kwargs={'remote_side': 'ImageVersion.id'})
    children: list['ImageVersion'] = Relationship(
        back_populates='parent')

    image_file_metadatas: list['ImageFileMetadata'] = Relationship(
        back_populates='version')
    gallery: 'Gallery' = Relationship(
        back_populates='image_versions')


class ImageFileMetadata(SQLModel, table=True):

    __tablename__ = 'image_file_metadata'  # type: ignore

    file_id: custom_types.ImageFileMetadata.file_id = Field(
        primary_key=True, index=True, unique=True, const=True, foreign_key=str(File.__tablename__) + '.id', ondelete='CASCADE')
    version_id: custom_types.ImageFileMetadata.version_id = Field(
        index=True, foreign_key=str(ImageVersion.__tablename__) + '.id', ondelete='CASCADE')
    scale: Optional[custom_types.ImageFileMetadata.scale] = Field(
        nullable=True, ge=1, le=99)

    version: 'ImageVersion' = Relationship(
        back_populates='image_file_metadatas')
    file: 'File' = Relationship(
        back_populates='image_file_metadata')
