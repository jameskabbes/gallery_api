from pydantic import BaseModel
from typing import Protocol, Unpack, TypeVar, TypedDict, Generic, NotRequired, Literal, Self, ClassVar, Type, Optional
from typing import TypeVar, Type, List, Callable, ClassVar, TYPE_CHECKING, Generic, Protocol, Any, Annotated, cast
from fastapi import APIRouter, Depends, HTTPException, status, Query
from functools import wraps, lru_cache
from enum import Enum
from collections.abc import Sequence


from arbor_imago import config, custom_types, models
from arbor_imago.services import base as base_service
from arbor_imago.schemas import pagination as pagination_schema, order_by as order_by_schema
from arbor_imago.auth import utils as auth_utils


def get_pagination(max_limit: int = 100, default_limit: int = 10):
    def dependency(limit: int = Query(default_limit, ge=1, le=max_limit, description='Quantity of results'), offset: int = Query(0, ge=0, description='Index of the first result')):
        return pagination_schema.Pagination(limit=limit, offset=offset)
    return dependency


def order_by_depends(
    order_by: list[base_service.TOrderBy_co] = Query(
        [], description='Ordered series of fields to sort the results by, in the order they should be applied'),
    order_by_desc: list[base_service.TOrderBy_co] = Query(
        [], description='Unordered series of fields which should be sorted in a descending manner, must be a subset of "order_by" fields')
) -> list[order_by_schema.OrderBy[base_service.TOrderBy_co]]:

    order_by_set = set(order_by)
    order_by_desc_set = set(order_by_desc)

    if not order_by_desc_set.issubset(order_by_set):
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            detail='"order_by_desc" fields must be a subset of "order_by" fields')

    return [
        order_by_schema.OrderBy[base_service.TOrderBy_co](
            field=field, ascending=field not in order_by_desc_set)
        for field in order_by
    ]


class NotFoundError(HTTPException, base_service.NotFoundError):
    def __init__(self, model: Type[models.Model], id: custom_types.Id):
        self.status_code = status.HTTP_404_NOT_FOUND
        self.detail = base_service.NotFoundError.not_found_message(model, id)

        base_service.NotFoundError.__init__(self, model, id)
        HTTPException.__init__(
            self, status_code=self.status_code, detail=self.detail)


class RouterVerbParams(TypedDict):
    authorization: auth_utils.GetAuthReturn


class WithId(Generic[custom_types.TId], TypedDict):
    id: custom_types.TId


class GetParams(Generic[custom_types.TId], RouterVerbParams, WithId[custom_types.TId]):
    pass


class GetManyParams(Generic[models.TModel, base_service.TOrderBy_co], RouterVerbParams, base_service.ReadManyBase[models.TModel, base_service.TOrderBy_co]):
    pass


class PostParams(Generic[base_service.TCreateModel], RouterVerbParams):
    create_model: base_service.TCreateModel


class PatchParams(Generic[custom_types.TId, base_service.TUpdateModel], RouterVerbParams, WithId[custom_types.TId]):
    update_model: base_service.TUpdateModel


class DeleteParams(Generic[custom_types.TId], RouterVerbParams, WithId[custom_types.TId]):
    pass


class HasPrefix(Protocol):
    _PREFIX: ClassVar[str]


class HasAdmin(Protocol):
    _ADMIN: ClassVar[bool]


class HasTag(Protocol):
    _TAG: ClassVar[str]


class Router(HasPrefix, HasAdmin, HasTag):
    def __init__(self):

        prefix = self._PREFIX
        if self._ADMIN:
            prefix = f'/admin{prefix}'

        tags: list[str | Enum] = [self._TAG]
        if self._ADMIN:
            tags.append('Admin')

        self.router = APIRouter(prefix=prefix, tags=tags)
        self._set_routes()

    def _set_routes(self):
        pass


class NotFoundException(HTTPException):

    def __init__(self, model: Type[models.Model], id: custom_types.Id):
        self.status_code = status.HTTP_404_NOT_FOUND
        self.detail = base_service.NotFoundError.not_found_message(model, id)
        super().__init__(status_code=self.status_code, detail=self.detail)


class HasService(
        Generic[models.TModel,
                custom_types.TId,
                base_service.TCreateModel,
                base_service.TUpdateModel,
                base_service.TOrderBy_co],
        Protocol):

    _SERVICE: Type[base_service.Service[
        models.TModel,
        custom_types.TId,
        base_service.TCreateModel,
        base_service.TUpdateModel,
        base_service.TOrderBy_co,
    ]]


