import jwt 
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET")
REFRESH_TOKEN_SECRET = os.getenv("REFRESH_TOKEN_SECRET")
ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(user_id: str)-> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"user_id": user_id, "exp":expire, "type":"access"}
    return jwt.encode(payload, ACCESS_TOKEN_SECRET, algorithm=ALGORITHM)

def create_refresh_token(user_id: str)-> str:
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"user_id":user_id, "exp":expire, "type":"refresh"}
    return jwt.encode(payload, REFRESH_TOKEN_SECRET, algorithm=ALGORITHM)

def verify_access_token(token:str)->dict:
    return jwt.decode(token, ACCESS_TOKEN_SECRET, algorithms=[ALGORITHM])

def verify_refresh_token(token:str)->dict:
    return jwt.decode(token, REFRESH_TOKEN_SECRET, algorithms=[ALGORITHM])