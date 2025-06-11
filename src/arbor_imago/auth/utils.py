from fastapi import Depends, Request
from fastapi.security import OAuth2, OAuth2PasswordRequestForm, OAuth2PasswordBearer, APIKeyHeader
from fastapi.openapi.models import OAuthFlowPassword
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security.utils import get_authorization_scheme_param
from fastapi.responses import JSONResponse
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from pydantic import BaseModel
import typing
from typing import Annotated, Generic
from fastapi import Request, HTTPException, status, Response
import datetime as datetime_module

from arbor_imago import custom_types, auth, utils, config, models, schemas, services
from arbor_imago.auth import exceptions
from arbor_imago.models import tables
from arbor_imago.schemas import user as user_schema, user_access_token as user_access_token_schema, sign_up as sign_up_schema, otp as otp_schema, auth_credential as auth_credential_schema
from arbor_imago.services.user import User as UserService
from arbor_imago.services.user_access_token import UserAccessToken as UserAccessTokenService
from arbor_imago.services.sign_up import SignUp as SignUpService
from arbor_imago.services.otp import OTP as OTPService
from arbor_imago.services.api_key import ApiKey as ApiKeyService
from arbor_imago.services import auth_credential as auth_credential_service


def set_access_token_cookie(response: Response, access_token: custom_types.JwtEncodedStr,  expiry: datetime_module.datetime | None = None):

    kwargs = {}
    if expiry:
        kwargs['expires'] = expiry

    response.set_cookie(
        **config.ACCESS_TOKEN_COOKIE,
        value=access_token,
        **kwargs
    )


def delete_access_token_cookie(response: Response):
    response.delete_cookie(config.ACCESS_TOKEN_COOKIE['key'])


class OAuth2PasswordBearerMultiSource(OAuth2):
    def __init__(
        self,
        flows: OAuthFlowsModel
    ):
        super().__init__(flows=flows, auto_error=False)

    async def __call__(self, request: Request) -> custom_types.JwtEncodedStr | None:

        tokens: set[custom_types.JwtEncodedStr] = set()
        provided_auth_types = set()

        # Authorization: bearer <token>
        authorization = request.headers.get("Authorization")
        if authorization:
            scheme, param = get_authorization_scheme_param(authorization)
            if scheme.lower() == "bearer":
                tokens.add(typing.cast(custom_types.JwtEncodedStr, param))
                provided_auth_types.add("bearer")

        # HTTP-only Cookie
        cookie_access_token = request.cookies.get(
            config.ACCESS_TOKEN_COOKIE['key'])
        if cookie_access_token:
            tokens.add(typing.cast(
                custom_types.JwtEncodedStr, cookie_access_token))
            provided_auth_types.add("cookie")

        if len(tokens) > 1:

            raise exceptions.different_tokens_provided(
                provided_auth_types, len(tokens)
            )

        elif len(tokens) == 1:
            return tokens.pop()
        else:
            return None


oauth2_scheme = OAuth2PasswordBearerMultiSource(
    flows=OAuthFlowsModel(password=OAuthFlowPassword(tokenUrl="auth/token/")))


class GetAuthReturn(BaseModel, Generic[schemas.TAuthCredentialInstance_co]):
    isAuthorized: bool = False
    exception: typing.Optional[HTTPException] = None
    user: typing.Optional[user_schema.UserPrivate] = None
    scope_ids: typing.Optional[set[custom_types.Scope.id]] = None
    auth_credential: typing.Optional[schemas.TAuthCredentialInstance_co] = None

    class Config:
        arbitrary_types_allowed = True

    @property
    def _user_id(self) -> custom_types.User.id | None:
        if self.user:
            return self.user.id
        else:
            return None


class _WithRequiredScopes(typing.TypedDict):
    required_scopes: typing.NotRequired[set[custom_types.Scope.name]]


class _WithOverrideLifetime(typing.TypedDict):
    override_lifetime: typing.NotRequired[datetime_module.timedelta]


class _WithPermittedTypes(typing.TypedDict):
    permitted_types: typing.NotRequired[set[schemas.AuthCredentialJwtType]]


class _WithRaiseExceptions(typing.TypedDict):
    raise_exceptions: typing.NotRequired[bool]


class MakeGetAuthDepedencyKwargs(
        _WithRequiredScopes,
        _WithOverrideLifetime,
        _WithPermittedTypes,
        _WithRaiseExceptions,
):
    pass


class GetAuthFromTableKwargs(
        _WithRequiredScopes,
        _WithOverrideLifetime):
    session: AsyncSession
    auth_credential_service: services.AuthCredentialTableService
    dt_now: typing.NotRequired[datetime_module.datetime]


class GetAuthFromJwtKwargs(
        _WithRequiredScopes,
        _WithOverrideLifetime,
        _WithPermittedTypes):
    token: typing.Optional[custom_types.JwtEncodedStr]


