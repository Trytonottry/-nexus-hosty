import asyncio
from datetime import datetime,timezone
from sqlalchemy import select
from .db import SessionLocal,init_db
from .models import Subscription
from .provisioning import provision_subscription,sync_subscription
async def main():
    await init_db()
    while True:
        async with SessionLocal() as db:
            ss=(await db.execute(select(Subscription).where(Subscription.status.in_(['active','provisioning_error'])))).scalars().all()
            now=datetime.now(timezone.utc)
            for s in ss:
                if s.expires_at<=now: s.status='expired';continue
                try:
                    if not s.xui_email or s.status=='provisioning_error': await provision_subscription(db,s)
                    else: await sync_subscription(db,s)
                except Exception: pass
            await db.commit()
        await asyncio.sleep(60)
if __name__=='__main__': asyncio.run(main())
