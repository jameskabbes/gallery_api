import typing
import jwt
from arbor_imago.core import types
from arbor_imago.core import config


def jwt_encode(payload: dict[str, typing.Any]) -> types.JwtEncodedStr:
    return jwt.encode(payload, config.BACKEND_SECRETS['JWT_SECRET_KEY'], algorithm=config.BACKEND_SECRETS['JWT_ALGORITHM'])


def jwt_decode(token: types.JwtEncodedStr) -> dict:
    return jwt.decode(token, config.BACKEND_SECRETS['JWT_SECRET_KEY'], algorithms=[config.BACKEND_SECRETS['JWT_ALGORITHM']])


def send_email(recipient: types.Email, subject: str, body: str):

    print('''
Email sent to: {}
Subject: {}
Body: {}'''.format(recipient, subject, body))


def send_sms(recipient: types.PhoneNumber, message: str):

    print('''
SMS sent to: {}
Message: {}'''.format(recipient, message))
