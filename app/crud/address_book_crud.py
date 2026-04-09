from sqlalchemy.orm import Session
from models import AddressBook
from typing import List, Optional
from datetime import datetime


def get_contact(db: Session, contact_id: int) -> Optional[AddressBook]:
    return db.query(AddressBook).filter(AddressBook.contact_id == contact_id).first()


def get_contacts(
    db: Session,
    company_id: str,
    contact_type: str = None,
    is_favorite: bool = None,
    skip: int = 0,
    limit: int = 100,
) -> List[AddressBook]:
    query = db.query(AddressBook).filter(AddressBook.company_id == company_id)

    if contact_type:
        query = query.filter(AddressBook.contact_type == contact_type)
    if is_favorite is not None:
        query = query.filter(AddressBook.is_favorite == is_favorite)

    return query.order_by(AddressBook.name).offset(skip).limit(limit).all()


def create_contact(db: Session, data: dict) -> AddressBook:
    contact = AddressBook(**data)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


def update_contact(db: Session, contact_id: int, update_data: dict) -> Optional[AddressBook]:
    contact = get_contact(db, contact_id)
    if not contact:
        return None

    for field, value in update_data.items():
        setattr(contact, field, value)

    contact.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(contact)
    return contact


def delete_contact(db: Session, contact_id: int) -> bool:
    contact = get_contact(db, contact_id)
    if not contact:
        return False

    db.delete(contact)
    db.commit()
    return True
