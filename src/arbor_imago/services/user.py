from sqlmodel import select, or_
from sqlmodel.ext.asyncio.session import AsyncSession
from pydantic import BaseModel
import pathlib

from arbor_imago import core_utils, custom_types, config
from arbor_imago.models.tables import User as UserTable
from arbor_imago.schemas import user as user_schema
from arbor_imago.services import base


class User(
        base.Service[
            UserTable,
            custom_types.User.id,
            user_schema.UserAdminCreate,
            user_schema.UserAdminUpdate,
            str
        ],
        base.SimpleIdModelService[
            UserTable,
            custom_types.User.id,
        ]
):

    _MODEL = UserTable
    DEFAULT_ROLE_ID = config.USER_ROLE_NAME_MAPPING['user']

    @classmethod
    def is_inst_public(cls, inst: UserTable) -> bool:
        return inst.username is not None

    @classmethod
    def get_inst_dir(cls, inst: UserTable, root: pathlib.Path) -> pathlib.Path:
        if cls.is_inst_public(inst):
            # since username is not None, it is a string (linter)
            return root / str(inst.username)
        else:
            return root / str(inst.id)

    @classmethod
    async def fetch_by_email(cls, session: AsyncSession, email: custom_types.User.email) -> UserTable | None:

        query = select(cls._MODEL).where(cls._MODEL.email == email)
        return (await session.exec(query)).one_or_none()

    @classmethod
    async def fetch_by_username(cls, session: AsyncSession, username: custom_types.User.username) -> UserTable | None:

        query = select(cls._MODEL).where(cls._MODEL.username == username)
        return (await session.exec(query)).one_or_none()

    @classmethod
    async def fetch_by_email_or_username(cls, session: AsyncSession, username_or_email: custom_types.User.email | custom_types.User.username) -> UserTable | None:

        query = select(cls._MODEL).where(
            or_(cls._MODEL.username == username_or_email, cls._MODEL.email == username_or_email))

        return (await session.exec(query)).one_or_none()

    @classmethod
    async def authenticate(cls, session: AsyncSession, username_or_email: custom_types.User.email | custom_types.User.username, password: custom_types.User.password) -> UserTable | None:

        user = await cls.fetch_by_email_or_username(session, username_or_email)

        if not user:
            return None
        if user.hashed_password is None:
            return None
        if not core_utils.verify_password(password, user.hashed_password):
            return None
        return user

    @classmethod
    def model_inst_from_create_model(cls, create_model):

        d = create_model.model_dump(exclude_unset=True, exclude={'password'})

        if 'password' in create_model.model_fields_set:
            if create_model.password is None:
                d['hashed_password'] = None
            else:
                d['hashed_password'] = cls.hash_password(
                    create_model.password)

        return cls._MODEL(
            id=custom_types.User.id(core_utils.generate_uuid()),
            ** d,
        )

    @classmethod
    async def _update_model_inst(cls, inst, update_model):

        for key, value in update_model.model_dump(exclude_unset=True, exclude={'password'}).items():
            setattr(inst, key, value)

        if 'password' in update_model.model_fields_set:
            if update_model.password is None:
                inst.hashed_password = None
            else:
                inst.hashed_password = cls.hash_password(
                    update_model.password)

    @classmethod
    async def is_username_available(cls, session: AsyncSession, username: custom_types.User.username) -> bool:

        query = select(cls._MODEL).where(cls._MODEL.username == username)
        return (await session.exec(query)).one_or_none() is not None

    @classmethod
    async def is_email_available(cls, session: AsyncSession, email: custom_types.User.email) -> bool:

        query = select(cls._MODEL).where(cls._MODEL.email == email)
        return (await session.exec(query)).one_or_none() is not None

    @classmethod
    async def _check_authorization_existing(cls, params):

        if not params['admin']:
            if params['model_inst'].id != params['authorized_user_id']:
                if cls.is_inst_public(params['model_inst']):
                    if params['operation'] == 'delete' or params['operation'] == 'patch':
                        raise base.UnauthorizedError(
                            'Unauthorized to {method} this user'.format(method=params['operation']))
                else:
                    raise base.NotFoundError(
                        UserTable, params['model_inst'].id)

    @classmethod
    async def _check_validation_post(cls, params):

        if 'username' in params['create_model'].model_fields_set:
            if params['create_model'].username is not None:
                await cls.is_username_available(params['session'], params['create_model'].username)
        if 'email' in params['create_model'].model_fields_set:
            if params['create_model'].email is not None:
                await cls.is_email_available(params['session'], params['create_model'].email)

    @classmethod
    async def _check_validation_patch(cls, params):
        if 'username' in params['update_model'].model_fields_set:
            if params['update_model'].username is not None:
                await cls.is_username_available(params['session'], params['update_model'].username)
        if 'email' in params['update_model'].model_fields_set:
            if params['update_model'].email is not None:
                await cls.is_email_available(params['session'], params['update_model'].email)

    @classmethod
    async def _check_authorization_new(cls, params: base.CheckAuthorizationNewParams[user_schema.UserAdminCreate]) -> None:

        if not params['admin']:
            raise base.UnauthorizedError('Unauthorized to create a new user.')

    @classmethod
    def hash_password(cls, password: custom_types.User.password) -> custom_types.User.hashed_password:
        return core_utils.hash_password(password)


'''



    @classmethod
    async def api_post_custom(cls, **kwargs):
        pass
        # root_gallery = await Gallery.api_post(Gallery.ApiPostParams(**params.model_dump(exclude=['create_model', 'cCreate_method_params', 'authorized_user_id']), authorized_user_id=new_user._id, create_model=GalleryAdminCreate(
        #     name='root', user_id=new_user._id, visibility_level=config.VISIBILITY_LEVEL_NAME_MAPPING['private']
        # )))


    @classmethod
    async def api_patch_custom(cls, test=None, **kwargs):
        # rename the root gallery if the username is updated
        # if 'username' in params.update_model.model_fields_set:
        #     root_gallery = await Gallery.get_root_gallery(params.session, self._id)
        #     await root_gallery.update(
        #         Gallery.ApiGetParams(**params.model_dump(exclude=['update_model', 'update_method_params']),
        #                             update_model=GalleryAdminUserUpdate(
        #             name=self._id if self.username == None else self.username
        #         ))
        #     )

        pass

    @classmethod
    async def api_delete_custom(cls, **kwargs):
        pass
        # await (await Gallery.get_root_gallery(params.session, self._id)).delete(session=params.session, c=params.c,
        #                                                                         authorized_user_id=params.authorized_user_id, admin=params.admin)




'''
