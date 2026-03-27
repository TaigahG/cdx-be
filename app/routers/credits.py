from fastapi import APIRouter, Depends, HTTPException, status, Query
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
    Check if user can perform a transfer.
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
    Check if user can perform a verification.
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
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must belong to a company"
        )
    
    if current_user.role not in ("owner", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners and admins can purchase credits"
        )
    
    from models import Company, Plan
    from services.strive_services import StripeService

    company = db.query(Company).filter(
        Company.company_id == current_user.company_id
    ).first()
    
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    
    plan = db.query(Plan).filter(Plan.plan_id == company.plan_id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Plan not found")
    
    # Validate: can they buy this many?
    try:
        credits = PlanEnforcementService._get_current_credits(db, company.company_id)
        purchasable = PlanEnforcementService._purchasable_credits(plan, credits)
        
        if purchasable is not None and purchase.quantity > purchasable:
            raise ValueError(f"Can only purchase {purchasable} more credits this period")
        
        if plan.max_overage_packages == 0:
            raise ValueError("Your plan does not allow overage purchases")
        
        if not plan.overage_price_per_shipment_aud:
            raise ValueError("No overage pricing defined for this plan")
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    # Create Stripe customer if needed
    if not company.stripe_customer_id:
        stripe_customer_id = StripeService.create_customer(
            company_id=company.company_id,
            company_name=company.company_name,
            billing_email=company.billing_email,
        )
        company.stripe_customer_id = stripe_customer_id
        db.commit()
    
    # Create Stripe Checkout session
    try:
        result = StripeService.create_credit_checkout(
            stripe_customer_id=company.stripe_customer_id,
            company_id=company.company_id,
            user_id=current_user.id,
            quantity=purchase.quantity,
            unit_price_aud=float(plan.overage_price_per_shipment_aud),
            plan_name=plan.plan_name,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create checkout session. Please try again.: {str(e)}"
        )


@router.get("/transactions")
def get_credit_transactions(
    skip: int = Query(default=0, ge=0),     
    limit: int = Query(default=50, ge=1, le=200),
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