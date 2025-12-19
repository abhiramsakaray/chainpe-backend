# Merchant Stablecoin Checkout - Stellar Payment Gateway

A Stripe-like hosted payment gateway backend that allows merchants to accept USDC payments on the Stellar network.

## Features

- 🔐 JWT-based authentication for merchants and admins
- 💳 Create hosted checkout payment sessions
- ⭐ Real-time Stellar blockchain payment detection
- 🔔 Webhook notifications to merchants
- 🎯 No fund custody - payment verification only
- 👑 Admin dashboard APIs

## Tech Stack

- **Language**: Python 3.10+
- **Framework**: FastAPI
- **Database**: PostgreSQL (SQLite for development)
- **Blockchain**: Stellar Testnet
- **SDK**: stellar-sdk

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Initialize Database

```bash
python init_db.py
```

### 4. Run Application

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### 5. Start Stellar Listener (Separate Terminal)

```bash
python -m app.services.stellar_listener
```

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Architecture

```
backend/
├── app/
│   ├── models/          # SQLAlchemy models
│   ├── routes/          # API endpoints
│   ├── services/        # Business logic
│   ├── schemas/         # Pydantic schemas
│   ├── core/            # Config, security
│   └── main.py          # FastAPI app
├── requirements.txt
└── .env
```

## Deployment

Recommended platforms:
- Render
- Railway
- Fly.io

**Important**: The Stellar listener must run as a background process alongside the main API.

## Security

- ✅ No private keys stored
- ✅ No fund custody
- ✅ JWT authentication
- ✅ Input validation
- ✅ HTTPS only in production
- ✅ Rate limiting

## License

MIT
