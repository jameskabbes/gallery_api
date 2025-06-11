import datetime as datetime_module
from typing import Optional, TypedDict, ClassVar, cast, Self, Literal, Protocol
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import ClassVar, TypedDict, cast, TypeVar, Generic, Type

from arbor_imago import custom_types, schemas
from arbor_imago.schemas import auth_credential as auth_credential_schema
from arbor_imago.services import base


def lifespan_to_expiry(lifespan: datetime_module.timedelta) -> custom_types.AuthCredential.expiry:
    return datetime_module.datetime.now().astimezone(datetime_module.UTC) + lifespan


TAuthCredential = TypeVar(
    'TAuthCredential', bound=schemas.AuthCredentialInstance, covariant=True)
TAuthCredentialTable = TypeVar(
    'TAuthCredentialTable', bound=schemas.AuthCredentialTableInstance)
TAuthCredentialTable_contra = TypeVar(
    'TAuthCredentialTable_contra', bound=schemas.AuthCredentialTableInstance, contravariant=True)

TAuthCredentialJwt = TypeVar(
    'TAuthCredentialJwt', bound=schemas.AuthCredentialJwtInstance)
TAuthCredentialJwt_co = TypeVar(
    'TAuthCredentialJwt_co', bound=schemas.AuthCredentialJwtInstance, covariant=True)
TAuthCredentialJwt_contra = TypeVar(
    'TAuthCredentialJwt_contra', bound=schemas.AuthCredentialJwtInstance, contravariant=True)

TAuthCredentialJwtAndTable = TypeVar(
    'TAuthCredentialJwtAndTable', bound=schemas.AuthCredentialJwtAndTableInstance)

TAuthCredentialJwtAndNotTable = TypeVar(
    'TAuthCredentialJwtAndNotTable', bound=schemas.AuthCredentialJwtAndNotTableInstance)

TSub = TypeVar('TSub')
TSub_co = TypeVar(
    'TSub_co', covariant=True)


class HasAuthType(Protocol[TAuthCredential]):
    auth_type: ClassVar[auth_credential_schema.Type]


class HasModelSub(Protocol[TAuthCredentialJwt_contra, TSub_co]):

    @classmethod
    def _model_sub(cls, inst: TAuthCredentialJwt_contra) -> TSub_co:
        ...


class HasModelInstFromJwtPayload(Protocol[TAuthCredentialJwt_co, TSub]):
    @classmethod
    def model_inst_from_jwt_payload(
            cls,
            payload: auth_credential_schema.JwtPayload[TSub]) -> TAuthCredentialJwt_co:
        ...


class Table(
    Generic[TAuthCredentialTable],
    HasAuthType[TAuthCredentialTable],
):
    @classmethod
    async def get_scope_ids(
            cls,
            session: AsyncSession,
            inst: TAuthCredentialTable,
    ) -> list[custom_types.Scope.id]:
        return []


class MissingRequiredClaimsError(Exception):
    def __init__(self, claims: set[str]) -> None:
        super().__init__(f"Missing required claims: {', '.join(claims)}")
        self.claims = claims


class JwtIO(
    Generic[TAuthCredentialJwt, TSub],
    HasAuthType[TAuthCredentialJwt],
    HasModelSub[TAuthCredentialJwt, TSub],
):
    _CLAIMS: ClassVar[set[str]] = {'type', 'exp', 'iat', 'sub'}

    @classmethod
    def validate_jwt_claims(cls, payload: auth_credential_schema.JwtPayload[TSub]):

        missing_claims = {
            claim for claim in cls._CLAIMS if claim not in payload}
        if missing_claims:
            raise MissingRequiredClaimsError(missing_claims)

    @classmethod
    def to_jwt_payload(cls, inst: TAuthCredentialJwt) -> auth_credential_schema.JwtPayload[TSub]:

        return {
            'type': cls.auth_type.value,
            'exp': inst.expiry.timestamp(),
            'iat': inst.issued.timestamp(),
            'sub': cls._model_sub(inst),
        }


class JwtAndSimpleIdTable(
        Generic[TAuthCredentialJwtAndTable, custom_types.TSimpleId],
        HasModelSub[TAuthCredentialJwtAndTable, custom_types.TSimpleId],
        base.HasModelId[TAuthCredentialJwtAndTable, custom_types.TSimpleId]):

    @classmethod
    def _model_sub(cls, inst: TAuthCredentialJwtAndTable) -> custom_types.TSimpleId:
        return cls.model_id(inst)


class JwtNotTable(
    Generic[TAuthCredentialJwtAndNotTable, TSub, base.TCreateModel],
    HasModelInstFromJwtPayload[TAuthCredentialJwtAndNotTable, TSub],
    base.HasModelInstFromCreateModel[TAuthCredentialJwtAndNotTable,
                                     base.TCreateModel],
    base.HasModel[TAuthCredentialJwtAndNotTable],
    HasModelSub[TAuthCredentialJwtAndNotTable, TSub],
):
    pass
