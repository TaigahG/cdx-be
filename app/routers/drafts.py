# routers/drafts.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User
from auth.dependencies import get_current_user
from services.draft_service import DraftService
from schemas import DocumentDraftSave

router = APIRouter()


@router.post("/")
def save_draft(
    draft: DocumentDraftSave,
    current_user: User = Depends(get_current_user),
):
    """
    Save a document draft to Redis.
    
    Use this when the user is filling out a document form and wants to
    save their progress without submitting. The draft auto-expires after 24 hours.
    
    If a draft already exists for this shipment + document_type, it gets overwritten.
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must belong to a company"
        )
    
    return DraftService.save_draft(
        company_id=current_user.company_id,
        user_id=current_user.id,
        shipment_id=draft.shipment_id,
        document_type=draft.document_type,
        form_data=draft.form_data,
    )


@router.get("/{shipment_id}/{document_type}")
def get_draft(
    shipment_id: str,
    document_type: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific draft for a shipment + document type.
    
    Frontend calls this when the user opens a document form to check
    if there's saved progress to restore.
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must belong to a company"
        )
    
    draft = DraftService.get_draft(
        company_id=current_user.company_id,
        user_id=current_user.id,
        shipment_id=shipment_id,
        document_type=document_type,
    )
    
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No draft found (may have expired)"
        )
    
    return draft


@router.get("/{shipment_id}")
def get_shipment_drafts(
    shipment_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get all drafts for a shipment.
    
    Frontend calls this when the user opens a shipment to show
    which documents have in-progress drafts.
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must belong to a company"
        )
    
    return DraftService.get_shipment_drafts(
        company_id=current_user.company_id,
        user_id=current_user.id,
        shipment_id=shipment_id,
    )


@router.delete("/{shipment_id}/{document_type}")
def delete_draft(
    shipment_id: str,
    document_type: str,
    current_user: User = Depends(get_current_user),
):
    """
    Delete a specific draft.
    
    Called after the user finalizes and submits the document to PostgreSQL.
    Also called if the user explicitly discards their draft.
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must belong to a company"
        )
    
    deleted = DraftService.delete_draft(
        company_id=current_user.company_id,
        user_id=current_user.id,
        shipment_id=shipment_id,
        document_type=document_type,
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No draft found to delete"
        )
    
    return {"message": f"Draft deleted for {document_type}"}


@router.delete("/{shipment_id}")
def delete_shipment_drafts(
    shipment_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Delete all drafts for a shipment.
    
    Called when a shipment is finalized or cancelled.
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must belong to a company"
        )
    
    deleted = DraftService.delete_shipment_drafts(
        company_id=current_user.company_id,
        user_id=current_user.id,
        shipment_id=shipment_id,
    )
    
    return {
        "message": f"Deleted {deleted} draft(s) for shipment {shipment_id}",
        "deleted_count": deleted,
    }