// src/pages/CreatePayment.tsx - CORRECTED VERSION
import React, { useState } from 'react';
import { chainpeService } from '../services/chainpe';

export const CreatePayment = () => {
  const [amount, setAmount] = useState('');
  const [orderId, setOrderId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [session, setSession] = useState<any>(null);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // Create payment session
      const response = await chainpeService.createSession({
        amount_usdc: parseFloat(amount),
        order_id: orderId || `ORDER-${Date.now()}`,
        // Optional URLs - can be omitted or set to actual URLs
        success_url: window.location.origin + '/dashboard/success',
        cancel_url: window.location.origin + '/dashboard',
        metadata: {
          created_from: 'dashboard',
          timestamp: new Date().toISOString()
        }
      });

      setSession(response);
      console.log('Payment session created:', response);
      
      // Optionally redirect to checkout
      // window.location.href = response.checkout_url;
    } catch (err: any) {
      console.error('Payment creation failed:', err);
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to create payment';
      setError(errorMsg);
      
      // Log the full error for debugging
      console.error('Full error:', {
        status: err.response?.status,
        data: err.response?.data,
        message: err.message
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="create-payment">
      <h1>Create Payment Session</h1>

      <form onSubmit={handleCreate}>
        <div className="form-group">
          <label>Amount (USDC)</label>
          <input
            type="number"
            step="0.01"
            min="0.01"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="50.00"
            required
          />
        </div>

        <div className="form-group">
          <label>Order ID (optional)</label>
          <input
            type="text"
            value={orderId}
            onChange={(e) => setOrderId(e.target.value)}
            placeholder="ORDER-123"
          />
          <small>Leave empty to auto-generate</small>
        </div>

        {error && (
          <div className="error-message">
            ❌ {error}
          </div>
        )}

        <button type="submit" disabled={loading}>
          {loading ? 'Creating...' : 'Create Payment Session'}
        </button>
      </form>

      {session && (
        <div className="session-details">
          <h2>✅ Payment Session Created!</h2>
          <div className="detail-row">
            <strong>Session ID:</strong>
            <code>{session.session_id}</code>
          </div>
          <div className="detail-row">
            <strong>Amount:</strong>
            <span>{session.amount_usdc} USDC</span>
          </div>
          <div className="detail-row">
            <strong>Order ID:</strong>
            <span>{session.order_id}</span>
          </div>
          <div className="detail-row">
            <strong>Status:</strong>
            <span className="status">{session.status}</span>
          </div>
          <div className="actions">
            <a 
              href={session.checkout_url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="button primary"
            >
              Open Checkout Page →
            </a>
            <button 
              onClick={() => navigator.clipboard.writeText(session.checkout_url)}
              className="button secondary"
            >
              📋 Copy Checkout URL
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
