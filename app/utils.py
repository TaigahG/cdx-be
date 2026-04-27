"""
Utility functions for ChainDoX backend
"""

import re
import random
from sqlalchemy.orm import Session


def slugify(text: str, max_length: int = 20) -> str:
    """
    Convert text to URL-friendly slug
    
    Examples:
        "ABC Trading Ltd" -> "ABC_TRADING"
        "John's Company" -> "JOHNS_COMPANY"
        "123 Corp & Co." -> "123_CORP_CO"
    """
    # Convert to uppercase
    text = text.upper()
    
    # Remove special characters, keep alphanumeric and spaces
    text = re.sub(r'[^A-Z0-9\s]', '', text)
    
    # Replace spaces with underscores
    text = re.sub(r'\s+', '_', text.strip())
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length]
    
    # Remove trailing underscores
    text = text.rstrip('_')
    
    return text


def generate_random_suffix(length: int = 4) -> str:
    """Generate random numeric suffix"""
    return str(random.randint(10**(length-1), 10**length - 1))


def generate_company_id(company_name: str, db: Session = None) -> str:
    """
    Generate unique company ID: COMPANY_NAME_1234
    
    Args:
        company_name: Company name to slugify
        db: Optional database session to check uniqueness
    
    Returns:
        Unique company ID like "ABC_TRADING_7382"
    """
    slug = slugify(company_name, max_length=20)
    
    # Generate ID with random suffix
    max_attempts = 10
    for _ in range(max_attempts):
        suffix = generate_random_suffix(4)
        company_id = f"{slug}_{suffix}"
        
        # If no DB session, return first attempt
        if db is None:
            return company_id
        
        # Check if ID already exists
        from crud.company_crud import company_exists
        if not company_exists(db, company_id):
            return company_id
    
    # Fallback: use longer random suffix if collision
    suffix = generate_random_suffix(6)
    return f"{slug}_{suffix}"


def generate_shipment_id(
    company_name: str = None, 
    shipment_name: str = None,
    db: Session = None
) -> str:
    """
    Generate unique shipment ID: SHIP_COMPANY_1234 or SHIP_1234
    
    Args:
        company_name: Optional company name for context
        shipment_name: Optional shipment name for context
        db: Optional database session to check uniqueness
    
    Returns:
        Unique shipment ID like "SHIP_ABC_7382"
    """
    # Use company name or shipment name for prefix
    if company_name:
        slug = slugify(company_name, max_length=15)
        prefix = f"SHIP_{slug}"
    elif shipment_name:
        slug = slugify(shipment_name, max_length=15)
        prefix = f"SHIP_{slug}"
    else:
        prefix = "SHIP"
    
    # Append shipment name as-is (uppercased, trimmed) if provided
    name_suffix = f"_{shipment_name.strip().upper()}" if shipment_name else ""

    # Generate ID with random suffix
    max_attempts = 10
    for _ in range(max_attempts):
        suffix = generate_random_suffix(4)
        shipment_id = f"{prefix}_{suffix}{name_suffix}"

        # If no DB session, return first attempt
        if db is None:
            return shipment_id

        # Check if ID already exists
        from crud.shipment_crud import shipment_exists
        if not shipment_exists(db, shipment_id):
            return shipment_id

    # Fallback: use longer random suffix if collision
    suffix = generate_random_suffix(6)
    return f"{prefix}_{suffix}{name_suffix}"


def generate_user_id(email: str, db: Session = None) -> str:
    """
    Generate unique user ID: USER_EMAIL_1234
    
    Args:
        email: User email
        db: Optional database session to check uniqueness
    
    Returns:
        Unique user ID like "USER_JOHN_7382"
    """
    # Extract username from email
    username = email.split('@')[0]
    slug = slugify(username, max_length=15)
    
    # Generate ID with random suffix
    max_attempts = 10
    for _ in range(max_attempts):
        suffix = generate_random_suffix(4)
        user_id = f"USER_{slug}_{suffix}"
        
        # If no DB session, return first attempt
        if db is None:
            return user_id
        
        # Check if ID already exists
        from crud.user_crud import get_user
        if not get_user(db, user_id):
            return user_id
    
    # Fallback: use longer random suffix if collision
    suffix = generate_random_suffix(6)
    return f"USER_{slug}_{suffix}"