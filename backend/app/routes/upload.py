from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from typing import Optional
from app.services.ml_service import ml_service
from app.database import Database

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/upload/baseline")
async def upload_baseline(
    file: UploadFile = File(...),
    kvk_season_id: str = Query(default="season_1")
):
    """
    Upload BASELINE CSV file.
    
    This should be uploaded ONCE at the start of KvK.
    All future comparisons will be made against this baseline.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    try:
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        result = await ml_service.process_and_save_baseline(
            csv_content=csv_content,
            kvk_season_id=kvk_season_id,
            file_name=file.filename
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error'))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/current")
async def upload_current(
    file: UploadFile = File(...),
    kvk_season_id: str = Query(default="season_1"),
    description: str = Query(default="")
):
    """
    Upload CURRENT data CSV file.
    
    Upload this after each fight to update the leaderboard.
    Deltas will be calculated against the baseline.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    try:
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        result = await ml_service.process_and_save_current(
            csv_content=csv_content,
            kvk_season_id=kvk_season_id,
            file_name=file.filename,
            description=description
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error'))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/baseline/{kvk_season_id}")
async def get_baseline(kvk_season_id: str):
    """Get baseline info for a season."""
    collection = Database.get_collection("baselines")
    baseline = await collection.find_one({"kvk_season_id": kvk_season_id})
    
    if not baseline:
        raise HTTPException(status_code=404, detail="Baseline not found")
    
    return {
        "kvk_season_id": baseline.get('kvk_season_id'),
        "file_name": baseline.get('file_name'),
        "timestamp": baseline.get('timestamp'),
        "player_count": baseline.get('player_count')
    }


@router.get("/data-status/{kvk_season_id}")
async def get_data_status(kvk_season_id: str):
    """Get status of baseline and current data for a season."""
    baseline_col = Database.get_collection("baselines")
    current_col = Database.get_collection("current_data")
    
    baseline = await baseline_col.find_one({"kvk_season_id": kvk_season_id})
    current = await current_col.find_one({"kvk_season_id": kvk_season_id})
    
    return {
        "kvk_season_id": kvk_season_id,
        "has_baseline": baseline is not None,
        "baseline_info": {
            "file_name": baseline.get('file_name'),
            "timestamp": baseline.get('timestamp'),
            "player_count": baseline.get('player_count')
        } if baseline else None,
        "has_current": current is not None,
        "current_info": {
            "file_name": current.get('file_name'),
            "timestamp": current.get('timestamp'),
            "player_count": current.get('player_count'),
            "description": current.get('description')
        } if current else None
    }
@router.get("/history/{kvk_season_id}")
async def get_upload_history(kvk_season_id: str):
    """Get upload history for a season."""
    collection = Database.get_collection("upload_history")
    
    cursor = collection.find(
        {"kvk_season_id": kvk_season_id}
    ).sort("timestamp", -1)
    
    history = await cursor.to_list(length=100)
    
    # Convert ObjectId to string
    for item in history:
        item["_id"] = str(item["_id"])
    
    return {
        "kvk_season_id": kvk_season_id,
        "count": len(history),
        "history": history
    }