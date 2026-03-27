# models.py

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Numeric, Text,
    ForeignKey, BigInteger, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from datetime import datetime


# 1. PLAN & PRICING MODELS


class PlanCategory(Base):
    __tablename__ = "plan_category"
    
    category_id = Column(Integer, primary_key=True, autoincrement=True)
    category_name = Column(String(100), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    plans = relationship("Plan", back_populates="category")


class Plan(Base):
    __tablename__ = "plan"
    
    plan_id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("plan_category.category_id"), nullable=False)
    
    # Plan Identity
    plan_name = Column(String(100), nullable=False)
    plan_slug = Column(String(100), unique=True, nullable=False)
    tier_level = Column(Integer, nullable=False)  # 0=Free, 1=Starter, 2=Growth, 3=Enterprise
    
    # Pricing
    base_price_aud = Column(Numeric(10, 2))
    is_contract_pricing = Column(Boolean, default=False, nullable=False)
    
    # User Limits
    included_users = Column(Integer)
    max_users = Column(Integer)
    additional_user_price_aud = Column(Numeric(10, 2))
    
    # Usage Limits
    included_shipments = Column(Integer)
    included_verifications = Column(Integer)
    included_evidence_bundles = Column(Integer)
    included_transfers = Column(Integer)
    
    # Overage Pricing
    overage_price_per_shipment_aud = Column(Numeric(10, 2))
    overage_price_per_verification_aud = Column(Numeric(10, 2))
    max_overage_packages = Column(Integer)
    has_hard_cap = Column(Boolean, default=False, nullable=False)
    
    # Feature Flags
    has_api_access = Column(Boolean, default=False, nullable=False)
    has_bulk_verification = Column(Boolean, default=False, nullable=False)
    has_branded_portal = Column(Boolean, default=False, nullable=False)
    has_audit_logs = Column(Boolean, default=False, nullable=False)
    has_priority_support = Column(Boolean, default=False, nullable=False)
    has_sla = Column(Boolean, default=False, nullable=False)
    has_multi_party_transfer = Column(Boolean, default=False, nullable=False)
    has_advanced_controls = Column(Boolean, default=False, nullable=False)
    issuance_price_aud = Column(Numeric(10, 2))
    value_cap_aud = Column(Numeric(10,2))

    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    sort_order = Column(Integer, default=0)

    #Stripe Integration
    stripe_price_id_monthly = Column(String(100))
    stripe_price_id_anually = Column(String(100))

    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    category = relationship("PlanCategory", back_populates="plans")
    companies = relationship("Company", back_populates="plan")
    
    # Indexes
    __table_args__ = (
        Index('idx_plan_slug', 'plan_slug'),
        Index('idx_plan_category', 'category_id'),
    )



# 2. COMPANY & CONTRACTS MODELS

class Company(Base):
    __tablename__ = "company"
    
    company_id = Column(String(100), primary_key=True)
    
    # Company Info
    company_name = Column(String(255), nullable=False)
    company_type = Column(String(50), nullable=False)  # 'exporter', 'association', 'bank', 'government', 'verifier'
    abn = Column(String(20))
    industry = Column(String(100))
    
    # Plan & Subscription
    plan_id = Column(Integer, ForeignKey("plan.plan_id"), nullable=False)
    
    # Custom Contract
    is_custom_contract = Column(Boolean, default=False, nullable=False)
    custom_monthly_price_aud = Column(Numeric(10, 2))
    custom_annual_price_aud = Column(Numeric(10, 2))
    custom_setup_fee_aud = Column(Numeric(10, 2))
    custom_shipments_limit = Column(Integer)
    custom_verifications_limit = Column(Integer)
    custom_users_limit = Column(Integer)
    custom_storage_gb = Column(Integer)
    
    # Contract Terms
    contract_start_date = Column(Date)
    contract_end_date = Column(Date)
    contract_renewal_type = Column(String(20))  # 'auto_renew', 'manual', 'fixed_term'
    contract_document_url = Column(String(500))
    signed_by = Column(String(255))
    signed_at = Column(DateTime)
    
    # SLA
    sla_uptime_guarantee = Column(Numeric(5, 2))
    sla_support_response_hours = Column(Integer)
    
    # Billing
    billing_email = Column(String(255), nullable=False)
    billing_address = Column(Text)
    payment_method = Column(String(50), nullable=False)  # 'credit_card', 'invoice', 'bank_transfer'
    stripe_customer_id = Column(String(100))
    stripe_subscription_id = Column(String(100))
    
    # Subscription Status
    subscription_status = Column(String(20), nullable=False)  # 'trial', 'active', 'past_due', 'cancelled', 'expired'
    subscription_started = Column(DateTime, nullable=False)
    trial_ends_at = Column(DateTime)
    next_billing_date = Column(Date)
    
    # Metadata
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    plan = relationship("Plan", back_populates="companies")
    users = relationship("User", back_populates="company", foreign_keys="User.company_id")
    shipments = relationship("Shipment", back_populates="company")
    files = relationship("File", back_populates="company")
    folders = relationship("Folder", back_populates="company")
    signatures = relationship("SignatureLibrary", back_populates="company")
    usage_records = relationship("CompanyUsage", back_populates="company")
    address_book = relationship("AddressBook", back_populates="company")
    contract_negotiations = relationship("ContractNegotiation", back_populates="company")
    logs = relationship("Log", back_populates="company")
    credits = relationship("CompanyCredits", back_populates="company")
    credit_transactions = relationship("CreditTransaction", back_populates="company")
    # creator = relationship("User", foreign_keys=[created_by])
    
    # Indexes
    __table_args__ = (
        Index('idx_company_plan', 'plan_id'),
        Index('idx_company_status', 'subscription_status'),
        Index('idx_company_type', 'company_type'),
    )


