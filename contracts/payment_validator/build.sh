#!/bin/bash
set -e

echo "🔨 Building ChainPe Payment Validator Contract..."

# Build optimized WASM
cargo build --target wasm32-unknown-unknown --release

# Optimize WASM file
stellar contract optimize \
    --wasm target/wasm32-unknown-unknown/release/chainpe_payment_validator.wasm \
    --wasm-out target/wasm32-unknown-unknown/release/chainpe_payment_validator_optimized.wasm

echo "✅ Build complete!"
echo "📦 Optimized WASM: target/wasm32-unknown-unknown/release/chainpe_payment_validator_optimized.wasm"
