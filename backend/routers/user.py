from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from crud import user as crud_user
from schemas import user as schemas_user
from dependencies import get_db

router = APIRouter()


@router.post("/", response_model=schemas_user.User, status_code=status.HTTP_201_CREATED)
def create_new_user(user: schemas_user.UserCreate, db: Session = Depends(get_db)):
    """Create new user (by line_user_id or email)"""
    # Check for duplicate line_user_id if provided
    if user.line_user_id:
        existing = crud_user.get_user_by_line_user_id(db, line_user_id=user.line_user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="LINE user ID already registered",
            )

    # Check for duplicate email if provided
    if user.email:
        existing = crud_user.get_user_by_email(db, email=user.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    return crud_user.create_user(db=db, user=user)


@router.get("/{line_user_id}", response_model=schemas_user.User)
def read_user(line_user_id: str, db: Session = Depends(get_db)):
    """Get user by LINE user ID"""
    db_user = crud_user.get_user_by_line_user_id(db, line_user_id=line_user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user


@router.put("/{line_user_id}", response_model=schemas_user.User)
def update_existing_user(
    line_user_id: str, user_update: schemas_user.UserUpdate, db: Session = Depends(get_db)
):
    """Update user information by LINE user ID"""
    db_user = crud_user.get_user_by_line_user_id(db, line_user_id=line_user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return crud_user.update_user(db=db, db_user=db_user, user_update=user_update)


@router.delete("/{line_user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(line_user_id: str, db: Session = Depends(get_db)):
    """Delete user by LINE user ID"""
    db_user = crud_user.get_user_by_line_user_id(db, line_user_id=line_user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    crud_user.delete_user(db=db, db_user=db_user)
    return None


@router.post("/api/line/link", response_model=schemas_user.User, status_code=status.HTTP_200_OK)
def line_liff_register(user: schemas_user.UserCreate, db: Session = Depends(get_db)):
    """
    LIFF アプリから line_user_id を使用してユーザーを登録・更新.
    既存ユーザーの場合はプロフィール情報を更新、新規の場合は作成.
    
    Request body:
        {
            "line_user_id": "U1234567890",
            "display_name": "太郎",
            "picture_url": "https://...",
            "status_message": "..."
        }
    """
    if not user.line_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="line_user_id is required",
        )

    # Create or update user by line_user_id
    db_user = crud_user.create_or_update_user_by_line_id(db, line_user_id=user.line_user_id, user_data=user)
    return db_user
    return None
