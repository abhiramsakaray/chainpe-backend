from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.core import get_db
from app.core.config import settings
from app.models import PaymentSession, PaymentStatus
from app.schemas import PaymentSessionDetail
from stellar_sdk import Keypair
from app.services.soroban_validator import validator_service
import qrcode
import io
import base64
import logging

router = APIRouter(prefix="/checkout", tags=["Checkout"])
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)


def generate_qr_code(data: str) -> str:
    """Generate QR code and return as base64 encoded image."""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"


@router.get("/{session_id}", response_class=HTMLResponse)
async def checkout_page(
    request: Request,
    session_id: str,
    db: Session = Depends(get_db)
):
    """Display hosted checkout page."""
    session = db.query(PaymentSession).filter(PaymentSession.id == session_id).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment session not found"
        )
    
    # Check if already paid
    if session.status == PaymentStatus.PAID:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Payment Complete</title>
            <meta http-equiv="refresh" content="2;url={session.success_url}">
        </head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>✅ Payment Complete!</h1>
            <p>Redirecting to merchant...</p>
        </body>
        </html>
        """
    
    # Check if expired
    expiry_time = session.created_at + timedelta(minutes=settings.PAYMENT_EXPIRY_MINUTES)
    if datetime.utcnow() > expiry_time:
        session.status = PaymentStatus.EXPIRED
        db.commit()
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Payment Expired</title>
            <meta http-equiv="refresh" content="2;url={session.cancel_url}">
        </head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>⏰ Payment Expired</h1>
            <p>This payment session has expired. Redirecting...</p>
        </body>
        </html>
        """
    
    # Generate payment instruction
    merchant_address = session.merchant.stellar_address
    
    # IMPORTANT: Payments go to merchant address (not contract)
    # Contract is used for validation only
    payment_address = merchant_address
    
    # Check if smart contract is available for validation
    contract_address = validator_service.get_contract_address()
    use_smart_contract = bool(contract_address)
    
    # Debug log
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Merchant ID: {session.merchant.id}")
    logger.info(f"Merchant Email: {session.merchant.email}")
    logger.info(f"Merchant Stellar Address: {merchant_address}")
    logger.info(f"Smart Contract (Validator): {contract_address}")
    logger.info(f"Payment Address (QR): {payment_address}")
    logger.info(f"Smart Contract Validation: {'ENABLED' if use_smart_contract else 'DISABLED'}")
    
    # Validate payment address
    if not payment_address:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Configuration Error</title>
        </head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>⚠️ Configuration Error</h1>
            <p>Merchant has not configured their Stellar wallet address.</p>
            <p>Please contact the merchant to complete their setup.</p>
        </body>
        </html>
        """, status_code=500)
    
    # Validate address format
    try:
        Keypair.from_public_key(merchant_address)
    except Exception as e:
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Configuration Error</title>
        </head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>⚠️ Invalid Stellar Address</h1>
            <p>Merchant's Stellar address is invalid: {merchant_address}</p>
            <p>Error: {str(e)}</p>
            <p>Please contact the merchant to fix their configuration.</p>
        </body>
        </html>
        """, status_code=500)
    
    payment_memo = session_id
    amount_usdc = session.amount_usdc
    
    # Calculate XLM equivalent (assuming 1 USDC ≈ 10 XLM for display, adjust based on market rate)
    # In production, fetch real-time XLM/USD rate from an API
    amount_xlm = str(float(amount_usdc) * 10)  # Placeholder conversion
    
    # Generate QR codes with just the address (most wallets only support address QR)
    # Users will need to manually enter amount and memo
    
    # Generate Address QR code (compatible with all wallets)
    qr_address = qrcode.QRCode(version=1, box_size=10, border=5)
    qr_address.add_data(payment_address)
    qr_address.make(fit=True)
    img_address = qr_address.make_image(fill_color="black", back_color="white")
    buffered_address = io.BytesIO()
    img_address.save(buffered_address, format="PNG")
    qr_code_address_b64 = base64.b64encode(buffered_address.getvalue()).decode()
    
    # Payment URIs for "Open in Wallet" buttons (may not work in all wallets)
    usdc_uri = (
        f"stellar:{payment_address}?"
        f"amount={amount_usdc}&"
        f"memo={payment_memo}&"
        f"memo_type=MEMO_TEXT&"
        f"asset_code={settings.USDC_ASSET_CODE}&"
        f"asset_issuer={settings.USDC_ASSET_ISSUER}"
    )
    
    xlm_uri = (
        f"stellar:{payment_address}?"
        f"amount={amount_xlm}&"
        f"memo={payment_memo}&"
        f"memo_type=MEMO_TEXT"
    )
    
    # Render template
    return templates.TemplateResponse("checkout.html", {
        "request": request,
        "session_id": session_id,
        "merchant_name": session.merchant.name,
        "amount_fiat": str(session.amount_fiat),
        "fiat_currency": session.fiat_currency,
        "amount_usdc": amount_usdc,
        "amount_xlm": amount_xlm,
        "stellar_address": payment_address,
        "use_smart_contract": use_smart_contract,
        "qr_code_address": qr_code_address_b64,
        "payment_memo": payment_memo,
        "usdc_asset_code": settings.USDC_ASSET_CODE,
        "usdc_asset_issuer": settings.USDC_ASSET_ISSUER,
        "usdc_uri": usdc_uri,
        "xlm_uri": xlm_uri,
        "success_url": session.success_url,
        "cancel_url": session.cancel_url
    })


@router.get("/api/{session_id}", response_model=PaymentSessionDetail)
async def get_checkout_details(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get checkout details as JSON (for frontend integration)."""
    session = db.query(PaymentSession).filter(PaymentSession.id == session_id).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment session not found"
        )
    
    return PaymentSessionDetail(
        id=session.id,
        merchant_name=session.merchant.name,
        merchant_stellar_address=session.merchant.stellar_address,
        amount_fiat=session.amount_fiat,
        fiat_currency=session.fiat_currency,
        amount_usdc=session.amount_usdc,
        status=session.status.value,
        success_url=session.success_url,
        cancel_url=session.cancel_url,
        tx_hash=session.tx_hash,
        created_at=session.created_at,
        paid_at=session.paid_at
    )
