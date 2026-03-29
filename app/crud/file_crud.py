from sqlalchemy.orm import Session
from sqlalchemy import update, func
from models import File, DocumentVerification, DocCounter
from typing import List, Optional

def get_file(db: Session, file_id: int) -> Optional[File]:
    """Get file by ID"""
    return db.query(File).filter(File.file_id == file_id).first()

def get_files(
    db: Session,
    company_id: str = None,
    shipment_id: str = None,
    folder_id: int = None,
    document_type: str = None,
    is_verified: bool = None,
    skip: int = 0,
    limit: int = 100
) -> List[File]:
    """Get all files with optional filters"""
    query = db.query(File)
    
    if company_id:
        query = query.filter(File.company_id == company_id)
    if shipment_id:
        query = query.filter(File.shipment_id == shipment_id)
    if folder_id:
        query = query.filter(File.folder_id == folder_id)
    if document_type:
        query = query.filter(File.document_type == document_type)
    if is_verified is not None:
        query = query.filter(File.is_verified == is_verified)
    
    return query.order_by(File.created_at.desc()).offset(skip).limit(limit).all()

def create_file(db: Session, file_data: dict, document_type: str = None) -> File:
    """Create a new file"""
    db_file = File(**file_data)
    db.add(db_file)
    if document_type:

        counter = db.query(DocCounter).filter(DocCounter.document_type == document_type).first()
        
        if not counter:
            db.add(DocCounter(document_type=document_type, total_doc_created = 1, total_doc_verified = 0, total_doc_transferred=0))
        else:
            stmt = update(DocCounter).where(DocCounter.document_type == document_type).values(total_doc_created = DocCounter.total_doc_created+1)
            db.execute(stmt)
    db.commit()
    db.refresh(db_file)
    return db_file

def update_file(db: Session, file_id: int, update_data: dict) -> Optional[File]:
    """Update file"""
    db_file = get_file(db, file_id)
    if not db_file:
        return None
    
    for field, value in update_data.items():
        setattr(db_file, field, value)
    
    from datetime import datetime
    db_file.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_file)
    return db_file

def delete_file(db: Session, file_id: int) -> bool:
    """Delete file"""
    db_file = get_file(db, file_id)
    if not db_file:
        return False
    
    db.delete(db_file)
    db.commit()
    return True

def get_file_verifications(db: Session, file_id: int) -> List[DocumentVerification]:
    """Get all verifications for a file"""
    return db.query(DocumentVerification).filter(
        DocumentVerification.file_id == file_id
    ).order_by(DocumentVerification.verified_at.desc()).all()


def increment_doc_counter(db: Session, document_type: str, field: str):
    """Increment a specific counter field for a document type.
    field must be one of: total_doc_created, total_doc_verified, total_doc_transferred
    """
    counter = db.query(DocCounter).filter(DocCounter.document_type == document_type).first()
    if not counter:
        initial = {"document_type": document_type, "total_doc_created": 0, "total_doc_verified": 0, "total_doc_transferred": 0}
        initial[field] = 1
        db.add(DocCounter(**initial))
    else:
        stmt = update(DocCounter).where(
            DocCounter.document_type == document_type
        ).values({field: getattr(DocCounter, field) + 1})
        db.execute(stmt)
    db.commit()

def get_doc_counters(db: Session) -> List[DocCounter]:
    """Get all document counters"""
    return db.query(DocCounter).all()

def get_doc_counter_totals(db: Session) -> dict:
    """Get summed totals across all document types"""
    result = db.query(
        func.sum(DocCounter.total_doc_created),
        func.sum(DocCounter.total_doc_verified),
        func.sum(DocCounter.total_doc_transferred)
    ).first()
    return {
        "total_doc_created": result[0] or 0,
        "total_doc_verified": result[1] or 0,
        "total_doc_transferred": result[2] or 0
    }