#![no_std]
use soroban_sdk::{contract, contractimpl, contracttype, token, Address, Env, String, Symbol};

#[derive(Clone)]
#[contracttype]
pub struct EscrowData {
    pub customer: Address,
    pub merchant: Address,
    pub amount: i128,
    pub status: EscrowStatus,
    pub created_at: u64,
    pub timeout_seconds: u64,
}

#[derive(Clone, Copy, PartialEq)]
#[contracttype]
#[repr(u32)]
pub enum EscrowStatus {
    Pending = 0,
    Completed = 1,
    Refunded = 2,
}

#[derive(Copy, Clone, Debug, Eq, PartialEq)]
#[contracttype]
#[repr(u32)]
pub enum Error {
    NotFound = 1,
    AlreadyCompleted = 2,
    TimeoutNotReached = 3,
    Unauthorized = 4,
    InvalidStatus = 5,
}

const ESCROW_KEY: Symbol = Symbol::short("ESCROW");
const CHAINPE_KEY: Symbol = Symbol::short("CHAINPE");

#[contract]
pub struct ChainPeEscrow;

#[contractimpl]
impl ChainPeEscrow {
    /// Initialize the contract with ChainPe admin address
    pub fn initialize(env: Env, chainpe_admin: Address) {
        // Ensure not already initialized
        if env.storage().instance().has(&CHAINPE_KEY) {
            panic!("Already initialized");
        }
        
        env.storage().instance().set(&CHAINPE_KEY, &chainpe_admin);
    }
    
    /// Create escrow payment
    /// Customer deposits USDC, held until merchant confirms delivery or timeout
    pub fn create_escrow(
        env: Env,
        customer: Address,
        merchant: Address,
        usdc_token: Address,
        amount: i128,
        session_id: String,
        timeout_seconds: u64,
    ) -> Result<(), Error> {
        // Verify customer authorization
        customer.require_auth();
        
        // Transfer USDC from customer to escrow contract
        let token_client = token::Client::new(&env, &usdc_token);
        token_client.transfer(&customer, &env.current_contract_address(), &amount);
        
        // Store escrow details
        let escrow_data = EscrowData {
            customer: customer.clone(),
            merchant: merchant.clone(),
            amount,
            status: EscrowStatus::Pending,
            created_at: env.ledger().timestamp(),
            timeout_seconds,
        };
        
        let key = (ESCROW_KEY, session_id);
        env.storage().persistent().set(&key, &escrow_data);
        
        // Emit event
        env.events().publish((Symbol::new(&env, "escrow_created"),), session_id);
        
        Ok(())
    }
    
    /// Merchant confirms delivery → Release funds to merchant
    pub fn release_payment(
        env: Env,
        session_id: String,
        usdc_token: Address,
    ) -> Result<(), Error> {
        let key = (ESCROW_KEY, session_id.clone());
        
        let mut escrow: EscrowData = env
            .storage()
            .persistent()
            .get(&key)
            .ok_or(Error::NotFound)?;
        
        // Only merchant can release
        escrow.merchant.require_auth();
        
        // Ensure still pending
        if escrow.status != EscrowStatus::Pending {
            return Err(Error::AlreadyCompleted);
        }
        
        // Transfer USDC to merchant
        let token_client = token::Client::new(&env, &usdc_token);
        token_client.transfer(
            &env.current_contract_address(),
            &escrow.merchant,
            &escrow.amount,
        );
        
        // Mark as completed
        escrow.status = EscrowStatus::Completed;
        env.storage().persistent().set(&key, &escrow);
        
        // Emit event
        env.events().publish((Symbol::new(&env, "payment_released"),), session_id);
        
        Ok(())
    }
    
    /// Customer requests refund after timeout
    pub fn refund_payment(
        env: Env,
        session_id: String,
        usdc_token: Address,
    ) -> Result<(), Error> {
        let key = (ESCROW_KEY, session_id.clone());
        
        let mut escrow: EscrowData = env
            .storage()
            .persistent()
            .get(&key)
            .ok_or(Error::NotFound)?;
        
        // Only customer can refund
        escrow.customer.require_auth();
        
        // Ensure still pending
        if escrow.status != EscrowStatus::Pending {
            return Err(Error::InvalidStatus);
        }
        
        // Check timeout has passed
        let current_time = env.ledger().timestamp();
        if current_time < escrow.created_at + escrow.timeout_seconds {
            return Err(Error::TimeoutNotReached);
        }
        
        // Transfer USDC back to customer
        let token_client = token::Client::new(&env, &usdc_token);
        token_client.transfer(
            &env.current_contract_address(),
            &escrow.customer,
            &escrow.amount,
        );
        
        // Mark as refunded
        escrow.status = EscrowStatus::Refunded;
        env.storage().persistent().set(&key, &escrow);
        
        // Emit event
        env.events().publish((Symbol::new(&env, "payment_refunded"),), session_id);
        
        Ok(())
    }
    
