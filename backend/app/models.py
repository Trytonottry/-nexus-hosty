from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

def utcnow(): return datetime.now(timezone.utc)
class User(Base):
    __tablename__="users"
    id: Mapped[int]=mapped_column(primary_key=True)
    email: Mapped[str]=mapped_column(String(320),unique=True,index=True)
    password_hash: Mapped[str]=mapped_column(String(255))
    is_active: Mapped[bool]=mapped_column(Boolean,default=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
class Plan(Base):
    __tablename__="plans"
    id: Mapped[int]=mapped_column(primary_key=True)
    code: Mapped[str]=mapped_column(String(32),unique=True)
    title: Mapped[str]=mapped_column(String(64))
    price_rub: Mapped[float]=mapped_column(Numeric(10,2))
    duration_days: Mapped[int]=mapped_column(Integer)
    traffic_gb: Mapped[int|None]=mapped_column(Integer,nullable=True)
    is_active: Mapped[bool]=mapped_column(Boolean,default=True)
class Subscription(Base):
    __tablename__="subscriptions"
    id: Mapped[int]=mapped_column(primary_key=True)
    user_id: Mapped[int]=mapped_column(ForeignKey("users.id"),index=True)
    plan_id: Mapped[int]=mapped_column(ForeignKey("plans.id"))
    starts_at: Mapped[datetime]=mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime]=mapped_column(DateTime(timezone=True))
    traffic_limit_gb: Mapped[int|None]=mapped_column(Integer,nullable=True)
    traffic_used_mb: Mapped[int]=mapped_column(Integer,default=0)
    status: Mapped[str]=mapped_column(String(32),default="pending",index=True)
    xui_node: Mapped[str|None]=mapped_column(String(64),nullable=True)
    xui_email: Mapped[str|None]=mapped_column(String(320),nullable=True,index=True)
    xui_sub_id: Mapped[str|None]=mapped_column(String(128),nullable=True,index=True)
    vpn_config_url: Mapped[str|None]=mapped_column(Text,nullable=True)
    vpn_links_json: Mapped[str|None]=mapped_column(Text,nullable=True)
class Order(Base):
    __tablename__="orders"
    id: Mapped[int]=mapped_column(primary_key=True)
    public_id: Mapped[str]=mapped_column(String(64),unique=True,index=True)
    user_id: Mapped[int]=mapped_column(ForeignKey("users.id"),index=True)
    plan_id: Mapped[int]=mapped_column(ForeignKey("plans.id"))
    amount: Mapped[float]=mapped_column(Numeric(10,2))
    currency: Mapped[str]=mapped_column(String(8),default="RUB")
    provider: Mapped[str]=mapped_column(String(32))
    provider_payment_id: Mapped[str|None]=mapped_column(String(255),nullable=True,index=True)
    status: Mapped[str]=mapped_column(String(32),default="pending",index=True)
    payment_url: Mapped[str|None]=mapped_column(Text,nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    paid_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
class PaymentEvent(Base):
    __tablename__="payment_events"
    id: Mapped[int]=mapped_column(primary_key=True)
    provider: Mapped[str]=mapped_column(String(32))
    event_key: Mapped[str]=mapped_column(String(255),unique=True,index=True)
    payload: Mapped[str]=mapped_column(Text)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
