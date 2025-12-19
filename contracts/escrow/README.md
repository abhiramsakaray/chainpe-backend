# ChainPe Escrow Contract - README

## Overview

This directory contains a Soroban smart contract for **escrow payments** on Stellar.

### What is Escrow?

Escrow holds customer funds in a smart contract until:
- **Merchant releases** (delivery confirmed), OR
- **Customer refunds** (after timeout), OR  
- **Admin force refunds** (dispute resolution)

### When to Use Escrow vs Direct Payment

| Feature | Direct Payment (Current) | Escrow Contract |
|---------|-------------------------|-----------------|
| **Use Case** | Simple checkout | Marketplace, P2P |
| **Fees** | 0.00001 XLM | ~0.1 XLM |
| **Custody** | No (direct to merchant) | Yes (contract holds) |
| **Trust** | Required | Smart contract enforced |
| **Refunds** | Manual | Automated |

## Files

```
escrow/
├── src/
│   └── lib.rs           # Main contract code (Rust)
├── Cargo.toml           # Rust dependencies
├── build.sh             # Build script
├── deploy.sh            # Deploy to testnet
├── test.sh              # Run tests
└── .gitignore           # Git ignore file
```

## Quick Start

### 1. Build

```bash
./build.sh
```

### 2. Deploy

```bash
# Set your deployer secret key
export STELLAR_DEPLOYER_SECRET_KEY="SXXX..."
export CHAINPE_ADMIN_ADDRESS="GXXX..."

./deploy.sh
```

### 3. Use in Backend

Update `backend/.env`:
```bash
SOROBAN_ESCROW_CONTRACT_ID=CXXXX...  # From deployment output
```

Restart backend and use `/api/escrow` endpoints!

## Full Documentation

See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for complete instructions.

## Contract Functions

- `initialize(chainpe_admin)` - One-time setup
- `create_escrow(...)` - Lock funds
- `release_payment(session_id)` - Merchant releases
- `refund_payment(session_id)` - Customer refunds (after timeout)
- `admin_refund(session_id)` - Admin force refund
- `get_escrow(session_id)` - Query status

## Testing

```bash
./test.sh
```

## License

MIT
