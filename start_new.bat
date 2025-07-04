@echo off
cls
echo.
echo ========================================
echo    🐱 Purrfect Spots - Quick Start
echo ========================================
echo.

REM Check if we're in the right directory
if not exist "frontend" (
    echo ❌ Error: frontend directory not found
    echo    Please run this script from the purrfect-spots root directory
    echo.
    pause
    exit /b 1
)

if not exist "backend" (
    echo ❌ Error: backend directory not found
    echo    Please run this script from the purrfect-spots root directory
    echo.
    pause
    exit /b 1
)

echo ⚙️  Step 1: Setting up Backend...
cd backend

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating Python virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment
        echo    Make sure Python is installed and accessible
        pause
        exit /b 1
    )
)

echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Failed to activate virtual environment
    pause
    exit /b 1
)

echo 📚 Installing backend dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ⚠️  Some dependencies failed to install (continuing anyway)
)

REM Check if .env file exists
if not exist ".env" (
    echo ⚠️  Warning: .env file not found
    echo    Creating .env from .env.example...
    copy .env.example .env >nul
    echo    Please edit .env file with your AWS credentials
    echo.
)

cd..

echo.
echo ⚙️  Step 2: Setting up Frontend...
cd frontend

echo 📚 Installing frontend dependencies...
call npm install
if errorlevel 1 (
    echo ❌ Failed to install frontend dependencies
    echo    Make sure Node.js and npm are installed
    pause
    exit /b 1
)

cd..

echo.
echo 🚀 Step 3: Choose how to start the application...
echo.
echo 1. Start Backend only
echo 2. Start Frontend only  
echo 3. Start Both (recommended)
echo.
set /p choice="Enter your choice (1-3): "

if "%choice%"=="1" goto start_backend
if "%choice%"=="2" goto start_frontend  
if "%choice%"=="3" goto start_both
echo Invalid choice. Starting both servers...
goto start_both

:start_backend
echo.
echo 🔧 Starting backend server...
cd backend
call venv\Scripts\activate.bat
echo ✅ Backend server starting at http://localhost:5000
echo 💡 Press Ctrl+C to stop the server
python app.py
goto end

:start_frontend
echo.
echo 🌐 Starting frontend development server...
cd frontend
echo ✅ Frontend server starting at http://localhost:5173
echo 💡 Press Ctrl+C to stop the server
npm run dev
goto end

:start_both
echo.
echo 🔧 Starting backend server in background...
start "Backend Server" cmd /c "cd backend && call venv\Scripts\activate.bat && python app.py && pause"

echo ⏳ Waiting for backend to start...
timeout /t 3 /nobreak >nul

echo 🌐 Starting frontend development server...
cd frontend
echo.
echo ✅ Both servers are starting!
echo 🌐 Frontend: http://localhost:5173
echo 🔧 Backend:  http://localhost:5000
echo.
echo 💡 Tips:
echo    - Frontend will run in this terminal
echo    - Backend runs in a separate window
echo    - Press Ctrl+C here to stop frontend
echo    - Close backend window to stop backend
echo.
npm run dev

:end
echo.
echo 👋 Thanks for using Purrfect Spots!
pause
