@echo off
echo === Deploying PurrFect Spots to Vercel ===

echo.
echo [1/2] Deploying Backend...
cd backend
call vercel --prod
if %errorlevel% neq 0 (
    echo Backend deployment failed!
    pause
    exit /b 1
)

echo.
echo [2/2] Deploying Frontend...
cd ..\frontend
call vercel --prod
if %errorlevel% neq 0 (
    echo Frontend deployment failed!
    pause
    exit /b 1
)

echo.
echo === Deployment completed! ===
echo.
echo Don't forget to:
echo 1. Update environment variables in Vercel Dashboard
echo 2. Update Google OAuth redirect URIs
echo 3. Update API URLs after deployment
echo.
pause
