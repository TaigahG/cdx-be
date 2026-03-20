# crud/folder_crud.py

from sqlalchemy.orm import Session
from models import Folder, File
from typing import List, Optional


def get_folder(db: Session, folder_id: int) -> Optional[Folder]:
    """Get folder by ID"""
    return db.query(Folder).filter(Folder.folder_id == folder_id).first()


def get_folders(
    db: Session,
    company_id: str = None,
    user_id: str = None,
    parent_folder_id: int = None,
    include_shared: bool = True,
    skip: int = 0,
    limit: int = 100
) -> List[Folder]:
    """Get folders with optional filters"""
    query = db.query(Folder)
    
    if company_id:
        query = query.filter(Folder.company_id == company_id)
    
    if user_id and include_shared:
        # Show user's own folders + shared folders in the company
        query = query.filter(
            (Folder.user_id == user_id) | (Folder.is_shared == True)
        )
    elif user_id:
        query = query.filter(Folder.user_id == user_id)
    
    if parent_folder_id is not None:
        query = query.filter(Folder.parent_folder_id == parent_folder_id)
    
    return query.order_by(Folder.name).offset(skip).limit(limit).all()


def get_root_folders(
    db: Session,
    company_id: str,
    user_id: str = None,
) -> List[Folder]:
    """Get top-level folders (no parent)"""
    query = db.query(Folder).filter(
        Folder.company_id == company_id,
        Folder.parent_folder_id == None,
    )
    
    if user_id:
        query = query.filter(
            (Folder.user_id == user_id) | (Folder.is_shared == True)
        )
    
    return query.order_by(Folder.name).all()


def create_folder(db: Session, folder_data: dict) -> Folder:
    """Create a new folder"""
    db_folder = Folder(**folder_data)
    db.add(db_folder)
    db.commit()
    db.refresh(db_folder)
    return db_folder


def update_folder(db: Session, folder_id: int, update_data: dict) -> Optional[Folder]:
    """Update folder"""
    db_folder = get_folder(db, folder_id)
    if not db_folder:
        return None
    
    for field, value in update_data.items():
        setattr(db_folder, field, value)
    
    from datetime import datetime
    db_folder.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_folder)
    return db_folder


def delete_folder(db: Session, folder_id: int) -> bool:
    """Delete folder"""
    db_folder = get_folder(db, folder_id)
    if not db_folder:
        return False
    
    db.delete(db_folder)
    db.commit()
    return True


def get_folder_file_count(db: Session, folder_id: int) -> int:
    """Get count of files in a folder"""
    return db.query(File).filter(File.folder_id == folder_id).count()


def get_child_folder_count(db: Session, folder_id: int) -> int:
    """Get count of child folders"""
    return db.query(Folder).filter(Folder.parent_folder_id == folder_id).count()