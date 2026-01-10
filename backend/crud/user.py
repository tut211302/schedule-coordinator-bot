from sqlalchemy.orm import Session

from backend.models.user import User
from backend.schemas.user import UserCreate, UserGoogleAuth, UserUpdate


def get_user_by_line_user_id(db: Session, line_user_id: str) -> User | None:
    return db.query(User).filter(User.line_user_id == line_user_id).first()


def create_user(db: Session, user: UserCreate) -> User:
    db_user = User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, db_user: User, user_update: UserUpdate) -> User:
    update_data = user_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user_google_auth(db: Session, db_user: User, google_auth_data: UserGoogleAuth) -> User:
    for key, value in google_auth_data.model_dump().items():
        setattr(db_user, key, value)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, db_user: User) -> None:
    db.delete(db_user)
    db.commit()
