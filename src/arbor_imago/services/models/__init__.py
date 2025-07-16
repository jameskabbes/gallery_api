from typing import Type, TypedDict, TypeVar

from arbor_imago.services.models.api_key_scope import ApiKeyScope as ApiKeyScopeService
from arbor_imago.services.models.api_key import ApiKey as ApiKeyService
from arbor_imago.services.models.file import File as FileService
from arbor_imago.services.models.gallery import Gallery as GalleryService
from arbor_imago.services.models.gallery_permission import GalleryPermission as GalleryPermissionService
from arbor_imago.services.models.image_version import ImageVersion as ImageVersionService
from arbor_imago.services.models.otp import OTP as OTPService
from arbor_imago.services.models.sign_up import SignUp as SignUpService
from arbor_imago.services.models.user_access_token import UserAccessToken as UserAccessTokenService
from arbor_imago.services.models.user import User as UserService

AuthCredentialService = Type[UserAccessTokenService] | Type[ApiKeyService] | Type[OTPService] | Type[SignUpService]
AuthCredentialJwtService = Type[UserAccessTokenService] | Type[ApiKeyService] | Type[SignUpService]


AUTH_CREDENTIAL_JWT_SERVICES: set[AuthCredentialJwtService] = {
    UserAccessTokenService,
    ApiKeyService,
    SignUpService,
}


AuthCredentialTableService = Type[UserAccessTokenService] | Type[ApiKeyService] | Type[OTPService]
AuthCredentialJwtAndTableService = Type[UserAccessTokenService] | Type[ApiKeyService]

AuthCredentialJwtAndNotTableService = Type[SignUpService]
AuthCredentialNotJwtAndTableService = Type[OTPService]


class AuthCredentialTypeToService(TypedDict):
    access_token: Type[UserAccessTokenService]
    api_key: Type[ApiKeyService]
    sign_up: Type[SignUpService]
    otp: Type[OTPService]


AUTH_CREDENTIAL_TYPE_TO_SERVICE: AuthCredentialTypeToService = {
    'access_token': UserAccessTokenService,
    'api_key': ApiKeyService,
    'sign_up': SignUpService,
    'otp': OTPService,
}

Service = UserService | UserAccessTokenService | ApiKeyService | OTPService | GalleryService | GalleryPermissionService | FileService | ImageVersionService | ApiKeyScopeService

TService = TypeVar('TService', bound=Service)
TService_co = TypeVar('TService_co', bound=Service, covariant=True)
TService_contra = TypeVar('TService_contra', bound=Service, contravariant=True)
