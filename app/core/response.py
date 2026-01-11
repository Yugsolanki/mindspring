from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar("T")


class SuccessResponseModel(BaseModel, Generic[T]):
    status: str = "success"
    message: Optional[str] = None
    data: Optional[T] = None


class ErrorResponseModel(BaseModel, Generic[T]):
    status: str = "error"
    message: Optional[str] = None
    error: Optional[T] = None
