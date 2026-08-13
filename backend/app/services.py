from datetime import datetime,timezone,timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Subscription,Plan,Order
from .provisioning import provision_subscription
async def activate_order(db,order):
    if order.status=="paid": return
    order.status="paid";order.paid_at=datetime.now(timezone.utc)
    plan=await db.get(Plan,order.plan_id);now=datetime.now(timezone.utc)
    result=await db.execute(select(Subscription).where(Subscription.user_id==order.user_id,Subscription.status.in_(["active","pending"])).order_by(Subscription.expires_at.desc()))
    current=result.scalars().first()
    if current and current.expires_at>now:
        current.expires_at=current.expires_at+timedelta(days=plan.duration_days);current.plan_id=plan.id;current.status="active"
        if plan.traffic_gb is not None: current.traffic_limit_gb=plan.traffic_gb
        sub=current
    else:
        sub=Subscription(user_id=order.user_id,plan_id=plan.id,starts_at=now,expires_at=now+timedelta(days=plan.duration_days),traffic_limit_gb=plan.traffic_gb,status="active")
        db.add(sub);await db.flush()
    await db.commit();await db.refresh(sub)
    try: await provision_subscription(db,sub)
    except Exception as exc:
        # Payment remains paid; provisioning can be retried by worker.
        sub.status="provisioning_error";await db.commit();raise RuntimeError(f"Платёж подтверждён, но VPN-клиент не создан: {exc}")
