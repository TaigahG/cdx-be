# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ChainDoX Backend (cdx-be) is a FastAPI-based REST API for a blockchain-based trade document verification and management platform. The system handles TradeTrust documents (electronic trade receipts, bills of lading, etc.) with multi-tenant SaaS architecture supporting different company types (exporters, banks, associations, governments, verifiers).

## Technology Stack

- **Framework**: FastAPI + Uvicorn
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Migrations**: Alembic
- **Authentication**: python-jose (JWT) + passlib (bcrypt)
- **Validation**: Pydantic v2
- **Cloud**: AWS (boto3 for S3)
- **Environment**: Python 3.9+

## Common Commands

### Setup & Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Setup database (first time)
python create_database.py

# Run migrations
alembic upgrade head

# Seed default permissions
python seed_permissions.py
```

### Running the Application
```bash
# Development server
uvicorn app.main:app --reload

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```


### Deploy to aws
```bash
docker build --platform linux/amd64 -t chaindox-backend .
docker tag chaindox-backend:latest 570044538513.dkr.ecr.ap-southeast-2.amazonaws.com/chaindox/backend:vx.x
docker push 570044538513.dkr.ecr.ap-southeast-2.amazonaws.com/chaindox/backend:vx.x
#current version is v2.3, each update sub version max is vx.5. Then start new version, example if reach v2.5 reach to v3.0, etc.
```

### Database Operations
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Upgrade to latest
alembic upgrade head

# Downgrade one revision
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

## Architecture

### Database Schema

The system uses a **multi-tenant architecture** with 8 core model groups:

1. **Plan & Pricing** (`PlanCategory`, `Plan`)
   - Tiered subscription plans (Free=0, Starter=1, Growth=2, Enterprise=3)
   - Feature flags (API access, bulk verification, branded portal, SLA, etc.)
   - Usage limits and overage pricing

2. **Company & Contracts** (`Company`, `ContractNegotiation`)
   - Company types: exporter, association, bank, government, verifier
   - Custom contracts with negotiated pricing
   - Subscription status: trial, active, past_due, cancelled, expired
   - Stripe integration for payments

3. **Users & Permissions** (`User`, `Permission`)
   - Role-based access control: owner, admin, member, viewer
   - Permission system controls 17 different capabilities
   - User invitation system with tracking

4. **Admin Users** (`AdminUser`)
   - Internal staff (super_admin, admin, sales)
   - Separate from customer users

5. **Shipments & Documents** (`Shipment`, `File`, `Folder`, `DocumentVerification`)
   - **Files store TradeTrust documents as JSONB** in `document_data` field
   - Document types: bill_of_lading, commercial_invoice, packing_list, certificate_of_origin, etr
   - Blockchain metadata: credential_id, token_id, token_registry, blockchain_network
   - QR code generation for public verification

6. **Signature Library** (`SignatureLibrary`)
   - Base64-encoded signature images stored in database
   - Per-user signature management

7. **Usage Tracking** (`CompanyUsage`)
   - Billing period tracking
   - Overage calculations for shipments, verifications, users
   - Invoice generation

8. **Audit Logs** (`Log`)
   - Action categories: auth, document, verification, shipment, billing, user_management, company
   - Tracks changes with before/after JSON

### Key Relationships

- `Company` → `Plan` (many-to-one)
- `Company` → `User` (one-to-many)
- `User` → `Permission` via role FK (many-to-one)
- `Shipment` → `File` (one-to-many)
- `File` → `DocumentVerification` (one-to-many)
- `Folder` → self-reference for nested folders

### Database Connection

Uses PostgreSQL with SSL configuration:
- **Production**: `sslmode=verify-full` with `certs/global-bundle.pem`
- **Development**: `sslmode=require`
- Connection pooling: 10 base connections, 20 max overflow

Database URL format is parsed from `.env` file's `DATABASE_URL` variable. The system automatically strips query parameters and applies SSL settings via `connect_args`.

## File Organization

```
app/
├── main.py          # FastAPI app entry point (currently empty)
├── models.py        # SQLAlchemy models (all 8 model groups)
├── schemas.py       # Pydantic schemas for request/response validation
├── database.py      # DB engine, session management, get_db() dependency
├── crud.py          # Database operations (currently empty)
└── routers/         # API route handlers (empty - routes not implemented yet)

alembic/
├── versions/        # Migration files
└── env.py          # Alembic environment config

create_database.py   # Creates 'chaindox' database
seed_permissions.py  # Seeds 4 default permission roles
test_connection.py   # Database connection test utility
```

## Important Implementation Details

### TradeTrust Document Structure

The `File.document_data` JSONB field must contain:
- `@context`: TradeTrust context
- `type`: Document type
- `credentialSubject`: Document payload
- `issuer`: Issuing entity

Validation is enforced in `FileCreate` schema (schemas.py:551-558).

### Permission System

Four roles are seeded by default (seed_permissions.py):
- **owner**: Full access (17/17 permissions)
- **admin**: Operational access (14/17 - no plan/payment changes)
- **member**: Document creation (7/17 permissions)
- **viewer**: Read-only + verification (3/17 permissions)

### ID Generation

- `User.id`: String (100) - likely UUID
- `Company.company_id`: String (100) - likely UUID
- `AdminUser.admin_id`: String (100) - likely UUID
- `Shipment.shipment_id`: String (100) - likely UUID
- All other entities use auto-incrementing integers

### Environment Variables

Required in `.env`:
- `DATABASE_URL`: PostgreSQL connection string
- `ENVIRONMENT`: "development" or "production" (affects SSL mode)

## Development Workflow

### Adding New Features

1. **Models**: Add/modify SQLAlchemy models in `models.py`
2. **Migration**: Run `alembic revision --autogenerate -m "description"`
3. **Schemas**: Add Pydantic schemas in `schemas.py` for validation
4. **CRUD**: Implement database operations in `crud.py`
5. **Routes**: Create router in `app/routers/`
6. **Main**: Register router in `app/main.py`

### Current State

The project has:
- ✅ Complete database schema (models.py)
- ✅ Complete Pydantic schemas (schemas.py)
- ✅ Database connection setup (database.py)
- ✅ Initial migration
- ✅ Permission seeding
- ❌ No API routes implemented (main.py is empty)
- ❌ No CRUD operations (crud.py is empty)
- ❌ No authentication middleware

### Next Steps for API Implementation

1. Implement authentication (JWT token generation/validation)
2. Build CRUD operations for core entities
3. Create routers for: auth, companies, users, plans, shipments, files
4. Add TradeTrust integration for document verification
5. Implement QR code generation for documents
6. Add usage tracking and billing logic
7. Create admin endpoints

## Database Indexes

Key performance indexes are defined on:
- Company: `plan_id`, `subscription_status`, `company_type`
- User: `email`, `company_id`, `role`
- File: `company_id + created_at`, `shipment_id`, `credential_id`, `token_id`
- DocumentVerification: `file_id + verified_at`, `company_id + verified_at`
- Log: `company_id + created_at`, `user_id + created_at`, `action_type + created_at`

## Security Considerations

- Passwords are hashed with bcrypt (passlib)
- JWT tokens for authentication (python-jose)
- Password validation: min 8 chars, 1 digit, 1 uppercase
- SSL required for all database connections
- Multi-tenant isolation via `company_id` foreign keys
