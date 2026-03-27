from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas import UserCreate, UserUpdate, UserResponse
from services import UserService

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
def list_users(company_id: str = None, skip: int = Query(default=0, ge=0), limit: int = Query(default=100, ge=1, le=200), db: Session = Depends(get_db)):
    """List all users with optional company filter"""
    return UserService.list_users(db, company_id, skip, limit)

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db)):
    """Get a specific user by ID"""
    user = UserService.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    try:
        return UserService.create_user(db, user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: str, user_update: UserUpdate, db: Session = Depends(get_db)):
    """Update a user"""
    try:
        user = UserService.update_user(db, user_id, user_update)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: str, db: Session = Depends(get_db)):
    """Delete a user"""
    try:
        if not UserService.delete_user(db, user_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))