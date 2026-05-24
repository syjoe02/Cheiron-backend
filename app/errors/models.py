from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str
    status: int


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
