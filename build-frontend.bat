@echo off
REM Build script for Vue.js + TypeScript frontend on Windows
REM This script performs comprehensive validation and optimization

setlocal enabledelayedexpansion

REM Default environment
if "%1"=="" (
    set ENVIRONMENT=production
) else (
    set ENVIRONMENT=%1
)

echo [INFO] Starting frontend build process for environment: %ENVIRONMENT%

REM Check if we're in the right directory
if not exist "package.json" (
    echo [ERROR] package.json not found. Please run this script from the frontend directory.
    exit /b 1
)

REM Check if Node.js is installed
node -v >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed. Please install Node.js to continue.
    exit /b 1
)

REM Get Node.js version
for /f "tokens=*" %%i in ('node -v') do set NODE_VERSION=%%i
echo [INFO] Using Node.js version: %NODE_VERSION%

REM Install dependencies if node_modules doesn't exist or package.json changed
if not exist "node_modules" (
    echo [INFO] Installing dependencies...
    npm ci --silent
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies
        exit /b 1
    )
) else (
    echo [INFO] Dependencies are up to date
)

REM Step 1: Check for syntax errors and potential issues
echo [INFO] Step 1: Checking for syntax errors and potential issues...

REM Run TypeScript type checking
echo [INFO] Running TypeScript type checking...
npm run type-check
if %errorlevel% neq 0 (
    echo [ERROR] TypeScript type checking failed
    exit /b 1
)

REM Step 2: Compile/transform source code
echo [INFO] Step 2: Compiling and transforming source code...

REM Set environment variables
set NODE_ENV=%ENVIRONMENT%

REM Build the application
if "%ENVIRONMENT%"=="production" (
    echo [INFO] Building for production...
    npm run build:prod
) else (
    echo [INFO] Building for %ENVIRONMENT%...
    npm run build
)

if %errorlevel% neq 0 (
    echo [ERROR] Build process failed
    exit /b 1
)

REM Step 3: Optimize assets and dependencies
echo [INFO] Step 3: Optimizing assets and dependencies...

REM Check if dist directory exists
if not exist "dist" (
    echo [ERROR] Build output directory (dist) not found
    exit /b 1
)

REM Get build statistics
for /f "tokens=3" %%a in ('dir dist /s /-c ^| find "bytes"') do set DIST_SIZE=%%a
echo [INFO] Build size: %DIST_SIZE% bytes

REM Count files in dist
set FILE_COUNT=0
for /f %%i in ('dir /b /s /a-d dist ^| find /c /v ""') do set FILE_COUNT=%%i
echo [INFO] Total files in build: %FILE_COUNT%

REM Step 4: Validate the final build for correctness
echo [INFO] Step 4: Validating the final build...

REM Check if index.html exists
if not exist "dist\index.html" (
    echo [ERROR] index.html not found in build output
    exit /b 1
)

REM Check for critical assets
if not exist "dist\assets" (
    echo [WARNING] Assets directory not found in build output
)

REM Check for JavaScript files
set JS_COUNT=0
for /f %%i in ('dir /b /s dist\*.js 2^>nul ^| find /c /v ""') do set JS_COUNT=%%i
if %JS_COUNT% equ 0 (
    echo [ERROR] No JavaScript files found in build output
    exit /b 1
)

REM Check for CSS files
set CSS_COUNT=0
for /f %%i in ('dir /b /s dist\*.css 2^>nul ^| find /c /v ""') do set CSS_COUNT=%%i
if %CSS_COUNT% equ 0 (
    echo [WARNING] No CSS files found in build output
)

REM Step 5: Generate build report
echo [INFO] Step 5: Generating build report...

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
echo   "node_version": "%NODE_VERSION%",
echo   "build_size": "%DIST_SIZE% bytes",
echo   "file_count": %FILE_COUNT%,
echo   "js_files": %JS_COUNT%,
echo   "css_files": %CSS_COUNT%,
echo   "status": "success"
echo }
) > %BUILD_REPORT%

echo [INFO] Build report generated: %BUILD_REPORT%

REM Success message
echo [INFO] Frontend build completed successfully!
echo [INFO] Build artifacts are available in the 'dist' directory

exit /b 0