"""
FastAPI Application Runner
Run this file to start the FastAPI server
"""

import uvicorn
from main import app

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
