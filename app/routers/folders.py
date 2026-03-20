# routers/folders.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas import FolderCreate, FolderUpdate, FolderResponse
from services.folder_service import FolderService
from models import User
from auth.dependencies import get_current_user

router = APIRouter()


@router.get("/", response_model=List[FolderResponse])
def list_folders(
    company_id: str = None,
    parent_folder_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List folders visible to the current user.
    Shows user's own folders + shared folders in their company.
    
    - No parent_folder_id → returns root-level folders
    - With parent_folder_id → returns children of that folder
    """
    cid = company_id or current_user.company_id
    
    if parent_folder_id is None:
        return FolderService.get_root_folders(db, cid, current_user.id)
    
    return FolderService.list_folders(
        db, cid, current_user.id, parent_folder_id, skip, limit
    )


@router.get("/{folder_id}", response_model=FolderResponse)
def get_folder(
    folder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific folder by ID"""
    folder = FolderService.get_folder(db, folder_id)
    if not folder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")
    
    # Check access — must be in the same company
    if folder.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    # Private folder — only the owner can see it
    if not folder.is_shared and folder.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This is a private folder")
    
    return folder


@router.post("/", response_model=FolderResponse, status_code=status.HTTP_201_CREATED)
def create_folder(
    folder: FolderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new folder.
    Automatically sets user_id and company_id from the authenticated user.
    """
    try:
        # Override with authenticated user's context
        folder_data = folder.model_dump()
        folder_data["user_id"] = current_user.id
        folder_data["company_id"] = current_user.company_id
        
        # Create using direct crud (we already validated via auth)
        from crud import folder_crud
        from models import Folder as FolderModel
        
        # Validate parent folder if provided
        if folder.parent_folder_id:
            parent = folder_crud.get_folder(db, folder.parent_folder_id)
            if not parent:
                raise ValueError(f"Parent folder with ID {folder.parent_folder_id} not found")
            if parent.company_id != current_user.company_id:
                raise ValueError("Parent folder belongs to a different company")
        
        return folder_crud.create_folder(db, folder_data)
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{folder_id}", response_model=FolderResponse)
def update_folder(
    folder_id: int,
    folder_update: FolderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a folder (rename, move, share/unshare, change color)"""
    try:
        # Check folder exists and user owns it
        folder = FolderService.get_folder(db, folder_id)
        if not folder:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")
        
        if folder.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the folder owner can edit it")
        
        updated = FolderService.update_folder(db, folder_id, folder_update)
        return updated
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_folder(
    folder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a folder — must be empty (no files or sub-folders)"""
    try:
        # Check folder exists and user owns it
        folder = FolderService.get_folder(db, folder_id)
        if not folder:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")
        
        if folder.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the folder owner can delete it")
        
        FolderService.delete_folder(db, folder_id)
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))