class ContractNegotiation(Base):
    __tablename__ = "contract_negotiations"
    
    negotiation_id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(String(100), ForeignKey("company.company_id"), nullable=False)
    
    # Customer Requirements
    requested_shipments = Column(Integer)
    requested_verifications = Column(Integer)
    requested_users = Column(Integer, nullable=False)
    requested_features = Column(JSONB, default={})
    additional_notes = Column(Text)
    
    # Pricing Proposals
    proposed_monthly_price_aud = Column(Numeric(10, 2), nullable=False)
    proposed_annual_price_aud = Column(Numeric(10, 2))
    proposed_setup_fee_aud = Column(Numeric(10, 2))
    discount_percentage = Column(Numeric(5, 2))
    discount_reason = Column(String(500))
    
    # Status
    status = Column(String(50), nullable=False)  # 'draft', 'sent_to_customer', 'under_review', 'negotiating', 'accepted', 'rejected'
    
    # Sales Info
    sales_rep_id = Column(String(100), nullable=False)
    customer_contact_email = Column(String(255), nullable=False)
    customer_contact_name = Column(String(255), nullable=False)
    
    # Proposal Document
    proposal_document_url = Column(String(500))
    quote_valid_until = Column(Date)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    accepted_at = Column(DateTime)
    rejected_at = Column(DateTime)
    
    # Relationships
    company = relationship("Company", back_populates="contract_negotiations")
    
    # Indexes
    __table_args__ = (
        Index('idx_negotiation_status', 'status'),
        Index('idx_negotiation_company', 'company_id'),
    )



# 3. USERS & PERMISSIONS MODELS

class Permission(Base):
    __tablename__ = "permissions"
    
    role = Column(String(50), primary_key=True)  # 'owner', 'admin', 'member', 'viewer'
    
    # User Management
    can_invite_users = Column(Boolean, default=False, nullable=False)
    can_remove_users = Column(Boolean, default=False, nullable=False)
    can_change_user_roles = Column(Boolean, default=False, nullable=False)
    
    # Company Management
    can_update_company_info = Column(Boolean, default=False, nullable=False)
    can_change_plan = Column(Boolean, default=False, nullable=False)
    can_update_payment = Column(Boolean, default=False, nullable=False)
    can_delete_company = Column(Boolean, default=False, nullable=False)
    can_view_billing = Column(Boolean, default=False, nullable=False)
    
    # Document Operations
    can_create_shipments = Column(Boolean, default=False, nullable=False)
    can_issue_documents = Column(Boolean, default=False, nullable=False)
    can_delete_documents = Column(Boolean, default=False, nullable=False)
    can_verify_documents = Column(Boolean, default=False, nullable=False)
    
    # Analytics & Reports
    can_view_analytics = Column(Boolean, default=False, nullable=False)
    can_export_data = Column(Boolean, default=False, nullable=False)
    can_view_audit_logs = Column(Boolean, default=False, nullable=False)
    
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    users = relationship("User", back_populates="permissions")


