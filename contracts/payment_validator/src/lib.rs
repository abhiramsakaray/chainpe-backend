#![no_std]
use soroban_sdk::{contract, contractimpl, contracttype, contracterror, Address, Env, String, symbol_short};

/// Payment session data stored in contract
/// Contract validates payment rules - actual payments go to merchant addresses
#[derive(Clone)]
#[contracttype]
pub struct PaymentSession {
    pub memo: String,           // Payment session ID (memo)
    pub merchant: Address,       // Merchant's Stellar address (receives payments)
    pub amount: i128,           // Expected minimum amount
    pub is_active: bool,        // Whether session is still active
    pub created_at: u64,        // Timestamp when session was created
}

#[contracterror]
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)]
#[repr(u32)]
pub enum Error {
    InvalidMemo = 1,
    SessionNotFound = 2,
    InsufficientAmount = 3,
    SessionExpired = 4,
    Unauthorized = 5,
}

#[contract]
pub struct ChainPeValidator;

#[contractimpl]
impl ChainPeValidator {
    /// Initialize contract with backend address (only backend can register sessions)
    pub fn initialize(env: Env, backend_address: Address) {
        let backend_key = symbol_short!("BACKEND");
        if env.storage().instance().has(&backend_key) {
            panic!("Already initialized");
        }
        env.storage().instance().set(&backend_key, &backend_address);
    }
    
    /// Backend registers a payment session (called when user creates checkout)
    pub fn register_session(
        env: Env,
        memo: String,
        merchant: Address,
        amount: i128,
    ) -> Result<(), Error> {
        // Only backend can register sessions
        let backend_key = symbol_short!("BACKEND");
        let backend: Address = env
            .storage()
            .instance()
            .get(&backend_key)
            .ok_or(Error::Unauthorized)?;
        backend.require_auth();
        
        // Get current ledger timestamp
        let created_at = env.ledger().timestamp();
        
        // Store session data
        let session = PaymentSession {
            memo: memo.clone(),
            merchant,
            amount,
            is_active: true,
            created_at,
        };
        
        env.storage().persistent().set(&memo, &session);
        
        // Emit event
        env.events().publish((symbol_short!("reg_sess"),), memo);
        
        Ok(())
    }
    
    /// Validate payment - called by backend after detecting payment
    /// Returns true if payment is valid, false otherwise
    pub fn validate_payment(
        env: Env,
        memo: String,
        amount: i128,
    ) -> Result<bool, Error> {
        // Get session
        let session: PaymentSession = env
            .storage()
            .persistent()
            .get(&memo)
            .ok_or(Error::SessionNotFound)?;
        
        // Check if session is active
        if !session.is_active {
            env.events().publish((symbol_short!("expired"),), memo);
            return Err(Error::SessionExpired);
        }
        
        // Check if amount is sufficient
        if amount < session.amount {
            env.events().publish(
                (symbol_short!("insuff"),),
                (memo.clone(), amount, session.amount)
            );
            return Err(Error::InsufficientAmount);
        }
        
        // Mark session as completed (deactivate)
        let mut updated_session = session.clone();
        updated_session.is_active = false;
        env.storage().persistent().set(&memo, &updated_session);
        
        // Emit success event
        env.events().publish(
            (symbol_short!("valid"),),
            (memo, session.merchant, amount)
        );
        
        Ok(true)
    }
    
    /// Backend deactivates session (when expired or cancelled)
    pub fn deactivate_session(env: Env, memo: String) -> Result<(), Error> {
        let backend_key = symbol_short!("BACKEND");
        let backend: Address = env
            .storage()
            .instance()
            .get(&backend_key)
            .ok_or(Error::Unauthorized)?;
        backend.require_auth();
        
        let mut session: PaymentSession = env
            .storage()
            .persistent()
            .get(&memo)
            .ok_or(Error::SessionNotFound)?;
        
        session.is_active = false;
        env.storage().persistent().set(&memo, &session);
        
        env.events().publish((symbol_short!("deact"),), memo);
        Ok(())
    }
    
    /// Get session details (for frontend verification)
    pub fn get_session(env: Env, memo: String) -> Option<PaymentSession> {
        env.storage().persistent().get(&memo)
    }
}

#[cfg(test)]
mod test {
    use super::*;
    use soroban_sdk::testutils::{Address as _, Ledger};
    use soroban_sdk::{Address, Env};

    #[test]
    fn test_payment_flow() {
        let env = Env::default();
        let contract_id = env.register_contract(None, ChainPeValidator);
        let client = ChainPeValidatorClient::new(&env, &contract_id);
        
        let backend = Address::generate(&env);
        let merchant = Address::generate(&env);
        let customer = Address::generate(&env);
        
        // Initialize
        client.initialize(&backend);
        
        // Register session
        let memo = String::from_str(&env, "pay_test123");
        client.register_session(&memo, &merchant, &100);
        
        // Verify session
        let session = client.get_session(&memo);
        assert!(session.is_some());
        assert!(session.unwrap().is_active);
    }
}
