import stripe
import os 
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from typing import Optional

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

class StripeService:

    @staticmethod
    def create_customer(
        company_id:str,
        company_name:str,
        billing_email:str
    ):
        
        customer = stripe.Customer.create(
            name=company_name,
            email=billing_email, 
            metadata={"chaindox_company_id": company_id,}
        )

        return customer.id
    
    @staticmethod
    def get_customer(
        stripe_cust_id:str
    ):
        return stripe.Customer.retrieve(stripe_cust_id)
    
    @staticmethod
    def update_customer(
        stripe_cust_id:str,
        name:str,
        email:str
    ) -> dict:
        update = {}

        if name:
            update["name"] = name
        if email:
            update["email"] = email

        
        if update:
            return stripe.Customer.modify(stripe_cust_id, **update)
        
        return None
    

    """
    SUBSCRIPTION 
    """

    @staticmethod
    def create_subscription_checkout(
        stripe_customer_id:str,
        stripe_price_id:str,
        company_id:str,
        success_url:str = None,
        cancel_url:str = None,
    ) -> dict:
        session = stripe.checkout.Session.create(
            customer=stripe_customer_id,
            mode="subscription",
            payment_method_types=["card"],
            line_items=[{
                "price":stripe_price_id,
                "quantity": 1
            }],
            metadata={
                "chaindox_company_id":company_id,
                "type":"subscription"
            },

            success_url=success_url or f"{FRONTEND_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=cancel_url or f"{FRONTEND_URL}/billing/cancelled",
            allow_promotion_codes=True,
            billing_address_collection="required",
            tax_id_collection={"enabled": True},
            customer_update={"name": "auto", "address":"auto"}
        )

        return{
            "session_id":session.id,
            "checkout_url":session.url
        }
    
    """
    CREDIT CHECKOUT
    """

    @staticmethod
    def create_credit_checkout(
        stripe_customer_id:str,
        company_id:str,
        user_id:str,
        quantity:int,
        unit_price_aud:float,
        plan_name:str = "Package Credit"
    ) -> dict:
        
        unit_amount = int(unit_price_aud * 100)

        session = stripe.checkout.Session.create(
            customer=stripe_customer_id,
            mode="payment",
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "aud",
                    "unit_amount": unit_amount,
                    "product_data": {
                        "name": f"ChainDoX {plan_name} — Package Credit",
                        "description": f"Overage package credit for additional shipments",
                    },
                },
                "quantity": quantity,
            }],
            metadata={
                "chaindox_company_id": company_id,
                "chaindox_user_id": user_id,
                "type": "credit",
                "quantity": str(quantity),
            },
            success_url=f"{FRONTEND_URL}/credits/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{FRONTEND_URL}/credits/cancelled",
        )
        
        return {
            "session_id": session.id,
            "checkout_url": session.url,
        }
    
    """
    SUBSCRIPTION MANAGEMENT
    """
    @staticmethod
    def get_subscription(stripe_subscription_id:str)->dict:
        return stripe.Subscription.retrieve(stripe_subscription_id)
    
    @staticmethod
    def cancel_subscription(
    stripe_subscription_id:str,
    at_period_end:bool = True
    ) -> dict:

        return stripe.Subscription.modify(stripe_subscription_id, cancel_at_period_end=at_period_end)
    
    @staticmethod
    def reactivate_subscription(
    stripe_subscription_id:str,
    ) -> dict:

        return stripe.Subscription.modify(stripe_subscription_id, cancel_at_period_end=False)
    
    @staticmethod
    def change_subscription_plan(
        stripe_subscription_id: str,
        new_stripe_price_id: str,
    ) -> dict:
        subscription = stripe.Subscription.retrieve(stripe_subscription_id)
        
        return stripe.Subscription.modify(
            stripe_subscription_id,
            items=[{
                "id": subscription["items"]["data"][0].id,
                "price": new_stripe_price_id,
            }],
            proration_behavior="create_prorations",
        )


    @staticmethod
    def create_billing_portal_session(
        stripe_customer_id: str,
        return_url: str = None,
    ) -> dict:
        """
        Create a Stripe Billing Portal session.
        
        Lets customers:
        - Update payment method
        - View invoices
        - Cancel subscription
        
        Returns: {portal_url} — frontend redirects to this.
        """
        session = stripe.billing_portal.Session.create(
            customer=stripe_customer_id,
            return_url=return_url or f"{FRONTEND_URL}/settings/billing",
        )
        
        return {
            "portal_url": session.url,
        }

    @staticmethod
    def verify_webhook(payload: bytes, sig_header: str) -> dict:
        """
        Verify and parse a Stripe webhook event.
        
        Args:
            payload: Raw request body bytes
            sig_header: Stripe-Signature header value
        
        Returns: Stripe event object
        Raises: ValueError if signature verification fails
        """
        webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        
        if not webhook_secret:
            raise ValueError("STRIPE_WEBHOOK_SECRET not configured")
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            return event
        except stripe.error.SignatureVerificationError:
            raise ValueError("Invalid webhook signature")
        
    @staticmethod
    def get_checkout_session(session_id: str) -> dict:
        """Retrieve a Checkout session (useful for verifying on success page)"""
        return stripe.checkout.Session.retrieve(
            session_id,
            expand=["subscription", "line_items"],
        )
 