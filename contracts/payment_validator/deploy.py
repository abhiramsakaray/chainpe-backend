"""
Deploy ChainPe Payment Validator Smart Contract to Stellar Testnet
"""
import os
import subprocess
from stellar_sdk import Keypair, Network, SorobanServer, Server, TransactionBuilder
from stellar_sdk.soroban_rpc import GetTransactionStatus
from stellar_sdk.exceptions import PrepareTransactionException
import time

# Configuration
RPC_URL = "https://soroban-testnet.stellar.org"
HORIZON_URL = "https://horizon-testnet.stellar.org"
NETWORK_PASSPHRASE = Network.TESTNET_NETWORK_PASSPHRASE
WASM_PATH = "target/wasm32-unknown-unknown/release/chainpe_payment_validator.wasm"

def get_deployer_keypair():
    """Get deployer keypair from stellar keys"""
    try:
        result = subprocess.run(
            ["stellar", "keys", "show", "deployer"],
            capture_output=True,
            text=True,
            check=True
        )
        secret = result.stdout.strip()
        return Keypair.from_secret(secret)
    except Exception as e:
        print(f"❌ Error getting deployer keys: {e}")
        print("Make sure you have created deployer keys with: stellar keys generate deployer --network testnet --fund")
        exit(1)

def deploy_contract():
    """Deploy the smart contract"""
    print("🚀 Starting contract deployment...")
    
    # Get deployer keypair
    deployer = get_deployer_keypair()
    print(f"📝 Deployer address: {deployer.public_key}")
    
    # Read WASM file
    if not os.path.exists(WASM_PATH):
        print(f"❌ WASM file not found: {WASM_PATH}")
        print("Run: cargo build --target wasm32-unknown-unknown --release")
        exit(1)
    
    with open(WASM_PATH, "rb") as f:
        wasm_binary = f.read()
    
    print(f"📦 WASM size: {len(wasm_binary)} bytes")
    
    # Create servers
    soroban_server = SorobanServer(RPC_URL)
    horizon_server = Server(HORIZON_URL)
    
    # Get source account from Horizon
    print("🔍 Loading account...")
    source = horizon_server.load_account(deployer.public_key)
    
    # Build transaction to upload WASM
    print("📤 Uploading WASM to Stellar...")
    tx = (
        TransactionBuilder(source, NETWORK_PASSPHRASE, base_fee=100_000)
        .append_upload_contract_wasm_op(wasm_binary)
        .set_timeout(300)
        .build()
    )
    
    # Prepare transaction
    try:
        prepared_tx = soroban_server.prepare_transaction(tx)
    except PrepareTransactionException as e:
        print(f"❌ Error preparing transaction: {e}")
        exit(1)
    
    # Sign and submit
    prepared_tx.sign(deployer)
    print("📡 Submitting transaction...")
    
    response = soroban_server.send_transaction(prepared_tx)
    print(f"✅ Transaction submitted: {response.hash}")
    
    # Wait for confirmation
    print("⏳ Waiting for confirmation...")
    for i in range(60):
        try:
            tx_response = soroban_server.get_transaction(response.hash)
            if tx_response.status == GetTransactionStatus.SUCCESS:
                print("✅ WASM uploaded successfully!")
                
                # Extract WASM hash from transaction result
                result = tx_response.result_meta_xdr
                print(f"\n📝 WASM Hash: {response.hash}")
                
                # Now deploy the contract
                print("\n🚀 Deploying contract instance...")
                source = horizon_server.load_account(deployer.public_key)
                
                # Create contract from uploaded WASM
                from stellar_sdk import xdr as stellar_xdr
                
                # Build create contract transaction
                tx2 = (
                    TransactionBuilder(source, NETWORK_PASSPHRASE, base_fee=100_000)
                    .append_create_contract_op(
                        wasm_id=response.hash.encode(),
                        address=deployer.public_key
                    )
                    .set_timeout(300)
                    .build()
                )
                
                prepared_tx2 = soroban_server.prepare_transaction(tx2)
                prepared_tx2.sign(deployer)
                
                response2 = soroban_server.send_transaction(prepared_tx2)
                print(f"📡 Contract deployment tx: {response2.hash}")
                
                # Wait for contract deployment
                for j in range(60):
                    tx_response2 = soroban_server.get_transaction(response2.hash)
                    if tx_response2.status == GetTransactionStatus.SUCCESS:
                        print("\n✅ Contract deployed successfully!")
                        print(f"\n🎉 CONTRACT ID: {response2.hash}")
                        print(f"\nAdd this to your .env file:")
                        print(f"PAYMENT_VALIDATOR_CONTRACT_ID={response2.hash}")
                        return response2.hash
                    elif tx_response2.status == GetTransactionStatus.FAILED:
                        print(f"❌ Deployment failed: {tx_response2}")
                        exit(1)
                    time.sleep(2)
                
                return None
                
            elif tx_response.status == GetTransactionStatus.FAILED:
                print(f"❌ Transaction failed: {tx_response}")
                exit(1)
        except Exception as e:
            pass
        
        time.sleep(2)
        print(".", end="", flush=True)
    
    print("\n❌ Transaction timeout")
    exit(1)

if __name__ == "__main__":
    try:
        contract_id = deploy_contract()
        if contract_id:
            print(f"\n✅ Deployment complete!")
            print(f"Contract ID: {contract_id}")
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
