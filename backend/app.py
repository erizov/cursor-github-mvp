from fastapi import FastAPI, Request
from prometheus_fastapi_instrumentator import Instrumentator
from backend.logging_config import configure_logging, get_logger
from backend.routers.recommendations import router as recommendations_router
from backend.routers.reports import router as reports_router
from backend.routers.index import router as index_router


def create_app() -> FastAPI:
    configure_logging()
    log = get_logger("app")
    app = FastAPI(title="AI Algorithm Teacher API", version="1.0.0")
    
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        response = None
        try:
            response = await call_next(request)
            log.info(
                "request",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                client=getattr(request.client, "host", None),
            )
            return response
        except Exception:
            log.exception("unhandled_error", method=request.method, path=request.url.path)
            raise
    app.include_router(index_router)
    app.include_router(recommendations_router, prefix="/api")
    app.include_router(reports_router, prefix="/api")
    Instrumentator().instrument(app).expose(app)
    return app


app = create_app()


