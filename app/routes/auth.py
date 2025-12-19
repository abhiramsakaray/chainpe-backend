from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import secrets
from app.core import get_db, hash_password, verify_password, create_access_token
from app.models import Merchant, Admin
from app.schemas import MerchantRegister, MerchantLogin, TokenResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


def generate_api_key() -> str:
    """Generate a secure API key for merchant."""
    return f"pk_live_{secrets.token_urlsafe(32)}"


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_merchant(
    merchant_data: MerchantRegister,
    db: Session = Depends(get_db)
):
    """Register a new merchant."""
    # Check if email already exists
    existing_merchant = db.query(Merchant).filter(Merchant.email == merchant_data.email).first()
    if existing_merchant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new merchant with API key
    new_merchant = Merchant(
        name=merchant_data.name,
        email=merchant_data.email,
        password_hash=hash_password(merchant_data.password),
        api_key=generate_api_key(),  # Auto-generate API key on registration
    )
    
    db.add(new_merchant)
    db.commit()
    db.refresh(new_merchant)
    
    # Generate JWT token
    access_token = create_access_token(
        data={"sub": str(new_merchant.id), "role": "merchant"}
    )
    
    return TokenResponse(
        access_token=access_token,
        api_key=new_merchant.api_key
    )


@router.post("/login", response_model=TokenResponse)
async def login_merchant(
    credentials: MerchantLogin,
    db: Session = Depends(get_db)
):
    """Login as a merchant or admin."""
    # First check if it's an admin
    admin = db.query(Admin).filter(Admin.email == credentials.email).first()
    if admin and verify_password(credentials.password, admin.password_hash):
        # Generate admin JWT token
        access_token = create_access_token(
            data={"sub": str(admin.id), "role": "admin"}
        )
        return TokenResponse(
            access_token=access_token,
            api_key=""  # Admins don't use API keys for payment creation
        )
    
    # Otherwise, check merchant
    merchant = db.query(Merchant).filter(Merchant.email == credentials.email).first()
    
    if not merchant or not verify_password(credentials.password, merchant.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not merchant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    # Generate API key if merchant doesn't have one (backward compatibility)
    if not merchant.api_key:
        merchant.api_key = generate_api_key()
        db.commit()
        db.refresh(merchant)
    
    # Generate JWT token
    access_token = create_access_token(
        data={"sub": str(merchant.id), "role": "merchant"}
    )
    
    return TokenResponse(
        access_token=access_token,
        api_key=merchant.api_key
    )
