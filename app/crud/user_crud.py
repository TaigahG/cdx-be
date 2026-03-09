from sqlalchemy.orm import Session
from models import User, Permission
from typing import List, Optional

def get_user(db: Session, user_id: str) -> Optional[User]:
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()

def get_users(db: Session, company_id: str = None, skip: int = 0, limit: int = 100) -> List[User]:
    """Get all users with optional company filter"""
    query = db.query(User)
    if company_id:
        query = query.filter(User.company_id == company_id)
    return query.offset(skip).limit(limit).all()

def create_user(db: Session, user_data: dict) -> User:
    """Create a new user"""
    db_user = User(**user_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: str, update_data: dict) -> Optional[User]:
    """Update user"""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    from datetime import datetime
    db_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: str) -> bool:
    """Delete user"""
    db_user = get_user(db, user_id)
    if not db_user:
        return False
    
    db.delete(db_user)
    db.commit()
    return True

def get_permission(db: Session, role: str) -> Optional[Permission]:
    """Get permission/role"""
    return db.query(Permission).filter(Permission.role == role).first()

def email_exists(db: Session, email: str) -> bool:
    """Check if email exists"""
    return get_user_by_email(db, email) is not None