#!/bin/bash

echo "=== Deploying PurrFect Spots to Vercel ==="

echo ""
echo "[1/2] Deploying Backend..."
cd backend
vercel --prod
if [ $? -ne 0 ]; then
    echo "Backend deployment failed!"
    exit 1
fi

echo ""
echo "[2/2] Deploying Frontend..."
cd ../frontend
vercel --prod
if [ $? -ne 0 ]; then
    echo "Frontend deployment failed!"
    exit 1
fi

echo ""
echo "=== Deployment completed! ==="
echo ""
echo "Don't forget to:"
echo "1. Update environment variables in Vercel Dashboard"
echo "2. Update Google OAuth redirect URIs"
echo "3. Update API URLs after deployment"
echo ""
