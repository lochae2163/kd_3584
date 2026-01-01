from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from typing import Optional
from app.services.ml_service import ml_service
from app.database import Database

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/upload/baseline")
async def upload_baseline(
    file: UploadFile = File(...),
    kvk_season_id: str = Query(default="season_1"),
    kingdom_id: str = Query(default="3584")
):
    """
    Upload BASELINE file (CSV or Excel).

    This should be uploaded ONCE at the start of KvK.
    All future comparisons will be made against this baseline.

    Supported formats:
    - CSV files (.csv)
    - Excel files (.xlsx, .xls) - Auto-detects correct sheet
    """
    # Check file extension
    is_csv = file.filename.endswith('.csv')
    is_excel = file.filename.endswith(('.xlsx', '.xls'))

    if not (is_csv or is_excel):
        raise HTTPException(
            status_code=400,
            detail="Only CSV (.csv) or Excel (.xlsx, .xls) files are allowed"
        )

    try:
        content = await file.read()

        # Process based on file type
        if is_csv:
            csv_content = content.decode('utf-8')
            result = await ml_service.process_and_save_baseline(
                csv_content=csv_content,
                kvk_season_id=kvk_season_id,
                file_name=file.filename
            )
        else:  # Excel
            result = await ml_service.process_and_save_baseline_excel(
                excel_bytes=content,
                kvk_season_id=kvk_season_id,
                file_name=file.filename,
                kingdom_id=kingdom_id
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
    description: str = Query(default=""),
    kingdom_id: str = Query(default="3584")
):
    """
    Upload CURRENT data file (CSV or Excel).

    Upload this after each fight to update the leaderboard.
    Deltas will be calculated against the baseline.

    Supported formats:
    - CSV files (.csv)
    - Excel files (.xlsx, .xls) - Auto-detects correct sheet
    """
    # Check file extension
    is_csv = file.filename.endswith('.csv')
    is_excel = file.filename.endswith(('.xlsx', '.xls'))

    if not (is_csv or is_excel):
        raise HTTPException(
            status_code=400,
            detail="Only CSV (.csv) or Excel (.xlsx, .xls) files are allowed"
        )

    try:
        content = await file.read()

        # Process based on file type
        if is_csv:
            csv_content = content.decode('utf-8')
            result = await ml_service.process_and_save_current(
                csv_content=csv_content,
                kvk_season_id=kvk_season_id,
                file_name=file.filename,
                description=description
            )
        else:  # Excel
            result = await ml_service.process_and_save_current_excel(
                excel_bytes=content,
                kvk_season_id=kvk_season_id,
                file_name=file.filename,
                description=description,
                kingdom_id=kingdom_id
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


@router.delete("/delete/baseline/{kvk_season_id}")
async def delete_baseline(kvk_season_id: str):
    """
    Delete baseline data for a season.

    WARNING: This will remove the baseline reference point.
    Current data comparisons will fail without a baseline.
    """
    baseline_col = Database.get_collection("baselines")

    # Check if baseline exists
    baseline = await baseline_col.find_one({"kvk_season_id": kvk_season_id})
    if not baseline:
        raise HTTPException(status_code=404, detail="Baseline not found")

    # Delete baseline
    result = await baseline_col.delete_one({"kvk_season_id": kvk_season_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=500, detail="Failed to delete baseline")

    return {
        "success": True,
        "message": f"Baseline deleted for {kvk_season_id}",
        "deleted_file": baseline.get('file_name'),
        "deleted_player_count": baseline.get('player_count')
    }


@router.delete("/delete/current/{kvk_season_id}")
async def delete_current_data(kvk_season_id: str):
    """
    Delete current data and all upload history for a season.

    This removes:
    - Current data snapshot
    - All upload history entries

    Baseline will remain intact.
    """
    current_col = Database.get_collection("current_data")
    history_col = Database.get_collection("upload_history")

    # Check if current data exists
    current = await current_col.find_one({"kvk_season_id": kvk_season_id})
    if not current:
        raise HTTPException(status_code=404, detail="Current data not found")

    # Delete current data
    current_result = await current_col.delete_one({"kvk_season_id": kvk_season_id})

    # Delete all upload history for this season
    history_result = await history_col.delete_many({"kvk_season_id": kvk_season_id})

    return {
        "success": True,
        "message": f"Current data and history deleted for {kvk_season_id}",
        "deleted_current": current_result.deleted_count > 0,
        "deleted_history_count": history_result.deleted_count,
        "deleted_file": current.get('file_name')
    }


@router.delete("/delete/all/{kvk_season_id}")
async def delete_all_data(kvk_season_id: str):
    """
    Delete ALL data for a season (baseline + current + history).

    WARNING: This is irreversible. All data for this season will be lost.
    Use this to completely reset a season or remove incorrect data.
    """
    baseline_col = Database.get_collection("baselines")
    current_col = Database.get_collection("current_data")
    history_col = Database.get_collection("upload_history")

    # Delete all data
    baseline_result = await baseline_col.delete_many({"kvk_season_id": kvk_season_id})
    current_result = await current_col.delete_many({"kvk_season_id": kvk_season_id})
    history_result = await history_col.delete_many({"kvk_season_id": kvk_season_id})

    total_deleted = baseline_result.deleted_count + current_result.deleted_count + history_result.deleted_count

    if total_deleted == 0:
        raise HTTPException(status_code=404, detail="No data found for this season")

    return {
        "success": True,
        "message": f"All data deleted for {kvk_season_id}",
        "deleted_baseline": baseline_result.deleted_count,
        "deleted_current": current_result.deleted_count,
        "deleted_history": history_result.deleted_count,
        "total_deleted": total_deleted
    }