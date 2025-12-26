from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database import Database
from app.models import Player, PlayerStats
from app.utils.csv_parser import CSVParser
from app.services.data_processor import DataProcessor
from app.routes.auth import router as auth_router
from app.routes.upload import router as upload_router
from app.routes.players import router as players_router


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("🚀 Starting KvK Tracker...")
    await Database.connect_db()
    yield
    logger.info("🛑 Shutting down...")
    await Database.close_db()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API for tracking Rise of Kingdoms KvK statistics",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)

app.include_router(upload_router)

app.include_router(players_router)

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "KvK Tracker API is running!",
        "version": settings.app_version,
        "status": "healthy"
    }

@app.get("/api/test")
async def test():
    """Test endpoint to verify API is working."""
    return {
        "message": "API is working!",
        "database": "connected" if Database.client else "disconnected"
    }

@app.get("/api/test-models")
async def test_models():
    """Test endpoint to verify models work."""
    test_player = Player(
        governor_id="12345",
        governor_name="TestPlayer",
        current_stats=PlayerStats(
            power=100000000,
            kill_points=50000000,
            deads=5000000,
            t4_kills=3000000,
            t5_kills=10000000
        )
    )
    return {
        "message": "Models working!",
        "sample_player": test_player.model_dump()
    }

@app.get("/api/test-csv-parse")  # ← Changed to GET
async def test_csv_parse():
    """Test CSV parsing with sample data."""
    
    # Sample CSV matching your format
    sample_csv = """governor_id,governor_name,power,deads,kill_points,t4_kills,t5_kills
53242709,ᴶᶜmasa4ん,"230,639,240","45,368,922","5,857,666,585","116,373,863","234,244,498"
117909431,ˢᵖPifouPrime,"132,252,619","15,751,633","2,040,563,385","80,556,988","58,679,221"
46489463,BladeCrazy,"127,517,285","24,864,060","6,526,578,201","155,795,233","245,977,724"
"""
    
    try:
        # Validate format
        validation = CSVParser.validate_csv_format(sample_csv)
        
        # Parse CSV
        players = CSVParser.parse_csv(sample_csv)
        
        return {
            "message": "CSV parsing successful!",
            "validation": validation,
            "player_count": len(players),
            "sample_player": players[0].model_dump() if players else None,
            "all_players": [p.model_dump() for p in players]
        }
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__
        }