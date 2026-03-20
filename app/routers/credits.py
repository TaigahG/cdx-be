# routers/credits.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User
from auth.dependencies import get_current_user
from services.plan_service import PlanEnforcementService
from schemas import CreditPurchaseRequest

router = APIRouter()


@router.get("/balance")
def get_credit_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get current credit balance and usage for your company.
    Shows: included amounts, usage, remaining, purchasable credits.
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must belong to a company to view credits"
        )
    
    try:
        return PlanEnforcementService.get_credit_balance(db, current_user.company_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/check/shipment")
def check_shipment_limit(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Check if you can create a new shipment (package).
    Returns whether it's allowed and what action is needed if not.
    
    Frontend calls this before showing the "Create Shipment" form.
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must belong to a company"
        )
    
    try:
        return PlanEnforcementService.check_can_create_shipment(db, current_user.company_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/check/transfer")
def check_transfer_limit(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Check if you can perform a transfer.
    Transfers are hard-capped — if at limit, only option is upgrade.
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must belong to a company"
        )
    
    try:
        return PlanEnforcementService.check_can_transfer(db, current_user.company_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/check/verification")
def check_verification_limit(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Check if you can perform a verification.
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must belong to a company"
        )
    
    try:
        return PlanEnforcementService.check_can_verify(db, current_user.company_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/purchase")
def purchase_credits(
    purchase: CreditPurchaseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purchase package credits (overage).
    
    In production, the flow would be:
    1. Frontend calls POST /credits/purchase
    2. Backend creates Stripe PaymentIntent, returns client_secret
    3. Frontend completes payment with Stripe
    4. Stripe webhook confirms payment
    5. Backend adds credits
    
    For now (no Stripe yet), this directly adds credits.
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must belong to a company"
        )
    
    # Permission check — owner and admin can purchase
    if current_user.role not in ("owner", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners and admins can purchase credits"
        )
    
    try:
        result = PlanEnforcementService.purchase_credits(
            db=db,
            company_id=current_user.company_id,
            user_id=current_user.id,
            quantity=purchase.quantity,
            stripe_payment_intent_id=None,  # Will be set when Stripe is integrated
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/transactions")
def get_credit_transactions(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get credit purchase history for your company.
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must belong to a company"
        )
    
    from models import CreditTransaction
    
    transactions = db.query(CreditTransaction).filter(
        CreditTransaction.company_id == current_user.company_id
    ).order_by(
        CreditTransaction.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return {
        "company_id": current_user.company_id,
        "transactions": [
            {
                "transaction_id": t.transaction_id,
                "credit_type": t.credit_type,
                "quantity": t.quantity,
                "price_per_credit_aud": float(t.price_per_credit_aud),
                "total_price_aud": float(t.total_price_aud),
                "payment_status": t.payment_status,
                "created_at": t.created_at,
            }
            for t in transactions
        ],
    }