from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas import AddressBookCreate, AddressBookUpdate, AddressBookResponse
from crud import address_book_crud
from auth.dependencies import get_current_user
from models import User

router = APIRouter()


@router.get("/", response_model=List[AddressBookResponse])
def list_contacts(
    contact_type: str = None,
    is_favorite: bool = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List address book contacts for the current user's company"""
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You must belong to a company")

    return address_book_crud.get_contacts(
        db, current_user.company_id, contact_type, is_favorite, skip, limit
    )


@router.get("/{contact_id}", response_model=AddressBookResponse)
def get_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific contact"""
    contact = address_book_crud.get_contact(db, contact_id)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    if contact.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return contact


@router.post("/", response_model=AddressBookResponse, status_code=status.HTTP_201_CREATED)
def create_contact(
    req: AddressBookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new address book contact"""
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You must belong to a company")

    data = req.model_dump()
    data["company_id"] = current_user.company_id
    data["created_by"] = current_user.id
    return address_book_crud.create_contact(db, data)


@router.put("/{contact_id}", response_model=AddressBookResponse)
def update_contact(
    contact_id: int,
    req: AddressBookUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an address book contact"""
    contact = address_book_crud.get_contact(db, contact_id)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    if contact.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    update_data = req.model_dump(exclude_unset=True)
    updated = address_book_crud.update_contact(db, contact_id, update_data)
    return updated


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an address book contact"""
    contact = address_book_crud.get_contact(db, contact_id)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    if contact.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    address_book_crud.delete_contact(db, contact_id)
