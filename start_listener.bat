@echo off
REM Start Stellar Listener (Windows)

echo ============================================================
echo   Starting Stellar Payment Listener
echo ============================================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

echo Starting listener...
echo Press Ctrl+C to stop
echo.
echo ============================================================
echo.

REM Start the listener
python -m app.services.stellar_listener
