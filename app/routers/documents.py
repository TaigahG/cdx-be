from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List
import json
from database import get_db
from schemas import FileCreate, FileUpdate, FileResponse
from services import FileService

router = APIRouter()

@router.get("/analytics")
def get_document_analytics(db: Session = Depends(get_db)):
    """Get document counter analytics for admin dashboard"""
    return FileService.get_analytics(db)

@router.post("/counter/verified", status_code=status.HTTP_200_OK)
def increment_verified(document_type: str = Query(...), db: Session = Depends(get_db)):
    """Increment verified counter for a document type (called by external verify service)"""
    FileService.increment_verified(db, document_type)
    return {"message": f"Verified counter incremented for {document_type}"}

@router.post("/counter/transferred", status_code=status.HTTP_200_OK)
def increment_transferred(document_type: str = Query(...), db: Session = Depends(get_db)):
    """Increment transferred counter for a document type (called by external transfer service)"""
    FileService.increment_transferred(db, document_type)
    return {"message": f"Transferred counter incremented for {document_type}"}

@router.get("/", response_model=List[FileResponse])
def list_documents(
    company_id: str = None,
    shipment_id: str = None,
    folder_id: int = None,
    document_type: str = None,
    is_verified: bool = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """List all documents with optional filters"""
    return FileService.list_files(
        db, company_id, shipment_id, folder_id, 
        document_type, is_verified, skip, limit
    )

@router.get("/{file_id}/download")
def download_document(file_id: int, db: Session = Depends(get_db)):
    """
    Download the raw document_data as a .json file.
    Frontend creates a blob from this for the user to download.
    Key ordering is preserved since document_data is stored as JSON (not JSONB).
    """
    file = FileService.get_file(db, file_id)
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # Serialize with indent for readability, ensure_ascii=False for unicode
    content = json.dumps(file.document_data, indent=2, ensure_ascii=False)
    filename = file.name if file.name.endswith(".json") else f"{file.name}.json"

    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
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