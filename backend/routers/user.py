from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend import crud, schemas
from backend.dependencies import get_db

router = APIRouter()


@router.post("/", response_model=schemas.user.User, status_code=status.HTTP_201_CREATED)
def create_new_user(user: schemas.user.UserCreate, db: Session = Depends(get_db)):
    """Create new user (by line_user_id or email)"""
    # Check for duplicate line_user_id if provided
    if user.line_user_id:
        existing = crud.user.get_user_by_line_user_id(db, line_user_id=user.line_user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="LINE user ID already registered",
            )

    # Check for duplicate email if provided
    if user.email:
        existing = crud.user.get_user_by_email(db, email=user.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    return crud.user.create_user(db=db, user=user)


@router.get("/{line_user_id}", response_model=schemas.user.User)
def read_user(line_user_id: str, db: Session = Depends(get_db)):
    """Get user by LINE user ID"""
    db_user = crud.user.get_user_by_line_user_id(db, line_user_id=line_user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user


@router.put("/{line_user_id}", response_model=schemas.user.User)
def update_existing_user(
    line_user_id: str, user_update: schemas.user.UserUpdate, db: Session = Depends(get_db)
):
    """Update user information by LINE user ID"""
    db_user = crud.user.get_user_by_line_user_id(db, line_user_id=line_user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return crud.user.update_user(db=db, db_user=db_user, user_update=user_update)


@router.delete("/{line_user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(line_user_id: str, db: Session = Depends(get_db)):
    """Delete user by LINE user ID"""
    db_user = crud.user.get_user_by_line_user_id(db, line_user_id=line_user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    crud.user.delete_user(db=db, db_user=db_user)
    return None
