import asyncio
from datetime import datetime, timedelta

from fastapi import FastAPI

from app.api.dependencies import get_expired_server_stopper, get_expiry_notifier
from app.api.routes import admin, servers, users
from app.infrastructure.config.settings import settings

app = FastAPI(title=settings.app_name, version="0.1.0")

app.include_router(users.router)
app.include_router(admin.router)
app.include_router(servers.router)


async def _run_midnight_expiry_worker(app: FastAPI) -> None:
    stopper = get_expired_server_stopper()
    notifier = get_expiry_notifier()
    while True:
        now = datetime.utcnow()
        next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        sleep_seconds = max((next_midnight - now).total_seconds(), 0)
        await asyncio.sleep(sleep_seconds)
        notifier.notify()
        stopper.stop_expired()


@app.on_event("startup")
async def start_expiry_scheduler() -> None:
    app.state.expiry_task = asyncio.create_task(_run_midnight_expiry_worker(app))


@app.on_event("shutdown")
async def stop_expiry_scheduler() -> None:
    task = getattr(app.state, "expiry_task", None)
    if task:
        task.cancel()


@app.get("/healthz")
def healthcheck():
    return {"status": "ok", "environment": settings.environment}
