from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Plan
from schemas import PlanResponse

router = APIRouter()


@router.get("/", response_model=List[PlanResponse])
def get_plans(db: Session = Depends(get_db)):
    """Get all active plans, sorted by sort_order"""
    plans = db.query(Plan).filter(Plan.is_active == True).order_by(Plan.sort_order).all()
    return plans


@router.get("/{plan_id}", response_model=PlanResponse)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    """Get a specific plan by ID"""
    plan = db.query(Plan).filter(Plan.plan_id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return plan
