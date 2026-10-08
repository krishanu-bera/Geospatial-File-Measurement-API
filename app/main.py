"""FastAPI application factory."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.files import router as files_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db import init_db
from app.exceptions import AppError
from app.schemas import ErrorResponse


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    settings = get_settings()
    configure_logging(settings.log_level)
    init_db()

    app = FastAPI(
        title="Geospatial File Measurement API",
        description="Upload zipped Shapefiles or KML files and receive metric area and length measurements.",
        version="1.0.0",
        responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
    )

    if settings.cors_origin_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origin_list,
            allow_credentials=True,
            allow_methods=["GET", "POST"],
            allow_headers=["*"],
        )

    static_dir = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    app.include_router(files_router)

    @app.get("/", include_in_schema=False)
    async def index() -> FileResponse:
        """Serve the single-page web UI."""

        return FileResponse(static_dir / "index.html")

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        """Return service health."""

        return {"status": "ok"}

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "not_found" if exc.status_code == 404 else "http_error"
        message = exc.detail if isinstance(exc.detail, str) else "HTTP error."
        return JSONResponse(status_code=exc.status_code, content={"error": {"code": code, "message": message}})

    @app.exception_handler(HTTPException)
    async def fastapi_http_error_handler(_: Request, exc: HTTPException) -> JSONResponse:
        code = "not_found" if exc.status_code == 404 else "http_error"
        message = exc.detail if isinstance(exc.detail, str) else "HTTP error."
        return JSONResponse(status_code=exc.status_code, content={"error": {"code": code, "message": message}})

    return app


app = create_app()
