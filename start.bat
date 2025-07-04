@echo off
echo.
echo 🐱 Purrfect Spots - Quick Start
echo ===============================
echo.

REM Check if we're in the right directory
if not exist "frontend" (
    echo Error: frontend directory not found
    echo Please run this script from the purrfect-spots root directory
    pause
    exit /b 1
)

if not exist "backend" (
    echo Error: backend directory not found
    echo Please run this script from the purrfect-spots root directory
    pause
    exit /b 1
)

echo Step 1: Setting up Backend...
cd backend

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install backend dependencies
echo Installing backend dependencies...
pip install -r requirements.txt

REM Check if .env file exists
if not exist ".env" (
    echo.
    echo ⚠️  WARNING: .env file not found!
    echo Please create .env file from .env.example and configure AWS credentials
    echo.
    echo 1. Copy .env.example to .env
    echo 2. Edit .env with your AWS credentials
    echo 3. Run this script again
    echo.
    pause
    exit /b 1
)

echo.
echo Step 2: Setting up Frontend...
cd ..\frontend

REM Install frontend dependencies
echo Installing frontend dependencies...
call npm install

echo.
echo Step 3: Starting applications...
echo.

REM Start backend in background
echo Starting backend server...
start "Backend Server" cmd /k "cd /d %cd%\..\backend && venv\Scripts\activate.bat && python app.py"

REM Wait a moment for backend to start
timeout /t 3 /nobreak > nul

REM Start frontend
echo Starting frontend development server...
start "Frontend Server" cmd /k "cd /d %cd% && npm run dev"

echo.
echo ✅ Both servers are starting!
echo.
echo Frontend: http://localhost:5173
echo Backend:  http://localhost:5000
echo.
echo Press any key to close this window...
pause > nul
