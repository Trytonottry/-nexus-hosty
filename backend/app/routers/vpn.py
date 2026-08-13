import json
from fastapi import APIRouter,Request,Depends,HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..models import Subscription
from ..security import decode_user_id
from ..provisioning import provision_subscription
router=APIRouter(prefix='/api/vpn',tags=['vpn'])
@router.get('configs')
async def configs(request:Request,db:AsyncSession=Depends(get_db)):
    uid=decode_user_id(request);ss=(await db.execute(select(Subscription).where(Subscription.user_id==uid,Subscription.status.in_(['active','provisioning_error'])))).scalars().all()
    return {'subscriptions':[{'id':s.id,'email':s.xui_email,'node':s.xui_node,'links':json.loads(s.vpn_links_json or '[]'),'subscription_url':s.vpn_config_url,'expires_at':s.expires_at.isoformat()} for s in ss]}
@router.post('/retry/{subscription_id}')
async def retry(subscription_id:int,request:Request,db:AsyncSession=Depends(get_db)):
    uid=decode_user_id(request);s=await db.scalar(select(Subscription).where(Subscription.id==subscription_id,Subscription.user_id==uid))
    if not s: raise HTTPException(404,'Подписка не найдена')
    try:
        links=await provision_subscription(db,s);s.status='active';await db.commit();return {'ok':True,'links':links}
    except Exception as e: raise HTTPException(502,str(e))
