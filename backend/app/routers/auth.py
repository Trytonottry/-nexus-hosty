from fastapi import APIRouter,Depends,HTTPException,Response,Request
from pydantic import BaseModel,EmailStr,Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..models import User
from ..security import hash_password,verify_password,create_access_token,decode_user_id
router=APIRouter(prefix="/api/auth",tags=["auth"])
class Credentials(BaseModel): email:EmailStr;password:str=Field(min_length=8,max_length=128)
def cookie(response,token): response.set_cookie("access_token",token,httponly=True,secure=__import__('app.config',fromlist=['settings']).settings.cookie_secure,samesite="lax",max_age=86400,path="/")
@router.post('/register')
async def register(data:Credentials,response:Response,db:AsyncSession=Depends(get_db)):
    email=data.email.lower()
    if await db.scalar(select(User).where(User.email==email)): raise HTTPException(409,"Пользователь уже зарегистрирован")
    u=User(email=email,password_hash=hash_password(data.password));db.add(u);await db.commit();await db.refresh(u);cookie(response,create_access_token(u.id));return {"ok":True,"email":u.email}
@router.post('/login')
async def login(data:Credentials,response:Response,db:AsyncSession=Depends(get_db)):
    u=await db.scalar(select(User).where(User.email==data.email.lower()))
    if not u or not verify_password(data.password,u.password_hash): raise HTTPException(401,"Неверный email или пароль")
    cookie(response,create_access_token(u.id));return {"ok":True,"email":u.email}
@router.post('/logout')
async def logout(response:Response): response.delete_cookie('access_token',path='/');return {'ok':True}
@router.get('/me')
async def me(request:Request,db:AsyncSession=Depends(get_db)):
    u=await db.get(User,decode_user_id(request))
    if not u: raise HTTPException(401,'Пользователь не найден')
    return {'id':u.id,'email':u.email}
