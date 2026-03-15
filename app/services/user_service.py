from sqlalchemy.orm import Session
from crud import user_crud, company_crud
from schemas import UserCreate, UserUpdate
from typing import List, Optional
from models import User
from passlib.context import CryptContext
from utils import generate_user_id
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    """Business logic for users"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password"""
        return pwd_context.hash(password)
    
    @staticmethod
    def get_user(db: Session, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return user_crud.get_user(db, user_id)
    
    @staticmethod
    def list_users(db: Session, company_id: str = None, skip: int = 0, limit: int = 100) -> List[User]:
        """List all users"""
        return user_crud.get_users(db, company_id, skip, limit)
    
    @staticmethod
    def create_user(db: Session, user: UserCreate) -> User:
        """Create user with validation"""
        
        # Validate company exists
        if not company_crud.company_exists(db, user.company_id):
            raise ValueError(f"Company with ID {user.company_id} not found")
        
        # Validate role/permission exists
        if not user_crud.get_permission(db, user.role):
            raise ValueError(f"Role {user.role} not found")
        
        # Check if email already exists
        if user_crud.email_exists(db, user.email):
            raise ValueError(f"User with email {user.email} already exists")
        
        # Hash password
        user_data = user.model_dump()
        user_data['password_hash'] = UserService.hash_password(user_data.pop('password'))
        user_data['id'] = generate_user_id(user_data['email'], db)
        
        # Create user
        return user_crud.create_user(db, user_data)
    
    @staticmethod
    def update_user(db: Session, user_id: str, user_update: UserUpdate) -> Optional[User]:
        """Update user with validation"""
        
        # Check user exists
        if not user_crud.get_user(db, user_id):
            raise ValueError(f"User with ID {user_id} not found")
        
        # Prepare update data
        update_data = user_update.model_dump(exclude_unset=True)
        
        # Hash password if provided
        if 'password' in update_data:
            update_data['password_hash'] = UserService.hash_password(update_data.pop('password'))
        
        # Update user
        return user_crud.update_user(db, user_id, update_data)
    
    @staticmethod
    def delete_user(db: Session, user_id: str) -> bool:
        """Delete user"""
        
        # Check user exists
        if not user_crud.get_user(db, user_id):
            raise ValueError(f"User with ID {user_id} not found")
        
        # Delete user
        return user_crud.delete_user(db, user_id)
