# ChainPe Payment Validator Contract

A Soroban smart contract that validates payment memos and automatically forwards payments to merchants or refunds invalid payments.

## Features

✅ **Memo Validation** - Checks if payment memo matches a registered session  
✅ **Auto-Forward** - Sends valid payments directly to merchant  
✅ **Auto-Refund** - Returns invalid/expired payments to sender  
✅ **Amount Validation** - Ensures payment amount matches expected value  
✅ **Session Management** - Backend can register/deactivate payment sessions  

## How It Works

```
1. User creates checkout → Backend registers session in contract
2. User sends USDC to contract with memo
3. Contract validates:
   - Memo exists? ✓
   - Session active? ✓
   - Amount correct? ✓
4. If valid → Forward to merchant
5. If invalid → Refund to user
```

## Build

```bash
chmod +x build.sh
./build.sh
```

## Deploy to Testnet

```bash
stellar contract deploy \
  --wasm target/wasm32-unknown-unknown/release/chainpe_payment_validator_optimized.wasm \
  --network testnet \
  --source BACKEND_SECRET_KEY
```

## Initialize

```bash
stellar contract invoke \
  --id CONTRACT_ID \
  --network testnet \
  --source BACKEND_SECRET_KEY \
  -- initialize \
  --backend_address BACKEND_PUBLIC_KEY
```

## Register Payment Session

```bash
stellar contract invoke \
  --id CONTRACT_ID \
  --network testnet \
  --source BACKEND_SECRET_KEY \
  -- register_session \
  --memo "pay_abc123" \
  --merchant MERCHANT_ADDRESS \
  --amount 1000000  # Amount in stroops (USDC with 7 decimals)
```

## User Sends Payment

User simply sends USDC to the contract address with memo = session_id. The contract automatically:
- Validates the memo
- Forwards to merchant if valid
- Refunds if invalid

## Events

- `session_registered` - New session created
- `payment_forwarded` - Valid payment sent to merchant  
- `refund_invalid_memo` - No session found for memo
- `refund_expired` - Session expired
- `refund_insufficient` - Amount too low
- `session_deactivated` - Session cancelled

## Integration with Backend

See `app/services/soroban_validator.py` for Python integration.
