from datetime import datetime, date
from typing import Any, Dict, Optional, List
from decimal import Decimal
from pydantic import BaseModel, EmailStr, Field, validator
from enum import Enum

class PlanCategoryBase(BaseModel):
    category_name: str = Field(..., max_length=100, description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    is_active: bool = Field(default=True, description="Is category active")

class PlanCategoryCreate(PlanCategoryBase):
    pass

class PlanCategoryUpdate(BaseModel):
    category_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None

class PlanCategoryResponse(PlanCategoryBase):
    category_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class PlanBase(BaseModel):
    category_id: int
    plan_name: str = Field(..., max_length=100)
    plan_slug: str = Field(..., max_length=100, description="URL-friendly slug")
    tier_level: int = Field(..., ge=0, description="0=Free, 1=Starter, 2=Growth, etc.")
    
    # Pricing
    base_price_aud: Optional[Decimal] = Field(None, description="Monthly base price")
    is_contract_pricing: bool = Field(default=False, description="Requires sales negotiation")
    
    # User Limits
    included_users: Optional[int] = Field(None, ge=0)
    max_users: Optional[int] = Field(None, ge=0, description="NULL = unlimited")
    additional_user_price_aud: Optional[Decimal] = Field(None)
    
    # Usage Limits
    included_shipments: Optional[int] = Field(None, ge=0)
    included_verifications: Optional[int] = Field(None, ge=0)
    included_evidence_bundles: Optional[int] = Field(None, ge=0)
    
    # Overage Pricing
    overage_price_per_shipment_aud: Optional[Decimal] = Field(None)
    overage_price_per_verification_aud: Optional[Decimal] = Field(None)
    has_hard_cap: bool = Field(default=False, description="Block at limit or allow overages")
    
    # Feature Flags
    has_api_access: bool = Field(default=False)
    has_bulk_verification: bool = Field(default=False)
    has_branded_portal: bool = Field(default=False)
    has_audit_logs: bool = Field(default=False)
    has_priority_support: bool = Field(default=False)
    has_sla: bool = Field(default=False)
    has_multi_party_transfer: bool = Field(default=False)
    has_advanced_controls: bool = Field(default=False)
    
    # Metadata
    is_active: bool = Field(default=True)
    is_featured: bool = Field(default=False)
    sort_order: int = Field(default=0)

class PlanCreate(PlanBase):
    pass

class PlanUpdate(BaseModel):
    category_id: Optional[int] = None
    plan_name: Optional[str] = Field(None, max_length=100)
    plan_slug: Optional[str] = Field(None, max_length=100)
    tier_level: Optional[int] = Field(None, ge=0)
    base_price_aud: Optional[Decimal] = None
    is_contract_pricing: Optional[bool] = None
    included_users: Optional[int] = None
    max_users: Optional[int] = None
    additional_user_price_aud: Optional[Decimal] = None
    included_shipments: Optional[int] = None
    included_verifications: Optional[int] = None
    included_evidence_bundles: Optional[int] = None
    overage_price_per_shipment_aud: Optional[Decimal] = None
    overage_price_per_verification_aud: Optional[Decimal] = None
    has_hard_cap: Optional[bool] = None
    has_api_access: Optional[bool] = None
    has_bulk_verification: Optional[bool] = None
    has_branded_portal: Optional[bool] = None
    has_audit_logs: Optional[bool] = None
    has_priority_support: Optional[bool] = None
    has_sla: Optional[bool] = None
    has_multi_party_transfer: Optional[bool] = None
    has_advanced_controls: Optional[bool] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    sort_order: Optional[int] = None

class PlanResponse(PlanBase):
    plan_id: int
    created_at: datetime
    updated_at: datetime
    
    category: Optional[PlanCategoryResponse] = None

    class Config:
        from_attributes = True

class CompanyType(str, Enum):
    EXPORTER = "exporter"
    ASSOCIATION = "association"
    BANK = "bank"
    GOVERNMENT = "government"
    VERIFIER = "verifier"

class SubscriptionStatus(str, Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class PaymentMethod(str, Enum):
    CREDIT_CARD = "credit_card"
    INVOICE = "invoice"
    BANK_TRANSFER = "bank_transfer"

class ContractRenewalType(str, Enum):
    AUTO_RENEW = "auto_renew"
    MANUAL = "manual"
    FIXED_TERM = "fixed_term"

class CompanyBase(BaseModel):
    company_name: str = Field(..., max_length=255)
    company_type: CompanyType
    abn: Optional[str] = Field(None, max_length=20, description="Australian Business Number")
    industry: Optional[str] = Field(None, max_length=100)
    
    plan_id: int
    
    # Custom Contract
    is_custom_contract: bool = Field(default=False)
    custom_monthly_price_aud: Optional[Decimal] = Field(None)
    custom_annual_price_aud: Optional[Decimal] = Field(None)
    custom_setup_fee_aud: Optional[Decimal] = Field(None)
    custom_shipments_limit: Optional[int] = Field(None, ge=0)
    custom_verifications_limit: Optional[int] = Field(None, ge=0)
    custom_users_limit: Optional[int] = Field(None, ge=0)
    custom_storage_gb: Optional[int] = Field(None, ge=0)
    
    # Contract Terms
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    contract_renewal_type: Optional[ContractRenewalType] = None
    contract_document_url: Optional[str] = Field(None, max_length=500)
    signed_by: Optional[str] = Field(None, max_length=255)
    signed_at: Optional[datetime] = None
    
    # SLA
    sla_uptime_guarantee: Optional[Decimal] = Field(None, ge=0, le=100)
    sla_support_response_hours: Optional[int] = Field(None, ge=0)
    
    # Billing
    billing_email: EmailStr
    billing_address: Optional[str] = None
    payment_method: PaymentMethod
    stripe_customer_id: Optional[str] = Field(None, max_length=100)
    
    # Subscription
    subscription_status: SubscriptionStatus = Field(default=SubscriptionStatus.TRIAL)
    trial_ends_at: Optional[datetime] = None
    next_billing_date: Optional[date] = None

class CompanyCreate(CompanyBase):
    created_by: str = Field(..., description="User ID who creates the company")
    subscription_started: datetime = Field(default_factory=datetime.utcnow)

class CompanyUpdate(BaseModel):
    company_name: Optional[str] = Field(None, max_length=255)
    company_type: Optional[CompanyType] = None
    abn: Optional[str] = None
    industry: Optional[str] = None
    plan_id: Optional[int] = None
    is_custom_contract: Optional[bool] = None
    custom_monthly_price_aud: Optional[Decimal] = None
    custom_annual_price_aud: Optional[Decimal] = None
    custom_setup_fee_aud: Optional[Decimal] = None
    custom_shipments_limit: Optional[int] = None
    custom_verifications_limit: Optional[int] = None
    custom_users_limit: Optional[int] = None
    custom_storage_gb: Optional[int] = None
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    contract_renewal_type: Optional[ContractRenewalType] = None
    contract_document_url: Optional[str] = None
    signed_by: Optional[str] = None
    signed_at: Optional[datetime] = None
    sla_uptime_guarantee: Optional[Decimal] = None
    sla_support_response_hours: Optional[int] = None
    billing_email: Optional[EmailStr] = None
    billing_address: Optional[str] = None
    payment_method: Optional[PaymentMethod] = None
    stripe_customer_id: Optional[str] = None
    subscription_status: Optional[SubscriptionStatus] = None
    trial_ends_at: Optional[datetime] = None
    next_billing_date: Optional[date] = None

class CompanyResponse(CompanyBase):
    company_id: str
    created_by: str
    subscription_started: datetime
    created_at: datetime
    updated_at: datetime
    
    # Include plan details
    plan: Optional[PlanResponse] = None

    class Config:
        from_attributes = True

class NegotiationStatus(str, Enum):
    DRAFT = "draft"
    SENT_TO_CUSTOMER = "sent_to_customer"
    UNDER_REVIEW = "under_review"
    NEGOTIATING = "negotiating"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class ContractNegotiationBase(BaseModel):
    company_id: str
    
    # Customer Requirements
    requested_shipments: Optional[int] = Field(None, ge=0)
    requested_verifications: Optional[int] = Field(None, ge=0)
    requested_users: int = Field(..., ge=1)
    requested_features: Optional[dict] = Field(default_factory=dict, description="JSON of requested features")
    additional_notes: Optional[str] = None
    
    # Pricing Proposals
    proposed_monthly_price_aud: Decimal = Field(...)
    proposed_annual_price_aud: Optional[Decimal] = Field(None)
    proposed_setup_fee_aud: Optional[Decimal] = Field(None)
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    discount_reason: Optional[str] = Field(None, max_length=500)
    
    # Sales Info
    sales_rep_id: str
    customer_contact_email: EmailStr
    customer_contact_name: str = Field(..., max_length=255)
    
    # Proposal Document
    proposal_document_url: Optional[str] = Field(None, max_length=500)
    quote_valid_until: Optional[date] = None
    
    status: NegotiationStatus = Field(default=NegotiationStatus.DRAFT)

class ContractNegotiationCreate(ContractNegotiationBase):
    pass

class ContractNegotiationUpdate(BaseModel):
    requested_shipments: Optional[int] = None
    requested_verifications: Optional[int] = None
    requested_users: Optional[int] = None
    requested_features: Optional[dict] = None
    additional_notes: Optional[str] = None
    proposed_monthly_price_aud: Optional[Decimal] = None
    proposed_annual_price_aud: Optional[Decimal] = None
    proposed_setup_fee_aud: Optional[Decimal] = None
    discount_percentage: Optional[Decimal] = None
    discount_reason: Optional[str] = None
    customer_contact_email: Optional[EmailStr] = None
    customer_contact_name: Optional[str] = None
    proposal_document_url: Optional[str] = None
    quote_valid_until: Optional[date] = None
    status: Optional[NegotiationStatus] = None

class ContractNegotiationResponse(ContractNegotiationBase):
    negotiation_id: int
    created_at: datetime
    updated_at: datetime
    accepted_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"

class PermissionBase(BaseModel):
    role: UserRole
    
    # User Management
    can_invite_users: bool = Field(default=False)
    can_remove_users: bool = Field(default=False)
    can_change_user_roles: bool = Field(default=False)
    
    # Company Management
    can_update_company_info: bool = Field(default=False)
    can_change_plan: bool = Field(default=False)
    can_update_payment: bool = Field(default=False)
    can_delete_company: bool = Field(default=False)
    can_view_billing: bool = Field(default=False)
    
    # Document Operations
    can_create_shipments: bool = Field(default=False)
    can_issue_documents: bool = Field(default=False)
    can_delete_documents: bool = Field(default=False)
    can_verify_documents: bool = Field(default=False)
    
    # Analytics & Reports
    can_view_analytics: bool = Field(default=False)
    can_export_data: bool = Field(default=False)
    can_view_audit_logs: bool = Field(default=False)
    
    description: Optional[str] = None

class PermissionCreate(PermissionBase):
    pass

class PermissionUpdate(BaseModel):
    can_invite_users: Optional[bool] = None
    can_remove_users: Optional[bool] = None
    can_change_user_roles: Optional[bool] = None
    can_update_company_info: Optional[bool] = None
    can_change_plan: Optional[bool] = None
    can_update_payment: Optional[bool] = None
    can_delete_company: Optional[bool] = None
    can_view_billing: Optional[bool] = None
    can_create_shipments: Optional[bool] = None
    can_issue_documents: Optional[bool] = None
    can_delete_documents: Optional[bool] = None
    can_verify_documents: Optional[bool] = None
    can_view_analytics: Optional[bool] = None
    can_export_data: Optional[bool] = None
    can_view_audit_logs: Optional[bool] = None
    description: Optional[str] = None

class PermissionResponse(PermissionBase):
    created_at: datetime

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., max_length=100)
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    wallet_address: Optional[str] = Field(None, max_length=255, description="Blockchain wallet address")
    role: UserRole = Field(default=UserRole.MEMBER)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Plain password - will be hashed")
    company_id: str
    is_owner: bool = Field(default=False)
    invited_by: Optional[str] = None

    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = None
    wallet_address: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class UserPasswordUpdate(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v

class UserResponse(UserBase):
    id: str
    company_id: str
    email_verified: bool
    email_verified_at: Optional[datetime] = None
    is_owner: bool
    invited_by: Optional[str] = None
    invited_at: Optional[datetime] = None
    invitation_accepted_at: Optional[datetime] = None
    joined_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Include permissions
    permissions: Optional[PermissionResponse] = None

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserInvite(BaseModel):
    email: EmailStr
    role: UserRole = Field(default=UserRole.MEMBER)
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None

class ShipmentStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    IN_TRANSIT = "in_transit"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class DocumentType(str, Enum):
    BILL_OF_LADING = "bill_of_lading"
    COMMERCIAL_INVOICE = "commercial_invoice"
    PACKING_LIST = "packing_list"
    CERTIFICATE_OF_ORIGIN = "certificate_of_origin"
    ETR = "etr"  # Electronic Trade Receipt

class DocumentStatus(str, Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    TRANSFERRED = "transferred"
    REVOKED = "revoked"

class VerificationType(str, Enum):
    INITIAL = "initial"
    RE_VERIFICATION = "re_verification"
    QR_SCAN = "qr_scan"
    API = "api"
    PUBLIC_LINK = "public_link"

class VerificationChannel(str, Enum):
    WEB = "web"
    MOBILE = "mobile"
    API = "api"

class VerificationResult(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"

# ===== SHIPMENT =====

class ShipmentBase(BaseModel):
    shipment_name: str = Field(..., max_length=255, description="Display name for shipment")
    shipment_reference: Optional[str] = Field(None, max_length=100, description="Customer reference")
    status: ShipmentStatus = Field(default=ShipmentStatus.DRAFT)

class ShipmentCreate(ShipmentBase):
    company_id: str
    created_by_user_id: str

class ShipmentUpdate(BaseModel):
    shipment_name: Optional[str] = Field(None, max_length=255)
    shipment_reference: Optional[str] = None
    status: Optional[ShipmentStatus] = None

class ShipmentResponse(ShipmentBase):
    shipment_id: str
    company_id: str
    created_by_user_id: str
    document_count: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    # Optionally include related documents
    documents: Optional[List['FileResponse']] = None

    class Config:
        from_attributes = True

# ===== FOLDER =====

class FolderBase(BaseModel):
    name: str = Field(..., max_length=255)
    parent_folder_id: Optional[int] = Field(None, description="Parent folder for nesting")
    is_shared: bool = Field(default=False, description="Shared with all company users")
    color: Optional[str] = Field(None, max_length=20, description="UI color tag")

class FolderCreate(FolderBase):
    user_id: str
    company_id: str

class FolderUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    parent_folder_id: Optional[int] = None
    is_shared: Optional[bool] = None
    color: Optional[str] = None

class FolderResponse(FolderBase):
    folder_id: int
    user_id: str
    company_id: str
    created_at: datetime
    updated_at: datetime
    
    # Optionally include child folders
    children: Optional[List['FolderResponse']] = None

    class Config:
        from_attributes = True

# ===== FILES (TradeTrust Documents) =====

class FileBase(BaseModel):
    name: str = Field(..., max_length=255, description="Display name like 'Bill of Lading.tt'")
    document_type: DocumentType
    document_data: Dict[str, Any] = Field(..., description="Full TradeTrust .tt document as JSON")
    
    # Optional organization
    shipment_id: Optional[str] = None
    folder_id: Optional[int] = None

class FileCreate(FileBase):
    company_id: str
    user_id: str
    
    @validator('document_data')
    def validate_tradetrust_structure(cls, v):
        """Validate TradeTrust document structure"""
        required_fields = ['@context', 'type', 'credentialSubject', 'issuer']
        for field in required_fields:
            if field not in v:
                raise ValueError(f'TradeTrust document must contain "{field}"')
        return v

class FileUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    shipment_id: Optional[str] = None
    folder_id: Optional[int] = None
    status: Optional[DocumentStatus] = None

class FileVerificationUpdate(BaseModel):
    """Internal schema for updating verification status"""
    is_verified: bool
    verified_at: Optional[datetime] = None
    verification_error_code: Optional[str] = None
    verification_error_message: Optional[str] = None
    qr_code_url: Optional[str] = None
    verification_link: Optional[str] = None
    status: Optional[DocumentStatus] = None

class FileResponse(FileBase):
    file_id: int
    company_id: str
    user_id: str
    
    # Blockchain info (extracted from document_data)
    credential_id: Optional[str] = None
    token_id: Optional[str] = None
    token_registry: Optional[str] = None
    blockchain_network: Optional[str] = None
    
    # File metadata
    file_size_bytes: int
    mime_type: str
    
    # Verification status
    is_verified: bool
    verified_at: Optional[datetime] = None
    verification_error_code: Optional[str] = None
    verification_error_message: Optional[str] = None
    
    # Public verification
    qr_code_url: Optional[str] = None
    verification_link: Optional[str] = None
    
    # Status
    status: DocumentStatus
    
    # Analytics
    verification_count: int
    view_count: int
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    issued_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class FileDownloadResponse(BaseModel):
    """Response for file download endpoint"""
    filename: str
    content: Dict[str, Any]  # TradeTrust document
    mime_type: str

# ===== DOCUMENT VERIFICATION =====

class DocumentVerificationBase(BaseModel):
    file_id: int
    
    # Who verified (all optional for anonymous scans)
    verified_by_company_id: Optional[str] = None
    verified_by_user_id: Optional[str] = None
    verifier_wallet_address: Optional[str] = Field(None, max_length=255, description="Blockchain wallet address")
    
    # How verified
    verification_type: VerificationType
    verification_channel: VerificationChannel
    
    # Result
    verification_result: VerificationResult
    verification_error_code: Optional[str] = Field(None, max_length=100)
    verification_error_message: Optional[str] = None
    
    # TradeTrust response
    tradetrust_response: Optional[Dict[str, Any]] = Field(None, description="Full TradeTrust verification response")
    
    # Location
    verification_location: Optional[Dict[str, Any]] = Field(None, description="Geographic location JSON")
    
    # Metadata
    user_agent: Optional[str] = Field(None, max_length=500)

class DocumentVerificationCreate(DocumentVerificationBase):
    verified_at: datetime = Field(default_factory=datetime.utcnow)

class DocumentVerificationResponse(DocumentVerificationBase):
    verification_id: int
    verified_at: datetime

    class Config:
        from_attributes = True

class PublicVerificationResponse(BaseModel):
    """Response for public QR code verification"""
    document_name: str
    document_type: DocumentType
    issuer: str
    issued_at: datetime
    is_valid: bool
    verified_at: datetime
    blockchain: Dict[str, str]  # network, tokenRegistry, tokenId
    error: Optional[Dict[str, str]] = None

class InvoiceStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"


class CompanyUsageBase(BaseModel):
    billing_period_start: date
    billing_period_end: date
    
    # Usage counters
    shipments_created: int = Field(default=0, ge=0)
    documents_created: int = Field(default=0, ge=0)
    verifications_performed: int = Field(default=0, ge=0)
    evidence_bundles_created: int = Field(default=0, ge=0)
    storage_used_gb: Decimal = Field(default=Decimal("0.0"), ge=0)
    active_user_count: int = Field(default=0, ge=0)
    peak_user_count: int = Field(default=0, ge=0)
    
    # Overage calculations
    shipment_overage: int = Field(default=0, ge=0)
    verification_overage: int = Field(default=0, ge=0)
    user_overage: int = Field(default=0, ge=0)
    
    # Charges
    overage_charges_aud: Decimal = Field(default=Decimal("0.0"), ge=0)
    additional_charges_aud: Decimal = Field(default=Decimal("0.0"), ge=0)
    total_charges_aud: Decimal = Field(default=Decimal("0.0"), ge=0)
    
    # Invoice
    invoice_id: Optional[str] = Field(None, max_length=100)
    invoice_status: Optional[InvoiceStatus] = None

class CompanyUsageCreate(CompanyUsageBase):
    company_id: str

class CompanyUsageUpdate(BaseModel):
    shipments_created: Optional[int] = None
    documents_created: Optional[int] = None
    verifications_performed: Optional[int] = None
    evidence_bundles_created: Optional[int] = None
    storage_used_gb: Optional[Decimal] = None
    active_user_count: Optional[int] = None
    peak_user_count: Optional[int] = None
    shipment_overage: Optional[int] = None
    verification_overage: Optional[int] = None
    user_overage: Optional[int] = None
    overage_charges_aud: Optional[Decimal] = None
    additional_charges_aud: Optional[Decimal] = None
    total_charges_aud: Optional[Decimal] = None
    invoice_id: Optional[str] = None
    invoice_status: Optional[InvoiceStatus] = None

class CompanyUsageResponse(CompanyUsageBase):
    usage_id: int
    company_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UsageSummary(BaseModel):
    plan_name: str
    billing_period_start: date
    billing_period_end: date
    
    # Shipments
    shipments_used: int
    shipments_limit: Optional[int]
    shipments_remaining: Optional[int]
    shipments_overage: int
    
    # Users
    users_active: int
    users_limit: Optional[int]
    users_remaining: Optional[int]
    users_overage: int
    
    # Verifications
    verifications_used: int
    verifications_limit: Optional[int]
    verifications_remaining: Optional[int]
    verifications_overage: int
    
    # Charges
    base_charge_aud: Decimal
    overage_charges_aud: Decimal
    total_charges_aud: Decimal
    
    # Next billing
    next_billing_date: Optional[date]


class ContactType(str, Enum):
    CUSTOMER = "customer"
    SUPPLIER = "supplier"
    SHIPPER = "shipper"
    CONSIGNEE = "consignee"
    CUSTOMS_AGENT = "customs_agent"

class AddressBookBase(BaseModel):
    contact_type: ContactType
    name: str = Field(..., max_length=255)
    company_name: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    
    # Address
    address_line_1: Optional[str] = Field(None, max_length=255)
    address_line_2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=2, description="2-letter country code")
    
    # Metadata
    notes: Optional[str] = None
    is_favorite: bool = Field(default=False)

class AddressBookCreate(AddressBookBase):
    company_id: str
    created_by: str

class AddressBookUpdate(BaseModel):
    contact_type: Optional[ContactType] = None
    name: Optional[str] = None
    company_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    notes: Optional[str] = None
    is_favorite: Optional[bool] = None

class AddressBookResponse(AddressBookBase):
    contact_id: int
    company_id: str
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class LogActionCategory(str, Enum):
    AUTH = "auth"
    DOCUMENT = "document"
    VERIFICATION = "verification"
    SHIPMENT = "shipment"
    BILLING = "billing"
    USER_MANAGEMENT = "user_management"
    COMPANY = "company"

class LogStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    ERROR = "error"

class LogBase(BaseModel):
    # Scope
    company_id: Optional[str] = None
    user_id: Optional[str] = None
    
    # Action
    action_type: str = Field(..., max_length=100, description="e.g., 'document_created', 'user_login'")
    action_category: LogActionCategory
    
    # Target resource
    resource_type: str = Field(..., max_length=50, description="e.g., 'file', 'shipment', 'user'")
    resource_id: str = Field(..., max_length=100)
    
    # Details
    details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Action details JSON")
    changes: Optional[Dict[str, Any]] = Field(None, description="Before/after changes JSON")
    
    # Request info
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = Field(None, max_length=500)
    request_id: Optional[str] = Field(None, max_length=100)
    
    # Result
    status: LogStatus
    error_message: Optional[str] = None

class LogCreate(LogBase):
    created_at: datetime = Field(default_factory=datetime.utcnow)

class LogResponse(LogBase):
    log_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class LogFilter(BaseModel):
    """Query parameters for filtering logs"""
    company_id: Optional[str] = None
    user_id: Optional[str] = None
    action_type: Optional[str] = None
    action_category: Optional[LogActionCategory] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    status: Optional[LogStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)

# ==========================================
# BULK OPERATIONS & SPECIAL SCHEMAS
# ==========================================

class BulkDocumentCreate(BaseModel):
    """Create multiple documents at once"""
    shipment_id: str
    documents: List[FileCreate] = Field(..., min_items=1, max_items=20)

class BulkDocumentResponse(BaseModel):
    """Response for bulk document creation"""
    success: bool
    shipment_id: str
    total_documents: int
    successful: int
    failed: int
    results: List[Dict[str, Any]]  

class DocumentVerificationRequest(BaseModel):
    """Request to verify a document"""
    file_id: int

class ReVerificationRequest(BaseModel):
    """Request to re-verify a failed document"""
    file_id: int

class DocumentDraftSave(BaseModel):
    """Save document draft to Redis"""
    shipment_id: str
    document_type: DocumentType
    form_data: Dict[str, Any]

class DocumentDraftResponse(BaseModel):
    """Response for draft save"""
    success: bool
    message: str
    expires_in: int  

class DocumentDraftsResponse(BaseModel):
    """Get all drafts for a shipment"""
    shipment_id: str
    drafts: Dict[str, Dict[str, Any]]  

# ==========================================
# SIGNATURE LIBRARY SCHEMAS (Database Storage)
# ==========================================
class SignatureBase(BaseModel):
    signature_name: str = Field(..., max_length=100, description="Display name like 'My Signature' ")
    is_default: bool = Field(default=False, description="Use this signature by default")
    notes: Optional[str] = Field(None, description="Optional Notes")

class SignatureLibraryCreate(SignatureBase):
    pass

class SignatureLibraryUpdate(SignatureBase):
    signature_name: Optional[str] = Field(None, max_length=100)
    is_default: Optional[bool] = None
    notes: Optional[str] = None

class SignatureLibraryResponse(SignatureBase):
    signature_id: int
    user_id: str
    comapny_id: str

    file_size_bytes: int
    mime_type:str

    created_at: str
    updated_at: str

    class Config:
        from_attribute = True

class SignatureDataResponse(BaseModel):
    """Response when requesting actual signature image data"""
    signature_id: int
    signature_name: str
    mime_type: str
    signature_data_base64: str = Field(..., description="Base64 encoded image - data:image/png;base64,...")

class SignatureUploadRequest(BaseModel):
    """Metadata when uploading signature via multipart form"""
    signature_name: str = Field(..., max_length=100)
    is_default: bool = Field(default=False)
    notes: Optional[str] = None

class SignatureUploadResponse(BaseModel):
    success: bool
    signature_id: int
    message: str
    signature: SignatureLibraryResponse

class SignatureListResponse(BaseModel):
    """Response for listing signatures"""
    total: int
    signatures: List[SignatureLibraryResponse]
    default_signature_id: Optional[int] = None
    
# ==========================================
# ADMIN SCHEMAS (Simplified - MVP)
# ==========================================

# ===== ADMIN AUTHENTICATION =====

class AdminRole(str, Enum):
    SUPER_ADMIN = "super_admin"      # Full access
    ADMIN = "admin"                   # Most functions
    SALES = "sales"                   # Contract negotiations only

class AdminUserBase(BaseModel):
    """Internal ChainDoX staff users"""
    email: EmailStr
    username: str = Field(..., max_length=100)
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    admin_role: AdminRole
    is_active: bool = Field(default=True)

class AdminUserCreate(AdminUserBase):
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v

class AdminUserResponse(AdminUserBase):
    admin_id: str
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AdminLogin(BaseModel):
    email: EmailStr
    password: str

class AdminToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin_user: AdminUserResponse

# ===== CONTRACT NEGOTIATION MANAGEMENT (Basic) =====

class NegotiationListResponse(BaseModel):
    """List negotiations for admin dashboard"""
    total: int
    pending: int
    accepted: int
    rejected: int
    negotiations: List[ContractNegotiationResponse]

# ===== CONTRACT CREATION =====

class ContractCreateFromNegotiation(BaseModel):
    """Create contract from accepted negotiation"""
    negotiation_id: int
    
    # Contract terms
    contract_start_date: date = Field(default_factory=date.today)
    contract_end_date: date
    contract_renewal_type: ContractRenewalType = Field(default=ContractRenewalType.MANUAL)
    
    # SLA (optional)
    sla_uptime_guarantee: Optional[Decimal] = Field(None, ge=0, le=100)
    sla_support_response_hours: Optional[int] = Field(None, ge=0)
    
    # Contract document
    contract_document_url: Optional[str] = Field(None, max_length=500, description="URL to signed contract PDF")

class ContractCreateManual(BaseModel):
    """Manually create custom contract without negotiation"""
    company_id: str
    plan_id: int
    
    # Custom pricing
    custom_monthly_price_aud: Decimal = Field(..., gt=0)
    custom_annual_price_aud: Optional[Decimal] = Field(None)
    
    # Custom limits
    custom_shipments_limit: Optional[int] = Field(None, ge=0)
    custom_verifications_limit: Optional[int] = Field(None, ge=0)
    custom_users_limit: int = Field(..., ge=1)
    
    # Contract terms
    contract_start_date: date
    contract_end_date: date
    contract_renewal_type: ContractRenewalType
    
    # SLA (optional)
    sla_uptime_guarantee: Optional[Decimal] = Field(None, ge=0, le=100)
    sla_support_response_hours: Optional[int] = Field(None, ge=0)
    
    # Document
    contract_document_url: Optional[str] = None
    signed_by: EmailStr

class ContractCreateResponse(BaseModel):
    success: bool
    message: str
    company: CompanyResponse
    contract_created_at: datetime

# ===== COMPANY MANAGEMENT (Basic) =====

class CompanyListFilter(BaseModel):
    """Basic filters for company list"""
    company_type: Optional[CompanyType] = None
    subscription_status: Optional[SubscriptionStatus] = None
    plan_id: Optional[int] = None
    is_custom_contract: Optional[bool] = None
    search: Optional[str] = Field(None, description="Search by company name or email")
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)

class CompanyListResponse(BaseModel):
    total: int
    companies: List[CompanyResponse]

class CompanySuspend(BaseModel):
    """Suspend/unsuspend company account"""
    reason: str = Field(..., description="Reason for suspension")

# ===== BILLING OVERVIEW (Basic) =====

class BillingOverview(BaseModel):
    """Basic billing overview for admin dashboard"""
    period_start: date
    period_end: date
    
    # Revenue
    total_revenue: Decimal
    
    # Customers
    total_customers: int
    active_customers: int
    trial_customers: int
    
    # By plan
    revenue_by_plan: Dict[str, Decimal]
    customers_by_plan: Dict[str, int]

class InvoiceListFilter(BaseModel):
    """Filter invoices"""
    company_id: Optional[str] = None
    status: Optional[InvoiceStatus] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)

class InvoiceAdminResponse(BaseModel):
    """Basic invoice details"""
    invoice_id: str
    company_id: str
    company_name: str
    
    billing_period_start: date
    billing_period_end: date
    
    # Charges
    base_charge: Decimal
    overage_charges: Decimal
    total_amount: Decimal
    
    # Status
    status: InvoiceStatus
    issued_at: datetime
    due_date: date

class InvoiceListResponse(BaseModel):
    total: int
    total_outstanding: Decimal
    invoices: List[InvoiceAdminResponse]

# ===== ADMIN DASHBOARD =====

class AdminDashboardOverview(BaseModel):
    
    total_customers: int
    active_customers: int
    total_mrr: Decimal
    pending_negotiations: int
    overdue_invoices: int
    recent_signups: List[CompanyResponse]
ShipmentResponse.model_rebuild()
FolderResponse.model_rebuild()