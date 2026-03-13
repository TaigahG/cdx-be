from sqlalchemy.orm import Session
import models
import schemas
from typing import Optional, List

def create_company(db: Session, company_data: dict) -> models.Company:
    db_company = models.Company(**company_data)
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

def get_company(db: Session, company_id: str) -> Optional[models.Company]:
    """Get a company"""
    return db.query(models.Company).filter(models.Company.company_id == company_id).first()

def get_companies(db: Session, skip: int=0, limit: int=100) -> List[models.Company]:
    """List of companies"""
    return db.query(models.Company).offset(skip).limit(limit).all()

def update_company(db: Session, company_id: str, update_data: dict) -> Optional[models.Company]:
    """Update company"""
    db_company = get_company(db, company_id)
    if not db_company:
        return None
    
    for field, value in update_data.items():
        setattr(db_company, field, value)
    
    from datetime import datetime
    db_company.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_company)
    return db_company

def delete_company(db: Session, company_id: str) -> bool:
    db_company = get_company(db, company_id)
    if not db_company:
        return False
    db.delete(db_company)
    db.commit()
    return True

def get_plan(db: Session, plan_id: int) -> Optional[models.Plan]:
    return db.query(models.Plan).filter(models.Plan.plan_id == plan_id).first()

def company_exists(db: Session, company_id: str) -> bool:
    return db.query(models.Company).filter(models.Company.company_id == company_id).first() is not None
