from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
import re
import datetime as datetime_module
import pathlib
import shutil

from arbor_imago import config, custom_types, utils, core_utils
from arbor_imago.models.tables import Gallery as GalleryTable
from arbor_imago.services.gallery_permission import GalleryPermission as GalleryPermissionService, base
from arbor_imago.schemas import gallery as gallery_schema


class Gallery(
        base.Service[
            GalleryTable,
            custom_types.Gallery.id,
            gallery_schema.GalleryAdminCreate,
            gallery_schema.GalleryAdminUpdate,
            str
        ],
        base.SimpleIdModelService[
            GalleryTable,
            custom_types.Gallery.id,
        ],
):

    _MODEL = GalleryTable

    @classmethod
    def model_folder_name(cls, inst: GalleryTable) -> custom_types.Gallery.folder_name:

        if inst.parent_id == None and inst.name == 'root':
            return inst.user_id
        elif inst.date == None:
            return inst.name
        else:
            return inst.date.isoformat() + ' ' + inst.name

    @classmethod
    def get_date_and_name_from_folder_name(cls, folder_name: custom_types.Gallery.folder_name) -> custom_types.GalleryDateAndName:

        match = re.match(r'^(\d{4}-\d{2}-\d{2}) (.+)$', folder_name)
        if match:
            date_str, name = match.groups()
            date = datetime_module.date.fromisoformat(date_str)
            return custom_types.GalleryDateAndName(
                date=date,
                name=name
            )
        else:
            return custom_types.GalleryDateAndName(
                date=None,
                name=folder_name
            )

    @classmethod
    async def is_available(cls, session: AsyncSession, gallery_available_admin: gallery_schema.GalleryAdminAvailable) -> bool:

        # raise an exception if the parent gallery does not exist
        if gallery_available_admin.parent_id is not None:
            await cls.fetch_by_id_with_exception(session, gallery_available_admin.parent_id)

        if (await session.exec(select(cls).where(
            cls._MODEL.name == gallery_available_admin.name,
            cls._MODEL.user_id == gallery_available_admin.user_id,
            cls._MODEL.parent_id == gallery_available_admin.parent_id,
            cls._MODEL.date == gallery_available_admin.date,
        ))).one_or_none():
            return False
        return True

    @classmethod
    async def _check_authorization_new(cls, params):
        if not params['admin']:
            if params['authorized_user_id'] != params['create_model'].user_id:
                raise base.UnauthorizedError(
                    'Unauthorized to post gallery for another user'
                )

    @classmethod
    async def _check_authorization_existing(cls, params):

        if not params['admin']:
            if params['authorized_user_id'] is not None and (params['authorized_user_id'] != params['model_inst'].user_id):

                if params['operation'] == 'delete':
                    raise base.UnauthorizedError(
                        'Unauthorized to {operation} this gallery'.format(operation=params['operation']))

                gallery_permission = await GalleryPermissionService.fetch_by_id(
                    params['session'], custom_types.GalleryPermissionId(
                        gallery_id=params['id'],
                        user_id=params['authorized_user_id']
                    )
                )

                # if the gallery is private and user has no access, pretend it doesn't exist
                if gallery_permission is None and params['model_inst'].visibility_level == config.VISIBILITY_LEVEL_NAME_MAPPING['private']:
                    raise base.NotFoundError(
                        GalleryTable, params['id'])

                # either public or user has access

                elif params['operation'] == 'get':
                    if gallery_permission is None or (gallery_permission.permission_level < config.PERMISSION_LEVEL_NAME_MAPPING['viewer']):
                        raise base.UnauthorizedError(
                            'Unauthorized to {operation} this gallery'.format(operation=params['operation']))

                elif params['operation'] == 'patch':
                    if gallery_permission is None or (gallery_permission.permission_level < config.PERMISSION_LEVEL_NAME_MAPPING['editor']):
                        raise base.UnauthorizedError(
                            'Unauthorized to {operation} this gallery'.format(operation=params['operation']))

    @classmethod
    async def _check_validation_post(cls, params):
        await cls.is_available(params['session'], gallery_schema.GalleryAdminAvailable(**params['create_model'].model_dump(include=set(gallery_schema.GalleryAdminAvailable.model_fields.keys()), exclude_unset=True)))

    @classmethod
    async def _check_validation_patch(cls, params):
        # take self, overwrite it with the update_model, and see if the combined model is available
        await cls.is_available(params['session'], gallery_schema.GalleryAdminAvailable(**{
            **params['model_inst'].model_dump(include=set(gallery_schema.GalleryAdminAvailable.model_fields.keys())), **params['update_model'].model_dump(include=set(gallery_schema.GalleryAdminAvailable.model_fields.keys()), exclude_unset=True)
        }))

    @classmethod
    async def get_dir(cls, session: AsyncSession, gallery: GalleryTable,  root: pathlib.Path) -> pathlib.Path:

        if gallery.parent_id is None:
            return root / cls.model_folder_name(gallery)
        else:
            a = await cls.get_dir(session, await cls.fetch_by_id_with_exception(session, gallery.parent_id), root)
            return a / cls.model_folder_name(gallery)

    @classmethod
    async def get_parents(cls, session: AsyncSession, gallery: GalleryTable) -> list[GalleryTable]:

        if gallery.parent_id is None:
            return []

        else:
            parents = (await cls.get_parents(session, await cls.fetch_by_id_with_exception(session, gallery.parent_id)))
            parents.append(gallery)
            return parents

    @classmethod
    async def get_root_gallery(cls, session: AsyncSession, user_id: custom_types.Gallery.user_id) -> GalleryTable | None:
        return (await session.exec(select(cls._MODEL).where(cls._MODEL.user_id == user_id).where(cls._MODEL.parent_id == None))).one_or_none()

    @classmethod
    def model_inst_from_create_model(cls, create_model):
        return cls._MODEL(
            id=core_utils.generate_uuid(),
            ** create_model.model_dump(exclude_unset=True, exclude_defaults=True, exclude_none=True)
        )

    # @classmethod
    # async def update(cls, params, custom_params={}):
    #     """Used in conjunction with API endpoints, raises exceptions while trying to update an instance of the model by ID"""

    #     model_inst = await cls.fetch_by_id_with_exception(params['session'], params['id'])

    #     await cls._check_authorization_existing({
    #         'session': params['session'],
    #         'c': params['c'],
    #         'model_inst': model_inst,
    #         'operation': 'update',
    #         'id': params['id'],
    #         'admin': params['admin'],
    #         'authorized_user_id': params['authorized_user_id']
    #     })
    #     await cls._check_validation_patch({**params, 'model_inst': model_inst})

    #     original_dir = await cls.get_dir(params['session'], model_inst, params['c'].galleries_dir)

    #     await cls._update_model_inst(model_inst, params['update_model'])

    #     # await cls._after_update({
    #     #     **params, 'model_inst': model_inst}, custom_params)

    #     # by default, rename the folder if the name, date, or parent_id has changed
    #     if custom_params.get('rename_folder', True):
    #         if 'name' in params['update_model'].model_fields_set or 'date' in params['update_model'].model_fields_set or 'parent_id' in params['update_model'].model_fields_set:
    #             new_dir = (await cls.get_dir(params['session'], model_inst, params['c'].galleries_dir)).parent / cls.model_folder_name(model_inst)
    #             original_dir.rename(new_dir)

    #     await params['session'].commit()
    #     await params['session'].refresh(model_inst)
    #     return model_inst

    # @classmethod
    # async def _after_create(cls, params, custom_params={}):

    #     if custom_params.get('mkdir', False):
    #         (await cls.get_dir(params['session'], params['model_inst'], params['c'].galleries_dir)).mkdir()

    #     return await super()._after_create(params, custom_params)

    # @classmethod
    # async def _after_delete(cls, params, custom_params={}):

    #     if custom_params.get('rmtree', False):
    #         shutil.rmtree((await cls.get_dir(params['session'], params['model_inst'], params['c'].galleries_dir)))

    # async def sync_with_local(self, session: Session, c: client.Client, dir: pathlib.Path) -> None:

    #     if not dir.exists():
    #         raise HTTPException(status.HTTP_404_NOT_FOUND,
    #                             detail='Directory not found')

    #     if self.folder_name != dir.name:
    #         raise HTTPException(status.HTTP_400_BAD_REQUEST,
    #                             detail='Folder name does not match gallery name')

    #     files: list[pathlib.Path] = []
    #     dirs: list[pathlib.Path] = []
    #     for item in dir.iterdir():
    #         if item.is_dir():
    #             dirs.append(item)
    #         if item.is_file():
    #             files.append(item)

    #     # Add new galleries, remove old ones
    #     local_galleries_by_folder_name = {
    #         item.name: item for item in dirs}
    #     db_galleries_by_folder_name = {
    #         gallery.folder_name: gallery for gallery in self.children}

    #     local_galleries_folder_names = set(
    #         local_galleries_by_folder_name.keys())
    #     db_galleries_folder_names = set(db_galleries_by_folder_name.keys())

    #     toadd = local_galleries_folder_names - db_galleries_folder_names
    #     to_remove = db_galleries_folder_names - local_galleries_folder_names

    #     for folder_name in to_remove:
    #         gallery = db_galleries_by_folder_name[folder_name]
    #         await Gallery.api_delete(session=session, c=c, id=gallery._id, authorized_user_id=self.user_id, admin=False, delete_method_kwargs=GalleryAdminApiDeleteParams(rmtree=False))

    #     for folder_name in toadd:
    #         date, name = self.get_date_and_name_from_folder_name(
    #             folder_name)
    #         new_gallery = await Gallery.api_post(
    #             session=session, c=c, authorized_user_id=self.user_id, admin=False, create_model=GalleryAdminCreate(name=name, user_id=self.user_id, visibility_level=self.visibility_level, parent_id=self.id, date=date),
    #             create_method_kwargs=GalleryAdminCreateParams(mkdir=False))

    #     # add new files, remove old ones
    #     local_file_by_names = {
    #         file.name: file for file in files}
    #     db_files_by_names = {
    #         file.name: file for file in self.files}

    #     local_file_names = set(local_file_by_names.keys())
    #     db_file_names = set(db_files_by_names.keys())

    #     toadd = local_file_names - db_file_names
    #     to_remove = db_file_names - local_file_names

    #     for file_name in to_remove:
    #         file = db_files_by_names[file_name]

    #         # if this is the last image tied to that version, delete the version too
    #         if file.suffix in ImageFileMetadataConfig._SUFFIXES:
    #             image_version = await ImageVersion.read(session, file.image_file_metadata.version_id)
    #             if len(image_version.image_file_metadatas) == 1:
    #                 await ImageVersion.api_delete(session=session, c=c, id=image_version.id, authorized_user_id=self.user_id, admin=False)

    #         await File.api_delete(session=session, c=c, id=file.id, authorized_user_id=self.user_id, admin=False, unlink=False)

    #     image_files: list[File] = []

    #     for file_name in toadd:
    #         stem = local_file_by_names[file_name].stem
    #         suffix = ''.join(suffixes) if (
    #             suffixes := local_file_by_names[file_name].suffixes) else None

    #         new_file = await File.api_post(
    #             session=session, c=c, authorized_user_id=self.user_id, admin=False, create_model=FileAdminCreate(stem=stem, suffix=suffix, gallery_id=self.id, size=local_file_by_names[file_name].stat().st_size))

    #         # rename the file, just to make sure the suffix is lowercase
    #         local_file_by_names[file_name].rename(
    #             local_file_by_names[file_name].with_name(new_file.name))

    #         if suffix in ImageFileMetadataConfig._SUFFIXES:
    #             image_files.append(new_file)

    #     # loop through files twice, adding the original images first
    #     for original_images in [True, False]:
    #         for image_file in image_files:

    #             base_name, version, scale = ImageFileMetadata.parse_file_stem(
    #                 image_file.stem)

    #             if original_images == (version == None):

    #                 parent_id = None
    #                 if version is not None:
    #                     image_version_og = session.exec(select(ImageVersion).where(ImageVersion.gallery_id == self._id).where(
    #                         ImageVersion.base_name == base_name).where(ImageVersion.version == None)).one_or_none()

    #                     # if an original exists, assume the version wants to link as the parent
    #                     if image_version_og:
    #                         parent_id = image_version_og._id

    #                 image_version_kwargs = {
    #                     'gallery_id': self.id,
    #                     'base_name': base_name if parent_id is None else None,
    #                     'version': version,
    #                     'parent_id': parent_id
    #                 }

    #                 image_version = session.exec(select(ImageVersion).where(
    #                     ImageVersion._build_conditions(image_version_kwargs))).one_or_none()

    #                 # this if the first file of this version
    #                 if not image_version:
    #                     image_version = await ImageVersion.api_post(session=session, c=c, authorized_user_id=self.user_id, admin=False, create_model=ImageVersionAdminCreate(**image_version_kwargs))

    #                 image_file_metadata = await ImageFileMetadata.api_post(session=session, c=c, authorized_user_id=self.user_id, admin=False, create_model=ImageFileMetadataAdminCreate(file_id=image_file.id, version_id=image_version.id, scale=scale))

    #     # recursively sync children
    #     for child in self.children:
    #         await child.sync_with_local(session, c, dir / child.folder_name)

    '''
        def sync_with_local(self):
        """sync database with local directory contents"""

        if input('Are you sure you want to sync with local? (y/n) ') != 'y':
            return

        # Studios
        studio_id_keys_to_add, studio_ids_to_delete = studio.Studio.find_to_add_and_delete(
            self.db[studio.Studio.COLLECTION_NAME], self.studios_dir)

        print('Studios to add')
        print(studio_id_keys_to_add)
        print('Studios to delete')
        print(studio_ids_to_delete)
        print()

        for studio_id_keys in studio_id_keys_to_add:
            new_studio = studio.Studio.make_from_id_keys(studio_id_keys)
            new_studio.insert(self.db[studio.Studio.COLLECTION_NAME])

        studio.Studio.delete_by_ids(
            self.db[studio.Studio.COLLECTION_NAME], list(studio_ids_to_delete))

        # Events
        # remove events that reference studios that no longer exist
        studio_id_keys_by_id = studio.Studio.find_id_keys_by_id(
            self.db[studio.Studio.COLLECTION_NAME])

        stale_event_ids = event.Event.find_ids(
            self.db[event.Event.COLLECTION_NAME], filter={'studio_id': {'$nin': list(studio_id_keys_by_id.keys())}})

        print('Stale event ids')
        print(stale_event_ids)
        print()

        event.Event.delete_by_ids(
            self.db[event.Event.COLLECTION_NAME], list(stale_event_ids))

        # loop through existing studios and update events
        for studio_id in studio_id_keys_by_id:
            studio_dir_name = studio_id_keys_by_id[studio_id][0]
            studio_dir = self.studios_dir.joinpath(studio_dir_name)

            event_id_keys_to_add, event_ids_to_delete = event.Event.find_to_add_and_delete(
                self.db[event.Event.COLLECTION_NAME], studio_dir, studio_id)

            print(studio_id)
            print(event_id_keys_to_add)
            print(event_ids_to_delete)
            print()

            for event_id_keys in event_id_keys_to_add:
                new_event = event.Event.make_from_id_keys(event_id_keys)
                new_event.insert(self.db[event.Event.COLLECTION_NAME])

            event.Event.delete_by_ids(
                self.db[event.Event.COLLECTION_NAME], list(event_ids_to_delete))

        # groups
        # remove groups that reference events that no longer exist
        event_id_keys_by_id = event.Event.find_id_keys_by_id(
            self.db[event.Event.COLLECTION_NAME])

        stale_file_ids = media.Media.find_ids(
            self.db[media.Media.COLLECTION_NAME], filter={'event_id': {'$nin': list(event_id_keys_by_id.keys())}})

        print('Stale file ids')
        print(stale_file_ids)
        print()

        media.Media.delete_by_ids(
            self.db[media.Media.COLLECTION_NAME], list(stale_file_ids))

        # loop through existing events and update groups
        for event_id in event_id_keys_by_id:
            event_dict = event.Event.id_keys_to_dict(
                event_id_keys_by_id[event_id])

            event_dir = self.studios_dir.joinpath(studio_id_keys_by_id[event_dict['studio_id']][0]).joinpath(
                event.Event.build_directory_name(
                    {'datetime': event_dict['datetime'], 'name': event_dict['name']})
            )

            file_id_keys_to_add, file_ids_to_delete = media.Media.find_to_add_and_delete(
                self.db[media.Media.COLLECTION_NAME], event_dir, event_id)

            print(event_id)
            print(file_id_keys_to_add)
            print(file_ids_to_delete)

            for file_id_keys in file_id_keys_to_add:
                file_class = media.Media.get_media_type_from_id_keys(
                    file_id_keys)
                if file_class is None:
                    Warning('File ending not recognized {} not recognized on file {}'.format(
                        file_id_keys['file_ending'], file_id_keys))
                    continue
                new_file = file_class.make_from_id_keys(file_id_keys)
                new_file.insert(self.db[media.Media.COLLECTION_NAME])

            media.Media.delete_by_ids(
                self.db[media.Media.COLLECTION_NAME], list(file_ids_to_delete))
        '''
