import bcrypt
import uuid
import secrets
from pathlib import Path


def deep_merge_dicts(primary_dict: dict, secondary_dict: dict) -> dict:
    """ Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
    updating only top-level keys, dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys. The ``secondary_dict`` is merged into
    ``primary_dict``.
    :param primary_dict: dict onto which the merge is executed
    :param secondary_dict: primary_dict merged into primary_dict
    :return: None
    """
    for k in secondary_dict:
        if (k in primary_dict and isinstance(primary_dict[k], dict) and isinstance(secondary_dict[k], dict)):  # noqa
            deep_merge_dicts(primary_dict[k], secondary_dict[k])
        else:
            primary_dict[k] = secondary_dict[k]
    return primary_dict


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def generate_uuid() -> str:
    return str(uuid.uuid4())


def generate_jwt_secret_key() -> str:
    return secrets.token_hex(32)
