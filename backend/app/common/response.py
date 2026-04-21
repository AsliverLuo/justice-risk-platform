from typing import Any

from pydantic import BaseModel


class ApiResponse(BaseModel):
    success: bool = True
    message: str = "ok"
    data: Any = None


def ok(data: Any = None, message: str = "ok") -> ApiResponse:
    return ApiResponse(success=True, message=message, data=data)
