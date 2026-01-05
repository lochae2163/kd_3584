from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from typing import Optional
from bson import ObjectId
from app.services.ml_service import ml_service
from app.services.season_service import season_service
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
    # Check if season is archived (read-only protection)
    is_archived = await season_service.is_season_archived(kvk_season_id)
    if is_archived:
        raise HTTPException(
            status_code=403,
            detail=f"Season {kvk_season_id} is archived and cannot be modified"
        )

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

        # Update season stats after baseline upload
        await season_service.update_season_stats(kvk_season_id)

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
    # Check if season is archived (read-only protection)
    is_archived = await season_service.is_season_archived(kvk_season_id)
    if is_archived:
        raise HTTPException(
            status_code=403,
            detail=f"Season {kvk_season_id} is archived and cannot be modified"
        )

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

        # Update season stats after current data upload
        await season_service.update_season_stats(kvk_season_id)

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


@router.delete("/delete/history/{history_id}")
async def delete_history_entry(history_id: str):
    """
    Delete a specific upload history entry by its ID.

    This allows selective deletion of individual uploads from history.
    The current leaderboard will NOT be affected unless this was the most recent upload.
    """
    history_col = Database.get_collection("upload_history")

    try:
        # Convert string ID to ObjectId
        obj_id = ObjectId(history_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid history ID format")

    # Find the history entry first to get its info
    history_entry = await history_col.find_one({"_id": obj_id})

    if not history_entry:
        raise HTTPException(status_code=404, detail="History entry not found")

    # Delete the history entry
    result = await history_col.delete_one({"_id": obj_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Failed to delete history entry")

    return {
        "success": True,
        "message": "History entry deleted successfully",
        "deleted_file": history_entry.get("file_name", "Unknown"),
        "deleted_timestamp": history_entry.get("timestamp")
    }


@router.get("/find-player-history/{kvk_season_id}/{governor_id}")
async def find_player_history(kvk_season_id: str, governor_id: str):
    """
    Search upload history to find when a player first appeared with stats.

    Returns all uploads where the player appears, showing their stats progression.
    """
    try:
        history_col = Database.get_collection("upload_history")
        uploads = await history_col.find(
            {"kvk_season_id": kvk_season_id}
        ).sort("timestamp", 1).to_list(length=100)

        player_appearances = []
        first_with_stats = None

        for idx, upload in enumerate(uploads, 1):
            players = upload.get('players', [])
            player = next((p for p in players if p['governor_id'] == governor_id), None)

            if player:
                stats = player.get('stats', {})
                has_kvk_stats = any(stats.get(field, 0) > 0 for field in ['kill_points', 'deads', 't4_kills', 't5_kills'])

                appearance = {
                    "upload_index": idx,
                    "upload_id": str(upload['_id']),
                    "timestamp": upload.get('timestamp'),
                    "description": upload.get('description'),
                    "stats": stats,
                    "has_kvk_stats": has_kvk_stats
                }

                player_appearances.append(appearance)

                if has_kvk_stats and not first_with_stats:
                    first_with_stats = appearance

        return {
            "success": True,
            "governor_id": governor_id,
            "kvk_season_id": kvk_season_id,
            "total_appearances": len(player_appearances),
            "first_appearance_with_stats": first_with_stats,
            "all_appearances": player_appearances
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search history: {str(e)}"
        )


@router.post("/reprocess-deltas/{kvk_season_id}")
async def reprocess_deltas(kvk_season_id: str):
    """
    Re-process current data to fix delta calculations.

    This endpoint:
    - Re-calculates deltas for all players
    - Fixes negative deltas for migrated out/back players
    - Updates baseline with new/returning players

    Use this after updating the delta calculation logic or to fix data issues.
    """
    try:
        # Get baseline
        baselines_col = Database.get_collection("baselines")
        baseline = await baselines_col.find_one({"kvk_season_id": kvk_season_id})

        if not baseline:
            raise HTTPException(
                status_code=404,
                detail=f"No baseline found for season {kvk_season_id}"
            )

        # Get current data
        current_col = Database.get_collection("current_data")
        current_data = await current_col.find_one({"kvk_season_id": kvk_season_id})

        if not current_data:
            raise HTTPException(
                status_code=404,
                detail=f"No current data found for season {kvk_season_id}"
            )

        # Re-calculate deltas using ML service
        players_with_deltas = ml_service.model.calculate_all_deltas(
            baseline.get('players', []),
            current_data.get('players', [])
        )

        # Update current_data
        await current_col.update_one(
            {"kvk_season_id": kvk_season_id},
            {"$set": {"players": players_with_deltas}}
        )

        # Update baseline with new/returning players
        new_players = [p for p in players_with_deltas if p.get('newly_added_to_baseline', False)]
        if new_players:
            baseline_players = baseline.get('players', [])

            for new_player in new_players:
                # Check if already in baseline
                existing_idx = next((i for i, p in enumerate(baseline_players)
                                   if p['governor_id'] == new_player['governor_id']), None)

                baseline_entry = {
                    "governor_id": new_player['governor_id'],
                    "governor_name": new_player['governor_name'],
                    "stats": new_player['stats']
                }

                if existing_idx is not None:
                    # Update existing entry (player returned/reset)
                    baseline_players[existing_idx] = baseline_entry
                else:
                    # Add new entry
                    baseline_players.append(baseline_entry)

            await baselines_col.update_one(
                {"kvk_season_id": kvk_season_id},
                {"$set": {"players": baseline_players}}
            )

        return {
            "success": True,
            "message": "Delta recalculation completed successfully",
            "kvk_season_id": kvk_season_id,
            "players_processed": len(players_with_deltas),
            "new_or_reset_players": len(new_players)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reprocess deltas: {str(e)}"
        )