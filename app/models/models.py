import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Numeric, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class PaymentStatus(str, enum.Enum):
    CREATED = "created"
    PAID = "paid"
    EXPIRED = "expired"


class Merchant(Base):
    __tablename__ = "merchants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    api_key = Column(String, unique=True, nullable=True, index=True)  # For API authentication
    stellar_address = Column(String, nullable=True)
    webhook_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    payment_sessions = relationship("PaymentSession", back_populates="merchant")


class PaymentSession(Base):
    __tablename__ = "payment_sessions"
    
    id = Column(String, primary_key=True)  # pay_xxx format
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), nullable=False)
    amount_fiat = Column(Numeric(precision=10, scale=2), nullable=False)
    fiat_currency = Column(String, nullable=False)
    amount_usdc = Column(String, nullable=False)
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.CREATED, nullable=False)
    success_url = Column(String, nullable=False)
    cancel_url = Column(String, nullable=False)
    tx_hash = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    paid_at = Column(DateTime, nullable=True)
    
    # Relationships
    merchant = relationship("Merchant", back_populates="payment_sessions")


class Admin(Base):
    __tablename__ = "admins"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
