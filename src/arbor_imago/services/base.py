from sqlmodel import SQLModel, select
from sqlalchemy.orm import InstrumentedAttribute
from sqlmodel.sql.expression import SelectOfScalar
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Any, Protocol, Unpack, TypeVar, TypedDict, Generic, NotRequired, Literal, Self, ClassVar, Type, Optional
from pydantic import BaseModel
from collections.abc import Sequence

from arbor_imago import custom_types, models
from arbor_imago.schemas.pagination import Pagination
from arbor_imago.schemas.order_by import OrderBy

TCreateModel = TypeVar('TCreateModel', bound=BaseModel)
TCreateModel_contra = TypeVar(
    'TCreateModel_contra', bound=BaseModel, contravariant=True)
TCreateModel_co = TypeVar('TCreateModel_co', bound=BaseModel, covariant=True)

TUpdateModel = TypeVar('TUpdateModel', bound=BaseModel)
TUpdateModel_contra = TypeVar(
    'TUpdateModel_contra', bound=BaseModel, contravariant=True)
TUpdateModel_co = TypeVar('TUpdateModel_co', bound=BaseModel, covariant=True)

TOrderBy_co = TypeVar('TOrderBy_co', bound=str, covariant=True)


class CRUDParamsBase(TypedDict):
    session: AsyncSession
    authorized_user_id: Optional[custom_types.User.id]
    admin: bool


class WithId(Generic[custom_types.TId], TypedDict):
    id: custom_types.TId


class WithModelInst(Generic[models.TModel_contra], TypedDict):
    model_inst: models.TModel_contra


class CreateParams(Generic[TCreateModel_contra], CRUDParamsBase):
    create_model: TCreateModel_contra


class ReadParams(Generic[custom_types.TId], CRUDParamsBase, WithId[custom_types.TId]):
    pass


class ReadManyBase(Generic[models.TModel, TOrderBy_co], TypedDict):
    pagination: Pagination
    order_bys: NotRequired[list[OrderBy[TOrderBy_co]]]
    query: NotRequired[SelectOfScalar[models.TModel] | None]


class ReadManyParams(Generic[models.TModel, TOrderBy_co], CRUDParamsBase, ReadManyBase[models.TModel, TOrderBy_co]):
    pass


class UpdateParams(Generic[custom_types.TId, TUpdateModel_contra], CRUDParamsBase, WithId[custom_types.TId]):
    update_model: TUpdateModel_contra


class DeleteParams(Generic[custom_types.TId], CRUDParamsBase, WithId[custom_types.TId]):
    pass


CheckAuthorizationExistingOperation = Literal['read', 'update', 'delete']


class CheckAuthorizationExistingParams(Generic[models.TModel_contra, custom_types.TId], CRUDParamsBase, WithId[custom_types.TId], WithModelInst[models.TModel_contra]):
    operation: CheckAuthorizationExistingOperation


class CheckAuthorizationNewParams(Generic[TCreateModel_contra], CreateParams[TCreateModel_contra]):
    pass


class CheckAuthorizationReadManyParams(Generic[models.TModel, TOrderBy_co], ReadManyParams[models.TModel, TOrderBy_co]):
    pass


class CheckValidationDeleteParams(Generic[custom_types.TId], DeleteParams[custom_types.TId]):
    pass


class CheckValidationPatchParams(Generic[models.TModel, custom_types.TId, TUpdateModel_contra], UpdateParams[custom_types.TId, TUpdateModel_contra], WithModelInst[models.TModel]):
    pass


class CheckValidationPostParams(Generic[TCreateModel_contra], CreateParams[TCreateModel_contra]):
    pass


class HasModel(Protocol[models.TModel_co]):
    _MODEL: Type[models.TModel_co]


class HasModelInstFromCreateModel(Protocol[models.TModel_co, TCreateModel_contra]):
    @classmethod
    def model_inst_from_create_model(cls, create_model: TCreateModel_contra) -> models.TModel_co:
        ...


class HasModelId(Protocol[models.TModel_contra, custom_types.TId_co]):
    @classmethod
    def model_id(cls, inst: models.TModel_contra) -> custom_types.TId_co:
        ...


class HasBuildSelectById(Protocol[models.TModel, custom_types.TId_contra]):
    @classmethod
    def _build_select_by_id(cls, id: custom_types.TId_contra) -> SelectOfScalar[models.TModel]:
        ...


