from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas import CompanyCreate, CompanyUpdate, CompanyResponse
from services import CompanyService

router = APIRouter()

@router.get("/", response_model=List[CompanyResponse])
def list_companies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return CompanyService.list_companies(db, skip, limit)

@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(company_id: str, db: Session = Depends(get_db)):
    company = CompanyService.get_company(db, company_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="COMPANY NOT FOUND")
    return company

@router.post("/", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
def create_company(company_id: CompanyCreate, db: Session = Depends(get_db)):
    try:
        return CompanyService.create_company(db, company_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put("/{company_id}", response_model=CompanyResponse)
def update_company(company_id: str, company_update: CompanyUpdate, db: Session = Depends(get_db)):
    try:
        company = CompanyService.update_company(db, company_id, company_update)
        if not company:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="COMPANY NOT FOUND")
        return company
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
@router.delete("/{company_id}", response_model=CompanyResponse)
def delete_company(company_id:str, db: Session = Depends(get_db)):
    try:
        if not CompanyService.delete_company(db, company_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))