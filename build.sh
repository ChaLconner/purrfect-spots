# Build script for production deployment
echo "Building Purrfect Spots for production..."

# Check if we're in the right directory
if [ ! -f "package.json" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "Error: Please run this script from the project root directory"
    exit 1
fi

# Build frontend
echo "Building frontend..."
cd frontend
npm install
npm run build
if [ $? -ne 0 ]; then
    echo "Frontend build failed!"
    exit 1
fi
cd ..

# Install backend dependencies
echo "Installing backend dependencies..."
cd backend
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Backend dependency installation failed!"
    exit 1
fi
cd ..

echo "Build complete!"
echo ""
echo "Next steps:"
echo "1. Set up environment variables (.env.production files)"
echo "2. Deploy frontend dist/ folder to your web server"
echo "3. Deploy backend to your Python hosting service"
echo "4. Configure your domain and SSL"
echo ""
echo "See DEPLOYMENT.md for detailed instructions."