def is_valid_time_bounds(
        issued: datetime_module.datetime,
        expiry: datetime_module.datetime,
        dt_now: datetime_module.datetime = datetime_module.datetime.now(
        ).astimezone(datetime_module.UTC),
        override_lifespan: datetime_module.timedelta | None = None) -> bool:
    """Validate the time bounds of the issued and expiry dates."""

    if dt_now > expiry:
        return False

    if override_lifespan is not None:
        if dt_now > (issued + override_lifespan):
            return False

    if dt_now < issued:
        return False

    return True


async def get_auth_from_auth_credential_table_inst(
    auth_credential_table_inst: schemas.TAuthCredentialTableInstance,
        **kwargs: typing.Unpack[GetAuthFromTableKwargs]
) -> GetAuthReturn[schemas.TAuthCredentialTableInstance]:

    session = kwargs.get('session')
    service = kwargs.get('auth_credential_service')
    required_scopes = kwargs.get('required_scopes', set())
    override_lifetime = kwargs.get('override_lifetime', None)
    dt_now = kwargs.get(
        'dt_now', datetime_module.datetime.now().astimezone(datetime_module.UTC))

    # validate time bounds
    if not is_valid_time_bounds(auth_credential_table_inst.issued, auth_credential_table_inst.expiry, dt_now, override_lifetime):
        await service.delete(
            {
                'session': session,
                'admin': True,
                'authorized_user_id': auth_credential_table_inst.user_id,
                'id': auth_credential_table_inst.id,
            }
        )
        return GetAuthReturn(exception=exceptions.authorization_expired())

    # if no user is associated with the auth_credential, raise an exception
    async with config.ASYNC_SESSIONMAKER() as session:
        user = await UserService.read(
            {
                'session': session,
                'id': auth_credential_table_inst.user_id,
                'admin': True,
                'authorized_user_id': auth_credential_table_inst.user_id,
            })

    if user is None:
        return GetAuthReturn(exception=exceptions.user_not_found())

    required_scope_ids = set(
        [config.SCOPE_NAME_MAPPING[scope_name]
            for scope_name in required_scopes]
    )

    scope_ids = set(await service.get_scope_ids(inst=auth_credential_table_inst, session=session))  # type: ignore # noqa

    if not required_scope_ids.issubset(scope_ids):
        return GetAuthReturn(exception=exceptions.not_permitted())

    return GetAuthReturn(
        isAuthorized=True,
        user=user_schema.UserPrivate.model_validate(user),
        scope_ids=scope_ids,
        auth_credential=auth_credential_table_inst
    )


async def get_auth_from_auth_credential_jwt(**kwargs: typing.Unpack[GetAuthFromJwtKwargs]) -> GetAuthReturn[schemas.AuthCredentialJwtInstance]:

    token = kwargs.get('token', None)
    required_scopes = kwargs.get('required_scopes', set())
    permitted_types = kwargs.get(
        'permitted_types', {UserAccessTokenService.auth_type.value, ApiKeyService.auth_type.value})
    override_lifetime = kwargs.get('override_lifetime', None)

    # 1. if token is blank
    if token is None:
        return GetAuthReturn(exception=exceptions.missing_authorization())

    # 2. make sure the token is a valid jwt
    try:
        payload = typing.cast(
            auth_credential_schema.JwtPayload[typing.Any], utils.jwt_decode(token))
    except:
        return GetAuthReturn(exception=exceptions.improper_format())

    # 3. make sure the jwt is a valid payload
    try:
        auth_credential_service.JwtIO.validate_jwt_claims(
            payload)  # type: ignore
    except auth_credential_service.MissingRequiredClaimsError as e:
        return GetAuthReturn(exception=exceptions.missing_required_claims(set(e.claims)))
    except Exception:
        raise

    # 4. check if the auth_credential type is permitted
    auth_type = payload['type']
    if auth_type not in permitted_types:
        return GetAuthReturn(exception=exceptions.authorization_type_not_permitted(auth_type))

    AuthCredentialService = services.AUTH_CREDENTIAL_TYPE_TO_SERVICE[auth_type]

    dt_now = datetime_module.datetime.now().astimezone(datetime_module.UTC)
    dt_expiry = datetime_module.datetime.fromtimestamp(
        payload['exp'], tz=datetime_module.UTC)
    dt_issued = datetime_module.datetime.fromtimestamp(
        payload['iat'], tz=datetime_module.UTC)

    # 5. validate time bounds encoded in the jwt
    if not is_valid_time_bounds(dt_issued, dt_expiry, dt_now, override_lifetime):
        return GetAuthReturn(exception=exceptions.authorization_expired())

    # if the auth_credential is stored in a table, check its db entry
    if issubclass(AuthCredentialService, auth_credential_service.Table):

        async with config.ASYNC_SESSIONMAKER() as session:

            AuthCredentialService = typing.cast(
                services.AuthCredentialJwtAndTableService, AuthCredentialService)

            auth_credential_table_inst_from_db = await AuthCredentialService.read({
                'session': session,
                'id': payload['sub'],
                'admin': True,
                'authorized_user_id': None
            })

            if not auth_credential_table_inst_from_db:
                return GetAuthReturn(exception=exceptions.authorization_expired())

            return await get_auth_from_auth_credential_table_inst(
                auth_credential_table_inst_from_db,
                auth_credential_service=AuthCredentialService,
                session=session,
                dt_now=dt_now,
                **{
                    k: v for k, v in {
                        'required_scopes': required_scopes,
                        'override_lifetime': override_lifetime
                    }.items() if v
                }
            )

    else:

        AuthCredentialService = typing.cast(
            services.AuthCredentialJwtAndNotTableService, AuthCredentialService)

        # non-table auth_credentials have no scopes
        if required_scopes:
            return GetAuthReturn(exception=exceptions.not_permitted())

        return GetAuthReturn(
            isAuthorized=True,
            user=None,
            scope_ids=set(),
            auth_credential=AuthCredentialService.model_inst_from_jwt_payload(
                payload)
        )


