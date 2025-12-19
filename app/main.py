from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import time
import logging
import os

from app.core.config import settings
from app.routes import auth, merchant, payments, checkout, admin, merchant_payments, public, admin_webhooks, escrow, sessions, integrations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Stellar Payment Gateway",
    description="A Stripe-like hosted payment gateway for USDC payments on Stellar",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS - Allow all origins for e-commerce integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Must be False when allow_origins is ["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    start_time = time.time()
    
    # Log request
    logger.info(f"→ {request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(
        f"← {request.method} {request.url.path} "
        f"[{response.status_code}] {process_time:.3f}s"
    )
    
    return response


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": str(exc) if settings.STELLAR_NETWORK == "testnet" else "An error occurred"
        }
    )


# Include routers
app.include_router(auth.router)
app.include_router(merchant.router)
app.include_router(merchant_payments.router)
app.include_router(payments.router)
app.include_router(sessions.router)  # Public API for merchant integrations
app.include_router(integrations.router)  # E-commerce platform integrations
app.include_router(checkout.router)
app.include_router(admin.router)
app.include_router(admin_webhooks.router)
app.include_router(public.router)
app.include_router(escrow.router)  # Soroban escrow endpoints

# Serve static files (ChainPe button SDK and demo)
public_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public")
if os.path.exists(public_dir):
    app.mount("/public", StaticFiles(directory=public_dir), name="public")
    logger.info(f"✅ Serving static files from {public_dir}")
else:
    logger.warning(f"⚠️  Public directory not found: {public_dir}")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Stellar Payment Gateway",
        "version": "1.0.0",
        "status": "operational",
        "network": settings.STELLAR_NETWORK,
        "docs": "/docs"
    }


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "network": settings.STELLAR_NETWORK
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    from app.core.database import Base, engine, SessionLocal
    from app.models import Admin
    from app.core.security import hash_password
    
    logger.info("=" * 60)
    logger.info("🚀 Stellar Payment Gateway Starting")
    logger.info("=" * 60)
    
    # Auto-create database tables if they don't exist
    try:
        logger.info("Initializing database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables ready")
        
        # Create admin account if it doesn't exist
        db = SessionLocal()
        try:
            existing_admin = db.query(Admin).filter(Admin.email == settings.ADMIN_EMAIL).first()
            if not existing_admin:
                admin = Admin(
                    email=settings.ADMIN_EMAIL,
                    password_hash=hash_password(settings.ADMIN_PASSWORD)
                )
                db.add(admin)
                db.commit()
                logger.info(f"✅ Admin account created: {settings.ADMIN_EMAIL}")
            else:
                logger.info(f"ℹ️  Admin account exists: {settings.ADMIN_EMAIL}")
        except Exception as e:
            logger.error(f"Admin account creation error: {e}")
            db.rollback()
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
    
    logger.info(f"Network: {settings.STELLAR_NETWORK}")
    logger.info(f"Base URL: {settings.APP_BASE_URL}")
    logger.info(f"USDC Asset: {settings.USDC_ASSET_CODE}:{settings.USDC_ASSET_ISSUER}")
    logger.info("=" * 60)
    logger.info("")
    logger.info("⚠️  IMPORTANT: Start the Stellar listener separately:")
    logger.info("   python -m app.services.stellar_listener")
    logger.info("")
    logger.info("=" * 60)


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("Shutting down Stellar Payment Gateway...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=True
    )
