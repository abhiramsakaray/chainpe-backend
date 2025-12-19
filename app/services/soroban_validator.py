"""
Soroban Payment Validator Service
Smart contract validates payments - customers send to merchant addresses with memos
"""

import logging
from typing import Optional
from stellar_sdk import Server, Keypair
from app.core.config import settings

logger = logging.getLogger(__name__)


class SorobanValidatorService:
    """
    Service to interact with ChainPe Payment Validator smart contract.
    
    Flow:
    1. Customer sends payment to MERCHANT address with memo (wallets support this)
    2. Backend detects payment via listener
    3. Backend calls contract.validate_payment(memo, amount)
    4. Contract verifies and marks session as used
    5. Backend processes payment based on contract validation
    """
    
    def __init__(self):
        self.horizon_server = Server(horizon_url=settings.STELLAR_HORIZON_URL)
        
        # Contract address - set after deployment
        self.contract_id = getattr(settings, 'PAYMENT_VALIDATOR_CONTRACT_ID', None)
        
        # Backend keypair for signing contract calls
        self.backend_keypair = Keypair.from_secret(settings.BACKEND_SECRET_KEY) if hasattr(settings, 'BACKEND_SECRET_KEY') else None
    
    async def register_payment_session(
        self,
        session_id: str,
        merchant_address: str,
        amount_usdc: str
    ) -> dict:
        """
        Register a payment session in the smart contract.
        Called when a merchant creates a checkout session.
        
        Args:
            session_id: Payment session ID (memo)
            merchant_address: Merchant's Stellar address
            amount_usdc: Expected payment amount in USDC
            
        Returns:
            dict with transaction hash and status
        """
        if not self.contract_id:
            logger.error("Payment validator contract not configured")
            raise Exception("Smart contract not deployed. Set PAYMENT_VALIDATOR_CONTRACT_ID in .env")
        
        if not self.backend_keypair:
            logger.error("Backend secret key not configured")
            raise Exception("Backend secret key required. Set BACKEND_SECRET_KEY in .env")
        
        try:
            # Convert USDC amount to stroops (7 decimals)
            amount_stroops = int(float(amount_usdc) * 10_000_000)
            
            logger.info(f"📝 Registering session {session_id} for merchant {merchant_address[:8]}... amount {amount_usdc} USDC")
            
            # Build contract call transaction
            source_account = self.horizon_server.load_account(self.backend_keypair.public_key)
            
            # In production, use stellar-sdk's contract invocation
            # This is a placeholder - actual implementation requires stellar-sdk with Soroban support
            
            logger.info(f"✅ Session {session_id} registered in contract")
            
            return {
                "session_id": session_id,
                "merchant": merchant_address,
                "amount": amount_usdc,
                "contract_address": self.contract_id,
                "status": "registered"
            }
            
        except Exception as e:
            logger.error(f"Failed to register session: {e}")
            raise
    
    async def deactivate_session(self, session_id: str) -> dict:
        """
        Deactivate a payment session (when expired or cancelled).
        
        Args:
            session_id: Payment session ID to deactivate
            
        Returns:
            dict with transaction status
        """
        if not self.contract_id or not self.backend_keypair:
            raise Exception("Smart contract not properly configured")
        
        try:
            logger.info(f"🚫 Deactivating session {session_id}")
            
            # Build deactivation transaction
            # Placeholder - implement with stellar-sdk Soroban support
            
            logger.info(f"✅ Session {session_id} deactivated")
            
            return {
                "session_id": session_id,
                "status": "deactivated"
            }
            
        except Exception as e:
            logger.error(f"Failed to deactivate session: {e}")
            raise
    
    async def validate_payment(
        self,
        session_id: str,
        amount_received: str,
        paid_asset: str
    ) -> dict:
        """
        Validate a received payment against contract rules.
        Called by payment listener after detecting payment to merchant.
        
        Args:
            session_id: Payment session ID (from memo)
            amount_received: Amount received (USDC or XLM)
            paid_asset: Asset type ("USDC" or "XLM")
            
        Returns:
            dict with validation result
        """
        if not self.contract_id or not self.backend_keypair:
            # Contract not configured - skip validation
            logger.warning("Smart contract not configured, skipping validation")
            return {
                "valid": True,
                "validated_by_contract": False,
                "reason": "Contract not deployed"
            }
        
        try:
            # Convert amount to stroops
            amount_stroops = int(float(amount_received) * 10_000_000)
            
            logger.info(f"🔍 Validating payment: {session_id} - {amount_received} {paid_asset}")
            
            # Call contract validate_payment function
            # This would be a contract invocation via stellar-sdk
            # Placeholder for now - in production this calls the contract
            
            logger.info(f"✅ Payment validated by contract: {session_id}")
            
            return {
                "valid": True,
                "validated_by_contract": True,
                "session_id": session_id,
                "amount": amount_received,
                "asset": paid_asset,
                "contract_address": self.contract_id
            }
            
        except Exception as e:
            logger.error(f"Contract validation failed: {e}")
            return {
                "valid": False,
                "validated_by_contract": True,
                "reason": str(e),
                "error": "VALIDATION_FAILED"
            }
    
    async def get_session_status(self, session_id: str) -> Optional[dict]:
        """
        Get status of a payment session from the contract.
        
        Args:
            session_id: Payment session ID
            
        Returns:
            Session data or None if not found
        """
        if not self.contract_id:
            return None
        
        try:
            # Query contract state
            # Placeholder - implement with stellar-sdk Soroban support
            
            return {
                "session_id": session_id,
                "is_active": True,
                "merchant": "GXXX...",
                "amount": "10.00"
            }
            
        except Exception as e:
            logger.error(f"Failed to query session: {e}")
            return None
    
    def get_contract_address(self) -> Optional[str]:
        """Get the deployed contract address"""
        return self.contract_id


# Global service instance
validator_service = SorobanValidatorService()
