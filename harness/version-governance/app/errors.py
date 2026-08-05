import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError


SQLSTATE_ERRORS = {
    "VG409": (409, "IMMUTABLE_OBJECT"),
    "23514": (422, "VALIDATION_ERROR"),
    "23505": (409, "CONFLICT"),
}


logger = logging.getLogger(__name__)


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DBAPIError)
    async def database_error(_: Request, error: DBAPIError) -> JSONResponse:
        original = error.orig
        sqlstate = getattr(original, "sqlstate", None) or getattr(original, "pgcode", None)
        mapped = SQLSTATE_ERRORS.get(sqlstate)
        if mapped is None:
            # Chuỗi lỗi thô của psycopg thường kèm câu SQL, tên bảng/cột và cả giá trị tham số.
            # Với SQLSTATE chưa map thì log ở server, client chỉ nhận mã chung.
            logger.exception("Unmapped database error (sqlstate=%s)", sqlstate)
            return JSONResponse(status_code=500, content={"detail": {"code": "DATABASE_ERROR"}})
        status, code = mapped
        return JSONResponse(status_code=status, content={"detail": {"code": code, "message": str(original)}})
