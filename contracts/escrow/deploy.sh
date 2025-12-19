#!/bin/bash

# Deploy ChainPe Escrow Contract to Stellar Testnet

set -e

echo "🚀 Deploying ChainPe Escrow Contract to Testnet..."

# Check if Soroban CLI is installed
if ! command -v soroban &> /dev/null; then
    echo "❌ Soroban CLI not found. Install with: cargo install --locked soroban-cli"
    exit 1
fi

# Load environment variables
if [ -f "../../.env" ]; then
    source ../../.env
fi

# Build the contract first
echo "1️⃣ Building contract..."
./build.sh

# Deploy to testnet
echo "2️⃣ Deploying to testnet..."

# You'll need to set these environment variables:
# STELLAR_DEPLOYER_SECRET_KEY - Your Stellar secret key for deployment

if [ -z "$STELLAR_DEPLOYER_SECRET_KEY" ]; then
    echo "❌ Please set STELLAR_DEPLOYER_SECRET_KEY environment variable"
    echo "Example: export STELLAR_DEPLOYER_SECRET_KEY=SXXXXXXXXX..."
    exit 1
fi

CONTRACT_ID=$(soroban contract deploy \
  --wasm target/wasm32-unknown-unknown/release/chainpe_escrow.optimized.wasm \
  --source $STELLAR_DEPLOYER_SECRET_KEY \
  --network testnet)

echo "✅ Contract deployed successfully!"
echo ""
echo "📝 Contract ID: $CONTRACT_ID"
echo ""
echo "Save this to your .env file:"
echo "SOROBAN_ESCROW_CONTRACT_ID=$CONTRACT_ID"
echo ""

# Initialize the contract
echo "3️⃣ Initializing contract with ChainPe admin address..."

if [ -z "$CHAINPE_ADMIN_ADDRESS" ]; then
    echo "⚠️  CHAINPE_ADMIN_ADDRESS not set. Please initialize manually:"
    echo "soroban contract invoke \\"
    echo "  --id $CONTRACT_ID \\"
    echo "  --source YOUR_SECRET \\"
    echo "  --network testnet \\"
    echo "  -- \\"
    echo "  initialize \\"
    echo "  --chainpe_admin YOUR_ADMIN_ADDRESS"
else
    soroban contract invoke \
      --id $CONTRACT_ID \
      --source $STELLAR_DEPLOYER_SECRET_KEY \
      --network testnet \
      -- \
      initialize \
      --chainpe_admin $CHAINPE_ADMIN_ADDRESS
    
    echo "✅ Contract initialized!"
fi

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Add CONTRACT_ID to .env: SOROBAN_ESCROW_CONTRACT_ID=$CONTRACT_ID"
echo "2. Get USDC contract ID from https://stellar.expert/explorer/testnet/asset/USDC"
echo "3. Restart your ChainPe backend"
