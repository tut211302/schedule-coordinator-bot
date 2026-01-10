from sqlalchemy.orm import Session

from backend.models.user import User
from backend.schemas.user import UserCreate, UserGoogleAuth, UserUpdate


def get_user_by_line_user_id(db: Session, line_user_id: str) -> User | None:
    """Get user by LINE user ID"""
    return db.query(User).filter(User.line_user_id == line_user_id).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    """Get user by email (for backward compatibility)"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, user: UserCreate) -> User:
    """Create new user"""
    db_user = User(**user.model_dump(exclude_unset=True))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_or_update_user_by_line_id(
    db: Session,
    line_user_id: str,
    user_data: UserCreate | UserUpdate,
) -> User:
    """Create new user or update existing user by LINE user ID"""
    existing_user = get_user_by_line_user_id(db, line_user_id=line_user_id)

    if existing_user:
        # Update existing
        update_dict = user_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(existing_user, key, value)
        db.add(existing_user)
        db.commit()
        db.refresh(existing_user)
        return existing_user
    else:
        # Create new
        if isinstance(user_data, UserUpdate):
            user_data_dict = user_data.model_dump(exclude_unset=True)
            user_data_dict["line_user_id"] = line_user_id
            user_data = UserCreate(**user_data_dict)
        return create_user(db, user_data)


def update_user(db: Session, db_user: User, user_update: UserUpdate) -> User:
    """Update existing user"""
    update_data = user_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user_google_auth(db: Session, db_user: User, google_auth_data: UserGoogleAuth) -> User:
    """Update user with Google authentication data"""
    db_user.access_token = google_auth_data.access_token
    db_user.refresh_token = google_auth_data.refresh_token
    db_user.token_expiry = google_auth_data.token_expiry
    db_user.calendar_connected = google_auth_data.calendar_connected
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, db_user: User) -> None:
    """Delete user"""
    db.delete(db_user)
    db.commit()
