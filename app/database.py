# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL")
environment = os.getenv("ENVIRONMENT", "development")

# SSL configuration for production
connect_args = {}
if os.getenv("ENVIRONMENT") == "production":
    connect_args = {
        "sslmode": "verify-full",
        "sslrootcert": "certs/global-bundle.pem"
    }
else:
    connect_args = {
        "sslmode": "require"
    }
if "?" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.split("?")[0]
# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()