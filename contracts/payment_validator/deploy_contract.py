"""
Complete contract deployment - upload and deploy
"""
import subprocess
import os

WASM_PATH = "target/wasm32-unknown-unknown/release/chainpe_payment_validator.wasm"

if not os.path.exists(WASM_PATH):
    print(f"❌ WASM file not found: {WASM_PATH}")
    exit(1)

print("🚀 Deploying contract...")
print("This will upload WASM and create contract instance")

# Use stellar contract install (upload) then deploy
print("\n📤 Step 1: Installing WASM...")
install_cmd = [
    "stellar", "contract", "upload",
    "--wasm", WASM_PATH,
    "--source", "deployer",
    "--network", "testnet",
    "--network-passphrase", "Test SDF Network ; September 2015"
]

try:
    result = subprocess.run(install_cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    if result.returncode == 0:
        wasm_hash = result.stdout.strip()
        print(f"✅ WASM installed! Hash: {wasm_hash}")
        
        # Now deploy
        print("\n🚀 Step 2: Deploying contract...")
        deploy_cmd = [
            "stellar", "contract", "deploy",
            "--wasm-hash", wasm_hash,
            "--source", "deployer",
            "--network", "testnet",
            "--network-passphrase", "Test SDF Network ; September 2015"
        ]
        
        result2 = subprocess.run(deploy_cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        if result2.returncode == 0:
            contract_id = result2.stdout.strip()
            print(f"\n✅ Contract deployed!")
            print(f"\nCONTRACT_ID: {contract_id}")
            print(f"\nAdd to .env:")
            print(f"PAYMENT_VALIDATOR_CONTRACT_ID={contract_id}")
        else:
            print(f"❌ Deploy error: {result2.stderr}")
    else:
        print(f"❌ Install error: {result.stderr}")
except Exception as e:
    print(f"❌ Error: {e}")
