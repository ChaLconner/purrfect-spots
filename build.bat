@echo off
REM Build script for production deployment (Windows)
echo Building Purrfect Spots for production...

REM Check if we're in the right directory
if not exist "package.json" (
    echo Error: Please run this script from the project root directory
    exit /b 1
)
if not exist "backend" (
    echo Error: Please run this script from the project root directory
    exit /b 1
)
if not exist "frontend" (
    echo Error: Please run this script from the project root directory
    exit /b 1
)

REM Build frontend
echo Building frontend...
cd frontend
call npm install
if errorlevel 1 (
    echo Frontend dependency installation failed!
    exit /b 1
)
call npm run build
if errorlevel 1 (
    echo Frontend build failed!
    exit /b 1
)
cd ..

REM Install backend dependencies
echo Installing backend dependencies...
cd backend
pip install -r requirements.txt
if errorlevel 1 (
    echo Backend dependency installation failed!
    exit /b 1
)
cd ..

echo Build complete!
echo.
echo Next steps:
echo 1. Set up environment variables (.env.production files)
echo 2. Deploy frontend dist/ folder to your web server
echo 3. Deploy backend to your Python hosting service
echo 4. Configure your domain and SSL
echo.
echo See DEPLOYMENT.md for detailed instructions.
