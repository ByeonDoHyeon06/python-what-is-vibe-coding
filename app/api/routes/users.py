from fastapi import APIRouter, Depends

from app.api.dependencies import get_user_registration, get_user_repository
from app.infrastructure.repositories.user_repository import UserRepository
from app.interfaces.schemas import UserCreate, UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead)
def register_user(
    payload: UserCreate,
    register = Depends(get_user_registration),
):
    user = register.execute(email=payload.email, phone_number=payload.phone_number)
    return UserRead.from_entity(user)


@router.get("", response_model=list[UserRead])
def list_users(user_repo: UserRepository = Depends(get_user_repository)):
    return [UserRead.from_entity(user) for user in user_repo.list()]
