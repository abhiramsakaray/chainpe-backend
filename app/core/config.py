from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./payment_gateway.db"
    
    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # Stellar
    STELLAR_NETWORK: str = "testnet"
    STELLAR_HORIZON_URL: str = "https://horizon-testnet.stellar.org"
    USDC_ASSET_CODE: str = "USDC"
    USDC_ASSET_ISSUER: str = "GBBD47IF6LWK7P7MDEVSCWR7DPUWV3NY3DTQEVFL4NAT4AQH3ZLLFLA5"
    
    # Payment
    PAYMENT_EXPIRY_MINUTES: int = 15
    WEBHOOK_RETRY_LIMIT: int = 3
    WEBHOOK_TIMEOUT_SECONDS: int = 10
    
    # Application
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_BASE_URL: str = "http://localhost:8000"
    APP_URL: str = "http://localhost:8000"  # Alias for APP_BASE_URL
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    
    # Admin
    ADMIN_EMAIL: str = "admin@paymentgateway.com"
    ADMIN_PASSWORD: str = "change-this-password"
    
    # Soroban Smart Contracts (Optional)
    SOROBAN_RPC_URL: str = "https://soroban-testnet.stellar.org"
    SOROBAN_ESCROW_CONTRACT_ID: str = ""  # Set after deploying contract
    SOROBAN_USDC_CONTRACT_ID: str = ""  # Testnet USDC contract address
    
    # Payment Validator Smart Contract
    PAYMENT_VALIDATOR_CONTRACT_ID: str = ""  # Smart contract for payment validation
    BACKEND_SECRET_KEY: str = ""  # Backend Stellar secret key for contract auth
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
