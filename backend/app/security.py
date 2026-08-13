from datetime import datetime,timedelta,timezone
import jwt
from fastapi import HTTPException,Request,status
from pwdlib import PasswordHash
from .config import settings
password_hash=PasswordHash.recommended()
def hash_password(p): return password_hash.hash(p)
def verify_password(p,h): return password_hash.verify(p,h)
def create_access_token(uid):
    exp=datetime.now(timezone.utc)+timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({"sub":str(uid),"exp":exp},settings.secret_key,algorithm="HS256")
def decode_user_id(request:Request):
    token=request.cookies.get("access_token")
    if not token: raise HTTPException(status_code=401,detail="Требуется авторизация")
    try: return int(jwt.decode(token,settings.secret_key,algorithms=["HS256"])["sub"])
    except Exception: raise HTTPException(status_code=401,detail="Сессия недействительна")
