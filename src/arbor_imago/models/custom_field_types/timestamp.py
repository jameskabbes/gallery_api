from sqlalchemy import Dialect
from sqlalchemy.types import TypeDecorator, REAL, DateTime
import datetime as datetime_module
from pydantic import ValidationInfo
import typing

from arbor_imago import custom_types

"""
Developer's Note:
This module defines a custom SQLAlchemy type decorator for Timestamp types

For databases that do not support datetimes types (SQLite), datetime objects are converted to floating point numbers (unix timestamps).
For precision of language, the table types are always referred to as "datetime.datetime" objects, since that best describes them. For SQLite applcations, these are actually floating point numbers, but this custom type solves the I/O.

When switching from different databases, this custom type should speed up the change process.

It should be noted that this adds a small amount of overhead to the database, but it is negligible for most applications.

"""


class Timestamp(TypeDecorator):
    impl = DateTime  # Default type (overridden for SQLite)
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect):
        # Use REAL for SQLite, DateTime for others
        if dialect.name == "sqlite":
            return REAL()
        return DateTime()

    def process_bind_param(self, value: datetime_module.datetime | None, dialect: Dialect) -> custom_types.timestamp | datetime_module.datetime | None:
        # Convert to float (Unix timestamp) for SQLite, pass datetime for others
        if value is None:
            return None
        if dialect.name == "sqlite":
            # Converts to float with microseconds for SQLite
            return value.timestamp()
        else:
            # Native datetime for other databases
            return value

    def process_result_value(self, value: custom_types.timestamp | datetime_module.datetime | None, dialect: Dialect) -> datetime_module.datetime | None:
        if value is None:
            return None
        if dialect.name == "sqlite":
            # Convert from float to datetime for SQLite
            return datetime_module.datetime.fromtimestamp(typing.cast(custom_types.timestamp, value)).astimezone(datetime_module.UTC)
        else:
            # For other databases, return the raw datetime object
            return typing.cast(datetime_module.datetime, value)


def validate_and_normalize_datetime(value: datetime_module.datetime, info: ValidationInfo) -> datetime_module.datetime:
    if value.tzinfo == None:
        raise ValueError(str(info.field_name) + ' must have a timezone')
    return value.astimezone(datetime_module.timezone.utc)
