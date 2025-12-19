# Soroban Smart Contract Deployment Guide

## 🚀 Quick Start - Deploy in 5 Minutes

### Prerequisites

```bash
# 1. Install Rust (if not already installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 2. Add wasm target
rustup target add wasm32-unknown-unknown

# 3. Install Soroban CLI
cargo install --locked soroban-cli --features opt

# 4. Configure Soroban for testnet
soroban network add \
  --global testnet \
  --rpc-url https://soroban-testnet.stellar.org:443 \
  --network-passphrase "Test SDF Network ; September 2015"
```

### Step 1: Build the Contract

```bash
cd contracts/escrow

# Make build script executable (Linux/Mac)
chmod +x build.sh
./build.sh

# Windows (use Git Bash or WSL)
bash build.sh
```

This creates: `target/wasm32-unknown-unknown/release/chainpe_escrow.optimized.wasm`

### Step 2: Get a Stellar Testnet Account

```bash
# Generate a new keypair
soroban keys generate deployer --network testnet

# Fund it with test XLM
soroban keys fund deployer --network testnet

# Check your address
soroban keys address deployer
```

**Save your secret key!** You'll need it for deployment.

### Step 3: Deploy the Contract

```bash
# Set your deployer secret (from Step 2)
export STELLAR_DEPLOYER_SECRET_KEY="SXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

# Set ChainPe admin address (same or different from deployer)
export CHAINPE_ADMIN_ADDRESS="GXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

# Deploy!
chmod +x deploy.sh
./deploy.sh
```

**Output will show:**
```
✅ Contract deployed successfully!

📝 Contract ID: CXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

Save this to your .env file:
SOROBAN_ESCROW_CONTRACT_ID=CXXXXXX...
```

### Step 4: Update Backend Configuration

Add to `backend/.env`:

```bash
# Soroban Configuration
SOROBAN_RPC_URL=https://soroban-testnet.stellar.org
SOROBAN_ESCROW_CONTRACT_ID=CXXXXXXXXXXXXXXXXXXXXXXXXXXXX  # From deployment
SOROBAN_USDC_CONTRACT_ID=CBXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX  # Testnet USDC contract
```

**Get USDC Contract ID:**
Visit: https://stellar.expert/explorer/testnet/asset/USDC and find the contract address.

### Step 5: Restart Backend

```bash
# Stop your backend
Ctrl+C

# Restart
uvicorn app.main:app --reload

# Test escrow endpoint
curl http://localhost:8000/docs
# Navigate to "Escrow (Soroban)" section
```

## 📖 Contract Functions

### 1. Initialize (One-time Setup)

```bash
soroban contract invoke \
  --id YOUR_CONTRACT_ID \
  --source deployer \
  --network testnet \
  -- \
  initialize \
  --chainpe_admin GXXXXXXXXX...
```

### 2. Create Escrow

```bash
soroban contract invoke \
  --id YOUR_CONTRACT_ID \
  --source customer \
  --network testnet \
  -- \
  create_escrow \
  --customer GCUSTOMERADDRESS \
  --merchant GMERCHANTADDRESS \
  --usdc_token CUSDCCONTRACTID \
  --amount 500000000 \
  --session_id "pay_abc123" \
  --timeout_seconds 86400
```

### 3. Release Payment (Merchant)

```bash
soroban contract invoke \
  --id YOUR_CONTRACT_ID \
  --source merchant \
  --network testnet \
  -- \
  release_payment \
  --session_id "pay_abc123" \
  --usdc_token CUSDCCONTRACTID
```

### 4. Refund Payment (Customer)

```bash
soroban contract invoke \
  --id YOUR_CONTRACT_ID \
  --source customer \
  --network testnet \
  -- \
  refund_payment \
  --session_id "pay_abc123" \
  --usdc_token CUSDCCONTRACTID
```

### 5. Get Escrow Details

```bash
soroban contract invoke \
  --id YOUR_CONTRACT_ID \
  --source deployer \
  --network testnet \
  -- \
  get_escrow \
  --session_id "pay_abc123"
```

## 🧪 Testing the Contract

```bash
cd contracts/escrow

# Run tests
chmod +x test.sh
./test.sh

# Or directly with cargo
cargo test
```

## 🌐 API Integration

### Create Escrow Payment

