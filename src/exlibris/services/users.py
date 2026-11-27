from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from exlibris.models import User
from exlibris.schemas import UserCreate
from exlibris.services.exceptions import DuplicateEmailError
from exlibris.services.security import hash_password


def create_user(session: Session, data: UserCreate) -> User:
    # is_admin is never taken from input: UserCreate has no such field, and admins are
    # granted only by the CLI command (#29).
    user = User(email=data.email, password_hash=hash_password(data.password))
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        # The UNIQUE constraint on email is the only one that can fail here, and it also
        # covers two concurrent registrations with the same address.
        session.rollback()
        raise DuplicateEmailError(data.email) from None
    session.refresh(user)
    return user