    /// ChainPe admin can force refund (customer protection)
    pub fn admin_refund(
        env: Env,
        session_id: String,
        usdc_token: Address,
    ) -> Result<(), Error> {
        // Get ChainPe admin
        let admin: Address = env
            .storage()
            .instance()
            .get(&CHAINPE_KEY)
            .ok_or(Error::Unauthorized)?;
        
        // Verify admin authorization
        admin.require_auth();
        
        let key = (ESCROW_KEY, session_id.clone());
        let mut escrow: EscrowData = env
            .storage()
            .persistent()
            .get(&key)
            .ok_or(Error::NotFound)?;
        
        // Ensure still pending
        if escrow.status != EscrowStatus::Pending {
            return Err(Error::InvalidStatus);
        }
        
        // Transfer USDC back to customer
        let token_client = token::Client::new(&env, &usdc_token);
        token_client.transfer(
            &env.current_contract_address(),
            &escrow.customer,
            &escrow.amount,
        );
        
        // Mark as refunded
        escrow.status = EscrowStatus::Refunded;
        env.storage().persistent().set(&key, &escrow);
        
        // Emit event
        env.events().publish((Symbol::new(&env, "admin_refund"),), session_id);
        
        Ok(())
    }
    
    /// Get escrow details
    pub fn get_escrow(env: Env, session_id: String) -> Result<EscrowData, Error> {
        let key = (ESCROW_KEY, session_id);
        env.storage()
            .persistent()
            .get(&key)
            .ok_or(Error::NotFound)
    }
}

#[cfg(test)]
mod test {
    use super::*;
    use soroban_sdk::{testutils::Address as _, token, Address, Env, String};

    #[test]
    fn test_escrow_flow() {
        let env = Env::default();
        env.mock_all_auths();

        let contract_id = env.register_contract(None, ChainPeEscrow);
        let client = ChainPeEscrowClient::new(&env, &contract_id);

        // Create mock addresses
        let admin = Address::generate(&env);
        let customer = Address::generate(&env);
        let merchant = Address::generate(&env);
        let token_admin = Address::generate(&env);

        // Deploy token contract
        let token_contract_id = env.register_stellar_asset_contract(token_admin.clone());
        let token_client = token::Client::new(&env, &token_contract_id);

        // Mint tokens to customer
        token_client.mint(&customer, &10000);

        // Initialize escrow contract
        client.initialize(&admin);

        // Create escrow
        let session_id = String::from_str(&env, "pay_test123");
        client.create_escrow(
            &customer,
            &merchant,
            &token_contract_id,
            &1000,
            &session_id,
            &86400, // 24 hours
        );

        // Verify escrow created
        let escrow = client.get_escrow(&session_id);
        assert_eq!(escrow.amount, 1000);
        assert_eq!(escrow.status, EscrowStatus::Pending);

        // Merchant releases payment
        client.release_payment(&session_id, &token_contract_id);

        // Verify completed
        let escrow = client.get_escrow(&session_id);
        assert_eq!(escrow.status, EscrowStatus::Completed);

        // Verify merchant received funds
        assert_eq!(token_client.balance(&merchant), 1000);
    }

    #[test]
    fn test_refund_after_timeout() {
        let env = Env::default();
        env.mock_all_auths();

        let contract_id = env.register_contract(None, ChainPeEscrow);
        let client = ChainPeEscrowClient::new(&env, &contract_id);

        let admin = Address::generate(&env);
        let customer = Address::generate(&env);
        let merchant = Address::generate(&env);
        let token_admin = Address::generate(&env);

        let token_contract_id = env.register_stellar_asset_contract(token_admin.clone());
        let token_client = token::Client::new(&env, &token_contract_id);

        token_client.mint(&customer, &10000);
        client.initialize(&admin);

        let session_id = String::from_str(&env, "pay_refund123");
        client.create_escrow(
            &customer,
            &merchant,
            &token_contract_id,
            &1000,
            &session_id,
            &100, // 100 seconds timeout
        );

        // Fast-forward time past timeout
        env.ledger().with_mut(|li| li.timestamp = 200);

        // Customer refunds
        client.refund_payment(&session_id, &token_contract_id);

        // Verify refunded
        let escrow = client.get_escrow(&session_id);
        assert_eq!(escrow.status, EscrowStatus::Refunded);

        // Verify customer got funds back
        assert_eq!(token_client.balance(&customer), 10000);
    }
}
