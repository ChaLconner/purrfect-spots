#!/bin/bash

# Frontend Deployment Script for PurrFect Spots

echo "🚀 Starting Frontend Deployment..."

# Check if we're in the frontend directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found. Please run this script from the frontend directory."
    exit 1
fi

echo "📦 Installing dependencies..."
npm ci

echo "🧹 Cleaning previous build..."
rm -rf dist

echo "🔧 Type checking..."
npm run type-check

echo "🏗️ Building for production..."
npm run build:prod

echo "📊 Build statistics:"
ls -lah dist/

echo "✅ Frontend build completed successfully!"
echo "📂 Build files are in the 'dist' directory"
echo "🌐 Ready for deployment to Vercel/Netlify"

# Optional: Auto-deploy to Vercel if vercel CLI is available
if command -v vercel &> /dev/null; then
    echo "🚀 Found Vercel CLI. Deploy now? (y/n)"
    read -r response
    if [[ "$response" == "y" || "$response" == "Y" ]]; then
        echo "🚀 Deploying to Vercel..."
        vercel --prod
        echo "✅ Deployment completed!"
    fi
else
    echo "💡 Install Vercel CLI to enable auto-deployment: npm i -g vercel"
fi
