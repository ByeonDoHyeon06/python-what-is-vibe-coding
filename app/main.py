from fastapi import FastAPI

from app.api.routes import admin, servers, users
from app.infrastructure.config.settings import settings

app = FastAPI(title=settings.app_name, version="0.1.0")

app.include_router(admin.router)
app.include_router(users.router)
app.include_router(servers.router)


@app.get("/healthz")
def healthcheck():
    return {"status": "ok", "environment": settings.environment}
