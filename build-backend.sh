#!/bin/bash

# Build script for Python FastAPI backend
# This script performs comprehensive validation and optimization

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Default environment
ENVIRONMENT=${1:-production}

print_status "Starting backend build process for environment: $ENVIRONMENT"

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found. Please run this script from the backend directory."
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3 to continue."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
REQUIRED_PYTHON_VERSION="3.8.0"

if [ "$(printf '%s\n' "$REQUIRED_PYTHON_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_PYTHON_VERSION" ]; then
    print_warning "Python version $PYTHON_VERSION is lower than recommended $REQUIRED_PYTHON_VERSION"
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is not installed. Please install pip3 to continue."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        print_error "Failed to create virtual environment"
        exit 1
    fi
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Step 1: Check for syntax errors and potential issues
print_status "Step 1: Checking for syntax errors and potential issues..."

# Install development dependencies for linting
print_status "Installing development dependencies..."
pip install flake8 black isort mypy

# Run flake8 for linting
print_status "Running flake8 for code linting..."
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
if [ $? -ne 0 ]; then
    print_error "Code linting failed"
    exit 1
fi

# Run black for code formatting check
print_status "Checking code formatting with black..."
black --check .
if [ $? -ne 0 ]; then
    print_warning "Code formatting issues found. Run 'black .' to fix them."
fi

# Run isort for import sorting check
print_status "Checking import sorting with isort..."
isort --check-only .
if [ $? -ne 0 ]; then
    print_warning "Import sorting issues found. Run 'isort .' to fix them."
fi

# Step 2: Install dependencies
print_status "Step 2: Installing dependencies..."

# Install production dependencies
print_status "Installing production dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    print_error "Failed to install dependencies"
    exit 1
fi

# Step 3: Compile/transform source code
print_status "Step 3: Compiling and transforming source code..."

# Compile Python files to check for syntax errors
print_status "Compiling Python files..."
python3 -m compileall .
if [ $? -ne 0 ]; then
    print_error "Python compilation failed"
    exit 1
fi

# Step 4: Optimize assets and dependencies
print_status "Step 4: Optimizing assets and dependencies..."

# Create a requirements file with exact versions for reproducible builds
print_status "Creating requirements file with exact versions..."
pip freeze > requirements-freeze.txt

# Step 5: Validate the final build for correctness
print_status "Step 5: Validating the final build..."

# Check if main.py exists
if [ ! -f "main.py" ]; then
    print_error "main.py not found"
    exit 1
fi

# Try to import the main application
print_status "Testing application import..."
python3 -c "import main; print('Application import successful')"
if [ $? -ne 0 ]; then
    print_error "Application import failed"
    exit 1
fi

# Step 6: Generate build report
print_status "Step 6: Generating build report..."

# Get package count
PACKAGE_COUNT=$(pip list | wc -l)
print_status "Total packages installed: $PACKAGE_COUNT"

# Get virtual environment size
VENV_SIZE=$(du -sh venv | cut -f1)
print_status "Virtual environment size: $VENV_SIZE"

BUILD_REPORT="build-report-$(date +%Y%m%d-%H%M%S).json"
cat > "$BUILD_REPORT" << EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")",
  "environment": "$ENVIRONMENT",
  "python_version": "$PYTHON_VERSION",
  "package_count": $PACKAGE_COUNT,
  "venv_size": "$VENV_SIZE",
  "status": "success"
}
EOF

print_status "Build report generated: $BUILD_REPORT"

# Success message
print_status "Backend build completed successfully!"
print_status "Virtual environment is ready for deployment"

exit 0