```bash
POST /api/escrow/create

{
  "customer_secret": "SCUSTOMERXXXXXXXXX...",
  "amount": "50.00",
  "session_id": "pay_abc123",
  "timeout_hours": 24
}
```

### Release Escrow (Merchant)

```bash
POST /api/escrow/release/pay_abc123
Authorization: Bearer MERCHANT_TOKEN
```

### Refund Escrow (Customer)

```bash
POST /api/escrow/refund

{
  "customer_secret": "SCUSTOMERXXXXXXXXX...",
  "session_id": "pay_abc123"
}
```

### Check Escrow Status

```bash
GET /api/escrow/status/pay_abc123
```

## 🔐 Security Notes

### Production Deployment

1. **Never expose secret keys** in API requests
2. Use **wallet signing** (Freighter, Albedo, etc.)
3. Implement **proper key management** (HSM, KMS)
4. Add **rate limiting** on escrow endpoints
5. Enable **webhook signatures** for events

### Example: Wallet Signing (Frontend)

```javascript
import { isConnected, signTransaction } from '@stellar/freighter-api';

async function createEscrow(sessionId, amount) {
  // Check wallet connected
  if (await isConnected()) {
    // Build transaction
    const tx = buildEscrowTransaction(sessionId, amount);
    
    // Sign with Freighter
    const signedTx = await signTransaction(tx);
    
    // Submit to backend
    await fetch('/api/escrow/submit', {
      method: 'POST',
      body: JSON.stringify({ signedTransaction: signedTx })
    });
  }
}
```

## 📊 Monitoring

### Watch Contract Events

```bash
soroban events \
  --id YOUR_CONTRACT_ID \
  --start-ledger XXXX \
  --network testnet
```

### Check Contract Balance

```bash
soroban contract invoke \
  --id YOUR_CONTRACT_ID \
  --source deployer \
  --network testnet \
  -- \
  get_escrow \
  --session_id "pay_abc123"
```

## 🐛 Troubleshooting

### Issue: "Contract not found"
**Solution:** Check CONTRACT_ID is correct in `.env`

### Issue: "Insufficient balance"
**Solution:** Fund your account with `soroban keys fund`

### Issue: "Authorization required"
**Solution:** Ensure correct signer (customer/merchant/admin)

### Issue: "Timeout not reached"
**Solution:** Wait for timeout period before refunding

## 📚 Resources

- **Soroban Docs:** https://soroban.stellar.org/docs
- **Contract Examples:** https://github.com/stellar/soroban-examples
- **Stellar Explorer:** https://stellar.expert/explorer/testnet
- **Freighter Wallet:** https://freighter.app

## 🚀 Production Deployment

### Deploy to Mainnet

```bash
# 1. Configure mainnet
soroban network add \
  --global mainnet \
  --rpc-url https://soroban-mainnet.stellar.org:443 \
  --network-passphrase "Public Global Stellar Network ; September 2015"

# 2. Generate production keys
soroban keys generate mainnet-deployer --network mainnet

# 3. Fund with real XLM (from exchange)

# 4. Deploy
soroban contract deploy \
  --wasm target/wasm32-unknown-unknown/release/chainpe_escrow.optimized.wasm \
  --source mainnet-deployer \
  --network mainnet

# 5. Initialize
soroban contract invoke \
  --id CONTRACT_ID \
  --source mainnet-deployer \
  --network mainnet \
  -- \
  initialize \
  --chainpe_admin YOUR_MAINNET_ADMIN_ADDRESS
```

### Update Backend for Mainnet

```bash
# .env
STELLAR_NETWORK=public
SOROBAN_RPC_URL=https://soroban-mainnet.stellar.org
SOROBAN_ESCROW_CONTRACT_ID=CMAINNETCONTRACTID...
SOROBAN_USDC_CONTRACT_ID=CMAINNETUSDCID...
```

## ✅ Deployment Checklist

- [ ] Rust and Soroban CLI installed
- [ ] Contract built successfully
- [ ] Testnet account funded
- [ ] Contract deployed to testnet
- [ ] Contract initialized with admin
- [ ] Backend .env updated with contract IDs
- [ ] API endpoints tested
- [ ] Integration tests passing
- [ ] Security review completed
- [ ] Ready for mainnet deployment

---

**Need help?** Check the [SOROBAN_INTEGRATION.md](./SOROBAN_INTEGRATION.md) guide.
