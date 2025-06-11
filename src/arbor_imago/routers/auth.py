import httpx
from fastapi import Depends, Request, Response, Form, status, BackgroundTasks, HTTPException
from sqlmodel import select
from pydantic import BaseModel
from typing import Annotated, cast

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from arbor_imago import config, custom_types, utils
from arbor_imago.auth import utils as auth_utils, exceptions as auth_exceptions
from arbor_imago.schemas import user_access_token as user_access_token_schema, user as user_schema, api as api_schema, sign_up as sign_up_schema
from arbor_imago.models.tables import User, UserAccessToken
from arbor_imago.models.models import SignUp
from arbor_imago.services import auth_credential as auth_credential_service
from arbor_imago.services.user import User as UserService
from arbor_imago.services.user_access_token import UserAccessToken as UserAccessTokenService
from arbor_imago.routers import base


class TokenResponse(BaseModel):
    access_token: custom_types.JwtEncodedStr
    token_type: str


class LoginWithPasswordResponse(auth_utils.GetUserSessionInfoNestedReturn):
    pass


class LoginWithMagicLinkRequest(BaseModel):
    token: custom_types.JwtEncodedStr


class LoginWithMagicLinkResponse(auth_utils.GetUserSessionInfoNestedReturn):
    pass


class LoginWithOTPEmailRequest(BaseModel):
    code: custom_types.OTP.code
    email: custom_types.User.email


class LoginWithGoogleRequest(BaseModel):
    id_token: str


class LoginWithGoogleResponse(auth_utils.GetUserSessionInfoNestedReturn):
    pass


class LoginWithOTPPhoneNumberRequest(BaseModel):
    code: custom_types.OTP.code
    phone_number: custom_types.User.phone_number


class SignUpRequest(BaseModel):
    token: custom_types.JwtEncodedStr


class SignUpResponse(auth_utils.GetUserSessionInfoNestedReturn):
    pass


class RequestSignUpEmailRequest(BaseModel):
    email: custom_types.User.email


class RequestSignUpSMSRequest(BaseModel):
    phone_number: custom_types.User.phone_number


class RequestMagicLinkEmailRequest(BaseModel):
    email: custom_types.User.email


class RequestMagicLinkSMSRequest(BaseModel):
    phone_number: custom_types.User.phone_number


class RequestOTPEmailRequest(BaseModel):
    email: custom_types.User.email


class RequestOTPSMSRequest(BaseModel):
    phone_number: custom_types.User.phone_number


