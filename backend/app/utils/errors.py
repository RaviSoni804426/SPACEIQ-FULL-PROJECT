from __future__ import annotations

from fastapi import HTTPException


class AppError(HTTPException):
    def __init__(self, status_code: int, detail: str, code: str) -> None:
        super().__init__(status_code=status_code, detail=detail, headers={"X-Error-Code": code})


def api_error(status_code: int, detail: str, code: str) -> AppError:
    return AppError(status_code=status_code, detail=detail, code=code)
