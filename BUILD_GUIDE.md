# Build Guide for PurrFect Spots

This guide explains how to use the build scripts for the PurrFect Spots project, which includes both a Vue.js frontend and a Python FastAPI backend.

## Overview

The build system is designed to:
1. Check for syntax errors and potential issues
2. Compile/transform source code as needed
3. Optimize assets and dependencies
4. Generate production-ready build artifacts
5. Validate the final build for correctness

## Prerequisites

### Frontend
- Node.js 18+ (recommended)
- npm or yarn

### Backend
- Python 3.8+ (recommended)
- pip

## Build Scripts

### Main Build Scripts

#### Linux/macOS
- `build.sh` - Main build script for the entire project
- `build-frontend.sh` - Frontend-only build script
- `build-backend.sh` - Backend-only build script

#### Windows
- `build.bat` - Main build script for the entire project
- `build-frontend.bat` - Frontend-only build script
- `build-backend.bat` - Backend-only build script

## Usage

### Building the Entire Project

#### Linux/macOS
```bash
# Build for production (default)
./build.sh

# Build for development
./build.sh development

# Build for staging
./build.sh staging
```

#### Windows
```cmd
# Build for production (default)
build.bat

# Build for development
build.bat development

# Build for staging
build.bat staging
```

### Building Only Frontend or Backend

#### Linux/macOS
```bash
# Build only frontend
./build.sh production frontend-only

# Build only backend
./build.sh production backend-only
```

#### Windows
```cmd
# Build only frontend
build.bat production frontend-only

# Build only backend
build.bat production backend-only
```

### Building Individual Components

#### Frontend

#### Linux/macOS
```bash
cd frontend
../build-frontend.sh production
```

#### Windows
```cmd
cd frontend
..\build-frontend.bat production
```

#### Backend

#### Linux/macOS
```bash
cd backend
../build-backend.sh production
```

#### Windows
```cmd
cd backend
..\build-backend.bat production
```

## Environments

### Development
- Source maps enabled
- No minification
- Console logs retained
- Debug information included

### Staging
- Source maps enabled
- Minification enabled
- Console logs retained
- Limited debug information

### Production
- Source maps disabled
- Full minification
- Console logs removed
- No debug information

## Build Process

### Frontend Build Process
1. Checks for Node.js and validates version
2. Installs dependencies if needed
3. Runs TypeScript type checking
4. Builds the application with Vite
5. Optimizes assets and dependencies
6. Validates the build output
7. Generates a build report

### Backend Build Process
1. Checks for Python and validates version
2. Creates and activates a virtual environment
3. Runs code quality checks (flake8, black, isort)
4. Installs dependencies
5. Compiles Python files
6. Creates a requirements file with exact versions
7. Validates the build
8. Generates a build report

## Build Reports

After each build, a report is generated in the `build-reports` directory:
- `frontend-build-report.json` - Frontend build details
- `backend-build-report.json` - Backend build details
- `overall-build-report-<timestamp>.json` - Overall build status

## CI/CD Integration

The build scripts are designed to work with CI/CD pipelines. See `.github/workflows/build.yml` for an example GitHub Actions workflow.

## Troubleshooting

### Common Issues

#### Frontend
- **Node.js version too low**: Upgrade to Node.js 18 or higher
- **TypeScript errors**: Fix type errors in your code
- **Build failures**: Check the error messages in the console

#### Backend
- **Python version too low**: Upgrade to Python 3.8 or higher
- **Dependency conflicts**: Check requirements.txt for conflicting versions
- **Import errors**: Verify all imports are correct

### Getting Help

If you encounter issues:
1. Check the build reports for detailed error information
2. Review the console output for specific error messages
3. Ensure all prerequisites are installed
4. Verify you're running the scripts from the correct directory

## Configuration

Build behavior can be customized by modifying the `build-config.json` file. This file contains settings for:
- Environment-specific configurations
- Build script paths
- Validation options
- Optimization settings
- Reporting preferences

## Advanced Usage

### Custom Build Scripts

You can create custom build scripts by modifying the existing ones or creating new ones based on your specific needs.

### Environment Variables

The build scripts respect the following environment variables:
- `NODE_ENV` - Sets the Node.js environment
- `PYTHON_ENV` - Sets the Python environment

### Build Hooks

You can add custom hooks to the build process by modifying the build scripts to run additional commands at specific points in the build process.