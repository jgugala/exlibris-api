from fastapi import APIRouter, HTTPException, status

from exlibris.dependencies import SessionDep
from exlibris.models import User
from exlibris.schemas import UserCreate, UserRead
from exlibris.services import users as users_service
from exlibris.services.exceptions import DuplicateEmailError

router = APIRouter(prefix="/auth", tags=["auth"])


# response_model=UserRead filters the returned User: password_hash is not a UserRead
# field, so it never reaches the response even though the ORM object has it.
@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserRead)
def register(data: UserCreate, session: SessionDep) -> User:
    try:
        return users_service.create_user(session, data)
    except DuplicateEmailError as exc:
        # This reveals that the address has an account. Accepted for registration, where
        # hiding it would mean an email confirmation flow, which is out of scope.
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from None
