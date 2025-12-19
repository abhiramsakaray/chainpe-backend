from pydantic import BaseModel, EmailStr, Field, HttpUrl
from typing import Optional
from datetime import datetime
from decimal import Decimal


# ============= AUTH SCHEMAS =============

class MerchantRegister(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8)


class MerchantLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    api_key: str  # Merchant's API key for creating payment sessions


# ============= MERCHANT SCHEMAS =============

class MerchantProfileUpdate(BaseModel):
    stellar_address: Optional[str] = None
    webhook_url: Optional[HttpUrl] = None


class MerchantProfile(BaseModel):
    id: str
    name: str
    email: str
    stellar_address: Optional[str]
    webhook_url: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= PAYMENT SESSION SCHEMAS =============

class PaymentSessionCreate(BaseModel):
    amount_usdc: Decimal = Field(..., gt=0, description="Amount in USDC")
    order_id: str = Field(..., min_length=1, max_length=255, description="Your order/transaction ID")
    success_url: Optional[str] = Field(None, description="URL to redirect to after successful payment")
    cancel_url: Optional[str] = Field(None, description="URL to redirect to if payment is cancelled")
    metadata: Optional[dict] = Field(None, description="Optional metadata (customer info, items, etc.)")


class PaymentSessionResponse(BaseModel):
    session_id: str
    checkout_url: str
    amount_usdc: Decimal
    order_id: Optional[str] = None
    expires_at: datetime
    status: str
    success_url: Optional[str]
    cancel_url: Optional[str]


class PaymentSessionStatus(BaseModel):
    session_id: str
    status: str
    amount_usdc: str
    order_id: Optional[str]
    tx_hash: Optional[str]
    created_at: datetime
    paid_at: Optional[datetime]
    expires_at: Optional[datetime]
    metadata: Optional[dict]
    
    class Config:
        from_attributes = True


class PaymentSessionDetail(BaseModel):
    id: str
    merchant_name: str
    merchant_stellar_address: Optional[str]
    amount_fiat: Decimal
    fiat_currency: str
    amount_usdc: str
    status: str
    success_url: str
    cancel_url: str
    tx_hash: Optional[str]
    created_at: datetime
    paid_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ============= WEBHOOK SCHEMAS =============

class WebhookPayload(BaseModel):
    event: str
    session_id: str
    amount: str
    currency: str
    tx_hash: str


# ============= ADMIN SCHEMAS =============

class MerchantListItem(BaseModel):
    id: str
    name: str
    email: str
    stellar_address: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class PaymentListItem(BaseModel):
    id: str
    merchant_id: str
    merchant_name: str
    amount_fiat: Decimal
    fiat_currency: str
    amount_usdc: str
    status: str
    tx_hash: Optional[str]
    created_at: datetime
    paid_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class MerchantDisable(BaseModel):
    is_active: bool
