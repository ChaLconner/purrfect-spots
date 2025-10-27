#!/bin/bash

# Build script for Vue.js + TypeScript frontend
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

print_status "Starting frontend build process for environment: $ENVIRONMENT"

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    print_error "package.json not found. Please run this script from the frontend directory."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js to continue."
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2)
REQUIRED_NODE_VERSION="18.0.0"

if [ "$(printf '%s\n' "$REQUIRED_NODE_VERSION" "$NODE_VERSION" | sort -V | head -n1)" != "$REQUIRED_NODE_VERSION" ]; then
    print_warning "Node.js version $NODE_VERSION is lower than recommended $REQUIRED_NODE_VERSION"
fi

# Install dependencies if node_modules doesn't exist or package.json changed
if [ ! -d "node_modules" ] || [ "package.json" -nt "node_modules" ]; then
    print_status "Installing dependencies..."
    npm ci --silent
    if [ $? -ne 0 ]; then
        print_error "Failed to install dependencies"
        exit 1
    fi
else
    print_status "Dependencies are up to date"
fi

# Step 1: Check for syntax errors and potential issues
print_status "Step 1: Checking for syntax errors and potential issues..."

# Run TypeScript type checking
print_status "Running TypeScript type checking..."
npm run type-check
if [ $? -ne 0 ]; then
    print_error "TypeScript type checking failed"
    exit 1
fi

# Step 2: Compile/transform source code
print_status "Step 2: Compiling and transforming source code..."

# Set environment variables
export NODE_ENV=$ENVIRONMENT

# Build the application
if [ "$ENVIRONMENT" = "production" ]; then
    print_status "Building for production..."
    npm run build:prod
else
    print_status "Building for $ENVIRONMENT..."
    npm run build
fi

if [ $? -ne 0 ]; then
    print_error "Build process failed"
    exit 1
fi

# Step 3: Optimize assets and dependencies
print_status "Step 3: Optimizing assets and dependencies..."

# Check if dist directory exists
if [ ! -d "dist" ]; then
    print_error "Build output directory (dist) not found"
    exit 1
fi

# Get build statistics
DIST_SIZE=$(du -sh dist | cut -f1)
print_status "Build size: $DIST_SIZE"

# Count files in dist
FILE_COUNT=$(find dist -type f | wc -l)
print_status "Total files in build: $FILE_COUNT"

# Step 4: Validate the final build for correctness
print_status "Step 4: Validating the final build..."

# Check if index.html exists
if [ ! -f "dist/index.html" ]; then
    print_error "index.html not found in build output"
    exit 1
fi

# Check for critical assets
if [ ! -d "dist/assets" ]; then
    print_warning "Assets directory not found in build output"
fi

# Check for JavaScript files
JS_COUNT=$(find dist -name "*.js" | wc -l)
if [ "$JS_COUNT" -eq 0 ]; then
    print_error "No JavaScript files found in build output"
    exit 1
fi

# Check for CSS files
CSS_COUNT=$(find dist -name "*.css" | wc -l)
if [ "$CSS_COUNT" -eq 0 ]; then
    print_warning "No CSS files found in build output"
fi

# Step 5: Generate build report
print_status "Step 5: Generating build report..."

BUILD_REPORT="build-report-$(date +%Y%m%d-%H%M%S).json"
cat > "$BUILD_REPORT" << EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")",
  "environment": "$ENVIRONMENT",
  "node_version": "$NODE_VERSION",
  "build_size": "$DIST_SIZE",
  "file_count": $FILE_COUNT,
  "js_files": $JS_COUNT,
  "css_files": $CSS_COUNT,
  "status": "success"
}
EOF

print_status "Build report generated: $BUILD_REPORT"

# Success message
print_status "Frontend build completed successfully!"
print_status "Build artifacts are available in the 'dist' directory"

exit 0