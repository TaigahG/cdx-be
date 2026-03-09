from sqlalchemy import create_engine, text
import os 
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

admin_url = DATABASE_URL.replace("/postgres?", "/postgres?").replace("/chaindox?", "/postgres?")

print("Creating chaindox database")

try:
    engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with engine.connect() as connection:
        result = connection.execute(text(
            "SELECT 1 FROM pg_database WHERE datname='chaindox'"
        ))
        if result.fetchone():
            print("DAtabse 'chaindox' already exists")
        else:
            connection.execute(text("CREATE DATABASE chaindox"))
            print("Database 'chaindox' created successfully")
    engine.dispose()

    print("SUCCESS")
except Exception as e:
    print(f"Error: {str(e)}")