def make_get_auth_dependency(**kwargs: typing.Unpack[MakeGetAuthDepedencyKwargs]):
    raise_exceptions = kwargs.get('raise_exceptions', True)

    async def get_authorization_dependency(response: Response, auth_token: typing.Annotated[custom_types.JwtEncodedStr | None, Depends(oauth2_scheme)]) -> GetAuthReturn:
        get_authorization_return = await get_auth_from_auth_credential_jwt(token=auth_token, **kwargs)
        if get_authorization_return.exception:
            if raise_exceptions:
                raise get_authorization_return.exception
        return get_authorization_return
    return get_authorization_dependency


class GetUserSessionInfoReturn(BaseModel):
    user: typing.Optional[user_schema.UserPrivate]
    scope_ids: typing.Optional[set[custom_types.Scope.id]]
    access_token: typing.Optional[user_access_token_schema.UserAccessTokenPublic]


assert config.AUTH_KEY == 'auth'


class GetUserSessionInfoNestedReturn(BaseModel):
    auth: GetUserSessionInfoReturn


def get_user_session_info(get_authorization_return: GetAuthReturn) -> GetUserSessionInfoNestedReturn:

    access_token: typing.Optional[user_access_token_schema.UserAccessTokenPublic] = None
    if get_authorization_return.auth_credential and isinstance(get_authorization_return.auth_credential, tables.UserAccessToken):
        access_token = user_access_token_schema.UserAccessTokenPublic(
            id=UserAccessTokenService.model_id(
                get_authorization_return.auth_credential),
            expiry=get_authorization_return.auth_credential.expiry
        )

    return GetUserSessionInfoNestedReturn(auth=GetUserSessionInfoReturn(
        user=get_authorization_return.user,
        scope_ids=get_authorization_return.scope_ids,
        access_token=access_token
    ))