class SimpleIdModelService(
    Generic[models.TSimpleModel, custom_types.TSimpleId],
    HasModel[models.TSimpleModel],
    HasModelId[models.TSimpleModel, custom_types.TSimpleId],
    HasBuildSelectById[models.TSimpleModel, custom_types.TSimpleId],
):

    _MODEL: Type[models.TSimpleModel]

    @classmethod
    def model_id(cls, inst: models.TSimpleModel) -> custom_types.TSimpleId:
        return inst.id  # type: ignore

    @classmethod
    def _build_select_by_id(cls, id: custom_types.TSimpleId) -> SelectOfScalar[models.TSimpleModel]:
        return select(cls._MODEL).where(cls._MODEL.id == id)


class ServiceError(Exception):
    error_message: str

    def __init__(self, error_message: str):
        self.error_message = error_message
        super().__init__(error_message)


class NotFoundError(ValueError, ServiceError):

    def __init__(self, model: Type[models.Model], id: custom_types.Id):
        self.error_message = NotFoundError.not_found_message(model, id)
        super().__init__(self.error_message)

    @staticmethod
    def not_found_message(model: Type[models.Model], id: custom_types.Id) -> str:
        return model.__name__ + ' with id `' + str(id) + '` not found'


class AlreadyExistsError(ServiceError):
    def __init__(self, model: Type[models.Model], id: custom_types.Id):
        self.error_message = model.__name__ + \
            ' with id `' + str(id) + '` already exists'
        super().__init__(self.error_message)


class NotAvailableError(ServiceError):
    pass


class UnauthorizedError(ServiceError):
    pass


