from pydantic import BaseModel


class DetailOnlyResponse(BaseModel):
    detail: str


class NotFoundResponse(DetailOnlyResponse):
    pass


class IsAvailableResponse(BaseModel):
    available: bool
