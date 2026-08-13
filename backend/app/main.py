from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from .config import settings
from .db import init_db,SessionLocal
from .models import Plan
from .plans import PLANS
from .routers import auth,dashboard,payments,vpn
@asynccontextmanager
async def lifespan(app):
    await init_db()
    async with SessionLocal() as db:
        for code,p in PLANS.items():
            if not await db.scalar(select(Plan).where(Plan.code==code)): db.add(Plan(code=code,title=p['title'],price_rub=p['price'],duration_days=p['days'],traffic_gb=None))
        await db.commit()
    yield
app=FastAPI(title=settings.app_name,version='1.1.0')
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in settings.cors_origins.split(',') if x.strip()],allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
app.include_router(auth.router);app.include_router(dashboard.router);app.include_router(payments.router);app.include_router(vpn.router)
@app.get('/api/health')
async def health(): return {'status':'ok'}
