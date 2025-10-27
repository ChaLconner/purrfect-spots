@echo off
REM Build script for Python FastAPI backend on Windows
REM This script performs comprehensive validation and optimization

setlocal enabledelayedexpansion

REM Default environment
if "%1"=="" (
    set ENVIRONMENT=production
) else (
    set ENVIRONMENT=%1
)

echo [INFO] Starting backend build process for environment: %ENVIRONMENT%

REM Check if we're in the right directory
if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found. Please run this script from the backend directory.
    exit /b 1
)

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed. Please install Python to continue.
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo [INFO] Using Python version: %PYTHON_VERSION%

REM Check if pip is installed
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] pip is not installed. Please install pip to continue.
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment
        exit /b 1
    )
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip

REM Step 1: Check for syntax errors and potential issues
echo [INFO] Step 1: Checking for syntax errors and potential issues...

REM Install development dependencies for linting
echo [INFO] Installing development dependencies...
pip install flake8 black isort mypy

REM Run flake8 for linting
echo [INFO] Running flake8 for code linting...
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
if %errorlevel% neq 0 (
    echo [ERROR] Code linting failed
    exit /b 1
)

REM Run black for code formatting check
echo [INFO] Checking code formatting with black...
black --check .
if %errorlevel% neq 0 (
    echo [WARNING] Code formatting issues found. Run 'black .' to fix them.
)

REM Run isort for import sorting check
echo [INFO] Checking import sorting with isort...
isort --check-only .
if %errorlevel% neq 0 (
    echo [WARNING] Import sorting issues found. Run 'isort .' to fix them.
)

REM Step 2: Install dependencies
echo [INFO] Step 2: Installing dependencies...

REM Install production dependencies
echo [INFO] Installing production dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    exit /b 1
)

REM Step 3: Compile/transform source code
echo [INFO] Step 3: Compiling and transforming source code...

REM Compile Python files to check for syntax errors
echo [INFO] Compiling Python files...
python -m compileall .
if %errorlevel% neq 0 (
    echo [ERROR] Python compilation failed
    exit /b 1
)

REM Step 4: Optimize assets and dependencies
echo [INFO] Step 4: Optimizing assets and dependencies...

REM Create a requirements file with exact versions for reproducible builds
echo [INFO] Creating requirements file with exact versions...
pip freeze > requirements-freeze.txt

REM Step 5: Validate the final build for correctness
echo [INFO] Step 5: Validating the final build...

REM Check if main.py exists
if not exist "main.py" (
    echo [ERROR] main.py not found
    exit /b 1
)

REM Try to import the main application
echo [INFO] Testing application import...
python -c "import main; print('Application import successful')"
if %errorlevel% neq 0 (
    echo [ERROR] Application import failed
    exit /b 1
)

REM Step 6: Generate build report
echo [INFO] Step 6: Generating build report...

REM Get package count
for /f %%i in ('pip list ^| find /c /v ""') do set PACKAGE_COUNT=%%i
echo [INFO] Total packages installed: %PACKAGE_COUNT%

REM Get virtual environment size
set VENV_SIZE=0
for /f "tokens=3" %%a in ('dir venv /s /-c ^| find "bytes"') do set VENV_SIZE=%%a
echo [INFO] Virtual environment size: %VENV_SIZE% bytes

REM Get current timestamp
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "timestamp=%YYYY%-%MM%-%DD%T%HH%:%Min%:%Sec%.000Z"

set BUILD_REPORT=build-report-%YYYY%%MM%%DD%-%HH%%Min%%Sec%.json
(
echo {
echo   "timestamp": "%timestamp%",
echo   "environment": "%ENVIRONMENT%",
echo   "python_version": "%PYTHON_VERSION%",
echo   "package_count": %PACKAGE_COUNT%,
echo   "venv_size": "%VENV_SIZE% bytes",
echo   "status": "success"
echo }
) > %BUILD_REPORT%

echo [INFO] Build report generated: %BUILD_REPORT%

REM Success message
echo [INFO] Backend build completed successfully!
echo [INFO] Virtual environment is ready for deployment

exit /b 0