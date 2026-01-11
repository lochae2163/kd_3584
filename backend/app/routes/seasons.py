"""
Season management API routes
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from app.services.season_service import season_service
from app.services.auth_service import get_current_admin
from app.models.season import CreateSeasonRequest, ActivateSeasonRequest, ArchiveSeasonRequest
from typing import List, Dict

# Admin-only season management routes
admin_router = APIRouter(prefix="/admin/seasons", tags=["Season Management"])

# Public season info routes
public_router = APIRouter(prefix="/api/seasons", tags=["Seasons"])


# ============== PUBLIC ROUTES (No Auth Required) ==============

@public_router.get("/active")
async def get_active_season():
    """
    Get the currently active season

    Returns the season that is currently accepting data uploads
    """
    active_season = await season_service.get_active_season()

    if not active_season:
        raise HTTPException(status_code=404, detail="No active season found")

    return {
        "success": True,
        "season_id": active_season.get('season_id'),
        "season_name": active_season.get('season_name'),
        "status": active_season.get('status'),
        "start_date": active_season.get('start_date'),
        "final_data_uploaded": active_season.get('final_data_uploaded', False)
    }


@public_router.get("/all")
async def get_all_seasons():
    """
    Get all seasons, sorted by newest first

    Returns list of all KvK seasons in the system
    """
    seasons = await season_service.get_all_seasons()

    return {
        "success": True,
        "count": len(seasons),
        "seasons": seasons
    }


@public_router.get("/{season_id}")
async def get_season(season_id: str):
    """
    Get a specific season by ID

    Returns detailed season information
    """
    season = await season_service.get_season(season_id)

    if not season:
        raise HTTPException(status_code=404, detail=f"Season {season_id} not found")

    return {
        "success": True,
        "season": season
    }


@public_router.get("/{season_id}/stats")
async def get_season_stats(season_id: str):
    """
    Get season statistics

    Returns upload counts, player counts, and data status
    """
    # Update stats first
    await season_service.update_season_stats(season_id)

    # Get season
    season = await season_service.get_season(season_id)

    if not season:
        raise HTTPException(status_code=404, detail=f"Season {season_id} not found")

    return {
        "success": True,
        "season_id": season_id,
        "stats": {
            "has_baseline": season.get('has_baseline', False),
            "has_current_data": season.get('has_current_data', False),
            "final_data_uploaded": season.get('final_data_uploaded', False),
            "total_uploads": season.get('total_uploads', 0),
            "player_count": season.get('player_count', 0),
            "status": season.get('status'),
            "is_active": season.get('is_active', False),
            "is_archived": season.get('is_archived', False)
        }
    }


# ============== ADMIN ROUTES (Auth Required) ==============

@admin_router.post("/create")
async def create_season(
    request: CreateSeasonRequest,
    current_admin: str = Depends(get_current_admin)
):
    """
    Create a new KvK season

    - Auto-generates season_id (season_1, season_2, etc.)
    - Sets status to 'preparing'
    - Does NOT activate automatically
    """
    result = await season_service.create_season(
        season_name=request.season_name,
        description=request.description,
        start_date=request.start_date,
        kingdom_id=request.kingdom_id
    )

    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('error'))

    return result


@admin_router.post("/activate")
async def activate_season(
    request: ActivateSeasonRequest,
    current_admin: str = Depends(get_current_admin)
):
    """
    Activate a season

    - Deactivates all other seasons
    - Sets this season as active
    - All future uploads will go to this season
    """
    result = await season_service.activate_season(request.season_id)

    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('error'))

    return result


@admin_router.post("/archive")
async def archive_season(
    request: ArchiveSeasonRequest,
    current_admin: str = Depends(get_current_admin)
):
    """
    Archive a season (mark as read-only)

    - Season becomes locked for editing
    - Cannot upload new data
    - Can still view historical data
    - Requires confirmation
    """
    if not request.confirm:
        raise HTTPException(
            status_code=400,
            detail="Confirmation required to archive season"
        )

    result = await season_service.archive_season(request.season_id)

    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('error'))

    return result


@admin_router.post("/{season_id}/mark-final-uploaded")
async def mark_final_data_uploaded(
    season_id: str,
    current_admin: str = Depends(get_current_admin)
):
    """
    Mark that final comprehensive data has been uploaded

    - Sets final_data_uploaded = True
    - Changes status to 'completed'
    - Prepares season for archiving
    """
    result = await season_service.mark_final_data_uploaded(season_id)

    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('error'))

    return result


@admin_router.post("/{season_id}/update-dates")
async def update_season_dates(
    season_id: str,
    request: dict,
    current_admin: str = Depends(get_current_admin)
):
    """
    Update season start and end dates

    - Allows manual editing of season dates
    - Dates are used across all season data displays
    """
    start_date = request.get('start_date')
    end_date = request.get('end_date')

    result = await season_service.update_season_dates(season_id, start_date, end_date)

    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('error'))

    return result
