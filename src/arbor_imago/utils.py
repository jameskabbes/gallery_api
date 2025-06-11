import typing
import jwt
from arbor_imago import custom_types, config


def jwt_encode(payload: dict[str, typing.Any]) -> custom_types.JwtEncodedStr:
    return jwt.encode(payload, config.BACKEND_SECRETS['JWT_SECRET_KEY'], algorithm=config.BACKEND_SECRETS['JWT_ALGORITHM'])


def jwt_decode(token: custom_types.JwtEncodedStr) -> dict:
    return jwt.decode(token, config.BACKEND_SECRETS['JWT_SECRET_KEY'], algorithms=[config.BACKEND_SECRETS['JWT_ALGORITHM']])


def send_email(recipient: custom_types.Email, subject: str, body: str):

    print('''
Email sent to: {}
Subject: {}
Body: {}'''.format(recipient, subject, body))


def send_sms(recipient: custom_types.PhoneNumber, message: str):

    print('''
SMS sent to: {}
Message: {}'''.format(recipient, message))
