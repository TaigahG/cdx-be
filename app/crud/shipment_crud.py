from sqlalchemy.orm import Session
from models import Shipment, File
from typing import List, Optional

def get_shipment(db: Session, shipment_id: str) -> Optional[Shipment]:
    """Get shipment by ID"""
    return db.query(Shipment).filter(Shipment.shipment_id == shipment_id).first()

def get_shipments(
    db: Session, 
    company_id: str = None, 
    status: str = None,
    skip: int = 0, 
    limit: int = 100
) -> List[Shipment]:
    """Get all shipments with optional filters"""
    query = db.query(Shipment)
    
    if company_id:
        query = query.filter(Shipment.company_id == company_id)
    if status:
        query = query.filter(Shipment.status == status)
    
    return query.order_by(Shipment.created_at.desc()).offset(skip).limit(limit).all()

def create_shipment(db: Session, shipment_data: dict) -> Shipment:
    """Create a new shipment"""
    db_shipment = Shipment(**shipment_data)
    db.add(db_shipment)
    db.commit()
    db.refresh(db_shipment)
    return db_shipment

def update_shipment(db: Session, shipment_id: str, update_data: dict) -> Optional[Shipment]:
    """Update shipment"""
    db_shipment = get_shipment(db, shipment_id)
    if not db_shipment:
        return None
    
    for field, value in update_data.items():
        setattr(db_shipment, field, value)
    
    from datetime import datetime
    db_shipment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_shipment)
    return db_shipment

def delete_shipment(db: Session, shipment_id: str) -> bool:
    """Delete shipment"""
    db_shipment = get_shipment(db, shipment_id)
    if not db_shipment:
        return False
    
    db.delete(db_shipment)
    db.commit()
    return True

def get_shipment_file_count(db: Session, shipment_id: str) -> int:
    """Get count of files in shipment"""
    return db.query(File).filter(File.shipment_id == shipment_id).count()

def shipment_exists(db: Session, shipment_id: str) -> bool:
    """Check if shipment exists"""
    return get_shipment(db, shipment_id) is not None