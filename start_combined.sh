#!/bin/bash

# Start Stellar listener in background
python -m app.services.stellar_listener &

# Start API server (foreground)
uvicorn app.main:app --host 0.0.0.0 --port $PORT