class User(Base):
    __tablename__ = "users"
    
    id = Column(String(100), primary_key=True)
    company_id = Column(String(100), ForeignKey("company.company_id"), nullable=True)
    
    # Authentication
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=True)
    email_verified = Column(Boolean, default=False, nullable=False)
    email_verified_at = Column(DateTime)
    
    # Profile
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20))
    wallet_address = Column(String(255))  # Blockchain wallet address
    
    # Role & Permissions
    role = Column(String(50), ForeignKey("permissions.role"), nullable=True)
    is_owner = Column(Boolean, default=False, nullable=False)
    
    # Invitation
    invited_by = Column(String(100), ForeignKey("users.id"))
    invited_at = Column(DateTime)
    invitation_accepted_at = Column(DateTime)
    
    # Activity
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    company = relationship("Company", back_populates="users", foreign_keys=[company_id])
    permissions = relationship("Permission", back_populates="users")
    invited_users = relationship("User", backref="inviter", remote_side=[id])
    shipments = relationship("Shipment", back_populates="created_by_user")
    files = relationship("File", back_populates="user")
    folders = relationship("Folder", back_populates="user")
    signatures = relationship("SignatureLibrary", back_populates="user")
    verifications = relationship("DocumentVerification", back_populates="verified_by_user")
    address_book_entries = relationship("AddressBook", back_populates="created_by_user")
    logs = relationship("Log", back_populates="user")
    credit_transactions = relationship("CreditTransaction", back_populates="user")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_email', 'email'),
        Index('idx_user_company', 'company_id'),
        Index('idx_user_role', 'role'),
    )



# 4. ADMIN USER MODEL

class AdminUser(Base):
    __tablename__ = "admin_users"
    
    admin_id = Column(String(100), primary_key=True)
    
    # Authentication
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # Profile
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    
    # Role
    admin_role = Column(String(50), nullable=False)  # 'super_admin', 'admin', 'sales'
    
    # Activity
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_admin_email', 'email'),
        Index('idx_admin_role', 'admin_role'),
    )


# 5. SHIPMENTS & DOCUMENTS MODELS
class Shipment(Base):
    __tablename__ = "shipment"
    
    shipment_id = Column(String(100), primary_key=True)
    company_id = Column(String(100), ForeignKey("company.company_id"), nullable=False)
    created_by_user_id = Column(String(100), ForeignKey("users.id"), nullable=False)
    
    # Identity
    shipment_name = Column(String(255), nullable=False)
    shipment_reference = Column(String(100))
    
    # Status
    status = Column(String(50), nullable=False)  # 'draft', 'active', 'in_transit', 'completed', 'cancelled'
    
    # Metadata
    document_count = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    
    # Relationships
    company = relationship("Company", back_populates="shipments")
    created_by_user = relationship("User", back_populates="shipments")
    files = relationship("File", back_populates="shipment")
    
    # Indexes
    __table_args__ = (
        Index('idx_shipment_company', 'company_id'),
        Index('idx_shipment_status', 'status'),
        Index('idx_shipment_created', 'created_at'),
    )


class Folder(Base):
    __tablename__ = "folder"
    
    folder_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), ForeignKey("users.id"), nullable=False)
    company_id = Column(String(100), ForeignKey("company.company_id"), nullable=False)
    
    # Folder Info
    name = Column(String(255), nullable=False)
    parent_folder_id = Column(Integer, ForeignKey("folder.folder_id"))
    
    # Metadata
    is_shared = Column(Boolean, default=False, nullable=False)
    color = Column(String(20))
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="folders")
    company = relationship("Company", back_populates="folders")
    parent_folder = relationship("Folder", remote_side=[folder_id], backref="child_folders")
    files = relationship("File", back_populates="folder")
    
    # Indexes
    __table_args__ = (
        Index('idx_folder_company', 'company_id'),
        Index('idx_folder_user', 'user_id'),
    )


