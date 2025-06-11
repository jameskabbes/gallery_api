from pydantic import BaseModel


class OrderBy[T](BaseModel):
    field: T
    ascending: bool
