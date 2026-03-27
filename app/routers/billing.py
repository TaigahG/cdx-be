# routers/billing.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from models import User, Company, Plan
from auth.dependencies import get_current_user
from services.strive_services import StripeService

router = APIRouter()


# ==========================================
# REQUEST SCHEMAS
# ==========================================

class SubscriptionCheckoutRequest(BaseModel):
    """Start a new subscription"""
    plan_id: int
    billing_period: str = "monthly"  # "monthly" or "annual"

class PlanChangeRequest(BaseModel):
    """Change to a different plan"""
    new_plan_id: int
    billing_period: str = "monthly"


# ==========================================
# SUBSCRIPTION CHECKOUT
# ==========================================

@router.post("/checkout/subscription")
def create_subscription_checkout(
    req: SubscriptionCheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a Stripe Checkout session for a new subscription.
    
    Returns a checkout_url — redirect the user there.
    After payment, Stripe sends a webhook → subscription goes active.
    
    Flow:
    1. Frontend calls this endpoint
    2. Backend creates Stripe Checkout session
    3. Frontend redirects to checkout_url
    4. User completes payment on Stripe's hosted page
    5. Stripe fires checkout.session.completed webhook
    6. Backend activates subscription
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must belong to a company"
        )
    
    if current_user.role not in ("owner", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners and admins can manage billing"
        )
    
    # Get company
    company = db.query(Company).filter(
        Company.company_id == current_user.company_id
    ).first()
    
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    
    # Get the target plan
    plan = db.query(Plan).filter(Plan.plan_id == req.plan_id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    
    # Get the right Stripe price ID
    if req.billing_period == "annual" and plan.stripe_price_id_annual:
        stripe_price_id = plan.stripe_price_id_annual
    else:
        stripe_price_id = plan.stripe_price_id_monthly
    
    if not stripe_price_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Plan '{plan.plan_name}' is not available for online checkout. Contact sales."
        )
    
    # Create Stripe customer if needed
    if not company.stripe_customer_id:
        stripe_customer_id = StripeService.create_customer(
            company_id=company.company_id,
            company_name=company.company_name,
            billing_email=company.billing_email,
        )
        company.stripe_customer_id = stripe_customer_id
        db.commit()
    
    # Create checkout session
    try:
        result = StripeService.create_subscription_checkout(
            stripe_customer_id=company.stripe_customer_id,
            stripe_price_id=stripe_price_id,
            company_id=company.company_id,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create checkout session. Please try again.: {str(e)}"
        )


# ==========================================
# PLAN CHANGES
# ==========================================

@router.post("/change-plan")
def change_plan(
    req: PlanChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Change subscription to a different plan.
    Stripe handles proration automatically.
    
    Only works if the company already has an active subscription.
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must belong to a company"
        )
    
    if current_user.role not in ("owner", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners and admins can manage billing"
        )
    
    company = db.query(Company).filter(
        Company.company_id == current_user.company_id
    ).first()
    
    if not company or not company.stripe_subscription_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active subscription to change. Use checkout to subscribe first."
        )
    
    # Get the new plan
    new_plan = db.query(Plan).filter(Plan.plan_id == req.new_plan_id).first()
    if not new_plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    
    # Get the right Stripe price ID
    if req.billing_period == "annual" and new_plan.stripe_price_id_annual:
        stripe_price_id = new_plan.stripe_price_id_annual
    else:
        stripe_price_id = new_plan.stripe_price_id_monthly
    
    if not stripe_price_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Plan '{new_plan.plan_name}' is not available for online billing. Contact sales."
        )
    
    try:
        result = StripeService.change_subscription_plan(
            stripe_subscription_id=company.stripe_subscription_id,
            new_stripe_price_id=stripe_price_id,
        )
        
        # Update our plan reference
        company.plan_id = new_plan.plan_id
        company.updated_at = __import__("datetime").datetime.utcnow()
        db.commit()
        
        return {
            "message": f"Plan changed to {new_plan.plan_name}",
            "new_plan_id": new_plan.plan_id,
            "new_plan_name": new_plan.plan_name,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change plan. Please try again."
        )


# ==========================================
# CANCEL / REACTIVATE
# ==========================================

@router.post("/cancel")
def cancel_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cancel subscription at end of current billing period.
    Company keeps access until the period ends.
    """
    if current_user.role not in ("owner",):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can cancel the subscription"
        )
    
    company = db.query(Company).filter(
        Company.company_id == current_user.company_id
    ).first()
    
    if not company or not company.stripe_subscription_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active subscription to cancel"
        )
    
    try:
        StripeService.cancel_subscription(company.stripe_subscription_id)
        return {"message": "Subscription will cancel at end of current billing period"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription. Please try again."
        )


@router.post("/reactivate")
def reactivate_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Undo a pending cancellation — keep the subscription active.
    Only works if the subscription hasn't actually ended yet.
    """
    if current_user.role not in ("owner", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners and admins can manage billing"
        )
    
    company = db.query(Company).filter(
        Company.company_id == current_user.company_id
    ).first()
    
    if not company or not company.stripe_subscription_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No subscription to reactivate"
        )
    
    try:
        StripeService.reactivate_subscription(company.stripe_subscription_id)
        
        company.subscription_status = "active"
        db.commit()
        
        return {"message": "Subscription reactivated"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reactivate subscription. Please try again."
        )


# ==========================================
# BILLING PORTAL
# ==========================================

@router.post("/portal")
def create_billing_portal(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Open Stripe's hosted billing portal.
    
    Lets the customer:
    - Update payment method (card details)
    - View and download invoices
    - View subscription details
    
    Returns portal_url — redirect the user there.
    """
    if current_user.role not in ("owner", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners and admins can access billing"
        )
    
    company = db.query(Company).filter(
        Company.company_id == current_user.company_id
    ).first()
    
    if not company or not company.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No billing account found. Subscribe to a plan first."
        )
    
    try:
        result = StripeService.create_billing_portal_session(company.stripe_customer_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to open billing portal. Please try again."
        )


# ==========================================
# SUBSCRIPTION STATUS
# ==========================================

@router.get("/status")
def get_billing_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get current billing/subscription status.
    Frontend uses this for the billing settings page.
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must belong to a company"
        )
    
    company = db.query(Company).filter(
        Company.company_id == current_user.company_id
    ).first()
    
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    
    plan = db.query(Plan).filter(Plan.plan_id == company.plan_id).first()
    
    # Get live Stripe subscription info if available
    stripe_info = None
    if company.stripe_subscription_id:
        try:
            sub = StripeService.get_subscription(company.stripe_subscription_id)
            stripe_info = {
                "status": sub.get("status"),
                "current_period_end": sub.get("current_period_end"),
                "cancel_at_period_end": sub.get("cancel_at_period_end"),
                "cancel_at": sub.get("cancel_at"),
            }
        except Exception:
            stripe_info = None
    
    return {
        "company_id": company.company_id,
        "plan_name": plan.plan_name if plan else "Unknown",
        "plan_id": company.plan_id,
        "subscription_status": company.subscription_status,
        "subscription_started": company.subscription_started,
        "trial_ends_at": company.trial_ends_at,
        "next_billing_date": company.next_billing_date,
        "has_stripe_customer": company.stripe_customer_id is not None,
        "has_active_subscription": company.stripe_subscription_id is not None,
        "stripe": stripe_info,
    }