from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from app.core import get_db
from app.core.config import settings
from app.models import Merchant, PaymentSession, PaymentStatus
from app.schemas import PaymentSessionCreate, PaymentSessionResponse, PaymentSessionStatus
from app.services.payment_utils import generate_session_id, convert_fiat_to_usdc
from app.core.auth import get_api_key
from app.services.soroban_validator import validator_service
import logging

router = APIRouter(prefix="/api/sessions", tags=["Payment Sessions - Public API"])
logger = logging.getLogger(__name__)


@router.post("/create", response_model=PaymentSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_payment_session_public(
    session_data: PaymentSessionCreate,
    api_key: str = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """
    Create a new payment session (public API endpoint for merchant integrations).
    
    This endpoint is used by the ChainPe button SDK and merchant websites to create
    payment sessions. Requires API key authentication.
    
    Example request body:
    ```json
    {
        "amount_usdc": 50.00,
        "order_id": "ORDER-12345",
        "success_url": "https://yourstore.com/success",
        "cancel_url": "https://yourstore.com/cart",
        "metadata": {
            "customer_email": "customer@example.com",
            "customer_name": "John Doe"
        }
    }
    ```
    
    Response includes checkout_url to redirect customer to.
    """
    # Get merchant from API key
    merchant = db.query(Merchant).filter(Merchant.api_key == api_key).first()
    
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found"
        )
    
    # Auto-generate Stellar address if not set (for demo purposes)
    if not merchant.stellar_address:
        # You can remove this check or set a default address
        # For now, we'll allow it and log a warning
        import logging
        logging.warning(f"Merchant {merchant.email} creating payment without Stellar address set")
    
    # Generate session ID
    session_id = generate_session_id()
    
    # Create payment session
    new_session = PaymentSession(
        id=session_id,  # Column name is 'id', not 'session_id'
        merchant_id=merchant.id,
        amount_fiat=session_data.amount_usdc,  # For now, using USDC as base
        fiat_currency="USD",
        amount_usdc=session_data.amount_usdc,
        status=PaymentStatus.CREATED,
        success_url=str(session_data.success_url) if session_data.success_url else "",
        cancel_url=str(session_data.cancel_url) if session_data.cancel_url else ""
    )
    
    # Set expiry time
    new_session.expires_at = datetime.utcnow() + timedelta(minutes=settings.PAYMENT_EXPIRY_MINUTES)
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    # Register session with smart contract (if contract is configured)
    contract_address = None
    try:
        contract_address = validator_service.get_contract_address()
        if contract_address and merchant.stellar_address:
            await validator_service.register_payment_session(
                session_id=new_session.id,
                merchant_address=merchant.stellar_address,
                amount_usdc=str(new_session.amount_usdc)
            )
            logger.info(f"✅ Session {new_session.id} registered in smart contract")
    except Exception as e:
        logger.warning(f"Could not register session in smart contract: {e}")
        # Continue without smart contract - fallback to direct payments
    
    # Generate checkout URL
    checkout_url = f"{settings.APP_URL}/checkout/{new_session.id}"
    
    return PaymentSessionResponse(
        session_id=new_session.id,
        checkout_url=checkout_url,
        amount_usdc=new_session.amount_usdc,
        order_id=session_data.order_id,
        expires_at=new_session.expires_at,
        status=new_session.status.value,
        success_url=new_session.success_url,
        cancel_url=new_session.cancel_url
    )


@router.get("/{session_id}", response_model=PaymentSessionStatus)
async def get_payment_session_public(
    session_id: str,
    api_key: Optional[str] = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """
    Get payment session status (public endpoint for verification).
    
    Used by merchant websites to verify payment status after customer returns
    from ChainPe checkout page.
    
    Example usage on success page:
    ```javascript
    const sessionId = new URLSearchParams(window.location.search).get('session_id');
    const response = await fetch(`/api/sessions/${sessionId}`, {
        headers: {'X-API-Key': 'your_api_key'}
    });
    const session = await response.json();
    if (session.status === 'paid') {
        // Show success message
    }
    ```
    """
    session = db.query(PaymentSession).filter(PaymentSession.id == session_id).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment session not found"
        )
    
    # Verify API key belongs to the merchant who created the session
    if api_key:
        merchant = db.query(Merchant).filter(Merchant.api_key == api_key).first()
        if not merchant or merchant.id != session.merchant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    # Check if session has expired
    if session.expires_at and datetime.utcnow() > session.expires_at:
        if session.status == PaymentStatus.CREATED:
            session.status = PaymentStatus.EXPIRED
            db.commit()
    
    return PaymentSessionStatus(
        session_id=session.id,
        status=session.status.value,
        amount_usdc=session.amount_usdc,
        order_id=session.order_id,
        tx_hash=session.tx_hash,
        created_at=session.created_at,
        paid_at=session.paid_at,
        expires_at=session.expires_at,
        metadata=session.metadata or {}
    )
