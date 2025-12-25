from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database import Database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lifespan context manager (replaces deprecated startup/shutdown events)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events.
    Runs once when server starts and when it stops.
    """
    # Startup
    logger.info("🚀 Starting up KvK Tracker API...")
    await Database.connect_db()
    yield
    # Shutdown
    logger.info("🛑 Shutting down...")
    await Database.close_db()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API for tracking Rise of Kingdoms KvK statistics",
    lifespan=lifespan
)

# CORS middleware (allows frontend to communicate with backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint (health check)
@app.get("/")
async def root():
    """
    Health check endpoint.
    Returns basic API information.
    """
    return {
        "message": "KvK Tracker API is running!",
        "version": settings.app_version,
        "status": "healthy"
    }

# Test endpoint
@app.get("/api/test")
async def test():
    """Test endpoint to verify API is working."""
    return {
        "message": "API is working!",
        "database": "connected" if Database.client else "disconnected"
    }

# We'll add route imports here later
# from app.routes import auth, players, upload, fights