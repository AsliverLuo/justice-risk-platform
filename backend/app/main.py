from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logger import setup_logging
from app.db.session import init_db


setup_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
    lifespan=lifespan,
)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get('/health')
def health() -> dict:
    return {
        'status': 'ok',
        'app': settings.app_name,
        'env': settings.app_env,
    }


if __name__ == '__main__':
    import uvicorn

    uvicorn.run('app.main:app', host='0.0.0.0', port=8000, reload=True)
