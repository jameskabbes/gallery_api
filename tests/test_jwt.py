import pytest
from ..src.arbor_imago.models.bases import auth_credential
from ..src.arbor_imago.models import SignUp
from ..src.arbor_imago.services.sign_up import SignUp as SignUpService
import datetime as datetime_module


example = SignUp(
    expiry=datetime_module.datetime(
        2023, 10, 1, 12, 0, 0, tzinfo=datetime_module.timezone.utc
    ),
    issued=datetime_module.datetime(
        2023, 10, 12, 12, 0, 0, tzinfo=datetime_module.timezone.utc
    ),
    email='a@a.com',
)


# def test_from_payload():

#     instance = SignUpService.from_payload(
#         {
#             'exp': example.expiry.timestamp(),
#             'iat': example.issued.timestamp(),
#             'sub': example.email,
#             'type': example.auth_type,
#         }
#     )

#     assert instance == example


# def test_to_payload():

#     payload = SignUp.to_payload(example)

#     assert payload == {
#         'exp': example.expiry,
#         'iat': example.issued,
#         'sub': example.email,
#         'type': example.auth_type,
#     }