class Service(
    Generic[
        models.TModel,
        custom_types.TId,
        TCreateModel,
        TUpdateModel,
        TOrderBy_co
    ],
    HasModel[models.TModel],
    HasModelInstFromCreateModel[models.TModel, TCreateModel],
    HasModelId[models.TModel, custom_types.TId],
    HasBuildSelectById[models.TModel, custom_types.TId],

):

    @classmethod
    async def fetch_one(cls, session: AsyncSession, query: SelectOfScalar[models.TModel]) -> models.TModel | None:
        return (await session.exec(query)).one_or_none()

    @classmethod
    async def fetch_many(cls, session: AsyncSession, pagination: Pagination, order_bys: list[OrderBy[TOrderBy_co]] = [], query: SelectOfScalar[models.TModel] | None = None) -> Sequence[models.TModel]:

        if query is None:
            query = select(cls._MODEL)

        query = cls.build_order_by(query, order_bys)
        query = query.offset(pagination.offset).limit(pagination.limit)

        return (await session.exec(query)).all()

    @classmethod
    async def fetch_by_id(cls, session: AsyncSession, id: custom_types.TId) -> models.TModel | None:
        query = cls._build_select_by_id(id)
        return await cls.fetch_one(session, query)

    @classmethod
    async def fetch_by_id_with_exception(cls, session: AsyncSession, id: custom_types.TId) -> models.TModel:
        inst = await cls.fetch_by_id(session, id)
        if inst is None:
            raise NotFoundError(cls._MODEL, id)
        return inst

    @classmethod
    def build_order_by(cls, query: SelectOfScalar[models.TModel], order_by: list[OrderBy[TOrderBy_co]]):
        for order in order_by:
            field: InstrumentedAttribute = getattr(cls, order.field)
            if order.ascending:
                query = query.order_by(field.asc())
            else:
                query = query.order_by(field.desc())

        return query

    @classmethod
    async def _check_authorization_existing(cls, params: CheckAuthorizationExistingParams[models.TModel, custom_types.TId]) -> None:
        """Check if the user is authorized to access the instance"""
        pass

    @classmethod
    async def _check_authorization_new(cls, params: CheckAuthorizationNewParams[TCreateModel]) -> None:
        """Check if the user is authorized to create a new instance"""
        pass

    @classmethod
    async def _check_authorization_read_many(cls, params: CheckAuthorizationReadManyParams[models.TModel, TOrderBy_co]) -> None:
        """Check if the user is authorized to read many instances"""
        pass

    @classmethod
    async def _check_validation_delete(cls, params: CheckValidationDeleteParams[custom_types.TId]) -> None:
        """Check if the user is authorized to delete the instance"""
        pass

    @classmethod
    async def _check_validation_patch(cls, params: CheckValidationPatchParams[models.TModel, custom_types.TId, TUpdateModel]) -> None:
        """Check if the user is authorized to update the instance"""
        pass

    @classmethod
    async def _check_validation_post(cls, params: CheckValidationPostParams[TCreateModel]) -> None:
        """Check if the user is authorized to create a new instance"""
        pass

    @classmethod
    async def read(cls, params: ReadParams[custom_types.TId]) -> models.TModel:
        """Used in conjunction with API endpoints, raises exceptions while trying to get an instance of the model by ID"""

        model_inst = await cls.fetch_by_id_with_exception(params['session'], params['id'])

        await cls._check_authorization_existing(
            {**params, 'model_inst': model_inst, 'operation': 'read'})

        return model_inst

    @classmethod
    async def read_many(cls, params: ReadManyParams[models.TModel, TOrderBy_co]) -> Sequence[models.TModel]:
        """Used in conjunction with API endpoints, raises exceptions while trying to get a list of instances of the model"""

        await cls._check_authorization_read_many(params)

        kwargs = {}
        if 'order_bys' in params:
            kwargs['order_bys'] = params['order_bys']
        if 'query' in params:
            kwargs['query'] = params['query']

        return await cls.fetch_many(params['session'], params['pagination'], **kwargs)

    @classmethod
    async def create(cls, params: CreateParams[TCreateModel]) -> models.TModel:
        """Used in conjunction with API endpoints, raises exceptions while trying to create a new instance of the model"""

        await cls._check_authorization_new(params)
        await cls._check_validation_post(params)

        model_inst = cls.model_inst_from_create_model(params['create_model'])

        params['session'].add(model_inst)
        await params['session'].commit()
        await params['session'].refresh(model_inst)
        return model_inst

    @classmethod
    def model_inst_from_create_model(cls, create_model: TCreateModel) -> models.TModel:
        return cls._MODEL(**create_model.model_dump())

    @classmethod
    async def update(cls, params: UpdateParams[custom_types.TId, TUpdateModel]) -> models.TModel:
        """Used in conjunction with API endpoints, raises exceptions while trying to update an instance of the model by ID"""

        # when changing this, be sure to update the services/gallery.py file as well

        model_inst = await cls.fetch_by_id_with_exception(params['session'], params['id'])

        await cls._check_authorization_existing({
            'session': params['session'],
            'model_inst': model_inst,
            'operation': 'read',
            'id': params['id'],
            'admin': params['admin'],
            'authorized_user_id': params['authorized_user_id']
        })
        await cls._check_validation_patch({**params, 'model_inst': model_inst})
        await cls._update_model_inst(model_inst, params['update_model'])

        await params['session'].commit()
        await params['session'].refresh(model_inst)
        return model_inst

    @classmethod
    async def _update_model_inst(cls, inst: models.TModel, update_model: TUpdateModel) -> None:
        """Update an instance of the model from the update model (TUpdateModel)"""

        inst.sqlmodel_update(update_model.model_dump(exclude_unset=True))

    @classmethod
    async def delete(cls, params: DeleteParams[custom_types.TId]) -> None:
        """Used in conjunction with API endpoints, raises exceptions while trying to delete an instance of the model by ID"""

        model_inst = await cls.fetch_by_id_with_exception(params['session'], params['id'])

        await cls._check_authorization_existing({
            'session': params['session'],
            'operation': 'delete',
            'id': params['id'],
            'model_inst': model_inst,
            'admin': params['admin'],
            'authorized_user_id': params['authorized_user_id']
        })
        await cls._check_validation_delete(params)
        await params['session'].delete(model_inst)
        await params['session'].commit()


'''


def generate(self) -> TId:
    if len(self.fields) == 1:
        return str(uuid.uuid4())
    return tuple(str(uuid.uuid4()) for _ in self.fields)



@classmethod
def export_plural_to_dict(cls, items: collections.abc.Iterable[typing.Self]) -> dict[TId, typing.Self]:
    return {item._id: item for item in items}





        
    # @classmethod
    # def _build_conditions(cls, filters: dict[str, typing.Any]):

    #     conditions = []
    #     for key in filters:
    #         value = filters[key]
    #         field: InstrumentedAttribute = getattr(cls, key)

    #         if isinstance(value, list):
    #             conditions.append(field.in_(value))
    #         else:
    #             conditions.append(field == value)

    #     return and_(*conditions)



'''
