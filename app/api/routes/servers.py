from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_server_provisioning, get_server_repository
from app.infrastructure.repositories.server_repository import ServerRepository
from app.interfaces.schemas import ServerCreate, ServerRead

router = APIRouter(prefix="/servers", tags=["servers"])


@router.post("", response_model=ServerRead)
def provision_server(
    payload: ServerCreate,
    provision = Depends(get_server_provisioning),
):
    try:
        server = provision.execute(user_id=payload.user_id, plan=payload.plan, location=payload.location)
        return ServerRead.from_entity(server)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/user/{user_id}", response_model=list[ServerRead])
def list_user_servers(user_id: UUID, repo: ServerRepository = Depends(get_server_repository)):
    servers = repo.list_for_user(user_id=user_id)
    return [ServerRead.from_entity(server) for server in servers]


@router.get("/{server_id}", response_model=ServerRead)
def get_server(server_id: UUID, repo: ServerRepository = Depends(get_server_repository)):
    server = repo.get(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return ServerRead.from_entity(server)
