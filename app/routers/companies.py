# routers/companies.py

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas import CompanyCreate, CompanyUpdate, CompanyResponse, UserInvite
from services import CompanyService
from models import User
from auth.dependencies import get_current_user

router = APIRouter()


@router.get("/", response_model=List[CompanyResponse])
def list_companies(skip: int = Query(default=0, ge=0), limit: int = Query(default=100, ge=1, le=200), db: Session = Depends(get_db)):
    return CompanyService.list_companies(db, skip, limit)


@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(company_id: str, db: Session = Depends(get_db)):
    company = CompanyService.get_company(db, company_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return company


@router.post("/", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
def create_company(
    company: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        if current_user.company_id is not None:
            raise ValueError("You already belong to a company")
        
        new_company = CompanyService.create_company(db, company)
        
        new_company.created_by = current_user.id
        
        # Assign user as owner of this company
        current_user.company_id = new_company.company_id
        current_user.role = "owner"
        current_user.is_owner = True
        db.commit()
        
        return new_company
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put("/{company_id}", response_model=CompanyResponse)
def update_company(company_id: str, company_update: CompanyUpdate, db: Session = Depends(get_db)):
    try:
        company = CompanyService.update_company(db, company_id, company_update)
        if not company:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
        return company
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(company_id: str, db: Session = Depends(get_db)):
    try:
        if not CompanyService.delete_company(db, company_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{company_id}/invite", status_code=status.HTTP_201_CREATED)
def invite_user(
    company_id: str,
    invite: UserInvite,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        from models import Company
        company = db.query(Company).filter(Company.company_id == company_id).first()
        if not company:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")


        if current_user.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't belong to this company"
            )
        
        if current_user.role not in ("owner", "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owners and admins can invite users"
            )
        
        if invite.role == "owner":
            raise ValueError("Cannot invite someone as owner. Use admin role instead.")
        
        from datetime import datetime
        from models import Plan
        plan =  db.query(Plan).filter(Plan.plan_id == company.plan_id).first()
        existing = db.query(User).filter(User.email == invite.email).first()


        if plan and plan.max_users is not None:
            current_user_count = db.query(User).filter(User.company_id == company_id, User.is_active == True).count()

            if current_user_count >= plan.max_users:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"User limit reached ({current_user_count}/{plan.max_users}). Upgrade your plan to invite more members."
                )
            
        if existing:
            if existing.company_id == company_id:
                raise ValueError(f"{invite.email} is already a member of this company")
            
            if existing.company_id is not None:
                raise ValueError(f"{invite.email} already belongs to another company")
            
            existing.company_id = company_id
            existing.role = invite.role
            existing.first_name = invite.first_name or existing.first_name
            existing.last_name = invite.last_name or existing.last_name
            existing.invited_by = current_user.id
            existing.invited_at = datetime.utcnow()
            existing.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            
            return {
                "message": f"{invite.email} has been added to your company",
                "user_id": existing.id,
                "email": existing.email,
                "role": existing.role,
                "company_id": company_id,
                "was_existing_user": True,
            }
        
        from utils import generate_user_id
        user_id = generate_user_id(invite.email, db)
        
        invited_user = User(
            id=user_id,
            company_id=company_id,
            email=invite.email,
            username=invite.email.split("@")[0],
            first_name=invite.first_name,
            last_name=invite.last_name,
            role=invite.role,
            is_owner=False,
            is_active=True,
            invited_by=current_user.id,
            invited_at=datetime.utcnow(),
            joined_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(invited_user)
        db.commit()
        db.refresh(invited_user)
        
        return {
            "message": f"Invitation created for {invite.email}",
            "user_id": invited_user.id,
            "email": invited_user.email,
            "role": invited_user.role,
            "company_id": company_id,
            "was_existing_user": False,
            "note": "User can now log in with Magic Link using this email",
        }
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))