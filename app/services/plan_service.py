# services/plan_enforcement_service.py

from sqlalchemy.orm import Session
from models import Company, Plan, CompanyUsage, CompanyCredits
from datetime import date, datetime


class PlanEnforcementService:
    """
    Checks plan limits before allowing actions.
    Called by other services before creating shipments, transfers, etc.
    """
    
    @staticmethod
    def _get_company_plan(db: Session, company_id: str) -> tuple:
        """Get company and its plan"""
        company = db.query(Company).filter(Company.company_id == company_id).first()
        if not company:
            raise ValueError(f"Company {company_id} not found")
        
        plan = db.query(Plan).filter(Plan.plan_id == company.plan_id).first()
        if not plan:
            raise ValueError(f"Plan not found for company {company_id}")
        
        return company, plan
    
    @staticmethod
    def _get_current_usage(db: Session, company_id: str) -> CompanyUsage:
        """Get or create usage record for current billing period"""
        today = date.today()
        
        usage = db.query(CompanyUsage).filter(
            CompanyUsage.company_id == company_id,
            CompanyUsage.billing_period_start <= today,
            CompanyUsage.billing_period_end >= today,
        ).first()
        
        if not usage:
            # Create usage record for this period (first day of month to last day)
            from calendar import monthrange
            period_start = today.replace(day=1)
            _, last_day = monthrange(today.year, today.month)
            period_end = today.replace(day=last_day)
            
            usage = CompanyUsage(
                company_id=company_id,
                billing_period_start=period_start,
                billing_period_end=period_end,
            )
            db.add(usage)
            db.commit()
            db.refresh(usage)
        
        return usage
    
    @staticmethod
    def _get_current_credits(db: Session, company_id: str) -> CompanyCredits:
        """Get or create credits record for current billing period"""
        today = date.today()
        
        credits = db.query(CompanyCredits).filter(
            CompanyCredits.company_id == company_id,
            CompanyCredits.billing_period_start <= today,
            CompanyCredits.billing_period_end >= today,
        ).first()
        
        if not credits:
            from calendar import monthrange
            period_start = today.replace(day=1)
            _, last_day = monthrange(today.year, today.month)
            period_end = today.replace(day=last_day)
            
            credits = CompanyCredits(
                company_id=company_id,
                billing_period_start=period_start,
                billing_period_end=period_end,
            )
            db.add(credits)
            db.commit()
            db.refresh(credits)
        
        return credits
    
    # ===== SHIPMENT (PACKAGE) CHECKS =====
    
    @staticmethod
    def check_can_create_shipment(db: Session, company_id: str) -> dict:
        """
        Check if company can create a new shipment.
        
        Returns:
            {
                "allowed": True/False,
                "reason": "free" / "credit_deducted" / "buy_credits" / "upgrade",
                "message": "Human readable message",
                "credits_remaining": int,
                "can_purchase": int,  # how many more credits they can buy
                "price_per_credit": Decimal or None,
            }
        """
        company, plan = PlanEnforcementService._get_company_plan(db, company_id)
        usage = PlanEnforcementService._get_current_usage(db, company_id)
        credits = PlanEnforcementService._get_current_credits(db, company_id)
        
        # Unlimited packages (e.g. Government contract)
        if plan.included_shipments is None:
            return {
                "allowed": True,
                "reason": "free",
                "message": "Unlimited packages on your plan",
                "credits_remaining": credits.package_credits_remaining,
                "can_purchase": None,
                "price_per_credit": plan.overage_price_per_shipment_aud,
            }
        
        if usage.shipments_created < plan.included_shipments:
            return {
                "allowed": True,
                "reason": "free",
                "message": f"Package {usage.shipments_created + 1} of {plan.included_shipments} included",
                "credits_remaining": credits.package_credits_remaining,
                "can_purchase": PlanEnforcementService._purchasable_credits(plan, credits),
                "price_per_credit": plan.overage_price_per_shipment_aud,
            }
        
        if credits.package_credits_remaining > 0:
            return {
                "allowed": True,
                "reason": "credit_deducted",
                "message": f"Using 1 package credit. {credits.package_credits_remaining - 1} remaining.",
                "credits_remaining": credits.package_credits_remaining - 1,
                "can_purchase": PlanEnforcementService._purchasable_credits(plan, credits),
                "price_per_credit": plan.overage_price_per_shipment_aud,
            }
        
        purchasable = PlanEnforcementService._purchasable_credits(plan, credits)
        
        if purchasable is None or purchasable > 0:
            price = plan.overage_price_per_shipment_aud
            return {
                "allowed": False,
                "reason": "buy_credits",
                "message": f"Package limit reached. Buy a credit (${price}/each). {purchasable if purchasable is not None else 'Unlimited'} available to purchase.",
                "credits_remaining": 0,
                "can_purchase": purchasable,
                "price_per_credit": price,
            }
        
        # Maxed out completely
        return {
            "allowed": False,
            "reason": "upgrade",
            "message": "Package limit reached and all overage credits used. Upgrade your plan.",
            "credits_remaining": 0,
            "can_purchase": 0,
            "price_per_credit": None,
        }
    
    @staticmethod
    def use_shipment(db: Session, company_id: str):
        """
        Increment shipment counter. Deduct credit if over included amount.
        Call this AFTER check_can_create_shipment returns allowed=True.
        """
        company, plan = PlanEnforcementService._get_company_plan(db, company_id)
        usage = PlanEnforcementService._get_current_usage(db, company_id)
        credits = PlanEnforcementService._get_current_credits(db, company_id)
        
        usage.shipments_created += 1
        
        # If over included amount, deduct a credit
        if plan.included_shipments is not None and usage.shipments_created > plan.included_shipments:
            if credits.package_credits_remaining > 0:
                credits.package_credits_remaining -= 1
                usage.shipment_overage += 1
            else:
                raise ValueError("No package credits remaining")
        
        db.commit()
    
    # ===== TRANSFER CHECKS =====
    
    @staticmethod
    def check_can_transfer(db: Session, company_id: str) -> dict:
        """
        Check if company can perform a transfer.
        Transfers are hard-capped — no credit purchase, only upgrade.
        """
        company, plan = PlanEnforcementService._get_company_plan(db, company_id)
        usage = PlanEnforcementService._get_current_usage(db, company_id)
        
        # Unlimited transfers
        if plan.included_transfers is None:
            return {
                "allowed": True,
                "reason": "free",
                "message": "Unlimited transfers on your plan",
                "transfers_used": usage.transfers_performed,
                "transfers_limit": None,
            }
        
        # No transfer rights (e.g. Public Verifier)
        if plan.included_transfers == 0:
            return {
                "allowed": False,
                "reason": "upgrade",
                "message": "Your plan does not include transfer rights. Upgrade to enable transfers.",
                "transfers_used": 0,
                "transfers_limit": 0,
            }
        
        # Within limit
        if usage.transfers_performed < plan.included_transfers:
            remaining = plan.included_transfers - usage.transfers_performed - 1
            return {
                "allowed": True,
                "reason": "free",
                "message": f"Transfer {usage.transfers_performed + 1} of {plan.included_transfers}. {remaining} remaining after this.",
                "transfers_used": usage.transfers_performed,
                "transfers_limit": plan.included_transfers,
            }
        
        # At or over limit — soft cap check for Enterprise
        if not plan.has_hard_cap:
            return {
                "allowed": True,
                "reason": "soft_limit",
                "message": f"Over transfer limit ({usage.transfers_performed}/{plan.included_transfers}) but soft cap allows continuation.",
                "transfers_used": usage.transfers_performed,
                "transfers_limit": plan.included_transfers,
            }
        
        # Hard blocked
        return {
            "allowed": False,
            "reason": "upgrade",
            "message": f"Transfer limit reached ({plan.included_transfers}). Upgrade your plan for more transfers.",
            "transfers_used": usage.transfers_performed,
            "transfers_limit": plan.included_transfers,
        }
    
    @staticmethod
    def use_transfer(db: Session, company_id: str):
        """Increment transfer counter."""
        usage = PlanEnforcementService._get_current_usage(db, company_id)
        usage.transfers_performed += 1
        db.commit()
    
    # ===== VERIFICATION CHECKS =====
    
    @staticmethod
    def check_can_verify(db: Session, company_id: str) -> dict:
        """
        Check if company can perform a verification.
        Hard-capped — no credit purchase, only upgrade.
        """
        company, plan = PlanEnforcementService._get_company_plan(db, company_id)
        usage = PlanEnforcementService._get_current_usage(db, company_id)
        
        # Unlimited verifications
        if plan.included_verifications is None:
            return {
                "allowed": True,
                "reason": "free",
                "message": "Unlimited verifications on your plan",
            }
        
        # Within limit
        if usage.verifications_performed < plan.included_verifications:
            return {
                "allowed": True,
                "reason": "free",
                "message": f"Verification {usage.verifications_performed + 1} of {plan.included_verifications}",
            }
        
        # Soft cap (Governance tier)
        if not plan.has_hard_cap and plan.overage_price_per_verification_aud:
            return {
                "allowed": True,
                "reason": "soft_limit",
                "message": f"Over verification limit. Additional verifications charged at ${plan.overage_price_per_verification_aud} each.",
            }
        
        # Hard blocked
        return {
            "allowed": False,
            "reason": "upgrade",
            "message": f"Verification limit reached ({plan.included_verifications}). Upgrade your plan.",
        }
    
    @staticmethod
    def use_verification(db: Session, company_id: str):
        """Increment verification counter."""
        usage = PlanEnforcementService._get_current_usage(db, company_id)
        usage.verifications_performed += 1
        db.commit()
    
    # ===== VALUE CAP CHECK =====
    
    @staticmethod
    def check_value_cap(db: Session, company_id: str, document_value_aud: float) -> dict:
        """Check if a document value exceeds the plan's value cap"""
        company, plan = PlanEnforcementService._get_company_plan(db, company_id)
        
        if plan.value_cap_aud is None:
            return {"allowed": True, "message": "No value cap on your plan"}
        
        if document_value_aud <= float(plan.value_cap_aud):
            return {"allowed": True, "message": f"Within value cap (${plan.value_cap_aud})"}
        
        return {
            "allowed": False,
            "reason": "value_cap",
            "message": f"Document value (${document_value_aud}) exceeds your plan's cap of ${plan.value_cap_aud}. Upgrade to remove the cap.",
        }
    
    # ===== CREDIT PURCHASE =====
    
    @staticmethod
    def purchase_credits(
        db: Session,
        company_id: str,
        user_id: str,
        quantity: int,
        stripe_payment_intent_id: str = None,
    ) -> dict:
        """
        Purchase package credits after payment is confirmed.
        
        Call this AFTER Stripe payment succeeds.
        """
        from models import CreditTransaction
        
        company, plan = PlanEnforcementService._get_company_plan(db, company_id)
        credits = PlanEnforcementService._get_current_credits(db, company_id)
        
        # Check if plan allows overage purchases
        if plan.max_overage_packages == 0:
            raise ValueError("Your plan does not allow overage purchases")
        
        if plan.overage_price_per_shipment_aud is None:
            raise ValueError("No overage pricing defined for this plan")
        
        # Check purchase limit
        purchasable = PlanEnforcementService._purchasable_credits(plan, credits)
        if purchasable is not None and quantity > purchasable:
            raise ValueError(f"Can only purchase {purchasable} more credits this period")
        
        # Calculate price
        price_per = plan.overage_price_per_shipment_aud
        total_price = price_per * quantity
        
        # Record transaction
        transaction = CreditTransaction(
            company_id=company_id,
            user_id=user_id,
            credit_type="package",
            quantity=quantity,
            price_per_credit_aud=price_per,
            total_price_aud=total_price,
            stripe_payment_intent_id=stripe_payment_intent_id,
            payment_status="completed",
        )
        db.add(transaction)
        
        # Add credits
        credits.package_credits_remaining += quantity
        credits.package_credits_purchased += quantity
        credits.total_credit_spend_aud += total_price
        
        db.commit()
        db.refresh(transaction)
        
        return {
            "message": f"Purchased {quantity} package credit(s)",
            "credits_remaining": credits.package_credits_remaining,
            "credits_purchased_this_period": credits.package_credits_purchased,
            "total_charged": float(total_price),
            "transaction_id": transaction.transaction_id,
        }
    
    # ===== BALANCE CHECK =====
    
    @staticmethod
    def get_credit_balance(db: Session, company_id: str) -> dict:
        """Get full credit/usage balance for a company"""
        company, plan = PlanEnforcementService._get_company_plan(db, company_id)
        usage = PlanEnforcementService._get_current_usage(db, company_id)
        credits = PlanEnforcementService._get_current_credits(db, company_id)
        
        # Package calculations
        packages_remaining_free = max(0, (plan.included_shipments or 0) - usage.shipments_created)
        
        # Transfer calculations
        transfers_remaining = None
        if plan.included_transfers is not None:
            transfers_remaining = max(0, plan.included_transfers - usage.transfers_performed)
        
        # Verification calculations
        verifications_remaining = None
        if plan.included_verifications is not None:
            verifications_remaining = max(0, plan.included_verifications - usage.verifications_performed)
        
        return {
            "company_id": company_id,
            "plan_name": plan.plan_name,
            "billing_period_start": usage.billing_period_start,
            "billing_period_end": usage.billing_period_end,
            
            "packages_included": plan.included_shipments,
            "packages_used": usage.shipments_created,
            "packages_remaining_free": packages_remaining_free,
            
            "package_credits_remaining": credits.package_credits_remaining,
            "package_credits_purchased": credits.package_credits_purchased,
            "max_purchasable": plan.max_overage_packages,
            "can_buy_more": PlanEnforcementService._purchasable_credits(plan, credits) != 0,
            "price_per_credit_aud": plan.overage_price_per_shipment_aud,
            
            "transfers_included": plan.included_transfers,
            "transfers_used": usage.transfers_performed,
            "transfers_remaining": transfers_remaining,
            
            "verifications_included": plan.included_verifications,
            "verifications_used": usage.verifications_performed,
            "verifications_remaining": verifications_remaining,
        }
    
    # ===== HELPERS =====
    
    @staticmethod
    def _purchasable_credits(plan: Plan, credits: CompanyCredits):
        """How many more credits can be purchased this period. None = unlimited."""
        if plan.max_overage_packages is None:
            return None  # Unlimited (Enterprise)
        if plan.max_overage_packages == 0:
            return 0  # No overages allowed (Free Trial)
        return max(0, plan.max_overage_packages - credits.package_credits_purchased)