class File(Base):
    __tablename__ = "files"
    
    file_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Ownership & Organization
    shipment_id = Column(String(100), ForeignKey("shipment.shipment_id"))
    company_id = Column(String(100), ForeignKey("company.company_id"), nullable=False)
    user_id = Column(String(100), ForeignKey("users.id"), nullable=False)
    folder_id = Column(Integer, ForeignKey("folder.folder_id"))
    
    # Document Identity
    name = Column(String(255), nullable=False)
    document_type = Column(String(50), nullable=False)  # 'bill_of_lading', 'commercial_invoice', 'packing_list', 'certificate_of_origin', 'etr'
    
    # TradeTrust Document Data
    document_data = Column(JSONB, nullable=False)
    
    # Blockchain Info (extracted from document_data)
    credential_id = Column(String(255))
    token_id = Column(String(255))
    token_registry = Column(String(255))
    blockchain_network = Column(String(50))
    
    # File Metadata
    file_size_bytes = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), default='application/json', nullable=False)
    
    # Verification Status
    is_verified = Column(Boolean, default=False, nullable=False)
    verified_at = Column(DateTime)
    verification_error_code = Column(String(100))
    verification_error_message = Column(Text)
    
    # QR Code & Public Verification
    qr_code_url = Column(String(500))
    verification_link = Column(String(500))
    
    # Document Status
    status = Column(String(50), nullable=False)  # 'draft', 'issued', 'transferred', 'revoked'
    
    # Analytics
    verification_count = Column(Integer, default=0, nullable=False)
    view_count = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    issued_at = Column(DateTime)
    
    # Relationships
    shipment = relationship("Shipment", back_populates="files")
    company = relationship("Company", back_populates="files")
    user = relationship("User", back_populates="files")
    folder = relationship("Folder", back_populates="files")
    verifications = relationship("DocumentVerification", back_populates="file")
    
    # Indexes
    __table_args__ = (
        Index('idx_file_company', 'company_id', 'created_at'),
        Index('idx_file_shipment', 'shipment_id'),
        Index('idx_file_credential', 'credential_id'),
        Index('idx_file_token', 'token_id'),
        Index('idx_file_verified', 'is_verified'),
    )


class DocumentVerification(Base):
    __tablename__ = "document_verification"
    
    verification_id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(Integer, ForeignKey("files.file_id"), nullable=False)
    
    # Who verified
    verified_by_company_id = Column(String(100), ForeignKey("company.company_id"))
    verified_by_user_id = Column(String(100), ForeignKey("users.id"))
    verifier_wallet_address = Column(String(255))
    
    # How verified
    verification_type = Column(String(50), nullable=False)  # 'initial', 're_verification', 'qr_scan', 'api', 'public_link'
    verification_channel = Column(String(50), nullable=False)  # 'web', 'mobile', 'api'
    
    # Result
    verification_result = Column(String(50), nullable=False)  # 'success', 'failed'
    verification_error_code = Column(String(100))
    verification_error_message = Column(Text)
    
    # TradeTrust Response
    tradetrust_response = Column(JSONB)
    
    # Location
    verification_location = Column(JSONB)
    
    # Metadata
    user_agent = Column(String(500))
    
    verified_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    file = relationship("File", back_populates="verifications")
    verified_by_user = relationship("User", back_populates="verifications")
    
    # Indexes
    __table_args__ = (
        Index('idx_verification_file', 'file_id', 'verified_at'),
        Index('idx_verification_company', 'verified_by_company_id', 'verified_at'),
        Index('idx_verification_type', 'verification_type'),
    )


# 6. SIGNATURE LIBRARY MODEL
class SignatureLibrary(Base):
    __tablename__ = "signature_library"
    
    signature_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), ForeignKey("users.id"), nullable=False)
    company_id = Column(String(100), ForeignKey("company.company_id"), nullable=False)
    
    # Metadata
    signature_name = Column(String(100), nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    notes = Column(Text)
    
    # Signature Data (stored as base64 in database)
    signature_data = Column(Text, nullable=False)  # Base64 encoded image
    
    # File Metadata
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="signatures")
    company = relationship("Company", back_populates="signatures")
    
    # Indexes
    __table_args__ = (
        Index('idx_signature_user', 'user_id'),
        Index('idx_signature_company', 'company_id'),
        Index('idx_signature_default', 'user_id', 'is_default'),
    )


# 7. USAGE TRACKING & BILLING MODELS
class CompanyUsage(Base):
    __tablename__ = "company_usage"
    
    usage_id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(String(100), ForeignKey("company.company_id"), nullable=False)
    
    # Billing Period
    billing_period_start = Column(Date, nullable=False)
    billing_period_end = Column(Date, nullable=False)
    
    # Usage Counters
    shipments_created = Column(Integer, default=0, nullable=False)
    documents_created = Column(Integer, default=0, nullable=False)
    verifications_performed = Column(Integer, default=0, nullable=False)
    evidence_bundles_created = Column(Integer, default=0, nullable=False)
    transfers_performed = Column(Integer, default=0, nullable=False)
    storage_used_gb = Column(Numeric(10, 2), default=0.0, nullable=False)
    active_user_count = Column(Integer, default=0, nullable=False)
    peak_user_count = Column(Integer, default=0, nullable=False)
    
    # Overage Calculations
    shipment_overage = Column(Integer, default=0, nullable=False)
    verification_overage = Column(Integer, default=0, nullable=False)
    user_overage = Column(Integer, default=0, nullable=False)
    transfer_overage = Column(Integer, default=0, nullable=False)
    
    # Charges
    overage_charges_aud = Column(Numeric(10, 2), default=0.0, nullable=False)
    additional_charges_aud = Column(Numeric(10, 2), default=0.0, nullable=False)
    total_charges_aud = Column(Numeric(10, 2), default=0.0, nullable=False)
    
    # Invoice
    invoice_id = Column(String(100))
    invoice_status = Column(String(50))  # 'pending', 'sent', 'paid', 'overdue'
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    company = relationship("Company", back_populates="usage_records")
    
    # Indexes
    __table_args__ = (
        Index('idx_usage_company', 'company_id', 'billing_period_end'),
        Index('idx_usage_period', 'billing_period_start', 'billing_period_end'),
    )

