import typing
from fastapi import Request, HTTPException, status, Response
from arbor_imago import custom_types, auth, config


def Base(status_code: int, detail: str, logout: bool) -> HTTPException:
    headers = {"WWW-Authenticate": "Bearer, Cookie"}
    if logout:
        headers[config.HEADER_KEYS['auth_logout']] = 'true'

    return HTTPException(
        status_code=status_code,
        detail=detail,
        headers=headers
    )


def different_tokens_provided(types: set[str], n: int) -> HTTPException:
    return Base(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="{n} different tokens provided from the following sources: {}. Only one unique token may be provided".format(
            n, ", ".join(types)),
        logout=False
    )


def missing_authorization() -> HTTPException:
    return Base(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing Authorization header or {} cookie".format(
            config.ACCESS_TOKEN_COOKIE['key']),
        logout=True
    )


def improper_format() -> HTTPException:
    return Base(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Improper format for authorization token",
        logout=True
    )


def missing_required_claims(claims: set[str]) -> HTTPException:
    return Base(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Missing required claims: {}".format(
            ", ".join(claims)),
        logout=False
    )


def authorization_expired() -> HTTPException:
    return Base(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authorization expired",
        logout=True
    )


def user_not_found() -> HTTPException:
    return Base(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="User not found",
        logout=True
    )


def not_permitted() -> HTTPException:
    return Base(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not permitted",
        logout=False
    )


def credentials() -> HTTPException:
    return Base(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        logout=True
    )


def invalid_otp() -> HTTPException:
    return Base(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid OTP",
        logout=True
    )


def authorization_type_not_permitted(type: custom_types.AuthCredential.type) -> HTTPException:
    return Base(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Authorization type '{}' not permitted for this endpoint".format(
            type),
        logout=False
    )
