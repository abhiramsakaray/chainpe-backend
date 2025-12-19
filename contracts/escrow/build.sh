#!/bin/bash

# Build the Soroban contract
echo "Building ChainPe Escrow Contract..."

# Build in release mode
cargo build --target wasm32-unknown-unknown --release

# Optimize the WASM
echo "Optimizing WASM..."
soroban contract optimize \
  --wasm target/wasm32-unknown-unknown/release/chainpe_escrow.wasm

echo "✅ Build complete!"
echo "WASM file: target/wasm32-unknown-unknown/release/chainpe_escrow.optimized.wasm"