def make_authenticate_user_with_username_and_password_dependency():
    async def authenticate_user_with_username_and_password(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> tables.User:

        async with config.ASYNC_SESSIONMAKER() as session:
            user = await UserService.authenticate(
                session, form_data.username, form_data.password)

            if user is None:
                raise exceptions.credentials()
            return user

    return authenticate_user_with_username_and_password


async def send_signup_link(session: AsyncSession, user: tables.User | None, email: custom_types.User.email):

    # existing user, send email to existing user
    if user:
        user_access_token = await UserAccessTokenService.create({
            'authorized_user_id': user.id,
            'session': session,
            'create_model': user_access_token_schema.UserAccessTokenAdminCreate(
                user_id=user.id,
                expiry=auth_credential_service.lifespan_to_expiry(
                    config.AUTH['credential_lifespans']['request_sign_up'])
            ),
            'admin': False
        })

        url = '{}{}/?token={}'.format(config.FRONTEND_URL,
                                      config.FRONTEND_ROUTES['verify_magic_link'], utils.jwt_encode(typing.cast(dict, UserAccessTokenService.to_jwt_payload(user_access_token))))

        if email:
            utils.send_email(
                email, 'Sign Up Request', 'Somebody requested to sign up with this email. An account already exists with this email. Click here to login instead: {}'.format(url))

    else:

        sign_up = SignUpService.model_inst_from_create_model(sign_up_schema.SignUpAdminCreate(
            email=email, expiry=auth_credential_service.lifespan_to_expiry(config.AUTH['credential_lifespans']['request_sign_up'])))

        sign_up_jwt = utils.jwt_encode(typing.cast(
            dict, SignUpService.to_jwt_payload(sign_up)))

        url = '{}{}/?token={}'.format(config.FRONTEND_URL,
                                      config.FRONTEND_ROUTES['verify_signup'], sign_up_jwt)

        if email:
            utils.send_email(email, 'Sign Up',
                             'Click here to sign up: {}'.format(url))


class LoginWithOTPResponse(GetUserSessionInfoNestedReturn):
    pass


async def login_otp(session: AsyncSession, user: tables.User | None, response: Response, code: custom_types.OTP.code) -> LoginWithOTPResponse:

    if user is None:
        raise exceptions.invalid_otp()

    query = select(OTPService._MODEL).where(
        OTPService._MODEL.user_id == user.id)
    otp = await OTPService.fetch_one(session, query)

    if otp is None or OTPService.verify_code(code, otp.hashed_code) is False:
        raise exceptions.invalid_otp()

    get_auth = await get_auth_from_auth_credential_table_inst(
        otp,
        session=session,
        auth_credential_service=OTPService,
        override_lifetime=config.AUTH['credential_lifespans']['access_token']
    )

    if get_auth.exception:
        raise get_auth.exception

    # if the code is active and correct, create a new access token
    user_access_token = await UserAccessTokenService.create({
        'authorized_user_id': user.id,
        'session': session,
        'create_model': user_access_token_schema.UserAccessTokenAdminCreate(
            user_id=user.id,
            expiry=auth_credential_service.lifespan_to_expiry(
                config.AUTH['credential_lifespans']['access_token']),
        ),
        'admin': False
    })

    set_access_token_cookie(response, utils.jwt_encode(typing.cast(
        dict, UserAccessTokenService.to_jwt_payload(user_access_token))), expiry=user_access_token.expiry)

    # one time link, delete the otp
    await OTPService.delete(
        {
            'session': session,
            'id': otp.id,
            'authorized_user_id': user.id,
            'admin': False
        }
    )

    return LoginWithOTPResponse(
        auth=GetUserSessionInfoReturn(
            user=user_schema.UserPrivate.model_validate(user),
            scope_ids=set(await UserAccessTokenService.get_scope_ids(session, user_access_token)),
            access_token=user_access_token_schema.UserAccessTokenPublic.model_validate(
                user_access_token)
        )
    )


async def create_magic_link(session: AsyncSession, user: tables.User, email: typing.Optional[custom_types.User.email] = None, phone_number: typing.Optional[custom_types.User.phone_number] = None) -> str:

    user_access_token = await UserAccessTokenService.create(
        {
            'authorized_user_id': user.id,
            'session': session,
            'admin': False,
            'create_model': user_access_token_schema.UserAccessTokenAdminCreate(user_id=user.id, expiry=auth_credential_service.lifespan_to_expiry(config.AUTH['credential_lifespans']['magic_link']))
        }
    )

    url = '{}{}/?token={}'.format(config.FRONTEND_URL,
                                  config.FRONTEND_ROUTES['verify_magic_link'], utils.jwt_encode(typing.cast(dict, UserAccessTokenService.to_jwt_payload(user_access_token))))

    return url


async def send_magic_link(url: str, user: tables.User, email: typing.Optional[custom_types.User.email] = None, phone_number: typing.Optional[custom_types.User.phone_number] = None):

    if email:
        utils.send_email(email, 'Magic Link',
                         'Click to login: {}'.format(url))
    if phone_number:
        if user.phone_number:
            utils.send_sms(user.phone_number, 'Click to login: {}'.format(url))


async def create_otp(session: AsyncSession, user: tables.User, email: typing.Optional[custom_types.User.email] = None, phone_number: typing.Optional[custom_types.User.phone_number] = None) -> custom_types.OTP.code:

    code = OTPService.generate_code()

    # if there is an existing OTP, delete it
    query = select(OTPService._MODEL).where(
        OTPService._MODEL.user_id == user.id)
    existing_otp = await OTPService.fetch_one(session, query)

    if existing_otp is not None:
        await OTPService.delete({
            'id': existing_otp.id,
            'session': session,
            'authorized_user_id': user.id,
            'admin': False
        })

    # create a new OTP, return it
    otp = await OTPService.create({
        'authorized_user_id': user.id,
        'session': session,
        'admin': False,
        'create_model': otp_schema.OTPAdminCreate(
            user_id=user.id, hashed_code=OTPService.hash_code(code), expiry=auth_credential_service.lifespan_to_expiry(config.AUTH['credential_lifespans']['otp'])
        )
    })

    return code


async def send_otp(code: custom_types.OTP.code, user: tables.User, email: typing.Optional[custom_types.User.email] = None, phone_number: typing.Optional[custom_types.User.phone_number] = None):

    if email:
        utils.send_email(email, 'OTP', 'Your OTP is: {}'.format(code))
    if phone_number:
        utils.send_sms(phone_number, 'Your OTP is: {}'.format(code))
