from sqlalchemy.orm import Session
from . import models, schemas
from typing import Optional, List

def creat_company(db: Session, company: schemas.CompanyCreate) -> models.Company:
    db_company = models.Company(**company.dict())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

def get_company(db: Session, company_id: str) -> Optional[models.Company]:
    """Get a company"""
    return db.query(models.Company).filter(models.Company.company_id == company_id).first()
def get_companie(db: Session, skip: int=0, limit: int=100) -> List[models.Company]:
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