from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy.orm import Session
from database import get_db
from services.strive_services import StripeService
from services.plan_service import PlanEnforcementService
from models import Company
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):

    payload = await request.body()
    sig_headers = request.headers.get("stripe-signature")

    if not sig_headers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header"
        )
    
    try:
        event = StripeService.verify_webhook(payload, sig_headers)
    except ValueError as e:
        logger.warning(f"Webhook verification failed: {e}")
        raise HTTPException(
            status_code= status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    event_type = event["type"]
    data = event["data"]["object"]

    logger.info(f"stripe webhook: {event_type} | ID {event['id']}")

    #try when every scenario above meet
    try:
        if event_type == "checkout.session.completed":
            _handle_checkout_completed(db, data)
        elif event_type == "invoice.paid":
            _handle_invoice_paid(db,data)
        elif event_type == "invoice.payment_failed":
            _handle_invoice_failed(db, data)
        elif event_type == "customer.subscription.updated":
            _handle_subscription_updated(db,data)
        elif event_type == "customer.subscription.deleted":
            _handle_subscription_deleted(db,data)
        else:
            logger.info(f"Unhandled event type: {event_type}")
    except Exception as e:
        logger.error(f"Error processing {event_type}: {e}", exc_info=True)

    return {"status":"ok"}

def _handle_checkout_completed(db:Session, session: dict):
    """
    checkout session completed/payment was successfull
    either subscription or credits.
    """

    metadata = session.get("metadata", {})
    checkout_type = metadata.get("type")
    company_id = metadata.get("chaindox_company_id")

    if not company_id:
        logger.warning(f"Checkout completed, no company id in meta data: {session['id']}")
        return

    company = db.query(Company).filter(Company.company_id == company_id).first()
    if not company:
        logger.error(f"Company was not found for checkout: {company_id}")
        return

    if checkout_type == "subscription":
        #activate
        _activate_subscription(db, company, session)
    elif checkout_type == "credit":
        #add credit
        _add_credits(db, company, session, metadata)
    else:
        logger.warning(f"Unknown checkout type: {checkout_type}")

def _activate_subscription(db:Session, company: Company, session: dict):
    subs_id = session.get("subscription")
    metadata = session.get("metadata", {})
    plan_id = metadata.get("plan_id")

    if subs_id:
        company.stripe_subscription_id = subs_id

    if plan_id:
        company.plan_id = int(plan_id)

    company.subscription_status = "active"
    company.updated_at = datetime.utcnow()

    db.commit()
    logger.info(f"Subscription activated for {company.company_id} | Stripe sub: {subs_id} | Plan: {plan_id}")

def _add_credits(db:Session, company:Company, session:dict, metadata:dict):
    user_id = metadata.get("chaindox_user_id")
    quantity = int(metadata.get("quantity", 0))
    payment_intent = session.get("payment_intent")

    if quantity <= 0:
        logger.error(f"Invalid credit quantity in checkout metadata: {quantity}")
        return
    
    try:
        PlanEnforcementService.purchase_credits(
            db=db,
            company_id=company.company_id,
            user_id=user_id,
            quantity=quantity,
            stripe_payment_intent_id=payment_intent
        )
        logger.info(f"credits added: {quantity} for {company.company_id} | payment intent: {payment_intent}")

    except ValueError as e:
        logger.error(f"failed to add credits for {company.company_id}: {e}")
def _handle_invoice_paid(db: Session, invoice: dict):
    customer_id = invoice.get("customer")
    subscription_id = invoice.get("subscription")
    
    company = db.query(Company).filter(
        Company.stripe_customer_id == customer_id
    ).first()
    
    if not company:
        logger.warning(f"No company for Stripe customer: {customer_id}")
        return
    
    # Ensure subscription is active
    if company.subscription_status != "active":
        company.subscription_status = "active"
    
    company.updated_at = datetime.utcnow()
    db.commit()
    
    logger.info(f"Invoice paid for {company.company_id} | Amount: {invoice.get('amount_paid')}")
 
 
def _handle_invoice_failed(db: Session, invoice: dict):
    customer_id = invoice.get("customer")
    
    company = db.query(Company).filter(
        Company.stripe_customer_id == customer_id
    ).first()
    
    if not company:
        logger.warning(f"No company for Stripe customer: {customer_id}")
        return
    
    company.subscription_status = "past_due"
    company.updated_at = datetime.utcnow()
    db.commit()
    
    logger.warning(
        f"Payment failed for {company.company_id} | "
        f"Invoice: {invoice.get('id')} | Status set to past_due"
    )
 
 
def _handle_subscription_updated(db: Session, subscription: dict):
    customer_id = subscription.get("customer")
    
    company = db.query(Company).filter(
        Company.stripe_customer_id == customer_id
    ).first()
    
    if not company:
        logger.warning(f"No company for Stripe customer: {customer_id}")
        return
    
    # Map Stripe status to our status
    stripe_status = subscription.get("status")
    status_map = {
        "active": "active",
        "past_due": "past_due",
        "canceled": "cancelled",
        "unpaid": "past_due",
        "trialing": "trial",
        "incomplete": "past_due",
        "incomplete_expired": "expired",
    }
    
    new_status = status_map.get(stripe_status, company.subscription_status)
    
    if subscription.get("cancel_at_period_end"):
        logger.info(f"Subscription cancellation pending for {company.company_id}")
    
    company.subscription_status = new_status
    company.stripe_subscription_id = subscription.get("id")
    company.updated_at = datetime.utcnow()
    
    db.commit()
    
    logger.info(
        f"Subscription updated for {company.company_id} | "
        f"Stripe status: {stripe_status} → ChainDoX status: {new_status}"
    )
 
 
def _handle_subscription_deleted(db: Session, subscription: dict):
    customer_id = subscription.get("customer")
    
    company = db.query(Company).filter(
        Company.stripe_customer_id == customer_id
    ).first()
    
    if not company:
        logger.warning(f"No company for Stripe customer: {customer_id}")
        return
    
    company.subscription_status = "cancelled"
    company.updated_at = datetime.utcnow()
    db.commit()
    
    logger.info(f"Subscription cancelled for {company.company_id}")