"""
Simple contract deployment - deploy from uploaded WASM hash
"""
import subprocess

WASM_HASH = "24613882f88820305bba170eb90d177beb6560ed088ba084adfe0c124c7c4e2f"

print("🚀 Deploying contract from uploaded WASM...")
print(f"WASM Hash: {WASM_HASH}")

# Deploy using stellar CLI
cmd = [
    "stellar", "contract", "deploy",
    "--wasm-hash", WASM_HASH,
    "--source", "deployer",
    "--rpc-url", "https://soroban-testnet.stellar.org",
    "--network-passphrase", "Test SDF Network ; September 2015"
]

try:
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', check=True)
    contract_id = result.stdout.strip()
    print(f"\n✅ Contract deployed!")
    print(f"CONTRACT_ID: {contract_id}")
    print(f"\nAdd to .env:")
    print(f"PAYMENT_VALIDATOR_CONTRACT_ID={contract_id}")
except subprocess.CalledProcessError as e:
    print(f"❌ Error: {e.stderr}")
except Exception as e:
    print(f"❌ Error: {e}")
