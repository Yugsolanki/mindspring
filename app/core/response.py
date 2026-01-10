from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar("T")


class SuccessResponseModel(BaseModel, Generic[T]):
    status: str = "success"
    message: str
    data: Optional[T] = None


class ErrorResponseModel(BaseModel, Generic[T]):
    status: str = "error"
    message: str
    error: Optional[T] = None
