@echo off
echo Starting Purrfect Spots Backend Server...
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found. Creating one...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies if needed
if not exist "venv\Lib\site-packages\flask" (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Check if .env file exists
if not exist ".env" (
    echo .env file not found. Please create one from .env.example
    echo Copy .env.example to .env and update with your AWS credentials
    pause
    exit /b 1
)

REM Start the server
echo Starting Flask server...
python app.py

pause
