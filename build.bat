@echo off
REM Main build script for the entire project on Windows
REM This script performs comprehensive validation and optimization for both frontend and backend

setlocal enabledelayedexpansion

REM Default environment
if "%1"=="" (
    set ENVIRONMENT=production
) else (
    set ENVIRONMENT=%1
)

REM Build flags
set BUILD_ONLY_FRONTEND=false
set BUILD_ONLY_BACKEND=false

if "%2"=="frontend-only" (
    set BUILD_ONLY_FRONTEND=true
)

if "%2"=="backend-only" (
    set BUILD_ONLY_BACKEND=true
)

echo ========================================
echo PurrFect Spots Build Process
echo ========================================
echo [INFO] Starting build process for environment: %ENVIRONMENT%

REM Check if we're in the right directory
if not exist "README.md" (
    echo [ERROR] README.md not found. Please run this script from the project root directory.
    exit /b 1
)

REM Create build reports directory if it doesn't exist
if not exist "build-reports" (
    mkdir build-reports
)

REM Initialize build status variables
set FRONTEND_BUILD_STATUS=not_started
set BACKEND_BUILD_STATUS=not_started
set OVERALL_BUILD_STATUS=success

REM Function to build frontend
:build_frontend
echo ========================================
echo Building Frontend
echo ========================================
set FRONTEND_BUILD_STATUS=in_progress

if not exist "frontend" (
    echo [ERROR] Frontend directory not found
    set FRONTEND_BUILD_STATUS=failed
    goto :frontend_build_end
)

cd frontend

REM Check if the build script exists
if not exist "..\build-frontend.bat" (
    echo [ERROR] Frontend build script not found
    set FRONTEND_BUILD_STATUS=failed
    cd ..
    goto :frontend_build_end
)

REM Run the frontend build script
call ..\build-frontend.bat %ENVIRONMENT%

if %errorlevel% equ 0 (
    set FRONTEND_BUILD_STATUS=success
    echo [INFO] Frontend build completed successfully
    
    REM Copy build report to the main reports directory
    if exist "build-report-*.json" (
        copy "build-report-*.json" "..\build-reports\frontend-build-report.json" >nul
    )
) else (
    set FRONTEND_BUILD_STATUS=failed
    echo [ERROR] Frontend build failed
    cd ..
    goto :frontend_build_end
)

cd ..

:frontend_build_end
exit /b

REM Function to build backend
:build_backend
echo ========================================
echo Building Backend
echo ========================================
set BACKEND_BUILD_STATUS=in_progress

if not exist "backend" (
    echo [ERROR] Backend directory not found
    set BACKEND_BUILD_STATUS=failed
    goto :backend_build_end
)

cd backend

REM Check if the build script exists
if not exist "..\build-backend.bat" (
    echo [ERROR] Backend build script not found
    set BACKEND_BUILD_STATUS=failed
    cd ..
    goto :backend_build_end
)

REM Run the backend build script
call ..\build-backend.bat %ENVIRONMENT%

if %errorlevel% equ 0 (
    set BACKEND_BUILD_STATUS=success
    echo [INFO] Backend build completed successfully
    
    REM Copy build report to the main reports directory
    if exist "build-report-*.json" (
        copy "build-report-*.json" "..\build-reports\backend-build-report.json" >nul
    )
) else (
    set BACKEND_BUILD_STATUS=failed
    echo [ERROR] Backend build failed
    cd ..
    goto :backend_build_end
)

cd ..

:backend_build_end
exit /b

REM Build based on parameters
if "%BUILD_ONLY_FRONTEND%"=="true" (
    call :build_frontend
) else if "%BUILD_ONLY_BACKEND%"=="true" (
    call :build_backend
) else (
    REM Build both frontend and backend
    call :build_frontend
    call :build_backend
)

REM Generate overall build report
echo ========================================
echo Generating Overall Build Report
echo ========================================

REM Get current timestamp
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "timestamp=%YYYY%-%MM%-%DD%T%HH%:%Min%:%Sec%.000Z"

set BUILD_REPORT=build-reports\overall-build-report-%YYYY%%MM%%DD%-%HH%%Min%%Sec%.json
(
echo {
echo   "timestamp": "%timestamp%",
echo   "environment": "%ENVIRONMENT%",
echo   "frontend_build_status": "%FRONTEND_BUILD_STATUS%",
echo   "backend_build_status": "%BACKEND_BUILD_STATUS%",
echo   "overall_build_status": "%OVERALL_BUILD_STATUS%"
echo }
) > %BUILD_REPORT%

echo [INFO] Overall build report generated: %BUILD_REPORT%

REM Print final status
echo ========================================
echo Build Summary
echo ========================================
echo [INFO] Frontend build status: %FRONTEND_BUILD_STATUS%
echo [INFO] Backend build status: %BACKEND_BUILD_STATUS%

if "%FRONTEND_BUILD_STATUS%"=="success" if "%BACKEND_BUILD_STATUS%"=="success" (
    echo [INFO] Overall build completed successfully!
    echo [INFO] Build artifacts are available in their respective directories
    exit /b 0
) else (
    echo [ERROR] Build process completed with errors
    exit /b 1
)