#!/bin/bash
# Start Stellar Listener (Linux/Mac)

echo "============================================================"
echo "  Starting Stellar Payment Listener"
echo "============================================================"
echo ""

# Activate virtual environment
source venv/bin/activate

echo "Starting listener..."
echo "Press Ctrl+C to stop"
echo ""
echo "============================================================"
echo ""

# Start the listener
python -m app.services.stellar_listener
