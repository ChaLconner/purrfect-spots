#!/bin/bash

# Main build script for the entire project
# This script performs comprehensive validation and optimization for both frontend and backend

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Default environment
ENVIRONMENT=${1:-production}
BUILD_ONLY_FRONTEND=${2:-false}
BUILD_ONLY_BACKEND=${3:-false}

print_header "PurrFect Spots Build Process"
print_status "Starting build process for environment: $ENVIRONMENT"

# Check if we're in the right directory
if [ ! -f "README.md" ]; then
    print_error "README.md not found. Please run this script from the project root directory."
    exit 1
fi

# Create build reports directory if it doesn't exist
mkdir -p build-reports

# Initialize build status variables
FRONTEND_BUILD_STATUS="not_started"
BACKEND_BUILD_STATUS="not_started"
OVERALL_BUILD_STATUS="success"

# Function to build frontend
build_frontend() {
    print_header "Building Frontend"
    FRONTEND_BUILD_STATUS="in_progress"
    
    if [ ! -d "frontend" ]; then
        print_error "Frontend directory not found"
        FRONTEND_BUILD_STATUS="failed"
        return 1
    fi
    
    cd frontend
    
    # Check if the build script exists
    if [ ! -f "../build-frontend.sh" ]; then
        print_error "Frontend build script not found"
        FRONTEND_BUILD_STATUS="failed"
        cd ..
        return 1
    fi
    
    # Run the frontend build script
    chmod +x ../build-frontend.sh
    ../build-frontend.sh $ENVIRONMENT
    
    if [ $? -eq 0 ]; then
        FRONTEND_BUILD_STATUS="success"
        print_status "Frontend build completed successfully"
        
        # Copy build report to the main reports directory
        if [ -f "build-report-"*.json ]; then
            cp build-report-*.json ../build-reports/frontend-build-report.json
        fi
    else
        FRONTEND_BUILD_STATUS="failed"
        print_error "Frontend build failed"
        cd ..
        return 1
    fi
    
    cd ..
}

# Function to build backend
build_backend() {
    print_header "Building Backend"
    BACKEND_BUILD_STATUS="in_progress"
    
    if [ ! -d "backend" ]; then
        print_error "Backend directory not found"
        BACKEND_BUILD_STATUS="failed"
        return 1
    fi
    
    cd backend
    
    # Check if the build script exists
    if [ ! -f "../build-backend.sh" ]; then
        print_error "Backend build script not found"
        BACKEND_BUILD_STATUS="failed"
        cd ..
        return 1
    fi
    
    # Run the backend build script
    chmod +x ../build-backend.sh
    ../build-backend.sh $ENVIRONMENT
    
    if [ $? -eq 0 ]; then
        BACKEND_BUILD_STATUS="success"
        print_status "Backend build completed successfully"
        
        # Copy build report to the main reports directory
        if [ -f "build-report-"*.json ]; then
            cp build-report-*.json ../build-reports/backend-build-report.json
        fi
    else
        BACKEND_BUILD_STATUS="failed"
        print_error "Backend build failed"
        cd ..
        return 1
    fi
    
    cd ..
}

# Build based on parameters
if [ "$BUILD_ONLY_FRONTEND" = "true" ]; then
    build_frontend
elif [ "$BUILD_ONLY_BACKEND" = "true" ]; then
    build_backend
else
    # Build both frontend and backend
    build_frontend
    build_backend
fi

# Generate overall build report
print_header "Generating Overall Build Report"

BUILD_REPORT="build-reports/overall-build-report-$(date +%Y%m%d-%H%M%S).json"
cat > "$BUILD_REPORT" << EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")",
  "environment": "$ENVIRONMENT",
  "frontend_build_status": "$FRONTEND_BUILD_STATUS",
  "backend_build_status": "$BACKEND_BUILD_STATUS",
  "overall_build_status": "$OVERALL_BUILD_STATUS"
}
EOF

print_status "Overall build report generated: $BUILD_REPORT"

# Print final status
print_header "Build Summary"
print_status "Frontend build status: $FRONTEND_BUILD_STATUS"
print_status "Backend build status: $BACKEND_BUILD_STATUS"

if [ "$FRONTEND_BUILD_STATUS" = "success" ] && [ "$BACKEND_BUILD_STATUS" = "success" ]; then
    print_status "Overall build completed successfully!"
    print_status "Build artifacts are available in their respective directories"
    exit 0
else
    print_error "Build process completed with errors"
    exit 1
fi