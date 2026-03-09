from sqlalchemy.orm import Session
from crud import company_crud, user_crud
from schemas import CompanyCreate, CompanyUpdate
from typing import List, Optional
from models import Company

class CompanyService:
    """Business logic for companies"""
    
    @staticmethod
    def get_company(db: Session, company_id: str) -> Optional[Company]:
        """Get company by ID"""
        return company_crud.get_company(db, company_id)
    
    @staticmethod
    def list_companies(db: Session, skip: int = 0, limit: int = 100) -> List[Company]:
        """List all companies"""
        return company_crud.get_companies(db, skip, limit)
    
    @staticmethod
    def create_company(db: Session, company: CompanyCreate) -> Company:
        """Create company with validation"""
        
        if not company_crud.get_plan(db, company.plan_id):
            raise ValueError(f"Plan with ID {company.plan_id} not found")
        
        if company_crud.company_exists(db, company.company_id):
            raise ValueError(f"Company with ID {company.company_id} already exists")
        
        # Create company
        return company_crud.create_company(db, company.model_dump())
    
    @staticmethod
    def update_company(db: Session, company_id: str, company_update: CompanyUpdate) -> Optional[Company]:
        """Update company with validation"""
        
        if not company_crud.company_exists(db, company_id):
            raise ValueError(f"Company with ID {company_id} not found")
        
        update_data = company_update.model_dump(exclude_unset=True)
        return company_crud.update_company(db, company_id, update_data)
    
    @staticmethod
    def delete_company(db: Session, company_id: str) -> bool:
        """Delete company with validation"""
        
        if not company_crud.company_exists(db, company_id):
            raise ValueError(f"Company with ID {company_id} not found")
        
        users = user_crud.get_users(db, company_id=company_id, limit=1)
        if users:
            raise ValueError(f"Cannot delete company with active users")
        
        return company_crud.delete_company(db, company_id)
