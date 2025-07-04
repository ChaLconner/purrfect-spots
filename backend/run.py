#!/usr/bin/env python3
"""
Production WSGI server for Purrfect Spots backend
"""
import os
from app import app

if __name__ == "__main__":
    # Get port from environment variable (for deployment)
    port = int(os.environ.get('PORT', 5000))
    
    # Run the application
    app.run(
        host='0.0.0.0',
        port=port,
        debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    )