class ServiceRouter(Generic[
    models.TModel,
    custom_types.TId,
    base_service.TCreateModel,
    base_service.TUpdateModel,
    base_service.TOrderBy_co,
],
    Router,
    HasService[
    models.TModel,
    custom_types.TId,
    base_service.TCreateModel,
    base_service.TUpdateModel,
    base_service.TOrderBy_co

]):

    # def make_get_many_endpoint(
    #         self,
    #         response_model: TGetManyResponse,
    #         pagination_depends: Callable = get_pagination(),
    #         order_by_depends: Callable = order_by_depends,
    #         get_auth_kwargs: auth_utils.MakeGetAuthDepedencyKwargs = {}
    # ) -> Callable:

    #     async def endpoint(
    #             pagination: Annotated[pagination_schema.Pagination, Depends(pagination_depends)],
    #             order_bys: Annotated[list[order_by_schema.OrderBy[base_service.TOrderBy_co]], Depends(order_by_depends)],
    #             authorization: Annotated[auth_utils.GetAuthReturn, Depends(
    #                 auth_utils.make_get_auth_dependency(
    #                     **get_auth_kwargs))],
    #     ) -> Sequence[TGetManyResponse]:

    #         items = await self.get_many({
    #             'authorization': authorization,
    #             'pagination': pagination,
    #             'order_bys': order_bys,
    #             'query': None,
    #         })
    #         return [response_model.model_validate(model) for model in items]

    #     return endpoint

    # def make_get_endpoint(
    #     self,
    #     response_model: TGetResponse,
    #     get_auth_kwargs: auth_utils.MakeGetAuthDepedencyKwargs = {}
    # ) -> Callable:
    #     async def endpoint(
    #             authorization: Annotated[auth_utils.GetAuthReturn, Depends(
    #                 auth_utils.make_get_auth_dependency(
    #                     **get_auth_kwargs))],
    #             id: types.TId,
    #     ) -> TGetResponse:
    #         item = await self.get({
    #             'authorization': authorization,
    #             'id': id
    #         })
    #         return response_model.model_validate(item)

    #     return endpoint

    # def make_post_endpoint(
    #     self,
    #     response_model: TPostResponse,
    #     create_model_param_name: str = 'item',
    #     get_auth_kwargs: auth_utils.MakeGetAuthDependencyNoClientKwargs = {}
    # ) -> Callable:
    #     async def endpoint(
    #             authorization: Annotated[auth_utils.GetAuthReturn, Depends(
    #                 auth_utils.make_get_auth_dependency(
    #                     **get_auth_kwargs, c=self.client))],
    #             **kwargs: Any,
    #     ) -> TPostResponse:
    #         model = await self.post({
    #             'authorization': authorization,
    #             'c': self.client,
    #             'create_model': cast(
    #                 base_service.TCreateModel, kwargs.get(create_model_param_name)),
    #         })
    #         return response_model.model_validate(model)

    #     endpoint.__annotations__ = {
    #         create_model_param_name: base_service.TCreateModel,
    #         'authorization': Annotated[auth_utils.GetAuthReturn, Depends(
    #             auth_utils.make_get_auth_dependency(
    #                 **get_auth_kwargs, c=self.client))],
    #         'return': response_model
    #     }

    #     return endpoint

    # def make_patch_endpoint(
    #         self,
    #         response_model: TUpdateResponse,
    #         id_param_name: str = 'id',
    #         get_auth_kwargs: auth_utils.MakeGetAuthDependencyNoClientKwargs = {}
    # ) -> Callable:

    #     async def endpoint(
    #             item: base_service.TUpdateModel,
    #             authorization: Annotated[auth_utils.GetAuthReturn, Depends(
    #                 auth_utils.make_get_auth_dependency(
    #                     c=self.client, **get_auth_kwargs))],
    #             **kwargs
    #     ) -> TUpdateResponse:
    #         id = cast(types.TId, kwargs.get(id_param_name))

    #         model = await self.patch({
    #             'authorization': authorization,
    #             'c': self.client,
    #             'id': id,
    #             'update_model': item,
    #         })
    #         return response_model.model_validate(model)

    #     return endpoint

    @classmethod
    async def _get(cls, params: GetParams[custom_types.TId]) -> models.TModel:

        async with config.ASYNC_SESSIONMAKER() as session:
            try:
                model_inst = await cls._SERVICE.read({
                    'admin': cls._ADMIN,
                    'session': session,
                    'id': params['id'],
                    'authorized_user_id': params['authorization']._user_id,
                })
            except base_service.NotFoundError as e:
                raise NotFoundException(
                    model=cls._SERVICE._MODEL, id=params['id']
                )
            except Exception as e:
                print(f"Exception type: {type(e)}")
                print(e)
                print('raising exception')
                raise

            return model_inst

    @classmethod
    async def _get_many(cls, params: GetManyParams[models.TModel, base_service.TOrderBy_co]) -> Sequence[models.TModel]:
        async with config.ASYNC_SESSIONMAKER() as session:
            try:
                d: base_service.ReadManyParams[models.TModel, base_service.TOrderBy_co] = {
                    'admin': cls._ADMIN,
                    'session': session,
                    'authorized_user_id': params['authorization']._user_id,
                    'pagination': params['pagination']}

                if 'order_bys' in params:
                    d['order_bys'] = params['order_bys']
                if 'query' in params:
                    d['query'] = params['query']

                model_insts = await cls._SERVICE.read_many(d)
            except Exception as e:
                raise

            return model_insts

    @classmethod
    async def _post(cls, params: PostParams[base_service.TCreateModel]) -> models.TModel:
        async with config.ASYNC_SESSIONMAKER() as session:

            try:
                model_inst = await cls._SERVICE.create({
                    'admin': cls._ADMIN,
                    'session': session,
                    'authorized_user_id': params['authorization']._user_id,
                    'create_model': params['create_model'],
                })
            except base_service.AlreadyExistsError as e:
                raise
            except Exception as e:
                raise

            return model_inst

    @classmethod
    async def _patch(cls, params: PatchParams[custom_types.TId, base_service.TUpdateModel]) -> models.TModel:
        async with config.ASYNC_SESSIONMAKER() as session:
            try:
                model_inst = await cls._SERVICE.update({
                    'admin': cls._ADMIN,
                    'session': session,
                    'id': params['id'],
                    'authorized_user_id': params['authorization']._user_id,
                    'update_model': params['update_model'],
                })
            except base_service.NotFoundError as e:
                raise NotFoundException(
                    model=cls._SERVICE._MODEL, id=params['id']
                )
            except Exception as e:
                raise

            return model_inst

    @classmethod
    async def _delete(cls, params: DeleteParams[custom_types.TId]) -> None:
        async with config.ASYNC_SESSIONMAKER() as session:
            try:
                await cls._SERVICE.delete({
                    'admin': cls._ADMIN,
                    'session': session,
                    'id': params['id'],
                    'authorized_user_id': params['authorization']._user_id,
                })
            except base_service.NotFoundError as e:
                raise NotFoundException(
                    model=cls._SERVICE._MODEL, id=params['id']
                )
            except Exception as e:
                raise

    @classmethod
    @lru_cache(maxsize=None)
    def get_responses(cls):
        return {}

    @classmethod
    @lru_cache(maxsize=None)
    def post_responses(cls):
        return {}

    @classmethod
    @lru_cache(maxsize=None)
    def patch_responses(cls):
        return {}

    @classmethod
    @lru_cache(maxsize=None)
    def delete_responses(cls):
        return {}

    # def get_item(self, func: Callable) -> Callable:
    #     @wraps(func)
    #     async def wrapper(*args, db: Session = Depends(get_session), **kwargs):
    #         # Extract the ID value from kwargs based on what the endpoint defined
    #         # Get the first parameter value
    #         id_value = next(iter(kwargs.values()))
    #         id_field = func.__annotations__.get(
    #             next(iter(kwargs)), int).__name__

    #         query = select(self.model).where(
    #             getattr(self.model, id_field) == id_value)
    #         item = db.exec(query).first()
    #         if item is None:
    #             raise HTTPException(
    #                 status_code=404, detail=f"{self.model.__name__} not found")
    #         return item
    #     return wrapper

    # def setup_routes(self):
    #     # Other routes remain similar but could also use decorators if needed
    #     model_class = self.model

    #     @self.router.post("/", response_model=model_class, status_code=status.HTTP_201_CREATED)
    #     async def create_item(item: model_class, db: Session = Depends(get_session)):
    #         db_item = model_class(**item.dict())
    #         db.add(db_item)
    #         db.commit()
    #         db.refresh(db_item)
    #         return db_item

    #     # ... other routes ...
