import json,uuid
from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..models import Order,Plan,PaymentEvent,User
from ..payments import create_yookassa_payment,create_cryptocloud_invoice
from ..security import decode_user_id
from ..services import activate_order
router=APIRouter(prefix='/api/payments',tags=['payments'])
class Checkout(BaseModel): plan:str;provider:str
@router.post('/checkout')
async def checkout(data:Checkout,request:Request,db:AsyncSession=Depends(get_db)):
    uid=decode_user_id(request);plan=await db.scalar(select(Plan).where(Plan.code==data.plan,Plan.is_active==True));u=await db.get(User,uid)
    if not plan: raise HTTPException(400,'Неизвестный тариф')
    if data.provider not in ('yookassa','cryptocloud'): raise HTTPException(400,'Неизвестный провайдер')
    oid='NEX-'+uuid.uuid4().hex[:16].upper();o=Order(public_id=oid,user_id=uid,plan_id=plan.id,amount=plan.price_rub,provider=data.provider);db.add(o);await db.commit()
    try:
        pid,url=await (create_yookassa_payment(float(plan.price_rub),f'{plan.title} — NEXUS VPN',oid) if data.provider=='yookassa' else create_cryptocloud_invoice(float(plan.price_rub),oid,u.email))
        if not url: raise RuntimeError('провайдер не вернул payment URL')
        o.provider_payment_id=pid;o.payment_url=url;await db.commit();return {'order_id':oid,'payment_url':url}
    except Exception as e:
        o.status='failed';await db.commit();raise HTTPException(502,str(e))
async def event(db,provider,key,payload,order):
    if await db.scalar(select(PaymentEvent).where(PaymentEvent.event_key==key)): return
    db.add(PaymentEvent(provider=provider,event_key=key,payload=json.dumps(payload,ensure_ascii=False)));await db.commit()
    if order: await activate_order(db,order)
@router.post('/webhook/yookassa')
async def yookassa(request:Request,db:AsyncSession=Depends(get_db)):
    p=await request.json();obj=p.get('object',{});oid=(obj.get('metadata') or {}).get('order_id');o=await db.scalar(select(Order).where(Order.public_id==oid)) if oid else None
    if p.get('event')=='payment.succeeded' and obj.get('status')=='succeeded': await event(db,'yookassa',f"yookassa:{obj.get('id')}:{p.get('event')}",p,o)
    return {'ok':True}
@router.post('/webhook/cryptocloud')
async def cryptocloud(request:Request,db:AsyncSession=Depends(get_db)):
    p=await request.json();x=p.get('data') or p.get('result') or p;oid=x.get('order_id') if isinstance(x,dict) else None;status=str(x.get('status','')).lower() if isinstance(x,dict) else ''
    if status in ('paid','success','succeeded','confirmed','completed') and oid:
        o=await db.scalar(select(Order).where(Order.public_id==oid));await event(db,'cryptocloud',f"cryptocloud:{x.get('uuid') or x.get('invoice_id') or oid}",p,o)
    return {'ok':True}
