# services/folder_service.py

from sqlalchemy.orm import Session
from crud import folder_crud, company_crud, user_crud
from schemas import FolderCreate, FolderUpdate
from typing import List, Optional
from models import Folder


class FolderService:
    """Business logic for folders"""
    
    @staticmethod
    def get_folder(db: Session, folder_id: int) -> Optional[Folder]:
        """Get folder by ID"""
        return folder_crud.get_folder(db, folder_id)
    
    @staticmethod
    def list_folders(
        db: Session,
        company_id: str = None,
        user_id: str = None,
        parent_folder_id: int = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Folder]:
        """List folders visible to the user"""
        return folder_crud.get_folders(
            db, company_id, user_id, parent_folder_id,
            include_shared=True, skip=skip, limit=limit
        )
    
    @staticmethod
    def get_root_folders(db: Session, company_id: str, user_id: str = None) -> List[Folder]:
        """Get top-level folders"""
        return folder_crud.get_root_folders(db, company_id, user_id)
    
    @staticmethod
    def create_folder(db: Session, folder: FolderCreate) -> Folder:
        """Create folder with validation"""
        
        # Validate company exists
        if not company_crud.company_exists(db, folder.company_id):
            raise ValueError(f"Company with ID {folder.company_id} not found")
        
        # Validate user exists
        if not user_crud.get_user(db, folder.user_id):
            raise ValueError(f"User with ID {folder.user_id} not found")
        
        # Validate parent folder exists (if nesting)
        if folder.parent_folder_id:
            parent = folder_crud.get_folder(db, folder.parent_folder_id)
            if not parent:
                raise ValueError(f"Parent folder with ID {folder.parent_folder_id} not found")
            # Ensure parent belongs to same company
            if parent.company_id != folder.company_id:
                raise ValueError("Parent folder belongs to a different company")
        
        return folder_crud.create_folder(db, folder.model_dump())
    
    @staticmethod
    def update_folder(db: Session, folder_id: int, folder_update: FolderUpdate) -> Optional[Folder]:
        """Update folder with validation"""
        
        db_folder = folder_crud.get_folder(db, folder_id)
        if not db_folder:
            raise ValueError(f"Folder with ID {folder_id} not found")
        
        # If moving to a new parent, validate it
        update_data = folder_update.model_dump(exclude_unset=True)
        if 'parent_folder_id' in update_data and update_data['parent_folder_id'] is not None:
            # Can't be its own parent
            if update_data['parent_folder_id'] == folder_id:
                raise ValueError("A folder cannot be its own parent")
            
            parent = folder_crud.get_folder(db, update_data['parent_folder_id'])
            if not parent:
                raise ValueError(f"Parent folder with ID {update_data['parent_folder_id']} not found")
            if parent.company_id != db_folder.company_id:
                raise ValueError("Parent folder belongs to a different company")
        
        return folder_crud.update_folder(db, folder_id, update_data)
    
    @staticmethod
    def delete_folder(db: Session, folder_id: int) -> bool:
        """Delete folder with validation — must be empty"""
        
        db_folder = folder_crud.get_folder(db, folder_id)
        if not db_folder:
            raise ValueError(f"Folder with ID {folder_id} not found")
        
        # Check for files inside
        file_count = folder_crud.get_folder_file_count(db, folder_id)
        if file_count > 0:
            raise ValueError(f"Cannot delete folder with {file_count} documents. Move or delete them first.")
        
        # Check for child folders
        child_count = folder_crud.get_child_folder_count(db, folder_id)
        if child_count > 0:
            raise ValueError(f"Cannot delete folder with {child_count} sub-folders. Delete them first.")
        
        return folder_crud.delete_folder(db, folder_id)