class AuthRouter(base.Router):

    _ADMIN = False
    _PREFIX = '/auth'
    _TAG = 'Auth'

    @classmethod
    async def auth_root(
        cls,
        authorization: Annotated[auth_utils.GetAuthReturn, Depends(
            auth_utils.make_get_auth_dependency(raise_exceptions=False))]
    ) -> auth_utils.GetUserSessionInfoNestedReturn:
        return auth_utils.get_user_session_info(authorization)

    @classmethod
    async def token(
        cls,
        user: Annotated[User, Depends(auth_utils.make_authenticate_user_with_username_and_password_dependency())],
        response: Response,
        stay_signed_in: bool = Form(False)
    ) -> TokenResponse:
        async with config.ASYNC_SESSIONMAKER() as session:

            user_access_token = await UserAccessTokenService.create({
                'session': session,
                'admin': False,
                'create_model': user_access_token_schema.UserAccessTokenAdminCreate(
                    user_id=user.id,
                    expiry=auth_credential_service.lifespan_to_expiry(config.AUTH[
                        'credential_lifespans']['access_token']),
                ),
                'authorized_user_id': user.id,
            })

            encoded_jwt = utils.jwt_encode(
                cast(dict, UserAccessTokenService.to_jwt_payload(user_access_token)))

            auth_utils.set_access_token_cookie(response, encoded_jwt, None if not stay_signed_in else auth_credential_service.lifespan_to_expiry(
                config.AUTH['credential_lifespans']['access_token']))
            return TokenResponse(access_token=encoded_jwt, token_type='bearer')

    @classmethod
    async def login_password(
        cls,
        user: Annotated[User, Depends(auth_utils.make_authenticate_user_with_username_and_password_dependency())],
        response: Response,
        request: Request,
        stay_signed_in: bool = Form(False)
    ) -> LoginWithPasswordResponse:

        async with config.ASYNC_SESSIONMAKER() as session:

            tokken_lifespan = config.AUTH['credential_lifespans']['access_token']

            user_access_token = await UserAccessTokenService.create({
                'session': session,
                'admin': False,
                'authorized_user_id': user.id,
                'create_model': user_access_token_schema.UserAccessTokenAdminCreate(
                    user_id=user.id,
                    expiry=auth_credential_service.lifespan_to_expiry(config.AUTH[
                        'credential_lifespans']['access_token']),
                ),
            })

            encoded_jwt = utils.jwt_encode(
                cast(dict, UserAccessTokenService.to_jwt_payload(user_access_token)))

            auth_utils.set_access_token_cookie(response, encoded_jwt, None if not stay_signed_in else auth_credential_service.lifespan_to_expiry(
                config.AUTH['credential_lifespans']['access_token']))

            user_private = user_schema.UserPrivate.model_validate(user)

            return LoginWithPasswordResponse(
                auth=auth_utils.GetUserSessionInfoReturn(
                    user=user_schema.UserPrivate.model_validate(
                        user),
                    scope_ids=set(
                        config.USER_ROLE_ID_SCOPE_IDS[user.user_role_id]),
                    access_token=user_access_token_schema.UserAccessTokenPublic.model_validate(
                        user_access_token),
                ))

    @classmethod
    async def login_magic_link(
        cls,
        response: Response,
        model: LoginWithMagicLinkRequest
    ) -> LoginWithMagicLinkResponse:

        authorization = await auth_utils.get_auth_from_auth_credential_jwt(
            token=model.token,
            permitted_types={'access_token'},
            override_lifetime=config.AUTH['credential_lifespans']['magic_link']
        )

        if authorization.exception:
            raise authorization.exception

        auth_credential = cast(
            UserAccessToken, authorization.auth_credential)

        async with config.ASYNC_SESSIONMAKER() as session:
            token_lifespan = config.AUTH['credential_lifespans']['access_token']
            user_access_token = await UserAccessTokenService.create(
                {
                    'session': session,
                    'admin': False,
                    'create_model': user_access_token_schema.UserAccessTokenAdminCreate(
                        user_id=auth_credential.user_id,
                        expiry=auth_credential_service.lifespan_to_expiry(
                            token_lifespan),
                    ),
                    'authorized_user_id': auth_credential.user_id,
                }
            )

            auth_utils.set_access_token_cookie(response, utils.jwt_encode(
                dict(UserAccessTokenService.to_jwt_payload(user_access_token))), expiry=auth_credential_service.lifespan_to_expiry(token_lifespan))

            # one time link, delete the auth_credential
            await session.delete(auth_credential)
            await session.commit()

        return LoginWithMagicLinkResponse(
            auth=auth_utils.GetUserSessionInfoReturn(
                user=user_schema.UserPrivate.model_validate(
                    authorization.user),
                scope_ids=set(
                    config.USER_ROLE_ID_SCOPE_IDS[cast(user_schema.UserPrivate, authorization.user).user_role_id]),
                access_token=user_access_token_schema.UserAccessTokenPublic.model_validate(
                    user_access_token
                )
            )
        )

    @classmethod
    async def login_otp_email(
        cls,
        model: LoginWithOTPEmailRequest,
        response: Response
    ) -> auth_utils.LoginWithOTPResponse:

        async with config.ASYNC_SESSIONMAKER() as session:
            user = (await session.exec(select(User).where(
                User.email == model.email))).one_or_none()
            return await auth_utils.login_otp(session, user, response, model.code)

    @classmethod
    async def login_otp_phone_number(
        cls,
        model: LoginWithOTPPhoneNumberRequest,
        response: Response
    ) -> auth_utils.LoginWithOTPResponse:

        async with config.ASYNC_SESSIONMAKER() as session:
            user = (await session.exec(select(User).where(
                User.phone_number == model.phone_number))).one_or_none()
            return await auth_utils.login_otp(session, user, response, model.code)

    @classmethod
    async def signup(cls, response: Response, model: SignUpRequest) -> SignUpResponse:

        authorization = await auth_utils.get_auth_from_auth_credential_jwt(
            token=model.token,
            permitted_types={'sign_up'},
            override_lifetime=config.AUTH['credential_lifespans']['request_sign_up'])

        # double check the user doesn't already exist
        async with config.ASYNC_SESSIONMAKER() as session:

            if (await session.exec(select(User).where(
                    User.email == cast(SignUp, authorization.auth_credential).email))).one_or_none() is not None:
                raise auth_exceptions.Base(
                    status.HTTP_409_CONFLICT,
                    'User already exists',
                    logout=False
                )

        async with config.ASYNC_SESSIONMAKER() as session:
            sign_up = cast(SignUp,
                           authorization.auth_credential)

            user = await UserService.create({
                'admin': True,
                'session': session,
                'create_model': user_schema.UserAdminCreate(email=sign_up.email, user_role_id=UserService.DEFAULT_ROLE_ID),
                'authorized_user_id': authorization._user_id,
            })

        token_expiry = auth_credential_service.lifespan_to_expiry(
            config.AUTH['credential_lifespans']['access_token'])

        user_access_token = await UserAccessTokenService.create({
            'session': session,
            'admin': False,
            'authorized_user_id': user.id,
            'create_model': user_access_token_schema.UserAccessTokenAdminCreate(
                user_id=user.id,
                expiry=token_expiry
            )
        })

        auth_utils.set_access_token_cookie(
            response,
            utils.jwt_encode(
                cast(dict, UserAccessTokenService.to_jwt_payload(user_access_token))),
            expiry=token_expiry)

        return SignUpResponse(
            auth=auth_utils.GetUserSessionInfoReturn(
                user=user_schema.UserPrivate.model_validate(user),
                scope_ids=set(
                    config.USER_ROLE_ID_SCOPE_IDS[user.user_role_id]),
                access_token=user_access_token_schema.UserAccessTokenPublic.model_validate(
                    user_access_token),
            )
        )

    @classmethod
    async def login_google(cls, request_token: LoginWithGoogleRequest, response: Response) -> LoginWithGoogleResponse:

        # Verify the ID token
        try:
            idinfo = id_token.verify_oauth2_token(
                request_token.id_token,  # <-- Make sure your frontend sends the ID token!
                google_requests.Request(),
                config.GOOGLE_CLIENT_ID
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Google ID token"
            )

        # fields: sub, name, given_name, family_name, picture, email, email_verified
        email = idinfo.get('email')
        if not email:
            raise auth_exceptions.Base(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Google account did not return an email',
                logout=False
            )

        async with config.ASYNC_SESSIONMAKER() as session:

            user = await UserService.fetch_by_email(session=session, email=email)

            if user is None:
                user = await UserService.create({
                    'session': session,
                    'authorized_user_id': None,
                    'create_model': user_schema.UserAdminCreate(email=email, user_role_id=UserService.DEFAULT_ROLE_ID),
                    'admin': True,
                })

            user_access_token = await UserAccessTokenService.create({
                'authorized_user_id': user.id,
                'create_model': user_access_token_schema.UserAccessTokenAdminCreate(
                    user_id=user.id,
                    expiry=auth_credential_service.lifespan_to_expiry(
                        config.AUTH['credential_lifespans']['access_token'])
                ),
                'admin': False,
                'session': session
            })

            auth_utils.set_access_token_cookie(
                response,
                utils.jwt_encode(
                    cast(dict, UserAccessTokenService.to_jwt_payload(user_access_token))),
            )

            return LoginWithGoogleResponse(
                auth=auth_utils.GetUserSessionInfoReturn(
                    user=user_schema.UserPrivate.model_validate(
                        user),
                    scope_ids=config.USER_ROLE_ID_SCOPE_IDS[user.user_role_id],
                    access_token=user_access_token_schema.UserAccessTokenPublic.model_validate(
                        user_access_token
                    )
                )
            )

    @classmethod
    async def request_sign_up_email(
        cls,
        model: RequestSignUpEmailRequest,
        background_tasks: BackgroundTasks
    ):

        async with config.ASYNC_SESSIONMAKER() as session:
            user = (await session.exec(select(User).where(
                User.email == model.email))).one_or_none()
            background_tasks.add_task(
                auth_utils.send_signup_link, session, user, email=model.email)
            return Response()

    @classmethod
    async def request_magic_link_email(cls, model: RequestMagicLinkEmailRequest, background_tasks: BackgroundTasks):

        async with config.ASYNC_SESSIONMAKER() as session:
            user = (await session.exec(select(User).where(
                User.email == model.email))).one_or_none()
            if user:
                magic_link = await auth_utils.create_magic_link(
                    session, user, email=model.email)
                background_tasks.add_task(
                    auth_utils.send_magic_link, magic_link, user, email=model.email)
        return Response()

    @classmethod
    async def request_magic_link_sms(cls, model: RequestMagicLinkSMSRequest, background_tasks: BackgroundTasks):
        async with config.ASYNC_SESSIONMAKER() as session:
            user = (await session.exec(select(User).where(
                User.phone_number == model.phone_number))).one_or_none()

            if user is not None:
                magic_link = await auth_utils.create_magic_link(
                    session, user, phone_number=model.phone_number)
                background_tasks.add_task(
                    auth_utils.send_magic_link, magic_link, user, phone_number=model.phone_number)
        return Response()

    @classmethod
    async def request_otp_email(cls, model: RequestOTPEmailRequest, background_tasks: BackgroundTasks):

        async with config.ASYNC_SESSIONMAKER() as session:
            user = (await session.exec(select(User).where(
                User.email == model.email))).one_or_none()

            if user:
                code = await auth_utils.create_otp(
                    session, user, email=model.email)
                background_tasks.add_task(
                    auth_utils.send_otp, code, user, email=model.email)
        return Response()

    @classmethod
    async def request_otp_sms(cls, model: RequestOTPSMSRequest, background_tasks: BackgroundTasks):

        async with config.ASYNC_SESSIONMAKER() as session:
            user = (await session.exec(select(User).where(
                User.phone_number == model.phone_number))).one_or_none()
            if user:
                code = await auth_utils.create_otp(
                    session, user, phone_number=model.phone_number)
                background_tasks.add_task(
                    auth_utils.send_otp, code, user, phone_number=model.phone_number)
        return Response()

    @classmethod
    async def logout(cls, response: Response, authorization: Annotated[auth_utils.GetAuthReturn[UserAccessToken], Depends(
            auth_utils.make_get_auth_dependency(raise_exceptions=False, permitted_types={'access_token'}))]) -> api_schema.DetailOnlyResponse:

        if authorization.isAuthorized:
            async with config.ASYNC_SESSIONMAKER() as session:
                await UserAccessTokenService.delete({
                    'session': session,
                    'admin': False,
                    'authorized_user_id': cast(custom_types.User.id, authorization._user_id),
                    'id': UserAccessTokenService.model_id(cast(UserAccessToken, authorization.auth_credential))
                })

        auth_utils.delete_access_token_cookie(response)
        return api_schema.DetailOnlyResponse(detail='Logged out')

    def _set_routes(self):

        self.router.get('/')(self.auth_root)
        self.router.post('/token/')(self.token)
        self.router.post('/login/password/', responses={status.HTTP_401_UNAUTHORIZED: {
                         'description': 'Could not validate credentials', 'model': api_schema.DetailOnlyResponse}})(self.login_password)
        self.router.post('/login/magic-link/', responses={status.HTTP_401_UNAUTHORIZED: {
                         'description': 'Invalid token', 'model': api_schema.DetailOnlyResponse}})(self.login_magic_link)
        self.router.post('/login/otp/email/')(self.login_otp_email)
        self.router.post(
            '/login/otp/phone_number/')(self.login_otp_phone_number)
        self.router.post('/signup/')(self.signup)
        self.router.post("/login/google/", responses={status.HTTP_400_BAD_REQUEST: {
                         'description': 'Invalid token', 'model': api_schema.DetailOnlyResponse}})(self.login_google)
        self.router.post('/request/signup/')(self.request_sign_up_email)
        self.router.post(
            '/request/magic-link/email/')(self.request_magic_link_email)
        self.router.post(
            '/request/magic-link/sms/')(self.request_magic_link_sms)
        self.router.post('/request/otp/email/')(self.request_otp_email)
        self.router.post('/request/otp/sms/')(self.request_otp_sms)
        self.router.post('/logout/')(self.logout)
