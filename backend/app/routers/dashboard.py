import json
from datetime import datetime,timezone
from fastapi import APIRouter,Request,Depends,HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..models import User,Subscription,Order,Plan
from ..security import decode_user_id
from ..provisioning import sync_subscription
router=APIRouter(prefix='/api/dashboard',tags=['dashboard'])
@router.get('')
async def dashboard(request:Request,db:AsyncSession=Depends(get_db)):
    uid=decode_user_id(request);u=await db.get(User,uid)
    if not u: raise HTTPException(401,'Пользователь не найден')
    subs=(await db.execute(select(Subscription).where(Subscription.user_id==uid).order_by(Subscription.expires_at.desc()))).scalars().all();now=datetime.now(timezone.utc);out=[]
    for s in subs:
        if s.xui_email and s.status in ('active','provisioning_error'): 
            try: await sync_subscription(db,s)
            except Exception: pass
        rem=max(0,int((s.expires_at-now).total_seconds()))
        if rem==0 and s.status=='active': s.status='expired'
        links=json.loads(s.vpn_links_json or '[]')
        out.append({'id':s.id,'plan':s.plan.title if hasattr(s,'plan') else (await db.get(Plan,s.plan_id)).title,'status':s.status,'starts_at':s.starts_at.isoformat(),'expires_at':s.expires_at.isoformat(),'remaining_seconds':rem,'remaining_days':rem//86400,'traffic_limit_gb':s.traffic_limit_gb,'traffic_used_mb':s.traffic_used_mb,'traffic_remaining_gb':None if s.traffic_limit_gb is None else max(0,s.traffic_limit_gb-s.traffic_used_mb/1024),'vpn_links':links,'xui_node':s.xui_node})
    orders=(await db.execute(select(Order,Plan).join(Plan,Order.plan_id==Plan.id).where(Order.user_id==uid).order_by(Order.created_at.desc()).limit(20))).all()
    history=[{'id':o.public_id,'plan':p.title,'amount':float(o.amount),'provider':o.provider,'status':o.status,'created_at':o.created_at.isoformat()} for o,p in orders]
    await db.commit();return {'email':u.email,'subscriptions':out,'orders':history}