class CompanyCredits(Base):
    __tablename__ = "company_credits"
    
    credit_id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(String(100), ForeignKey("company.company_id"), nullable=False)
    
    # Billing Period
    billing_period_start = Column(Date, nullable=False)
    billing_period_end = Column(Date, nullable=False)
    
    # Package Credits (the only purchasable overage)
    package_credits_remaining = Column(Integer, default=0, nullable=False)
    package_credits_purchased = Column(Integer, default=0, nullable=False)  # Compared against plan.max_overage_packages
    
    # Total spent on credits this period
    total_credit_spend_aud = Column(Numeric(10, 2), default=0.0, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    company = relationship("Company", back_populates="credits")
    
    # Indexes
    __table_args__ = (
        Index('idx_credits_company', 'company_id', 'billing_period_end'),
    )
 
 
class CreditTransaction(Base):
    __tablename__ = "credit_transactions"
    
    transaction_id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(String(100), ForeignKey("company.company_id"), nullable=False)
    user_id = Column(String(100), ForeignKey("users.id"), nullable=False)
    
    # What was purchased
    credit_type = Column(String(50), nullable=False) 
    quantity = Column(Integer, nullable=False) 
    price_per_credit_aud = Column(Numeric(10, 2), nullable=False) 
    total_price_aud = Column(Numeric(10, 2), nullable=False) 
    
    # Payment
    stripe_payment_intent_id = Column(String(255))  
    payment_status = Column(String(50), nullable=False) 
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    company = relationship("Company", back_populates="credit_transactions")
    user = relationship("User", back_populates="credit_transactions")
    
    # Indexes
    __table_args__ = (
        Index('idx_credit_tx_company', 'company_id', 'created_at'),
        Index('idx_credit_tx_payment', 'stripe_payment_intent_id'),
    )

# 8. SUPPORTING TABLES
class AddressBook(Base):
    __tablename__ = "address_book"
    
    contact_id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(String(100), ForeignKey("company.company_id"), nullable=False)
    
    # Contact Info
    contact_type = Column(String(50), nullable=False)  # 'customer', 'supplier', 'shipper', 'consignee', 'customs_agent'
    name = Column(String(255), nullable=False)
    company_name = Column(String(255))
    email = Column(String(255))
    phone = Column(String(20))
    
    # Address
    address_line_1 = Column(String(255))
    address_line_2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(2))  # 2-letter country code
    
    # Metadata
    notes = Column(Text)
    is_favorite = Column(Boolean, default=False, nullable=False)
    
    created_by = Column(String(100), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    company = relationship("Company", back_populates="address_book")
    created_by_user = relationship("User", back_populates="address_book_entries")
    
    # Indexes
    __table_args__ = (
        Index('idx_address_company', 'company_id'),
        Index('idx_address_type', 'contact_type'),
    )


class Log(Base):
    __tablename__ = "logs"
    
    log_id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Scope
    company_id = Column(String(100), ForeignKey("company.company_id"))
    user_id = Column(String(100), ForeignKey("users.id"))
    
    # Action
    action_type = Column(String(100), nullable=False)
    action_category = Column(String(50), nullable=False)  # 'auth', 'document', 'verification', 'shipment', 'billing', 'user_management', 'company'
    
    # Target Resource
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(100), nullable=False)
    
    # Details
    details = Column(JSONB, default={})
    changes = Column(JSONB)  # Before/after for updates
    
    # Request Info
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    request_id = Column(String(100))
    
    # Result
    status = Column(String(50), nullable=False)  # 'success', 'failure', 'error'
    error_message = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    company = relationship("Company", back_populates="logs")
    user = relationship("User", back_populates="logs")
    
    # Indexes
    __table_args__ = (
        Index('idx_log_company', 'company_id', 'created_at'),
        Index('idx_log_user', 'user_id', 'created_at'),
        Index('idx_log_action', 'action_type', 'created_at'),
        Index('idx_log_resource', 'resource_type', 'resource_id'),
    )