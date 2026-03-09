from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas import FileCreate, FileUpdate, FileResponse
from services import FileService

router = APIRouter()

@router.get("/", response_model=List[FileResponse])
def list_documents(
    company_id: str = None,
    shipment_id: str = None,
    folder_id: int = None,
    document_type: str = None,
    is_verified: bool = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all documents with optional filters"""
    return FileService.list_files(
        db, company_id, shipment_id, folder_id, 
        document_type, is_verified, skip, limit
    )

@router.get("/{file_id}", response_model=FileResponse)
def get_document(file_id: int, db: Session = Depends(get_db)):
    """Get a specific document by ID"""
    file = FileService.get_file(db, file_id)
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return file

@router.post("/", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
def create_document(file: FileCreate, db: Session = Depends(get_db)):
    """Create a new document/file"""
    try:
        return FileService.create_file(db, file)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put("/{file_id}", response_model=FileResponse)
def update_document(file_id: int, file_update: FileUpdate, db: Session = Depends(get_db)):
    """Update a document"""
    try:
        file = FileService.update_file(db, file_id, file_update)
        if not file:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        return file
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(file_id: int, db: Session = Depends(get_db)):
    """Delete a document"""
    try:
        if not FileService.delete_file(db, file_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{file_id}/verification")
def get_document_verification(file_id: int, db: Session = Depends(get_db)):
    """Get document verification status and history"""
    try:
        return FileService.get_file_verification_history(db, file_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.patch("/{file_id}/verify")
def verify_document(file_id: int, is_verified: bool, db: Session = Depends(get_db)):
    """Update document verification status"""
    try:
        FileService.verify_file(db, file_id, is_verified)
        return {"message": "Document verification status updated", "is_verified": is_verified}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))