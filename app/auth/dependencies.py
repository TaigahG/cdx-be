from fastapi import Request, HTTPException, status, Depends
from sqlalchemy.orm import Session
from jwt.exceptions import PyJWTError as JWTError
from auth.jwt_utils import verify_access_token
from database import get_db
from models import User


def get_current_user(request: Request, db:Session = Depends(get_db)) -> User:
    token = request.cookies.get("accessToken")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,detail="Not Authorized"
        )
    
    try:
        payload = verify_access_token(token)
        user_id = payload.get("user_id")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not Authorized"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,detail="Not Authorized"
        )
    
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,detail="Not Authorized"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,detail="Account is deactivated"
        )
    
    return user